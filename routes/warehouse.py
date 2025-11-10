"""
Warehouse Worker Dashboard and Simplified Interface

Provides streamlined interface for warehouse workers focused on their core tasks.
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import (Receipt, Shipment, StockMovement, InventoryLocation, Location, Item,
                    Batch, InventoryTransaction, PurchaseOrder, ExternalProcess)
from datetime import datetime, timedelta
from role_utils import role_required, get_user_permissions

warehouse_bp = Blueprint('warehouse', __name__)


@warehouse_bp.route('/dashboard')
@login_required
@role_required('warehouse_worker', 'user', 'manager', 'admin')
def dashboard():
    """Simplified warehouse worker dashboard"""

    # Get today's activity
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's receipts
    today_receipts = Receipt.query.filter(
        Receipt.received_date >= today
    ).order_by(Receipt.received_date.desc()).limit(10).all()

    # Today's shipments
    today_shipments = Shipment.query.filter(
        Shipment.ship_date >= today
    ).order_by(Shipment.ship_date.desc()).limit(10).all()

    # Recent stock movements
    recent_movements = StockMovement.query.order_by(
        StockMovement.moved_at.desc()
    ).limit(10).all()

    # Pending tasks for warehouse
    pending_pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['submitted', 'partial'])
    ).order_by(PurchaseOrder.expected_date).limit(5).all()

    pending_external = ExternalProcess.query.filter(
        ExternalProcess.status.in_(['sent', 'in_progress'])
    ).order_by(ExternalProcess.expected_return).limit(5).all()

    # Inventory alerts (low stock)
    low_stock_items = db.session.query(Item, InventoryLocation).join(
        InventoryLocation, Item.id == InventoryLocation.item_id
    ).filter(
        Item.is_active == True,
        Item.reorder_level > 0,
        InventoryLocation.quantity <= Item.reorder_level
    ).limit(10).all()

    # Quick stats
    stats = {
        'today_receipts': len(today_receipts),
        'today_shipments': len(today_shipments),
        'pending_pos': PurchaseOrder.query.filter(
            PurchaseOrder.status.in_(['submitted', 'partial'])
        ).count(),
        'pending_external': ExternalProcess.query.filter(
            ExternalProcess.status.in_(['sent', 'in_progress'])
        ).count(),
        'low_stock_count': len(low_stock_items),
        'total_locations': Location.query.filter_by(is_active=True).count()
    }

    # User permissions
    permissions = get_user_permissions(current_user)

    return render_template('warehouse/dashboard.html',
                         today_receipts=today_receipts,
                         today_shipments=today_shipments,
                         recent_movements=recent_movements,
                         pending_pos=pending_pos,
                         pending_external=pending_external,
                         low_stock_items=low_stock_items,
                         stats=stats,
                         permissions=permissions)


@warehouse_bp.route('/quick-receive')
@login_required
@role_required('warehouse_worker', 'user', 'manager', 'admin')
def quick_receive():
    """Quick receive interface - simplified for warehouse workers"""

    # Get pending POs
    pending_pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['submitted', 'partial'])
    ).order_by(PurchaseOrder.po_number.desc()).all()

    # Get pending external processes
    pending_external = ExternalProcess.query.filter(
        ExternalProcess.status.in_(['sent', 'in_progress'])
    ).order_by(ExternalProcess.process_number.desc()).all()

    # Get active locations
    locations = Location.query.filter_by(is_active=True).order_by(Location.code).all()

    return render_template('warehouse/quick_receive.html',
                         pending_pos=pending_pos,
                         pending_external=pending_external,
                         locations=locations)


@warehouse_bp.route('/quick-ship')
@login_required
@role_required('warehouse_worker', 'user', 'manager', 'admin')
def quick_ship():
    """Quick ship interface - simplified for warehouse workers"""

    locations = Location.query.filter_by(is_active=True).order_by(Location.code).all()

    return render_template('warehouse/quick_ship.html', locations=locations)


@warehouse_bp.route('/stock-lookup')
@login_required
@role_required('warehouse_worker', 'user', 'manager', 'admin')
def stock_lookup():
    """Quick stock lookup interface"""

    query = request.args.get('q', '').strip()
    location_id = request.args.get('location_id', type=int)

    results = []

    if query and len(query) >= 2:
        # Search for items
        items_query = Item.query.filter(
            db.or_(
                Item.sku.ilike(f'%{query}%'),
                Item.name.ilike(f'%{query}%'),
                Item.neo_code.ilike(f'%{query}%')
            ),
            Item.is_active == True
        ).limit(20)

        items = items_query.all()

        for item in items:
            # Get inventory by location
            inv_query = InventoryLocation.query.filter_by(item_id=item.id)
            if location_id:
                inv_query = inv_query.filter_by(location_id=location_id)

            inventories = inv_query.all()

            # Get batches
            batch_query = Batch.query.filter(
                Batch.item_id == item.id,
                Batch.quantity_available > 0,
                Batch.status == 'active'
            )
            if location_id:
                batch_query = batch_query.filter_by(location_id=location_id)

            batches = batch_query.order_by(Batch.received_date.asc()).all()

            total_qty = sum(inv.quantity for inv in inventories)

            results.append({
                'item': item,
                'total_quantity': total_qty,
                'inventories': inventories,
                'batches': batches,
                'batch_count': len(batches)
            })

    locations = Location.query.filter_by(is_active=True).order_by(Location.code).all()

    return render_template('warehouse/stock_lookup.html',
                         results=results,
                         query=query,
                         location_id=location_id,
                         locations=locations)


@warehouse_bp.route('/my-activity')
@login_required
@role_required('warehouse_worker', 'user', 'manager', 'admin')
def my_activity():
    """View user's recent activity"""

    # Receipts created by user
    my_receipts = Receipt.query.filter_by(
        received_by=current_user.id
    ).order_by(Receipt.received_date.desc()).limit(20).all()

    # Stock movements by user
    my_movements = StockMovement.query.filter_by(
        moved_by=current_user.id
    ).order_by(StockMovement.moved_at.desc()).limit(20).all()

    # Shipments created by user
    my_shipments = Shipment.query.filter_by(
        created_by=current_user.id
    ).order_by(Shipment.ship_date.desc()).limit(20).all()

    # Inventory transactions by user
    my_transactions = InventoryTransaction.query.filter_by(
        created_by=current_user.id
    ).order_by(InventoryTransaction.created_at.desc()).limit(30).all()

    return render_template('warehouse/my_activity.html',
                         my_receipts=my_receipts,
                         my_movements=my_movements,
                         my_shipments=my_shipments,
                         my_transactions=my_transactions)
