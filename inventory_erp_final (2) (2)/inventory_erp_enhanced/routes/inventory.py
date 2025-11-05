from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import InventoryLocation, Location, Item, InventoryTransaction

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
def index():
    inventory = InventoryLocation.query.join(Item).join(Location).all()
    return render_template('inventory/index.html', inventory=inventory)

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
        item_id = request.form.get('item_id')
        from_location_id = request.form.get('from_location_id')
        to_location_id = request.form.get('to_location_id')
        quantity = int(request.form.get('quantity'))
        notes = request.form.get('notes')
        
        # Check if source has enough quantity
        from_inv = InventoryLocation.query.filter_by(
            item_id=item_id,
            location_id=from_location_id
        ).first()
        
        if not from_inv or from_inv.quantity < quantity:
            flash('Insufficient quantity at source location!', 'danger')
            return redirect(url_for('inventory.transfer'))
        
        # Deduct from source
        from_inv.quantity -= quantity
        
        # Add to destination
        to_inv = InventoryLocation.query.filter_by(
            item_id=item_id,
            location_id=to_location_id
        ).first()
        
        if not to_inv:
            to_inv = InventoryLocation(
                item_id=item_id,
                location_id=to_location_id,
                quantity=quantity
            )
            db.session.add(to_inv)
        else:
            to_inv.quantity += quantity
        
        # Create transaction records
        out_trans = InventoryTransaction(
            item_id=item_id,
            location_id=from_location_id,
            transaction_type='transfer_out',
            quantity=-quantity,
            notes=f"Transfer to location {to_location_id}. {notes}",
            created_by=current_user.id
        )
        
        in_trans = InventoryTransaction(
            item_id=item_id,
            location_id=to_location_id,
            transaction_type='transfer_in',
            quantity=quantity,
            notes=f"Transfer from location {from_location_id}. {notes}",
            created_by=current_user.id
        )
        
        db.session.add(out_trans)
        db.session.add(in_trans)
        db.session.commit()
        
        flash('Inventory transferred successfully!', 'success')
        return redirect(url_for('inventory.index'))
    
    items = Item.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    return render_template('inventory/transfer.html', items=items, locations=locations)

@inventory_bp.route('/transactions')
@login_required
def transactions():
    transactions = InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).limit(100).all()
    return render_template('inventory/transactions.html', transactions=transactions)
