from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, StockMovement, Item, Location, InventoryLocation
from inventory_utils import move_stock, get_stock_by_location, get_movement_history, check_location_capacity
from filter_utils import TableFilter
from datetime import datetime

stock_movements_bp = Blueprint('stock_movements', __name__)

@stock_movements_bp.route('/')
@login_required
def index():
    """List all stock movements with filtering"""
    # Initialize filter
    table_filter = TableFilter(StockMovement, request.args)

    # Configure filters
    table_filter.add_filter('item_id', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('movement_type', operator='eq')
    table_filter.add_date_filter('moved_at')
    table_filter.add_search(['movement_number', 'reason', 'notes'])

    # Apply filters to base query
    query = StockMovement.query
    query = table_filter.apply(query)

    # Order and execute
    movements = query.order_by(StockMovement.moved_at.desc()).limit(500).all()

    # Get filter options
    items = Item.query.filter_by(is_active=True).order_by(Item.sku).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.code).all()

    # Prepare filter config for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'item_id',
                'label': 'Item',
                'options': [{'value': item.id, 'label': f"{item.sku} - {item.name}"} for item in items]
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'pending', 'label': 'Pending'},
                    {'value': 'in_transit', 'label': 'In Transit'},
                    {'value': 'completed', 'label': 'Completed'},
                    {'value': 'cancelled', 'label': 'Cancelled'},
                ]
            },
            {
                'name': 'movement_type',
                'label': 'Type',
                'options': [
                    {'value': 'transfer', 'label': 'Transfer'},
                    {'value': 'relocation', 'label': 'Relocation'},
                    {'value': 'rebalance', 'label': 'Rebalance'},
                ]
            }
        ],
        'date_ranges': [
            {'name': 'moved_at', 'label': 'Movement Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    current_filters = table_filter.get_active_filters()

    return render_template('stock_movements/index.html',
                         movements=movements,
                         filter_config=filter_config,
                         current_filters=current_filters)

@stock_movements_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new stock movement"""
    if request.method == 'POST':
        try:
            item_id = request.form.get('item_id', type=int)
            from_location_id = request.form.get('from_location_id', type=int)
            to_location_id = request.form.get('to_location_id', type=int)
            quantity = request.form.get('quantity', type=int)
            from_bin_location = request.form.get('from_bin_location', '').strip() or None
            to_bin_location = request.form.get('to_bin_location', '').strip() or None
            reason = request.form.get('reason')
            notes = request.form.get('notes')
            movement_type = request.form.get('movement_type', 'transfer')

            success, message, movement = move_stock(
                item_id=item_id,
                from_location_id=from_location_id,
                to_location_id=to_location_id,
                quantity=quantity,
                moved_by=current_user.id,
                reason=reason,
                notes=notes,
                movement_type=movement_type,
                from_bin_location=from_bin_location,
                to_bin_location=to_bin_location
            )

            if success:
                flash(f'{message}. Movement #{movement.movement_number}', 'success')
                return redirect(url_for('stock_movements.view', id=movement.id))
            else:
                flash(f'Error: {message}', 'error')

        except Exception as e:
            flash(f'Error creating stock movement: {str(e)}', 'error')

    # GET request
    items = Item.query.filter_by(is_active=True).order_by(Item.sku).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.code).all()

    return render_template('stock_movements/new.html', items=items, locations=locations)

@stock_movements_bp.route('/<int:id>')
@login_required
def view(id):
    """View stock movement details"""
    movement = StockMovement.query.get_or_404(id)
    return render_template('stock_movements/view.html', movement=movement)

@stock_movements_bp.route('/api/stock-by-location/<int:item_id>')
@login_required
def api_stock_by_location(item_id):
    """API endpoint to get stock breakdown by location"""
    location_type = request.args.get('type')
    stock_data = get_stock_by_location(item_id, location_type)
    return jsonify(stock_data)

@stock_movements_bp.route('/api/location-capacity/<int:location_id>')
@login_required
def api_location_capacity(location_id):
    """API endpoint to check location capacity"""
    capacity_info = check_location_capacity(location_id)
    if capacity_info:
        return jsonify(capacity_info)
    return jsonify({'error': 'Location not found'}), 404

@stock_movements_bp.route('/api/available-stock')
@login_required
def api_available_stock():
    """Get available stock for item at specific location"""
    item_id = request.args.get('item_id', type=int)
    location_id = request.args.get('location_id', type=int)

    if not item_id or not location_id:
        return jsonify({'error': 'item_id and location_id required'}), 400

    inv_loc = InventoryLocation.query.filter_by(
        item_id=item_id,
        location_id=location_id
    ).first()

    quantity = inv_loc.quantity if inv_loc else 0

    return jsonify({
        'item_id': item_id,
        'location_id': location_id,
        'available_quantity': quantity
    })
