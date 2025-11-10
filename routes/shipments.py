from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import Shipment, ShipmentItem, Location, Item, InventoryLocation, InventoryTransaction, User, Client
from filter_utils import TableFilter
from batch_utils import consume_batches_fifo, calculate_fifo_cost

shipments_bp = Blueprint('shipments', __name__)

@shipments_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(Shipment, request.args)

    # Add filters
    table_filter.add_filter('from_location_id', operator='eq')
    table_filter.add_filter('client_id', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('created_by', operator='eq')
    table_filter.add_date_filter('ship_date')
    table_filter.add_search(['shipment_number', 'customer_name', 'tracking_number', 'notes'])

    # Apply filters
    query = Shipment.query
    query = table_filter.apply(query)
    shipments = query.order_by(Shipment.created_at.desc()).all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'from_location_id',
                'label': 'From Location',
                'options': [{'value': loc.id, 'label': f"{loc.code} - {loc.name}"}
                           for loc in Location.query.filter_by(is_active=True).order_by(Location.code).all()]
            },
            {
                'name': 'client_id',
                'label': 'Client',
                'options': [{'value': c.id, 'label': c.name} for c in Client.query.order_by(Client.name).all()]
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'pending', 'label': 'Pending'},
                    {'value': 'shipped', 'label': 'Shipped'},
                    {'value': 'delivered', 'label': 'Delivered'},
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
            {'name': 'ship_date', 'label': 'Ship Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('shipments/index.html',
                         shipments=shipments,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

@shipments_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Generate shipment number
        last_shipment = Shipment.query.order_by(Shipment.id.desc()).first()
        if last_shipment:
            last_num = int(last_shipment.shipment_number.split('-')[-1])
            shipment_number = f"SHP-{last_num + 1:06d}"
        else:
            shipment_number = "SHP-000001"
        
        from_location_id = request.form.get('from_location_id')
        
        shipment = Shipment(
            shipment_number=shipment_number,
            from_location_id=from_location_id,
            customer_name=request.form.get('customer_name'),
            shipping_address=request.form.get('shipping_address'),
            ship_date=datetime.utcnow(),
            tracking_number=request.form.get('tracking_number'),
            notes=request.form.get('notes'),
            created_by=current_user.id,
            status='pending'
        )
        
        db.session.add(shipment)
        db.session.flush()
        
        # Process shipment items
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')

        all_items_available = True

        for item_id, qty in zip(item_ids, quantities):
            if item_id and qty and int(qty) > 0:
                # Check inventory
                inv_loc = InventoryLocation.query.filter_by(
                    item_id=int(item_id),
                    location_id=from_location_id
                ).first()

                if not inv_loc or inv_loc.quantity < int(qty):
                    item = Item.query.get(int(item_id))
                    flash(f'Insufficient quantity for {item.name} at selected location!', 'danger')
                    all_items_available = False
                    break

                # Create shipment item
                shipment_item = ShipmentItem(
                    shipment_id=shipment.id,
                    item_id=int(item_id),
                    quantity=int(qty)
                )
                db.session.add(shipment_item)

                # Consume batches using FIFO
                try:
                    consumed_batches = consume_batches_fifo(
                        item_id=int(item_id),
                        quantity_needed=int(qty),
                        location_id=from_location_id,
                        reference_type='shipment',
                        reference_id=shipment.id,
                        notes=f"Shipment {shipment_number}",
                        created_by=current_user.id
                    )

                    # Calculate FIFO cost
                    fifo_cost = calculate_fifo_cost(consumed_batches)

                    # Deduct from inventory
                    inv_loc.quantity -= int(qty)

                    # Create transaction with FIFO cost information
                    transaction = InventoryTransaction(
                        item_id=int(item_id),
                        location_id=from_location_id,
                        transaction_type='shipment',
                        quantity=-int(qty),
                        reference_type='shipment',
                        reference_id=shipment.id,
                        notes=f"FIFO cost: {fifo_cost['total_cost']:.2f} ({len(consumed_batches)} batches)",
                        created_by=current_user.id
                    )
                    db.session.add(transaction)

                except ValueError as e:
                    flash(f'Error consuming batches: {str(e)}', 'danger')
                    all_items_available = False
                    break
        
        if not all_items_available:
            db.session.rollback()
            locations = Location.query.filter_by(is_active=True).all()
            items = Item.query.filter_by(is_active=True).all()
            return render_template('shipments/new.html', locations=locations, items=items)
        
        db.session.commit()
        
        flash(f'Shipment {shipment_number} created successfully!', 'success')
        return redirect(url_for('shipments.view', id=shipment.id))
    
    locations = Location.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    return render_template('shipments/new.html', locations=locations, items=items)

@shipments_bp.route('/<int:id>')
@login_required
def view(id):
    shipment = Shipment.query.get_or_404(id)
    return render_template('shipments/view.html', shipment=shipment)

@shipments_bp.route('/<int:id>/ship')
@login_required
def ship(id):
    shipment = Shipment.query.get_or_404(id)
    shipment.status = 'shipped'
    db.session.commit()
    
    flash(f'Shipment {shipment.shipment_number} marked as shipped!', 'success')
    return redirect(url_for('shipments.view', id=shipment.id))

@shipments_bp.route('/<int:id>/deliver')
@login_required
def deliver(id):
    shipment = Shipment.query.get_or_404(id)
    shipment.status = 'delivered'
    db.session.commit()
    
    flash(f'Shipment {shipment.shipment_number} marked as delivered!', 'success')
    return redirect(url_for('shipments.view', id=shipment.id))
