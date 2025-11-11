from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import InventoryLocation, Location, Item, InventoryTransaction, Batch
from filter_utils import TableFilter

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(InventoryLocation, request.args)

    # Add filters
    table_filter.add_filter('item_id', operator='eq')
    table_filter.add_filter('location_id', operator='eq')
    table_filter.add_search(['bin_location'])

    # Apply filters
    query = InventoryLocation.query.join(Item).join(Location)
    query = table_filter.apply(query)
    inventory = query.all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'item_id',
                'label': 'Item',
                'options': [{'value': item.id, 'label': f"{item.sku} - {item.name}"}
                           for item in Item.query.filter_by(is_active=True).order_by(Item.sku).all()]
            },
            {
                'name': 'location_id',
                'label': 'Location',
                'options': [{'value': loc.id, 'label': f"{loc.code} - {loc.name}"}
                           for loc in Location.query.filter_by(is_active=True).order_by(Location.code).all()]
            }
        ],
        'date_ranges': [],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('inventory/index.html',
                         inventory=inventory,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

@inventory_bp.route('/locations')
@login_required
def locations():
    locations = Location.query.all()
    return render_template('inventory/locations.html', locations=locations)

@inventory_bp.route('/locations/new', methods=['GET', 'POST'])
@login_required
def new_location():
    if request.method == 'POST':
        location = Location(
            code=request.form.get('code').upper(),
            name=request.form.get('name'),
            type=request.form.get('type'),
            address=request.form.get('address')
        )
        db.session.add(location)
        db.session.commit()
        
        flash(f'Location {location.name} created successfully!', 'success')
        return redirect(url_for('inventory.locations'))
    
    return render_template('inventory/new_location.html')

@inventory_bp.route('/adjust', methods=['GET', 'POST'])
@login_required
def adjust():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        location_id = request.form.get('location_id')
        quantity = int(request.form.get('quantity'))
        notes = request.form.get('notes')
        
        # Get or create inventory location
        inv_loc = InventoryLocation.query.filter_by(
            item_id=item_id,
            location_id=location_id
        ).first()
        
        if not inv_loc:
            inv_loc = InventoryLocation(
                item_id=item_id,
                location_id=location_id,
                quantity=0
            )
            db.session.add(inv_loc)
        
        old_qty = inv_loc.quantity
        inv_loc.quantity += quantity
        
        # Create transaction record
        transaction = InventoryTransaction(
            item_id=item_id,
            location_id=location_id,
            transaction_type='adjustment',
            quantity=quantity,
            notes=f"Adjustment from {old_qty} to {inv_loc.quantity}. {notes}",
            created_by=current_user.id
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        flash('Inventory adjusted successfully!', 'success')
        return redirect(url_for('inventory.index'))
    
    items = Item.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    return render_template('inventory/adjust.html', items=items, locations=locations)

@inventory_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        from inventory_utils import move_stock

        item_id = request.form.get('item_id', type=int)
        from_location_id = request.form.get('from_location_id', type=int)
        to_location_id = request.form.get('to_location_id', type=int)
        quantity = request.form.get('quantity', type=int)
        from_bin_location = request.form.get('from_bin_location', '').strip() or None
        to_bin_location = request.form.get('to_bin_location', '').strip() or None
        notes = request.form.get('notes')

        # Use the move_stock utility function which handles all the logic
        success, message, movement = move_stock(
            item_id=item_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            moved_by=current_user.id,
            reason='Manual Transfer',
            notes=notes,
            movement_type='transfer',
            from_bin_location=from_bin_location,
            to_bin_location=to_bin_location
        )

        if success:
            flash(f'{message}!', 'success')
            return redirect(url_for('inventory.index'))
        else:
            flash(f'Transfer failed: {message}', 'danger')
            return redirect(url_for('inventory.transfer'))

    items = Item.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    return render_template('inventory/transfer.html', items=items, locations=locations)

@inventory_bp.route('/transactions')
@login_required
def transactions():
    transactions = InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).limit(100).all()
    return render_template('inventory/transactions.html', transactions=transactions)

@inventory_bp.route('/api/availability/<int:item_id>/<int:location_id>')
@login_required
def get_availability(item_id, location_id):
    """API endpoint to get item availability at a specific location"""
    inv_loc = InventoryLocation.query.filter_by(
        item_id=item_id,
        location_id=location_id
    ).first()

    if inv_loc:
        return jsonify({
            'success': True,
            'quantity': inv_loc.quantity
        })
    else:
        return jsonify({
            'success': True,
            'quantity': 0
        })

@inventory_bp.route('/bins')
@login_required
def bins():
    """List all warehouse bins"""
    location_id = request.args.get('location_id', type=int)

    # Get all unique bins from batches
    query = db.session.query(
        Batch.location_id,
        Batch.bin_location,
        db.func.count(db.distinct(Batch.item_id)).label('unique_items'),
        db.func.sum(Batch.quantity_available).label('total_quantity')
    ).filter(
        Batch.bin_location.isnot(None),
        Batch.quantity_available > 0,
        Batch.status == 'active'
    )

    if location_id:
        query = query.filter(Batch.location_id == location_id)

    bins_data = query.group_by(Batch.location_id, Batch.bin_location).all()

    # Format the data
    bins = []
    for bin_data in bins_data:
        location = Location.query.get(bin_data.location_id)
        bins.append({
            'location': location,
            'bin_location': bin_data.bin_location,
            'unique_items': bin_data.unique_items,
            'total_quantity': bin_data.total_quantity
        })

    locations = Location.query.filter_by(is_active=True).all()

    return render_template('inventory/bins.html', bins=bins, locations=locations, selected_location_id=location_id)

@inventory_bp.route('/bins/<int:location_id>/<bin_location>')
@login_required
def bin_details(location_id, bin_location):
    """View details of a specific bin"""
    location = Location.query.get_or_404(location_id)

    # Get all batches in this bin
    batches = Batch.query.filter_by(
        location_id=location_id,
        bin_location=bin_location,
        status='active'
    ).filter(
        Batch.quantity_available > 0
    ).order_by(Batch.received_date.asc()).all()

    # Get inventory location data for items in this bin
    items_in_bin = db.session.query(
        Item,
        db.func.sum(Batch.quantity_available).label('total_quantity')
    ).join(
        Batch, Batch.item_id == Item.id
    ).filter(
        Batch.location_id == location_id,
        Batch.bin_location == bin_location,
        Batch.status == 'active',
        Batch.quantity_available > 0
    ).group_by(Item.id).all()

    return render_template('inventory/bin_details.html',
                         location=location,
                         bin_location=bin_location,
                         batches=batches,
                         items_in_bin=items_in_bin)
