from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, BillOfMaterials, BOMComponent, Item
from datetime import datetime

bom_bp = Blueprint('bom', __name__)

@bom_bp.route('/')
@login_required
def index():
    """List all BOMs"""
    boms = BillOfMaterials.query.order_by(BillOfMaterials.created_at.desc()).all()
    return render_template('bom/index.html', boms=boms)

@bom_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new BOM"""
    if request.method == 'POST':
        try:
            # Generate BOM number
            last_bom = BillOfMaterials.query.order_by(BillOfMaterials.id.desc()).first()
            if last_bom:
                num = int(last_bom.bom_number.split('-')[1]) + 1
            else:
                num = 1
            bom_number = f'BOM-{num:05d}'

            # Create BOM
            bom = BillOfMaterials(
                bom_number=bom_number,
                finished_item_id=request.form.get('finished_item_id'),
                version=request.form.get('version', '1.0'),
                status='draft',
                production_time_minutes=request.form.get('production_time_minutes', type=int),
                scrap_factor=request.form.get('scrap_factor', 0.0, type=float),
                notes=request.form.get('notes'),
                created_by=current_user.id
            )
            db.session.add(bom)
            db.session.flush()  # Get the BOM ID

            # Add components
            component_ids = request.form.getlist('component_item_id[]')
            quantities = request.form.getlist('quantity[]')
            sequences = request.form.getlist('sequence[]')
            component_notes = request.form.getlist('component_notes[]')

            for idx, comp_id in enumerate(component_ids):
                if comp_id and quantities[idx]:
                    component = BOMComponent(
                        bom_id=bom.id,
                        component_item_id=int(comp_id),
                        quantity=float(quantities[idx]),
                        sequence=int(sequences[idx]) if sequences[idx] else idx + 1,
                        notes=component_notes[idx] if idx < len(component_notes) else None
                    )
                    db.session.add(component)

            db.session.commit()
            flash(f'BOM {bom_number} created successfully!', 'success')
            return redirect(url_for('bom.view', id=bom.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating BOM: {str(e)}', 'error')

    # GET request
    items = Item.query.filter_by(is_active=True).order_by(Item.sku).all()
    return render_template('bom/new.html', items=items)

@bom_bp.route('/<int:id>')
@login_required
def view(id):
    """View BOM details"""
    bom = BillOfMaterials.query.get_or_404(id)
    return render_template('bom/view.html', bom=bom)

@bom_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit BOM"""
    bom = BillOfMaterials.query.get_or_404(id)

    if bom.status == 'active':
        flash('Cannot edit an active BOM. Create a new version instead.', 'warning')
        return redirect(url_for('bom.view', id=id))

    if request.method == 'POST':
        try:
            bom.finished_item_id = request.form.get('finished_item_id')
            bom.version = request.form.get('version', '1.0')
            bom.production_time_minutes = request.form.get('production_time_minutes', type=int)
            bom.scrap_factor = request.form.get('scrap_factor', 0.0, type=float)
            bom.notes = request.form.get('notes')
            bom.updated_at = datetime.utcnow()

            # Remove existing components
            BOMComponent.query.filter_by(bom_id=bom.id).delete()

            # Add updated components
            component_ids = request.form.getlist('component_item_id[]')
            quantities = request.form.getlist('quantity[]')
            sequences = request.form.getlist('sequence[]')
            component_notes = request.form.getlist('component_notes[]')

            for idx, comp_id in enumerate(component_ids):
                if comp_id and quantities[idx]:
                    component = BOMComponent(
                        bom_id=bom.id,
                        component_item_id=int(comp_id),
                        quantity=float(quantities[idx]),
                        sequence=int(sequences[idx]) if sequences[idx] else idx + 1,
                        notes=component_notes[idx] if idx < len(component_notes) else None
                    )
                    db.session.add(component)

            db.session.commit()
            flash(f'BOM {bom.bom_number} updated successfully!', 'success')
            return redirect(url_for('bom.view', id=bom.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating BOM: {str(e)}', 'error')

    items = Item.query.filter_by(is_active=True).order_by(Item.sku).all()
    return render_template('bom/edit.html', bom=bom, items=items)

@bom_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
def activate(id):
    """Activate a BOM (makes it the active version)"""
    bom = BillOfMaterials.query.get_or_404(id)

    if bom.status == 'active':
        flash('BOM is already active.', 'info')
        return redirect(url_for('bom.view', id=id))

    try:
        # Deactivate other BOMs for this item
        BillOfMaterials.query.filter_by(
            finished_item_id=bom.finished_item_id,
            status='active'
        ).update({'status': 'obsolete'})

        # Activate this BOM
        bom.status = 'active'
        bom.activated_at = datetime.utcnow()

        db.session.commit()
        flash(f'BOM {bom.bom_number} activated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error activating BOM: {str(e)}', 'error')

    return redirect(url_for('bom.view', id=id))

@bom_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a BOM (only if draft)"""
    bom = BillOfMaterials.query.get_or_404(id)

    if bom.status != 'draft':
        flash('Can only delete draft BOMs.', 'error')
        return redirect(url_for('bom.view', id=id))

    try:
        bom_number = bom.bom_number
        db.session.delete(bom)
        db.session.commit()
        flash(f'BOM {bom_number} deleted successfully!', 'success')
        return redirect(url_for('bom.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting BOM: {str(e)}', 'error')
        return redirect(url_for('bom.view', id=id))

@bom_bp.route('/<int:id>/copy', methods=['POST'])
@login_required
def copy_bom(id):
    """Create a copy of an existing BOM"""
    original = BillOfMaterials.query.get_or_404(id)

    try:
        # Generate new BOM number
        last_bom = BillOfMaterials.query.order_by(BillOfMaterials.id.desc()).first()
        num = int(last_bom.bom_number.split('-')[1]) + 1
        bom_number = f'BOM-{num:05d}'

        # Create new BOM
        new_bom = BillOfMaterials(
            bom_number=bom_number,
            finished_item_id=original.finished_item_id,
            version=request.form.get('version', original.version),
            status='draft',
            production_time_minutes=original.production_time_minutes,
            scrap_factor=original.scrap_factor,
            notes=f'Copied from {original.bom_number}\n{original.notes or ""}',
            created_by=current_user.id
        )
        db.session.add(new_bom)
        db.session.flush()

        # Copy components
        for comp in original.components:
            new_comp = BOMComponent(
                bom_id=new_bom.id,
                component_item_id=comp.component_item_id,
                quantity=comp.quantity,
                sequence=comp.sequence,
                is_optional=comp.is_optional,
                notes=comp.notes
            )
            db.session.add(new_comp)

        db.session.commit()
        flash(f'BOM copied as {bom_number}!', 'success')
        return redirect(url_for('bom.view', id=new_bom.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error copying BOM: {str(e)}', 'error')
        return redirect(url_for('bom.view', id=id))

@bom_bp.route('/api/item/<int:item_id>')
@login_required
def api_item_info(item_id):
    """API endpoint to get item information"""
    item = Item.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'sku': item.sku,
        'name': item.name,
        'cost': item.cost,
        'unit_of_measure': item.unit_of_measure
    })
