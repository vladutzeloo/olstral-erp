from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import PurchaseOrder, PurchaseOrderItem, Supplier, Item

po_bp = Blueprint('purchase_orders', __name__)

@po_bp.route('/')
@login_required
def index():
    pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return render_template('purchase_orders/index.html', pos=pos)

@po_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Generate PO number
        last_po = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
        if last_po:
            last_num = int(last_po.po_number.split('-')[-1])
            po_number = f"PO-{last_num + 1:06d}"
        else:
            po_number = "PO-000001"
        
        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=request.form.get('supplier_id'),
            order_date=datetime.utcnow(),
            expected_date=datetime.strptime(request.form.get('expected_date'), '%Y-%m-%d') if request.form.get('expected_date') else None,
            notes=request.form.get('notes'),
            created_by=current_user.id,
            status='draft'
        )
        
        db.session.add(po)
        db.session.flush()  # Get PO id
        
        # Add items
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('unit_price[]')
        
        total = 0
        for item_id, qty, price in zip(item_ids, quantities, prices):
            if item_id and qty and price:
                po_item = PurchaseOrderItem(
                    po_id=po.id,
                    item_id=int(item_id),
                    quantity_ordered=int(qty),
                    unit_price=float(price)
                )
                db.session.add(po_item)
                total += int(qty) * float(price)
        
        po.total_amount = total
        db.session.commit()
        
        flash(f'Purchase Order {po_number} created successfully!', 'success')
        return redirect(url_for('purchase_orders.view', id=po.id))
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    return render_template('purchase_orders/new.html', suppliers=suppliers, items=items)

@po_bp.route('/<int:id>')
@login_required
def view(id):
    po = PurchaseOrder.query.get_or_404(id)
    return render_template('purchase_orders/view.html', po=po)

@po_bp.route('/<int:id>/submit')
@login_required
def submit(id):
    po = PurchaseOrder.query.get_or_404(id)
    po.status = 'submitted'
    db.session.commit()
    
    flash(f'Purchase Order {po.po_number} submitted!', 'success')
    return redirect(url_for('purchase_orders.view', id=po.id))

@po_bp.route('/<int:id>/cancel')
@login_required
def cancel(id):
    po = PurchaseOrder.query.get_or_404(id)
    po.status = 'cancelled'
    db.session.commit()
    
    flash(f'Purchase Order {po.po_number} cancelled!', 'warning')
    return redirect(url_for('purchase_orders.view', id=po.id))

@po_bp.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('purchase_orders/suppliers.html', suppliers=suppliers)

@po_bp.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
def new_supplier():
    if request.method == 'POST':
        # Generate supplier code
        last_supplier = Supplier.query.order_by(Supplier.id.desc()).first()
        if last_supplier:
            last_num = int(last_supplier.code.split('-')[-1])
            code = f"SUP-{last_num + 1:04d}"
        else:
            code = "SUP-0001"
        
        supplier = Supplier(
            code=code,
            name=request.form.get('name'),
            contact_person=request.form.get('contact_person'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            payment_terms=request.form.get('payment_terms')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash(f'Supplier {supplier.name} created successfully!', 'success')
        return redirect(url_for('purchase_orders.suppliers'))
    
    return render_template('purchase_orders/new_supplier.html')
