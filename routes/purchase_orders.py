from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import PurchaseOrder, PurchaseOrderItem, Supplier, Item, User
from filter_utils import TableFilter

po_bp = Blueprint('purchase_orders', __name__)

@po_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(PurchaseOrder, request.args)

    # Add filters
    table_filter.add_filter('supplier_id', operator='eq')
    table_filter.add_filter('po_type', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('created_by', operator='eq')
    table_filter.add_date_filter('order_date')
    table_filter.add_date_filter('expected_date')
    table_filter.add_search(['po_number', 'notes'])

    # Apply filters
    query = PurchaseOrder.query
    query = table_filter.apply(query)
    pos = query.order_by(PurchaseOrder.created_at.desc()).all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'supplier_id',
                'label': 'Supplier',
                'options': [{'value': s.id, 'label': s.name} for s in Supplier.query.order_by(Supplier.name).all()]
            },
            {
                'name': 'po_type',
                'label': 'Type',
                'options': [
                    {'value': 'items', 'label': 'Items'},
                    {'value': 'materials', 'label': 'Materials'},
                    {'value': 'external_process', 'label': 'External Process'}
                ]
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'draft', 'label': 'Draft'},
                    {'value': 'submitted', 'label': 'Submitted'},
                    {'value': 'partial', 'label': 'Partial'},
                    {'value': 'received', 'label': 'Received'},
                    {'value': 'cancelled', 'label': 'Cancelled'}
                ]
            },
            {
                'name': 'created_by',
                'label': 'Created By',
                'options': [{'value': u.id, 'label': u.username} for u in User.query.order_by(User.username).all()]
            }
        ],
        'date_ranges': [
            {'name': 'order_date', 'label': 'Order Date'},
            {'name': 'expected_date', 'label': 'Expected Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('purchase_orders/index.html',
                         pos=pos,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

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
    # Initialize filter
    table_filter = TableFilter(Supplier, request.args)

    # Add filters
    table_filter.add_filter('is_active', operator='eq')
    table_filter.add_filter('is_external_processor', operator='eq')
    table_filter.add_date_filter('created_at')
    table_filter.add_search(['code', 'name', 'contact_person', 'email', 'phone'])

    # Apply filters
    query = Supplier.query
    query = table_filter.apply(query)
    suppliers = query.order_by(Supplier.name).all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'is_active',
                'label': 'Status',
                'options': [
                    {'value': '1', 'label': 'Active'},
                    {'value': '0', 'label': 'Inactive'}
                ]
            },
            {
                'name': 'is_external_processor',
                'label': 'Type',
                'options': [
                    {'value': '1', 'label': 'External Processor'},
                    {'value': '0', 'label': 'Regular Supplier'}
                ]
            }
        ],
        'date_ranges': [
            {'name': 'created_at', 'label': 'Created Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('purchase_orders/suppliers.html',
                         suppliers=suppliers,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

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
