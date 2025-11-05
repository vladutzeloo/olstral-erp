from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from extensions import db
from models import ExternalProcess, Supplier, Item, InventoryLocation, InventoryTransaction, Location, User
from filter_utils import TableFilter

external_processes_bp = Blueprint('external_processes', __name__)

@external_processes_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(ExternalProcess, request.args)

    # Add filters
    table_filter.add_filter('supplier_id', operator='eq')
    table_filter.add_filter('process_type', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('creates_new_sku', operator='eq')
    table_filter.add_filter('created_by', operator='eq')
    table_filter.add_date_filter('sent_date')
    table_filter.add_date_filter('expected_return')
    table_filter.add_search(['process_number', 'process_result', 'notes'])

    # Apply filters
    query = ExternalProcess.query
    query = table_filter.apply(query)
    processes = query.order_by(ExternalProcess.created_at.desc()).all()

    # Get unique process types for filter
    process_types = db.session.query(ExternalProcess.process_type).distinct().all()
    process_type_options = [{'value': pt[0], 'label': pt[0]} for pt in process_types if pt[0]]

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'supplier_id',
                'label': 'Supplier',
                'options': [{'value': s.id, 'label': s.name}
                           for s in Supplier.query.filter_by(is_external_processor=True).order_by(Supplier.name).all()]
            },
            {
                'name': 'process_type',
                'label': 'Process Type',
                'options': process_type_options
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'sent', 'label': 'Sent'},
                    {'value': 'in_progress', 'label': 'In Progress'},
                    {'value': 'completed', 'label': 'Completed'},
                    {'value': 'cancelled', 'label': 'Cancelled'}
                ]
            },
            {
                'name': 'creates_new_sku',
                'label': 'Transforms SKU',
                'options': [
                    {'value': '1', 'label': 'Yes - Creates New SKU'},
                    {'value': '0', 'label': 'No - Same SKU'}
                ]
            },
            {
                'name': 'created_by',
                'label': 'Created By',
                'options': [{'value': u.id, 'label': u.username} for u in User.query.order_by(User.username).all()]
            }
        ],
        'date_ranges': [
            {'name': 'sent_date', 'label': 'Sent Date'},
            {'name': 'expected_return', 'label': 'Expected Return'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('external_processes/index.html',
                         processes=processes,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

@external_processes_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        try:
            # Generate process number
            last_process = ExternalProcess.query.order_by(ExternalProcess.id.desc()).first()
            if last_process:
                last_num = int(last_process.process_number.split('-')[-1])
                process_number = f"EXT-{last_num + 1:06d}"
            else:
                process_number = "EXT-000001"
            
            item_id = int(request.form.get('item_id'))
            location_id = int(request.form.get('location_id'))
            quantity = int(request.form.get('quantity_sent'))
            supplier_id = int(request.form.get('supplier_id'))
            process_type = request.form.get('process_type')
            process_result = request.form.get('process_result', '').strip()
            
            # Check if this creates a new SKU (transformation)
            creates_new_sku = request.form.get('creates_new_sku') == 'yes'
            returned_item_id = None
            
            if creates_new_sku:
                returned_item_id = request.form.get('returned_item_id')
                if returned_item_id:
                    returned_item_id = int(returned_item_id)
                else:
                    # Need to create new item for the transformed product
                    flash('Please select or create the item that will be returned after processing', 'warning')
                    suppliers = Supplier.query.filter_by(is_active=True, is_external_processor=True).all()
                    items = Item.query.filter_by(is_active=True).all()
                    locations = Location.query.filter_by(is_active=True).all()
                    return render_template('external_processes/new.html', 
                                         suppliers=suppliers, items=items, locations=locations)
            
            # Check inventory availability
            inv_loc = InventoryLocation.query.filter_by(
                item_id=item_id,
                location_id=location_id
            ).first()
            
            if not inv_loc or inv_loc.quantity < quantity:
                flash('Insufficient quantity at selected location!', 'danger')
                suppliers = Supplier.query.filter_by(is_active=True).all()
                items = Item.query.filter_by(is_active=True).all()
                locations = Location.query.filter_by(is_active=True).all()
                return render_template('external_processes/new.html', 
                                     suppliers=suppliers, items=items, locations=locations)
            
            # Calculate expected return date
            expected_return = None
            if request.form.get('expected_return'):
                expected_return = datetime.strptime(request.form.get('expected_return'), '%Y-%m-%d')
            else:
                # Auto-calculate based on supplier's typical lead time
                supplier = Supplier.query.get(supplier_id)
                if supplier and supplier.typical_lead_time_days:
                    expected_return = datetime.utcnow() + timedelta(days=supplier.typical_lead_time_days)
            
            process = ExternalProcess(
                process_number=process_number,
                item_id=item_id,
                returned_item_id=returned_item_id,
                supplier_id=supplier_id,
                quantity_sent=quantity,
                process_type=process_type,
                process_result=process_result,
                creates_new_sku=creates_new_sku,
                sent_date=datetime.utcnow(),
                expected_return=expected_return,
                cost=float(request.form.get('cost', 0)),
                notes=request.form.get('notes'),
                created_by=current_user.id,
                status='sent'
            )
            
            db.session.add(process)
            db.session.flush()
            
            # Deduct from inventory
            inv_loc.quantity -= quantity
            
            # Create transaction
            transaction = InventoryTransaction(
                item_id=item_id,
                location_id=location_id,
                transaction_type='process_out',
                quantity=-quantity,
                reference_type='external_process',
                reference_id=process.id,
                notes=f"Sent for {process_type}" + (f" - {process_result}" if process_result else ""),
                created_by=current_user.id
            )
            db.session.add(transaction)
            
            db.session.commit()
            
            flash(f'External Process {process_number} created successfully!', 'success')
            return redirect(url_for('external_processes.view', id=process.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating external process: {str(e)}', 'danger')
            return redirect(url_for('external_processes.new'))
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    external_processors = Supplier.query.filter_by(is_active=True, is_external_processor=True).all()
    items = Item.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    
    return render_template('external_processes/new.html', 
                         suppliers=suppliers, 
                         external_processors=external_processors,
                         items=items, 
                         locations=locations)

@external_processes_bp.route('/search_items')
@login_required
def search_items():
    query = request.args.get('q', '').strip()
    location_id = request.args.get('location_id', '').strip()
    
    if len(query) < 2 or not location_id:
        return jsonify([])
    
    # Search for items with inventory at the specified location
    items = Item.query.join(InventoryLocation).filter(
        db.or_(
            Item.sku.ilike(f'%{query}%'),
            Item.name.ilike(f'%{query}%')
        ),
        Item.is_active == True,
        InventoryLocation.location_id == int(location_id),
        InventoryLocation.quantity > 0
    ).limit(20).all()
    
    results = []
    for item in items:
        inv_loc = InventoryLocation.query.filter_by(
            item_id=item.id,
            location_id=int(location_id)
        ).first()
        
        if inv_loc and inv_loc.quantity > 0:
            results.append({
                'id': item.id,
                'sku': item.sku,
                'name': item.name,
                'available': inv_loc.quantity,
                'label': f"{item.sku} - {item.name} (Available: {inv_loc.quantity})"
            })
    
    return jsonify(results)

@external_processes_bp.route('/search_all_items')
@login_required
def search_all_items():
    """Search all items for returned item selection (not location-dependent)"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    items = Item.query.filter(
        db.or_(
            Item.sku.ilike(f'%{query}%'),
            Item.name.ilike(f'%{query}%')
        ),
        Item.is_active == True
    ).limit(20).all()
    
    results = [{
        'id': item.id,
        'sku': item.sku,
        'name': item.name,
        'label': f"{item.sku} - {item.name}"
    } for item in items]
    
    return jsonify(results)

@external_processes_bp.route('/get_supplier_info/<int:supplier_id>')
@login_required
def get_supplier_info(supplier_id):
    """Get supplier details including typical processes and lead times"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    return jsonify({
        'name': supplier.name,
        'is_external_processor': supplier.is_external_processor,
        'typical_lead_time_days': supplier.typical_lead_time_days,
        'typical_process_types': supplier.typical_process_types.split(',') if supplier.typical_process_types else [],
        'shipping_account': supplier.shipping_account,
        'pickup_instructions': supplier.pickup_instructions
    })

@external_processes_bp.route('/<int:id>')
@login_required
def view(id):
    process = ExternalProcess.query.get_or_404(id)
    return render_template('external_processes/view.html', process=process)

@external_processes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    process = ExternalProcess.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            process.process_type = request.form.get('process_type')
            process.process_result = request.form.get('process_result', '').strip()
            process.expected_return = datetime.strptime(request.form.get('expected_return'), '%Y-%m-%d') if request.form.get('expected_return') else None
            process.cost = float(request.form.get('cost', 0))
            process.notes = request.form.get('notes')
            
            # Allow updating returned item if not yet received
            if process.quantity_returned == 0:
                creates_new_sku = request.form.get('creates_new_sku') == 'yes'
                process.creates_new_sku = creates_new_sku
                
                if creates_new_sku:
                    returned_item_id = request.form.get('returned_item_id')
                    if returned_item_id:
                        process.returned_item_id = int(returned_item_id)
                else:
                    process.returned_item_id = None
            
            db.session.commit()
            
            flash(f'External Process {process.process_number} updated successfully!', 'success')
            return redirect(url_for('external_processes.view', id=process.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating process: {str(e)}', 'danger')
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    return render_template('external_processes/edit.html', process=process, suppliers=suppliers, items=items)

@external_processes_bp.route('/<int:id>/cancel')
@login_required
def cancel(id):
    process = ExternalProcess.query.get_or_404(id)
    
    if process.quantity_returned > 0:
        flash('Cannot cancel process that has already received items!', 'danger')
        return redirect(url_for('external_processes.view', id=process.id))
    
    process.status = 'cancelled'
    db.session.commit()
    
    flash(f'External Process {process.process_number} cancelled!', 'warning')
    return redirect(url_for('external_processes.view', id=process.id))
