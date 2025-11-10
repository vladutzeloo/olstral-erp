from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from extensions import db
from models import Item, InventoryLocation, PurchaseOrder, Shipment, ExternalProcess, Batch, ProductionOrder

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Get total items
    total_items = Item.query.filter_by(is_active=True).count()

    # Get total inventory value (owned batches only, excluding lohn/consignment)
    inventory_value = db.session.query(
        func.sum(Batch.quantity_available * Batch.cost_per_unit)
    ).filter(
        Batch.status == 'active',
        Batch.ownership_type == 'owned'
    ).scalar() or 0
    
    # Get low stock items
    low_stock_items = []
    items = Item.query.filter_by(is_active=True).all()
    for item in items:
        total_qty = item.get_total_quantity()
        if total_qty <= item.reorder_level and item.reorder_level > 0:
            low_stock_items.append({
                'item': item,
                'current_qty': total_qty,
                'reorder_level': item.reorder_level
            })
    
    # Get pending purchase orders
    pending_pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['draft', 'submitted', 'partial'])
    ).count()
    
    # Get pending external processes
    pending_processes = ExternalProcess.query.filter(
        ExternalProcess.status.in_(['sent', 'in_progress'])
    ).count()
    
    # Get active production orders
    active_production_orders = ProductionOrder.query.filter(
        ProductionOrder.status.in_(['released', 'in_progress'])
    ).count()

    # Recent activities
    recent_pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(5).all()
    recent_shipments = Shipment.query.order_by(Shipment.created_at.desc()).limit(5).all()
    recent_production_orders = ProductionOrder.query.order_by(ProductionOrder.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                         total_items=total_items,
                         inventory_value=inventory_value,
                         low_stock_count=len(low_stock_items),
                         low_stock_items=low_stock_items[:10],
                         pending_pos=pending_pos,
                         pending_processes=pending_processes,
                         active_production_orders=active_production_orders,
                         recent_pos=recent_pos,
                         recent_shipments=recent_shipments,
                         recent_production_orders=recent_production_orders)
