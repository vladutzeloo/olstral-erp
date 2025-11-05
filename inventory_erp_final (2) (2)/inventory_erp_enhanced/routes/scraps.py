from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import Scrap, Item, Location, InventoryLocation, InventoryTransaction

scraps_bp = Blueprint('scraps', __name__)

@scraps_bp.route('/')
@login_required
def index():
    scraps = Scrap.query.order_by(Scrap.created_at.desc()).all()
    return render_template('scraps/index.html', scraps=scraps)

@scraps_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Generate scrap number
        last_scrap = Scrap.query.order_by(Scrap.id.desc()).first()
        if last_scrap:
            last_num = int(last_scrap.scrap_number.split('-')[-1])
            scrap_number = f"SCRAP-{last_num + 1:06d}"
        else:
            scrap_number = "SCRAP-000001"
        
        item_id = int(request.form.get('item_id'))
        location_id = int(request.form.get('location_id'))
        quantity = int(request.form.get('quantity'))
        
        # Check inventory availability
        inv_loc = InventoryLocation.query.filter_by(
            item_id=item_id,
            location_id=location_id
        ).first()
        
        if not inv_loc or inv_loc.quantity < quantity:
            flash('Insufficient quantity at selected location!', 'danger')
            items = Item.query.filter_by(is_active=True).all()
            locations = Location.query.filter_by(is_active=True).all()
            return render_template('scraps/new.html', items=items, locations=locations)
        
        scrap = Scrap(
            scrap_number=scrap_number,
            item_id=item_id,
            location_id=location_id,
            quantity=quantity,
            reason=request.form.get('reason'),
            source_type='warehouse',
            scrap_date=datetime.utcnow(),
            scrapped_by=current_user.id,
            notes=request.form.get('notes')
        )
        
        db.session.add(scrap)
        db.session.flush()
        
        # Deduct from inventory
        inv_loc.quantity -= quantity
        
        # Create transaction
        transaction = InventoryTransaction(
            item_id=item_id,
            location_id=location_id,
            transaction_type='scrap',
            quantity=-quantity,
            reference_type='scrap',
            reference_id=scrap.id,
            notes=f"Scrapped: {scrap.reason}",
            created_by=current_user.id
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        flash(f'Scrap {scrap_number} created successfully!', 'success')
        return redirect(url_for('scraps.view', id=scrap.id))
    
    items = Item.query.filter_by(is_active=True).all()
    locations = Location.query.filter_by(is_active=True).all()
    return render_template('scraps/new.html', items=items, locations=locations)

@scraps_bp.route('/<int:id>')
@login_required
def view(id):
    scrap = Scrap.query.get_or_404(id)
    return render_template('scraps/view.html', scrap=scrap)

@scraps_bp.route('/search_items')
@login_required
def search_items():
    query = request.args.get('q', '').strip()
    location_id = request.args.get('location_id', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    # Build base query
    items_query = Item.query.filter(
        db.or_(
            Item.sku.ilike(f'%{query}%'),
            Item.name.ilike(f'%{query}%')
        ),
        Item.is_active == True
    )
    
    # If location is specified, only show items with inventory at that location
    if location_id:
        items_query = items_query.join(InventoryLocation).filter(
            InventoryLocation.location_id == int(location_id),
            InventoryLocation.quantity > 0
        )
    
    items = items_query.limit(20).all()
    
    results = []
    for item in items:
        item_data = {
            'id': item.id,
            'sku': item.sku,
            'name': item.name,
            'label': f"{item.sku} - {item.name}"
        }
        
        # Add available quantity if location is specified
        if location_id:
            inv_loc = InventoryLocation.query.filter_by(
                item_id=item.id,
                location_id=int(location_id)
            ).first()
            if inv_loc:
                item_data['available'] = inv_loc.quantity
                item_data['label'] += f" (Available: {inv_loc.quantity})"
        
        results.append(item_data)
    
    return jsonify(results)
