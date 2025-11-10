"""
Production Order Utilities with FIFO Batch Tracking

Provides helper functions for:
- Starting production with FIFO component consumption
- Completing production with finished goods receipts
- Calculating production costs based on FIFO
- Production traceability
"""

from datetime import datetime
from extensions import db
from models import ProductionOrder, ProductionConsumption, BillOfMaterials, Item, Receipt, InventoryLocation
from batch_utils import consume_batches_fifo, create_batch, calculate_fifo_cost


def start_production(production_order_id, user_id):
    """
    Start production order - consumes component materials using FIFO

    Args:
        production_order_id: Production order ID
        user_id: User starting the production

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'consumed_components': list,
            'total_material_cost': float
        }

    Raises:
        ValueError: If insufficient materials or invalid state
    """
    import json

    production_order = ProductionOrder.query.get(production_order_id)
    if not production_order:
        raise ValueError(f"Production order {production_order_id} not found")

    if production_order.status not in ['draft', 'released']:
        raise ValueError(f"Cannot start production in status: {production_order.status}")

    consumed_components = []
    total_material_cost = 0.0

    # Determine component list (BOM or Manual)
    components_to_consume = []

    if production_order.bom_id:
        # BOM mode
        bom = production_order.bom
        if not bom or bom.status != 'active':
            raise ValueError(f"No active BOM found for this production order")

        for bom_component in bom.components:
            components_to_consume.append({
                'item_id': bom_component.component_item_id,
                'item': bom_component.component,
                'quantity_per_unit': bom_component.quantity
            })
    elif production_order.manual_components:
        # Manual mode
        manual_comps = json.loads(production_order.manual_components)
        for comp in manual_comps:
            item = Item.query.get(comp['item_id'])
            if not item:
                raise ValueError(f"Component item {comp['item_id']} not found")
            components_to_consume.append({
                'item_id': comp['item_id'],
                'item': item,
                'quantity_per_unit': comp['quantity']
            })
    else:
        raise ValueError("Production order has neither BOM nor manual components defined")

    try:
        # Consume each component using FIFO
        for component in components_to_consume:
            required_quantity = int(component['quantity_per_unit'] * production_order.quantity_ordered)

            if required_quantity <= 0:
                continue

            # Consume batches using FIFO
            consumed_batches = consume_batches_fifo(
                item_id=component['item_id'],
                quantity_needed=required_quantity,
                location_id=production_order.location_id,
                reference_type='production_order',
                reference_id=production_order.id,
                notes=f"Production Order {production_order.order_number}",
                created_by=user_id
            )

            # Create consumption records linking batches to production order
            for batch_info in consumed_batches:
                consumption = ProductionConsumption(
                    production_order_id=production_order.id,
                    component_item_id=component['item_id'],
                    batch_id=batch_info['batch_id'],
                    quantity_consumed=batch_info['quantity'],
                    cost_per_unit=batch_info['cost_per_unit'],
                    total_cost=batch_info['quantity'] * batch_info['cost_per_unit'],
                    consumed_date=datetime.utcnow(),
                    consumed_by=user_id,
                    notes=f"Batch {batch_info['batch_number']} consumed"
                )
                db.session.add(consumption)

            # Calculate cost for this component
            fifo_cost = calculate_fifo_cost(consumed_batches)
            total_material_cost += fifo_cost['total_cost']

            # Update inventory
            inv_loc = InventoryLocation.query.filter_by(
                item_id=component['item_id'],
                location_id=production_order.location_id
            ).first()
            if inv_loc:
                inv_loc.quantity -= required_quantity

            consumed_components.append({
                'item': component['item'].name,
                'item_sku': component['item'].sku,
                'quantity': required_quantity,
                'batches_consumed': len(consumed_batches),
                'total_cost': fifo_cost['total_cost'],
                'average_cost': fifo_cost['average_cost_per_unit']
            })

        # Update production order
        production_order.status = 'in_progress'
        production_order.actual_start_date = datetime.utcnow()
        production_order.material_cost = total_material_cost
        production_order.total_cost = production_order.calculate_total_cost()

        db.session.commit()

        return {
            'success': True,
            'message': f'Production started successfully. Consumed {len(consumed_components)} component types.',
            'consumed_components': consumed_components,
            'total_material_cost': total_material_cost
        }

    except ValueError as e:
        db.session.rollback()
        raise ValueError(f"Failed to start production: {str(e)}")
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Unexpected error starting production: {str(e)}")


