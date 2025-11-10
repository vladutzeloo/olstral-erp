"""
Batch and FIFO Inventory Management Utilities

Provides helper functions for:
- Creating batches during reception
- FIFO-based batch consumption
- Batch transfers between locations
- Batch availability checking
"""

from datetime import datetime
from extensions import db
from models import Batch, BatchTransaction, InventoryTransaction, InventoryLocation


def create_batch(item_id, receipt_id, location_id, quantity, **kwargs):
    """
    Create a new batch during reception

    Args:
        item_id: Item ID
        receipt_id: Receipt ID that created this batch
        location_id: Location where batch is stored
        quantity: Quantity in batch
        **kwargs: Optional fields (batch_number, supplier_batch_number, po_id, internal_order_number,
                 external_process_id, cost_per_unit, ownership_type, expiry_date, notes, created_by,
                 bin_location)

    Returns:
        Batch: Created batch object
    """
    # Use provided batch number or auto-generate
    batch_number = kwargs.get('batch_number')
    if not batch_number:
        # Auto-generate batch number
        last_batch = Batch.query.order_by(Batch.id.desc()).first()
        if last_batch:
            # Try to extract number from last batch, handle custom batch numbers
            try:
                if last_batch.batch_number.startswith('BATCH-'):
                    last_num = int(last_batch.batch_number.split('-')[-1])
                    batch_number = f"BATCH-{last_num + 1:06d}"
                else:
                    # If last batch doesn't follow pattern, start from current ID
                    batch_number = f"BATCH-{last_batch.id + 1:06d}"
            except (ValueError, IndexError):
                # If parsing fails, use ID-based numbering
                batch_number = f"BATCH-{last_batch.id + 1:06d}"
        else:
            batch_number = "BATCH-000001"

    # Create batch
    ownership_type = kwargs.get('ownership_type', 'owned')
    batch = Batch(
        batch_number=batch_number,
        item_id=item_id,
        receipt_id=receipt_id,
        location_id=location_id,
        bin_location=kwargs.get('bin_location'),
        quantity_original=quantity,
        quantity_available=quantity,
        received_date=datetime.utcnow(),
        supplier_batch_number=kwargs.get('supplier_batch_number'),
        po_id=kwargs.get('po_id'),
        internal_order_number=kwargs.get('internal_order_number'),
        external_process_id=kwargs.get('external_process_id'),
        cost_per_unit=kwargs.get('cost_per_unit', 0.0),
        ownership_type=ownership_type,
        expiry_date=kwargs.get('expiry_date'),
        status='active',
        notes=kwargs.get('notes'),
        created_by=kwargs.get('created_by')
    )

    db.session.add(batch)
    db.session.flush()

    # Create initial batch transaction
    transaction = BatchTransaction(
        batch_id=batch.id,
        transaction_type='receipt',
        quantity=quantity,
        reference_type='receipt',
        reference_id=receipt_id,
        to_location_id=location_id,
        notes=f"Batch created from receipt",
        created_by=kwargs.get('created_by')
    )
    db.session.add(transaction)

    return batch


def get_available_batches_fifo(item_id, location_id=None, exclude_expired=True):
    """
    Get available batches for an item in FIFO order (oldest first)

    Args:
        item_id: Item ID
        location_id: Optional location filter
        exclude_expired: Exclude expired batches (default True)

    Returns:
        list[Batch]: List of available batches in FIFO order
    """
    query = Batch.query.filter(
        Batch.item_id == item_id,
        Batch.quantity_available > 0,
        Batch.status == 'active'
    )

    if location_id:
        query = query.filter(Batch.location_id == location_id)

    if exclude_expired:
        query = query.filter(
            db.or_(
                Batch.expiry_date.is_(None),
                Batch.expiry_date > datetime.utcnow()
            )
        )

    # Order by received_date (FIFO - First In, First Out)
    return query.order_by(Batch.received_date.asc()).all()


def consume_batches_fifo(item_id, quantity_needed, location_id, **kwargs):
    """
    Consume batches using FIFO logic (oldest batches first)

    Args:
        item_id: Item ID
        quantity_needed: Total quantity to consume
        location_id: Location to consume from
        **kwargs: reference_type, reference_id, notes, created_by

    Returns:
        list[dict]: List of consumed batches with details:
                   [{'batch_id': x, 'batch_number': 'BATCH-000001', 'quantity': y, 'cost_per_unit': z}, ...]

    Raises:
        ValueError: If insufficient quantity available
    """
    # Get available batches in FIFO order
    available_batches = get_available_batches_fifo(item_id, location_id)

    # Check if sufficient quantity available
    total_available = sum(b.quantity_available for b in available_batches)
    if total_available < quantity_needed:
        raise ValueError(
            f"Insufficient quantity available for item {item_id}. "
            f"Needed: {quantity_needed}, Available: {total_available}"
        )

    consumed_batches = []
    remaining_needed = quantity_needed

    # Consume from oldest batches first (FIFO)
    for batch in available_batches:
        if remaining_needed <= 0:
            break

        # Determine how much to consume from this batch
        consume_qty = min(batch.quantity_available, remaining_needed)

        # Consume from batch
        batch.consume(consume_qty)

        # Create batch transaction
        transaction = BatchTransaction(
            batch_id=batch.id,
            transaction_type='consumption',
            quantity=-consume_qty,
            reference_type=kwargs.get('reference_type'),
            reference_id=kwargs.get('reference_id'),
            from_location_id=location_id,
            notes=kwargs.get('notes', f"FIFO consumption"),
            created_by=kwargs.get('created_by')
        )
        db.session.add(transaction)

        # Track consumed batch details
        consumed_batches.append({
            'batch_id': batch.id,
            'batch_number': batch.batch_number,
            'quantity': consume_qty,
            'cost_per_unit': batch.cost_per_unit
        })

        remaining_needed -= consume_qty

    return consumed_batches


