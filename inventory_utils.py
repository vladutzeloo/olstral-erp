"""
Inventory utility functions for stock management
"""

from extensions import db
from models import InventoryLocation, StockMovement, InventoryTransaction
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError


def move_stock(item_id, from_location_id, to_location_id, quantity,
               moved_by, reason=None, notes=None, movement_type='transfer'):
    """
    Move stock from one location to another with full traceability.

    Args:
        item_id: ID of the item to move
        from_location_id: Source location ID
        to_location_id: Destination location ID
        quantity: Quantity to move
        moved_by: User ID performing the move
        reason: Reason for the move (optional)
        notes: Additional notes (optional)
        movement_type: Type of movement (transfer, relocation, rebalance)

    Returns:
        tuple: (success: bool, message: str, movement: StockMovement or None)
    """
    try:
        # Validate inputs
        if quantity <= 0:
            return False, "Quantity must be greater than zero", None

        if from_location_id == to_location_id:
            return False, "Source and destination locations must be different", None

        # Get or create source inventory location
        from_inv = InventoryLocation.query.filter_by(
            item_id=item_id,
            location_id=from_location_id
        ).first()

        if not from_inv or from_inv.quantity < quantity:
            available = from_inv.quantity if from_inv else 0
            return False, f"Insufficient stock. Available: {available}, Requested: {quantity}", None

        # Get or create destination inventory location
        to_inv = InventoryLocation.query.filter_by(
            item_id=item_id,
            location_id=to_location_id
        ).first()

        if not to_inv:
            to_inv = InventoryLocation(
                item_id=item_id,
                location_id=to_location_id,
                quantity=0
            )
            db.session.add(to_inv)

        # Generate movement number
        last_movement = StockMovement.query.order_by(StockMovement.id.desc()).first()
        if last_movement:
            num = int(last_movement.movement_number.split('-')[1]) + 1
        else:
            num = 1
        movement_number = f'MOV-{num:06d}'

        # Create stock movement record
        movement = StockMovement(
            movement_number=movement_number,
            item_id=item_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            movement_type=movement_type,
            reason=reason,
            status='completed',
            moved_by=moved_by,
            moved_at=datetime.utcnow(),
            notes=notes
        )
        db.session.add(movement)

        # Update inventory quantities
        from_inv.quantity -= quantity
        to_inv.quantity += quantity
        from_inv.updated_at = datetime.utcnow()
        to_inv.updated_at = datetime.utcnow()

        # Create inventory transactions for audit trail
        # Deduction from source
        trans_out = InventoryTransaction(
            item_id=item_id,
            location_id=from_location_id,
            transaction_type='transfer_out',
            quantity=-quantity,
            reference_type='stock_movement',
            reference_id=movement.id,
            notes=f"Moved to {to_inv.location.name}. {reason or ''}",
            created_by=moved_by,
            created_at=datetime.utcnow()
        )
        db.session.add(trans_out)

        # Addition to destination
        trans_in = InventoryTransaction(
            item_id=item_id,
            location_id=to_location_id,
            transaction_type='transfer_in',
            quantity=quantity,
            reference_type='stock_movement',
            reference_id=movement.id,
            notes=f"Moved from {from_inv.location.name}. {reason or ''}",
            created_by=moved_by,
            created_at=datetime.utcnow()
        )
        db.session.add(trans_in)

        # Commit all changes
        db.session.commit()

        return True, f"Successfully moved {quantity} units", movement

    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}", None
    except Exception as e:
        db.session.rollback()
        return False, f"Error: {str(e)}", None


def get_stock_by_location(item_id, location_type=None):
    """
    Get stock breakdown by location for an item.

    Args:
        item_id: ID of the item
        location_type: Filter by location type (optional)

    Returns:
        list: List of dicts with location and quantity info
    """
    from models import Item, Location

    item = Item.query.get(item_id)
    if not item:
        return []

    result = []
    for inv_loc in item.inventory_locations:
        if location_type and inv_loc.location.type != location_type:
            continue

        result.append({
            'location_id': inv_loc.location_id,
            'location_code': inv_loc.location.code,
            'location_name': inv_loc.location.name,
            'location_type': inv_loc.location.type,
            'zone': inv_loc.location.zone,
            'quantity': inv_loc.quantity,
            'bin_location': inv_loc.bin_location,
            'last_counted': inv_loc.last_counted
        })

    return result


def get_movement_history(item_id=None, location_id=None, limit=50):
    """
    Get stock movement history.

    Args:
        item_id: Filter by item (optional)
        location_id: Filter by location (involved in movement) (optional)
        limit: Maximum number of records to return

    Returns:
        list: List of StockMovement records
    """
    query = StockMovement.query

    if item_id:
        query = query.filter_by(item_id=item_id)

    if location_id:
        query = query.filter(
            (StockMovement.from_location_id == location_id) |
            (StockMovement.to_location_id == location_id)
        )

    return query.order_by(StockMovement.moved_at.desc()).limit(limit).all()


def check_location_capacity(location_id):
    """
    Check current capacity usage for a location.

    Returns:
        dict: Capacity information
    """
    from models import Location

    location = Location.query.get(location_id)
    if not location:
        return None

    current_qty = location.get_current_quantity()

    return {
        'location_id': location.id,
        'location_name': location.name,
        'current_quantity': current_qty,
        'capacity': location.capacity,
        'capacity_percentage': location.get_capacity_percentage(),
        'is_over_capacity': location.is_over_capacity(),
        'available_capacity': location.capacity - current_qty if location.capacity else None
    }