def complete_production(production_order_id, quantity_produced, quantity_scrapped, user_id, scrap_reason=None):
    """
    Complete production order - creates receipt for finished goods with FIFO cost

    Args:
        production_order_id: Production order ID
        quantity_produced: Quantity of good finished goods
        quantity_scrapped: Quantity scrapped during production
        user_id: User completing the production
        scrap_reason: Optional reason for scrap

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'receipt_number': str,
            'batch_number': str,
            'cost_per_unit': float
        }

    Raises:
        ValueError: If invalid state or quantities
    """
    from models import Receipt, ReceiptItem, Scrap, InventoryTransaction

    production_order = ProductionOrder.query.get(production_order_id)
    if not production_order:
        raise ValueError(f"Production order {production_order_id} not found")

    if production_order.status != 'in_progress':
        raise ValueError(f"Production order is not in progress (status: {production_order.status})")

    total_quantity = quantity_produced + quantity_scrapped
    if total_quantity > production_order.quantity_ordered:
        raise ValueError(f"Total quantity ({total_quantity}) exceeds ordered quantity ({production_order.quantity_ordered})")

    try:
        # Generate receipt number
        last_receipt = Receipt.query.order_by(Receipt.id.desc()).first()
        if last_receipt:
            last_num = int(last_receipt.receipt_number.split('-')[-1])
            receipt_number = f"RCV-{last_num + 1:06d}"
        else:
            receipt_number = "RCV-000001"

        # Create receipt
        receipt = Receipt(
            receipt_number=receipt_number,
            source_type='production',
            internal_order_number=production_order.order_number,
            location_id=production_order.location_id,
            received_date=datetime.utcnow(),
            received_by=user_id,
            notes=f"Production completed for {production_order.order_number}"
        )
        db.session.add(receipt)
        db.session.flush()

        # Create receipt item
        receipt_item = ReceiptItem(
            receipt_id=receipt.id,
            item_id=production_order.finished_item_id,
            quantity=total_quantity,
            scrap_quantity=quantity_scrapped
        )
        db.session.add(receipt_item)

        # Calculate cost per unit (FIFO cost from consumed materials)
        cost_per_unit = 0.0
        if quantity_produced > 0:
            cost_per_unit = production_order.total_cost / quantity_produced

        batch_number = None

        # Update inventory for good quantity
        if quantity_produced > 0:
            inv_loc = InventoryLocation.query.filter_by(
                item_id=production_order.finished_item_id,
                location_id=production_order.location_id
            ).first()

            if not inv_loc:
                inv_loc = InventoryLocation(
                    item_id=production_order.finished_item_id,
                    location_id=production_order.location_id,
                    quantity=quantity_produced
                )
                db.session.add(inv_loc)
            else:
                inv_loc.quantity += quantity_produced

            # Create inventory transaction
            transaction = InventoryTransaction(
                item_id=production_order.finished_item_id,
                location_id=production_order.location_id,
                transaction_type='receipt',
                quantity=quantity_produced,
                reference_type='production_order',
                reference_id=production_order.id,
                notes=f"Production completed: {production_order.order_number}",
                created_by=user_id
            )
            db.session.add(transaction)

            # Create batch for finished goods with FIFO cost
            batch = create_batch(
                item_id=production_order.finished_item_id,
                receipt_id=receipt.id,
                location_id=production_order.location_id,
                quantity=quantity_produced,
                internal_order_number=production_order.order_number,
                cost_per_unit=cost_per_unit,
                notes=f"Produced from {production_order.order_number}. Material cost: ${production_order.material_cost:.2f}",
                created_by=user_id
            )
            batch_number = batch.batch_number

        # Handle scrap if any
        if quantity_scrapped > 0:
            # Generate scrap number
            last_scrap = Scrap.query.order_by(Scrap.id.desc()).first()
            if last_scrap:
                last_num = int(last_scrap.scrap_number.split('-')[-1])
                scrap_number = f"SCRAP-{last_num + 1:06d}"
            else:
                scrap_number = "SCRAP-000001"

            scrap = Scrap(
                scrap_number=scrap_number,
                item_id=production_order.finished_item_id,
                location_id=production_order.location_id,
                quantity=quantity_scrapped,
                reason=scrap_reason or 'Production scrap',
                source_type='production',
                source_id=production_order.id,
                scrapped_by=user_id,
                notes=f"Scrapped during production {production_order.order_number}"
            )
            db.session.add(scrap)

        # Update production order
        production_order.quantity_produced += quantity_produced
        production_order.quantity_scrapped += quantity_scrapped
        production_order.actual_completion_date = datetime.utcnow()

        # Check if fully completed
        if production_order.quantity_produced + production_order.quantity_scrapped >= production_order.quantity_ordered:
            production_order.status = 'completed'

        db.session.commit()

        return {
            'success': True,
            'message': f'Production completed successfully. Produced {quantity_produced} units.',
            'receipt_number': receipt_number,
            'batch_number': batch_number,
            'cost_per_unit': cost_per_unit,
            'total_cost': production_order.total_cost
        }

    except Exception as e:
        db.session.rollback()
        raise Exception(f"Failed to complete production: {str(e)}")


