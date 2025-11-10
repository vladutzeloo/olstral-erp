from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import (ProductionOrder, ProductionConsumption, BillOfMaterials, Item, Location, User)
from filter_utils import TableFilter
from production_utils import (start_production, complete_production,
                              get_production_traceability, calculate_production_requirements)

production_orders_bp = Blueprint('production_orders', __name__)

@production_orders_bp.route('/')
@login_required
def index():
    """List all production orders"""
    # Initialize filter
    table_filter = TableFilter(ProductionOrder, request.args)

    # Add filters
    table_filter.add_filter('finished_item_id', operator='eq')
    table_filter.add_filter('location_id', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('created_by', operator='eq')
    table_filter.add_date_filter('start_date')
    table_filter.add_search(['order_number', 'notes'])

    # Apply filters
    query = ProductionOrder.query
    query = table_filter.apply(query)
    orders = query.order_by(ProductionOrder.created_at.desc()).all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'finished_item_id',
                'label': 'Finished Item',
                'options': [{'value': item.id, 'label': f"{item.sku} - {item.name}"}
                           for item in Item.query.filter_by(is_active=True).order_by(Item.sku).all()]
            },
            {
                'name': 'location_id',
                'label': 'Location',
                'options': [{'value': loc.id, 'label': f"{loc.code} - {loc.name}"}
                           for loc in Location.query.filter_by(is_active=True).order_by(Location.code).all()]
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'draft', 'label': 'Draft'},
                    {'value': 'released', 'label': 'Released'},
                    {'value': 'in_progress', 'label': 'In Progress'},
                    {'value': 'completed', 'label': 'Completed'},
                    {'value': 'cancelled', 'label': 'Cancelled'}
                ]
            },
            {
                'name': 'created_by',
                'label': 'Created By',
                'options': [{'value': u.id, 'label': u.username} for u in User.query.order_by(User.username).all()]
            }
        ],
        'date_ranges': [
            {'name': 'start_date', 'label': 'Start Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('production_orders/index.html',
                         orders=orders,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())


@production_orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new production order"""
    if request.method == 'POST':
        try:
            import json

            # Get custom order number or generate one
            order_number = request.form.get('order_number', '').strip()
            if not order_number:
                last_order = ProductionOrder.query.order_by(ProductionOrder.id.desc()).first()
                if last_order:
                    last_num = int(last_order.order_number.split('-')[-1])
                    order_number = f"PROD-{last_num + 1:06d}"
                else:
                    order_number = "PROD-000001"

            # Check if order number already exists
            existing = ProductionOrder.query.filter_by(order_number=order_number).first()
            if existing:
                flash(f'Production order number {order_number} already exists!', 'danger')
                return redirect(url_for('production_orders.new'))

            # Get form data
            production_mode = request.form.get('production_mode')
            finished_item_id = request.form.get('finished_item_id')
            quantity_ordered = int(request.form.get('quantity_ordered'))
            location_id = request.form.get('location_id')
            start_date_str = request.form.get('start_date')
            due_date_str = request.form.get('due_date')

            # Validate
            if not finished_item_id or not quantity_ordered or not location_id:
                flash('Please fill in all required fields', 'danger')
                return redirect(url_for('production_orders.new'))

            # Parse dates
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None

            # Handle BOM vs Manual mode
            bom_id = None
            manual_components_json = None

            if production_mode == 'bom':
                bom_id = request.form.get('bom_id')
                if not bom_id:
                    flash('Please select a BOM', 'danger')
                    return redirect(url_for('production_orders.new'))
                bom_id = int(bom_id)
            else:  # manual mode
                # Get manual components
                component_ids = request.form.getlist('component_item_id[]')
                component_quantities = request.form.getlist('component_quantity[]')

                manual_components = []
                for i, comp_id in enumerate(component_ids):
                    if comp_id and component_quantities[i]:
                        manual_components.append({
                            'item_id': int(comp_id),
                            'quantity': float(component_quantities[i])
                        })

                if not manual_components:
                    flash('Please add at least one component', 'danger')
                    return redirect(url_for('production_orders.new'))

                manual_components_json = json.dumps(manual_components)

            # Create production order
            production_order = ProductionOrder(
                order_number=order_number,
                finished_item_id=int(finished_item_id),
                bom_id=bom_id,
                location_id=int(location_id),
                quantity_ordered=quantity_ordered,
                manual_components=manual_components_json,
                start_date=start_date,
                due_date=due_date,
                status='draft',
                notes=request.form.get('notes'),
                created_by=current_user.id
            )

            db.session.add(production_order)
            db.session.commit()

            flash(f'Production Order {order_number} created successfully!', 'success')
            return redirect(url_for('production_orders.view', id=production_order.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating production order: {str(e)}', 'danger')
            return redirect(url_for('production_orders.new'))

    # Get data for form
    items = Item.query.filter_by(is_active=True).order_by(Item.sku).all()
    boms = BillOfMaterials.query.filter_by(status='active').order_by(BillOfMaterials.bom_number).all()
    locations = Location.query.filter(
        Location.is_active == True,
        Location.type.in_(['production', 'warehouse'])
    ).order_by(Location.code).all()

    return render_template('production_orders/new.html', items=items, boms=boms, locations=locations)


@production_orders_bp.route('/<int:id>')
@login_required
def view(id):
    """View production order details"""
    order = ProductionOrder.query.get_or_404(id)

    # Get traceability info if production has started
    traceability = None
    if order.status in ['in_progress', 'completed']:
        traceability = get_production_traceability(id)

    return render_template('production_orders/view.html', order=order, traceability=traceability)


@production_orders_bp.route('/<int:id>/release', methods=['POST'])
@login_required
def release(id):
    """Release production order (make it ready to start)"""
    order = ProductionOrder.query.get_or_404(id)

    if order.status != 'draft':
        flash('Only draft orders can be released', 'danger')
        return redirect(url_for('production_orders.view', id=id))

    order.status = 'released'
    db.session.commit()

    flash(f'Production Order {order.order_number} released!', 'success')
    return redirect(url_for('production_orders.view', id=id))


@production_orders_bp.route('/<int:id>/start', methods=['POST'])
@login_required
def start(id):
    """Start production - consumes components using FIFO"""
    order = ProductionOrder.query.get_or_404(id)

    try:
        result = start_production(id, current_user.id)

        flash(result['message'], 'success')
        flash(f"Material cost (FIFO): ${result['total_material_cost']:.2f}", 'info')

        return redirect(url_for('production_orders.view', id=id))

    except ValueError as e:
        flash(f'Cannot start production: {str(e)}', 'danger')
        return redirect(url_for('production_orders.view', id=id))
    except Exception as e:
        flash(f'Error starting production: {str(e)}', 'danger')
        return redirect(url_for('production_orders.view', id=id))


@production_orders_bp.route('/<int:id>/complete', methods=['GET', 'POST'])
@login_required
def complete(id):
    """Complete production - create receipt for finished goods"""
    order = ProductionOrder.query.get_or_404(id)

    if request.method == 'POST':
        try:
            quantity_produced = int(request.form.get('quantity_produced', 0))
            quantity_scrapped = int(request.form.get('quantity_scrapped', 0))
            scrap_reason = request.form.get('scrap_reason')

            result = complete_production(id, quantity_produced, quantity_scrapped, current_user.id, scrap_reason)

            flash(result['message'], 'success')
            flash(f"Receipt: {result['receipt_number']}, Batch: {result['batch_number']}", 'info')
            flash(f"Cost per unit (FIFO): ${result['cost_per_unit']:.2f}", 'info')

            return redirect(url_for('production_orders.view', id=id))

        except ValueError as e:
            flash(f'Cannot complete production: {str(e)}', 'danger')
            return redirect(url_for('production_orders.complete', id=id))
        except Exception as e:
            flash(f'Error completing production: {str(e)}', 'danger')
            return redirect(url_for('production_orders.complete', id=id))

    # Show completion form
    remaining_quantity = order.quantity_ordered - order.quantity_produced - order.quantity_scrapped
    return render_template('production_orders/complete.html', order=order, remaining_quantity=remaining_quantity)


@production_orders_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    """Cancel production order"""
    order = ProductionOrder.query.get_or_404(id)

    if order.status == 'completed':
        flash('Cannot cancel completed order', 'danger')
        return redirect(url_for('production_orders.view', id=id))

    if order.status == 'in_progress':
        flash('Cannot cancel order in progress. Complete or contact admin.', 'danger')
        return redirect(url_for('production_orders.view', id=id))

    order.status = 'cancelled'
    db.session.commit()

    flash(f'Production Order {order.order_number} cancelled', 'warning')
    return redirect(url_for('production_orders.view', id=id))


@production_orders_bp.route('/api/bom_items/<int:bom_id>')
@login_required
def get_bom_items(bom_id):
    """API endpoint to get BOM components for production planning"""
    bom = BillOfMaterials.query.get_or_404(bom_id)

    components = []
    for component in bom.components:
        components.append({
            'component_id': component.component_item_id,
            'sku': component.component.sku,
            'name': component.component.name,
            'quantity_per_unit': component.quantity,
            'unit_of_measure': component.unit_of_measure or component.component.unit_of_measure
        })

    return jsonify({
        'success': True,
        'bom_number': bom.bom_number,
        'finished_item': {
            'id': bom.finished_item_id,
            'sku': bom.finished_item.sku,
            'name': bom.finished_item.name
        },
        'components': components
    })


@production_orders_bp.route('/api/requirements/<int:bom_id>/<int:quantity>')
@login_required
def get_requirements(bom_id, quantity):
    """API endpoint to check component availability for production"""
    location_id = request.args.get('location_id', type=int)

    if not location_id:
        return jsonify({'success': False, 'error': 'Location required'}), 400

    try:
        requirements = calculate_production_requirements(bom_id, quantity, location_id)
        return jsonify({'success': True, 'requirements': requirements})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
