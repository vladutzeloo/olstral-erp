from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import Shipment, ShipmentItem, Location, Item, InventoryLocation, InventoryTransaction

shipments_bp = Blueprint('shipments', __name__)

@shipments_bp.route('/')
@login_required
def index():
    shipments = Shipment.query.order_by(Shipment.created_at.desc()).all()
    return render_template('shipments/index.html', shipments=shipments)

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
                
                # Deduct from inventory
                inv_loc.quantity -= int(qty)
                
                # Create transaction
                transaction = InventoryTransaction(
                    item_id=int(item_id),
                    location_id=from_location_id,
                    transaction_type='shipment',
                    quantity=-int(qty),
                    reference_type='shipment',
                    reference_id=shipment.id,
                    created_by=current_user.id
                )
                db.session.add(transaction)
        
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