def get_production_traceability(production_order_id):
    """
    Get full traceability for a production order

    Args:
        production_order_id: Production order ID

    Returns:
        dict: Complete traceability information including consumed batches and finished goods batches
    """
    production_order = ProductionOrder.query.get(production_order_id)
    if not production_order:
        return None

    # Get consumed batches grouped by component
    consumed_by_component = {}
    for consumption in production_order.consumption_records:
        component_sku = consumption.component.sku
        if component_sku not in consumed_by_component:
            consumed_by_component[component_sku] = {
                'item_name': consumption.component.name,
                'item_sku': component_sku,
                'total_quantity': 0,
                'total_cost': 0.0,
                'batches': []
            }

        consumed_by_component[component_sku]['total_quantity'] += consumption.quantity_consumed
        consumed_by_component[component_sku]['total_cost'] += consumption.total_cost
        consumed_by_component[component_sku]['batches'].append({
            'batch_number': consumption.batch.batch_number,
            'quantity': consumption.quantity_consumed,
            'cost_per_unit': consumption.cost_per_unit,
            'total_cost': consumption.total_cost,
            'received_date': consumption.batch.received_date,
            'supplier_batch': consumption.batch.supplier_batch_number
        })

    # Get finished goods batches
    finished_batches = []
    for batch in production_order.finished_item.batches:
        if batch.internal_order_number == production_order.order_number:
            finished_batches.append({
                'batch_number': batch.batch_number,
                'quantity': batch.quantity_original,
                'quantity_available': batch.quantity_available,
                'cost_per_unit': batch.cost_per_unit,
                'received_date': batch.received_date,
                'status': batch.status
            })

    return {
        'order_number': production_order.order_number,
        'finished_item': {
            'sku': production_order.finished_item.sku,
            'name': production_order.finished_item.name
        },
        'quantity_ordered': production_order.quantity_ordered,
        'quantity_produced': production_order.quantity_produced,
        'quantity_scrapped': production_order.quantity_scrapped,
        'status': production_order.status,
        'consumed_components': list(consumed_by_component.values()),
        'finished_batches': finished_batches,
        'costs': {
            'material_cost': production_order.material_cost,
            'labor_cost': production_order.labor_cost,
            'overhead_cost': production_order.overhead_cost,
            'total_cost': production_order.total_cost,
            'cost_per_unit': production_order.total_cost / production_order.quantity_produced if production_order.quantity_produced > 0 else 0
        },
        'dates': {
            'created': production_order.created_at,
            'start_date': production_order.start_date,
            'due_date': production_order.due_date,
            'actual_start': production_order.actual_start_date,
            'actual_completion': production_order.actual_completion_date
        }
    }


def calculate_production_requirements(bom_id, quantity_to_produce, location_id):
    """
    Calculate component requirements and check availability

    Args:
        bom_id: BOM ID
        quantity_to_produce: Quantity of finished goods to produce
        location_id: Production location

    Returns:
        dict: Requirements and availability for each component
    """
    from models import Batch

    bom = BillOfMaterials.query.get(bom_id)
    if not bom:
        raise ValueError(f"BOM {bom_id} not found")

    requirements = []

    for component in bom.components:
        required_qty = int(component.quantity * quantity_to_produce)

        # Check available inventory
        inv_loc = InventoryLocation.query.filter_by(
            item_id=component.component_item_id,
            location_id=location_id
        ).first()

        available_qty = inv_loc.quantity if inv_loc else 0

        # Get available batches
        batches = Batch.query.filter(
            Batch.item_id == component.component_item_id,
            Batch.location_id == location_id,
            Batch.quantity_available > 0,
            Batch.status == 'active'
        ).order_by(Batch.received_date.asc()).all()

        requirements.append({
            'component_sku': component.component.sku,
            'component_name': component.component.name,
            'required_quantity': required_qty,
            'available_quantity': available_qty,
            'shortage': max(0, required_qty - available_qty),
            'is_sufficient': available_qty >= required_qty,
            'available_batches': len(batches),
            'unit_of_measure': component.unit_of_measure or component.component.unit_of_measure
        })

    all_sufficient = all(r['is_sufficient'] for r in requirements)

    return {
        'bom_number': bom.bom_number,
        'finished_item': bom.finished_item.name,
        'quantity_to_produce': quantity_to_produce,
        'requirements': requirements,
        'all_components_available': all_sufficient
    }
