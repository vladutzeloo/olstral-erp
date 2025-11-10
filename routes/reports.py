from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from extensions import db
from models import Item, InventoryLocation, InventoryTransaction, PurchaseOrder, Shipment, ExternalProcess, Batch

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/inventory-valuation')
@login_required
def inventory_valuation():
    # Calculate inventory value based on batches (FIFO cost tracking)
    # Only include owned batches (exclude lohn/consignment materials)
    results = db.session.query(
        Item,
        func.sum(Batch.quantity_available).label('total_qty'),
        func.sum(Batch.quantity_available * Batch.cost_per_unit).label('total_value')
    ).join(Batch).filter(
        Batch.status == 'active',
        Batch.ownership_type == 'owned'  # Exclude consignment and lohn materials
    ).group_by(Item.id).all()

    # Calculate total value (owned inventory only)
    total_value = sum(r.total_value or 0 for r in results)

    # Also get consignment/lohn quantities for reporting (but not valued)
    consignment_results = db.session.query(
        Item,
        func.sum(Batch.quantity_available).label('total_qty'),
        Batch.ownership_type
    ).join(Batch).filter(
        Batch.status == 'active',
        Batch.ownership_type.in_(['consignment', 'lohn'])
    ).group_by(Item.id, Batch.ownership_type).all()

    return render_template('reports/inventory_valuation.html',
                         results=results,
                         total_value=total_value,
                         consignment_results=consignment_results)

@reports_bp.route('/low-stock')
@login_required
def low_stock():
    items = Item.query.filter_by(is_active=True).all()
    low_stock_items = []
    
    for item in items:
        total_qty = item.get_total_quantity()
        if total_qty <= item.reorder_level and item.reorder_level > 0:
            low_stock_items.append({
                'item': item,
                'current_qty': total_qty,
                'reorder_level': item.reorder_level,
                'reorder_qty': item.reorder_quantity,
                'shortage': item.reorder_level - total_qty
            })
    
    return render_template('reports/low_stock.html', items=low_stock_items)

@reports_bp.route('/transaction-history')
@login_required
def transaction_history():
    transactions = InventoryTransaction.query.order_by(
        InventoryTransaction.created_at.desc()
    ).limit(500).all()
    
    return render_template('reports/transaction_history.html', transactions=transactions)

@reports_bp.route('/purchase-order-status')
@login_required
def purchase_order_status():
    pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    
    stats = {
        'draft': PurchaseOrder.query.filter_by(status='draft').count(),
        'submitted': PurchaseOrder.query.filter_by(status='submitted').count(),
        'partial': PurchaseOrder.query.filter_by(status='partial').count(),
        'received': PurchaseOrder.query.filter_by(status='received').count(),
        'cancelled': PurchaseOrder.query.filter_by(status='cancelled').count()
    }
    
    return render_template('reports/purchase_order_status.html', pos=pos, stats=stats)

@reports_bp.route('/external-process-status')
@login_required
def external_process_status():
    processes = ExternalProcess.query.order_by(ExternalProcess.created_at.desc()).all()
    
    stats = {
        'sent': ExternalProcess.query.filter_by(status='sent').count(),
        'in_progress': ExternalProcess.query.filter_by(status='in_progress').count(),
        'partial': ExternalProcess.query.filter_by(status='partial').count(),
        'completed': ExternalProcess.query.filter_by(status='completed').count(),
        'cancelled': ExternalProcess.query.filter_by(status='cancelled').count()
    }
    
    return render_template('reports/external_process_status.html', processes=processes, stats=stats)
