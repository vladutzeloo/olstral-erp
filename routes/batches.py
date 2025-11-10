from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from extensions import db
from models import Batch, BatchTransaction, Item, Location
from filter_utils import TableFilter
from batch_utils import get_batch_summary, get_available_batches_fifo

batches_bp = Blueprint('batches', __name__)

@batches_bp.route('/')
@login_required
def index():
    """List all active batches"""
    # Initialize filter
    table_filter = TableFilter(Batch, request.args)

    # Add filters
    table_filter.add_filter('item_id', operator='eq')
    table_filter.add_filter('location_id', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_date_filter('received_date')
    table_filter.add_search(['batch_number', 'supplier_batch_number', 'internal_order_number'])

    # Apply filters
    query = Batch.query
    query = table_filter.apply(query)
    batches = query.order_by(Batch.received_date.desc()).all()

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
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'active', 'label': 'Active'},
                    {'value': 'depleted', 'label': 'Depleted'},
                    {'value': 'expired', 'label': 'Expired'},
                    {'value': 'quarantine', 'label': 'Quarantine'}
                ]
            }
        ],
        'date_ranges': [
            {'name': 'received_date', 'label': 'Received Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('batches/index.html',
                         batches=batches,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())


@batches_bp.route('/<int:id>')
@login_required
def view(id):
    """View batch details"""
    batch = Batch.query.get_or_404(id)
    transactions = BatchTransaction.query.filter_by(batch_id=id).order_by(BatchTransaction.created_at.desc()).all()
    return render_template('batches/view.html', batch=batch, transactions=transactions)


@batches_bp.route('/api/item_batches/<int:item_id>')
@login_required
def get_item_batches(item_id):
    """API endpoint to get all active batches for an item (FIFO order)"""
    location_id = request.args.get('location_id', type=int)

    batches = get_available_batches_fifo(item_id, location_id)

    return jsonify({
        'success': True,
        'batches': [
            {
                'id': b.id,
                'batch_number': b.batch_number,
                'location': b.location.name,
                'location_id': b.location_id,
                'quantity_available': b.quantity_available,
                'received_date': b.received_date.isoformat(),
                'cost_per_unit': b.cost_per_unit,
                'supplier_batch_number': b.supplier_batch_number
            }
            for b in batches
        ]
    })


@batches_bp.route('/api/item_summary/<int:item_id>')
@login_required
def get_item_summary(item_id):
    """API endpoint to get batch summary for an item"""
    location_id = request.args.get('location_id', type=int)

    summary = get_batch_summary(item_id, location_id)

    return jsonify({
        'success': True,
        'summary': summary
    })
