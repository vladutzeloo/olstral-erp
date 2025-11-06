from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import (Receipt, ReceiptItem, PurchaseOrder, PurchaseOrderItem, Location, Item,
                    InventoryLocation, InventoryTransaction, ExternalProcess, Scrap, Supplier, User)
from filter_utils import TableFilter
from pdf_generator import ReceiptPDF

receipts_bp = Blueprint('receipts', __name__)

@receipts_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(Receipt, request.args)

    # Add filters
    table_filter.add_filter('source_type', operator='eq')
    table_filter.add_filter('location_id', operator='eq')
    table_filter.add_filter('received_by', operator='eq')
    table_filter.add_date_filter('received_date')
    table_filter.add_search(['receipt_number', 'internal_order_number', 'notes'])

    # Apply filters
    query = Receipt.query
    query = table_filter.apply(query)
    receipts = query.order_by(Receipt.created_at.desc()).all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'source_type',
                'label': 'Source Type',
                'options': [
                    {'value': 'purchase_order', 'label': 'Purchase Order'},
                    {'value': 'production', 'label': 'Production'},
                    {'value': 'external_process', 'label': 'External Process'}
                ]
            },
            {
                'name': 'location_id',
                'label': 'Location',
                'options': [{'value': loc.id, 'label': f"{loc.code} - {loc.name}"}
                           for loc in Location.query.filter_by(is_active=True).order_by(Location.code).all()]
            },
            {
                'name': 'received_by',
                'label': 'Received By',
                'options': [{'value': u.id, 'label': u.username} for u in User.query.order_by(User.username).all()]
            }
        ],
        'date_ranges': [
            {'name': 'received_date', 'label': 'Received Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('receipts/index.html',
                         receipts=receipts,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

@receipts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        try:
            # Generate receipt number
            last_receipt = Receipt.query.order_by(Receipt.id.desc()).first()
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                receipt_number = f"RCV-{last_num + 1:06d}"
            else:
                receipt_number = "RCV-000001"
            
            source_type = request.form.get('source_type', 'purchase_order')
            po_id = request.form.get('po_id')
            external_process_id = request.form.get('external_process_id')
            location_id = request.form.get('location_id')
            
            receipt = Receipt(
                receipt_number=receipt_number,
                source_type=source_type,
                po_id=int(po_id) if po_id else None,
                external_process_id=int(external_process_id) if external_process_id else None,
                internal_order_number=request.form.get('internal_order_number'),
                location_id=location_id,
                received_date=datetime.utcnow(),
                received_by=current_user.id,
                notes=request.form.get('notes')
            )
            
            db.session.add(receipt)
            db.session.flush()
            
            # Process receipt items
            item_ids = request.form.getlist('item_id[]')
            quantities = request.form.getlist('quantity[]')
            scrap_quantities = request.form.getlist('scrap_quantity[]')
            
            for item_id, qty, scrap_qty in zip(item_ids, quantities, scrap_quantities):
                if item_id and qty and int(qty) > 0:
                    scrap_qty = int(scrap_qty) if scrap_qty else 0
                    good_qty = int(qty) - scrap_qty
                    
                    # Create receipt item
                    receipt_item = ReceiptItem(
                        receipt_id=receipt.id,
                        item_id=int(item_id),
                        quantity=int(qty),
                        scrap_quantity=scrap_qty
                    )
                    db.session.add(receipt_item)
                    
                    # Update inventory (only good quantity)
                    if good_qty > 0:
                        inv_loc = InventoryLocation.query.filter_by(
                            item_id=int(item_id),
                            location_id=location_id
                        ).first()
                        
                        if not inv_loc:
                            inv_loc = InventoryLocation(
                                item_id=int(item_id),
                                location_id=location_id,
                                quantity=good_qty
                            )
                            db.session.add(inv_loc)
                        else:
                            inv_loc.quantity += good_qty
                        
                        # Create transaction for good items
                        transaction = InventoryTransaction(
                            item_id=int(item_id),
                            location_id=location_id,
                            transaction_type='receipt',
                            quantity=good_qty,
                            reference_type='receipt',
                            reference_id=receipt.id,
                            notes=f"Good quantity from {source_type}",
                            created_by=current_user.id
                        )
                        db.session.add(transaction)
                    
                    # Handle scrap if any
                    if scrap_qty > 0:
                        # Generate scrap number
                        last_scrap = Scrap.query.order_by(Scrap.id.desc()).first()
                        if last_scrap:
                            last_num = int(last_scrap.scrap_number.split('-')[-1])
                            scrap_number = f"SCRAP-{last_num + 1:06d}"
                        else:
                            scrap_number = "SCRAP-000001"
                        
                        scrap = Scrap(
                            scrap_number=scrap_number,
                            item_id=int(item_id),
                            location_id=location_id,
                            quantity=scrap_qty,
                            reason='Damaged during reception',
                            source_type='receipt',
                            source_id=receipt.id,
                            scrapped_by=current_user.id,
                            notes=f"Scrapped from {receipt_number}"
                        )
                        db.session.add(scrap)
                        
                        # Create transaction for scrap
                        transaction = InventoryTransaction(
                            item_id=int(item_id),
                            location_id=location_id,
                            transaction_type='scrap',
                            quantity=-scrap_qty,
                            reference_type='scrap',
                            notes=f"Scrapped from receipt {receipt_number}",
                            created_by=current_user.id
                        )
                        db.session.add(transaction)
                    
                    # Update PO item if linked to PO
                    if po_id:
                        po_item = PurchaseOrderItem.query.filter_by(
                            po_id=int(po_id),
                            item_id=int(item_id)
                        ).first()
                        
                        if po_item:
                            po_item.quantity_received += int(qty)
                    
                    # Update external process if linked
                    if external_process_id:
                        ext_process = ExternalProcess.query.get(int(external_process_id))
                        if ext_process:
                            # Check if this is the returned item (transformed) or original
                            if ext_process.returned_item_id and ext_process.returned_item_id == int(item_id):
                                # Receiving transformed item
                                ext_process.quantity_returned += int(qty)
                            elif ext_process.item_id == int(item_id):
                                # Receiving original item back (no transformation)
                                ext_process.quantity_returned += int(qty)
                            
                            ext_process.actual_return = datetime.utcnow()
                            
                            if ext_process.quantity_returned >= ext_process.quantity_sent:
                                ext_process.status = 'completed'
                            else:
                                ext_process.status = 'in_progress'
            
            # Update PO status if linked
            if po_id:
                po = PurchaseOrder.query.get(int(po_id))
                all_received = all(
                    poi.quantity_received >= poi.quantity_ordered
                    for poi in po.items
                )
                any_received = any(
                    poi.quantity_received > 0
                    for poi in po.items
                )
                
                if all_received:
                    po.status = 'received'
                elif any_received:
                    po.status = 'partial'
            
            db.session.commit()
            
            flash(f'Receipt {receipt_number} created successfully!', 'success')
            return redirect(url_for('receipts.view', id=receipt.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating receipt: {str(e)}', 'danger')
            return redirect(url_for('receipts.new'))
    
    pos = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['submitted', 'partial'])
    ).all()

    # Prepare POs with serializable items data
    pos_data = []
    for po in pos:
        po_dict = {
            'id': int(po.id),
            'po_number': str(po.po_number),
            'supplier_name': str(po.supplier.name),
            'items': [
                {
                    'item': {
                        'id': int(item.item.id),
                        'sku': str(item.item.sku),
                        'name': str(item.item.name)
                    },
                    'quantity_ordered': int(item.quantity_ordered),
                    'quantity_received': int(item.quantity_received)
                }
                for item in po.items
            ]
        }
        pos_data.append(po_dict)

    external_processes = ExternalProcess.query.filter(
        ExternalProcess.status.in_(['sent', 'in_progress'])
    ).all()
    locations = Location.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()

    return render_template('receipts/new.html', pos=pos_data, external_processes=external_processes,
                         locations=locations, items=items)

@receipts_bp.route('/search_items')
@login_required
def search_items():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    # Search items by SKU or name
    items = Item.query.filter(
        db.or_(
            Item.sku.ilike(f'%{query}%'),
            Item.name.ilike(f'%{query}%')
        ),
        Item.is_active == True
    ).limit(20).all()
    
    results = [{
        'id': item.id,
        'sku': item.sku,
        'name': item.name,
        'label': f"{item.sku} - {item.name}"
    } for item in items]
    
    return jsonify(results)

@receipts_bp.route('/get_external_process_info/<int:process_id>')
@login_required
def get_external_process_info(process_id):
    """Get detailed info about external process for smart reception"""
    process = ExternalProcess.query.get_or_404(process_id)
    
    # Determine which item to receive
    if process.creates_new_sku and process.returned_item_id:
        # Transformed item - receive the new SKU
        receive_item = process.returned_item
        receive_item_id = process.returned_item_id
        transformation_note = f"Originally sent: {process.item.sku} → Received: {receive_item.sku} ({process.process_result})"
    else:
        # Same item - receive original
        receive_item = process.item
        receive_item_id = process.item_id
        transformation_note = None
    
    return jsonify({
        'process_number': process.process_number,
        'supplier_name': process.supplier.name,
        'process_type': process.process_type,
        'process_result': process.process_result,
        'creates_new_sku': process.creates_new_sku,
        'sent_item': {
            'id': process.item_id,
            'sku': process.item.sku,
            'name': process.item.name
        },
        'receive_item': {
            'id': receive_item_id,
            'sku': receive_item.sku,
            'name': receive_item.name
        },
        'quantity_sent': process.quantity_sent,
        'quantity_returned': process.quantity_returned,
        'remaining': process.quantity_sent - process.quantity_returned,
        'transformation_note': transformation_note
    })

@receipts_bp.route('/<int:id>')
@login_required
def view(id):
    receipt = Receipt.query.get_or_404(id)
    return render_template('receipts/view.html', receipt=receipt)

@receipts_bp.route('/<int:id>/pdf')
@login_required
def download_pdf(id):
    """Generate and download PDF for receipt"""
    receipt = Receipt.query.get_or_404(id)

    # Generate PDF
    pdf_generator = ReceiptPDF()
    pdf_buffer = pdf_generator.generate(receipt)

    # Send file
    filename = f"Receipt_{receipt.receipt_number}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