def transfer_batch(batch_id, from_location_id, to_location_id, quantity, **kwargs):
    """
    Transfer batch (or partial batch) between locations

    Args:
        batch_id: Batch ID to transfer
        from_location_id: Source location
        to_location_id: Destination location
        quantity: Quantity to transfer
        **kwargs: reference_type, reference_id, notes, created_by

    Returns:
        Batch: New batch at destination (if partial) or updated batch (if full transfer)

    Raises:
        ValueError: If insufficient quantity or invalid locations
    """
    batch = Batch.query.get(batch_id)
    if not batch:
        raise ValueError(f"Batch {batch_id} not found")

    if batch.location_id != from_location_id:
        raise ValueError(f"Batch is not at source location {from_location_id}")

    if quantity > batch.quantity_available:
        raise ValueError(
            f"Cannot transfer {quantity} from batch {batch.batch_number}. "
            f"Only {batch.quantity_available} available."
        )

    # Full transfer - just update location
    if quantity == batch.quantity_available:
        batch.location_id = to_location_id

        # Create transaction
        transaction = BatchTransaction(
            batch_id=batch.id,
            transaction_type='transfer',
            quantity=quantity,
            reference_type=kwargs.get('reference_type', 'stock_movement'),
            reference_id=kwargs.get('reference_id'),
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            notes=kwargs.get('notes', 'Batch transfer'),
            created_by=kwargs.get('created_by')
        )
        db.session.add(transaction)

        return batch

    # Partial transfer - create new batch at destination
    else:
        # Reduce source batch
        batch.quantity_available -= quantity

        # Create transaction for source
        transaction_out = BatchTransaction(
            batch_id=batch.id,
            transaction_type='transfer_out',
            quantity=-quantity,
            reference_type=kwargs.get('reference_type', 'stock_movement'),
            reference_id=kwargs.get('reference_id'),
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            notes=kwargs.get('notes', 'Partial batch transfer out'),
            created_by=kwargs.get('created_by')
        )
        db.session.add(transaction_out)

        # Create new batch at destination
        new_batch = Batch(
            batch_number=f"{batch.batch_number}-SPLIT",
            item_id=batch.item_id,
            receipt_id=batch.receipt_id,
            location_id=to_location_id,
            bin_location=kwargs.get('to_bin_location'),  # New bin location at destination
            quantity_original=quantity,
            quantity_available=quantity,
            received_date=batch.received_date,  # Keep original received date for FIFO
            expiry_date=batch.expiry_date,
            supplier_batch_number=batch.supplier_batch_number,
            po_id=batch.po_id,
            internal_order_number=batch.internal_order_number,
            external_process_id=batch.external_process_id,
            cost_per_unit=batch.cost_per_unit,
            ownership_type=batch.ownership_type,
            status='active',
            notes=f"Split from {batch.batch_number}",
            created_by=kwargs.get('created_by')
        )
        db.session.add(new_batch)
        db.session.flush()

        # Create transaction for destination
        transaction_in = BatchTransaction(
            batch_id=new_batch.id,
            transaction_type='transfer_in',
            quantity=quantity,
            reference_type=kwargs.get('reference_type', 'stock_movement'),
            reference_id=kwargs.get('reference_id'),
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            notes=kwargs.get('notes', 'Partial batch transfer in'),
            created_by=kwargs.get('created_by')
        )
        db.session.add(transaction_in)

        return new_batch


def get_batch_summary(item_id, location_id=None):
    """
    Get summary of batches for an item

    Args:
        item_id: Item ID
        location_id: Optional location filter

    Returns:
        dict: Summary with total_batches, total_quantity, oldest_batch_date, batches_list
    """
    query = Batch.query.filter(
        Batch.item_id == item_id,
        Batch.quantity_available > 0,
        Batch.status == 'active'
    )

    if location_id:
        query = query.filter(Batch.location_id == location_id)

    batches = query.order_by(Batch.received_date.asc()).all()

    return {
        'total_batches': len(batches),
        'total_quantity': sum(b.quantity_available for b in batches),
        'oldest_batch_date': batches[0].received_date if batches else None,
        'newest_batch_date': batches[-1].received_date if batches else None,
        'batches': [
            {
                'batch_number': b.batch_number,
                'location': b.location.name,
                'quantity': b.quantity_available,
                'received_date': b.received_date,
                'expiry_date': b.expiry_date,
                'cost_per_unit': b.cost_per_unit,
                'supplier_batch_number': b.supplier_batch_number,
                'source': (
                    f"PO {b.purchase_order.po_number}" if b.po_id else
                    f"Production {b.internal_order_number}" if b.internal_order_number else
                    f"External Process {b.external_process.process_number}" if b.external_process_id else
                    "Unknown"
                )
            }
            for b in batches
        ]
    }


def calculate_fifo_cost(consumed_batches):
    """
    Calculate total FIFO cost for consumed batches

    Args:
        consumed_batches: List of consumed batch dicts from consume_batches_fifo()

    Returns:
        dict: {'total_cost': x, 'average_cost_per_unit': y}
    """
    if not consumed_batches:
        return {'total_cost': 0.0, 'average_cost_per_unit': 0.0}

    total_cost = sum(b['quantity'] * b['cost_per_unit'] for b in consumed_batches)
    total_quantity = sum(b['quantity'] for b in consumed_batches)
    avg_cost = total_cost / total_quantity if total_quantity > 0 else 0.0

    return {
        'total_cost': total_cost,
        'average_cost_per_unit': avg_cost,
        'batch_details': consumed_batches
    }
