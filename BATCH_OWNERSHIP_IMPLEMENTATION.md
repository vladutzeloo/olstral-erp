# Batch Ownership & Manual Batch Number Implementation

## Overview

This implementation adds material ownership tracking and manual batch number input to the ERP system, addressing key requirements for managing consignment and lohn (customer-owned) materials.

## Features Implemented

### 1. Manual Batch Number Input
- **Previous behavior**: Batch numbers were auto-generated as BATCH-XXXXXX
- **New behavior**: Users can input custom batch numbers during receipt
- **Fallback**: If left blank, system auto-generates batch number
- **Benefits**:
  - Match supplier batch numbers directly
  - Use your own batch numbering scheme
  - Better integration with external systems

### 2. Manual Cost Per Unit Input
- **Previous behavior**: Cost per unit automatically taken from item master
- **New behavior**: Users can input cost per unit for each batch during receipt
- **Fallback**: If left blank, uses item master cost
- **Benefits**:
  - Handle price variations between shipments
  - Record actual supplier costs
  - More accurate FIFO costing

### 3. Ownership Type Tracking
Three ownership types are now supported:

#### Owned (Default)
- Materials owned by your company
- **Counted in inventory value**
- Normal inventory operations

#### Consignment
- Materials owned by supplier but stored at your location
- **NOT counted in inventory value**
- Typically paid when consumed, not when received

#### Lohn
- Materials owned by customer sent for processing
- **NOT counted in inventory value**
- Common in toll manufacturing/contract processing

## Database Changes

### Batch Model Updates

New field added to `batches` table:
```sql
ownership_type VARCHAR(20) DEFAULT 'owned'
-- Values: 'owned', 'consignment', 'lohn'
```

## Implementation Details

### 1. Model Changes (`models.py`)
- Added `ownership_type` column to `Batch` model
- Default value: 'owned'
- Comment added explaining consignment/lohn materials don't count toward inventory value

### 2. Batch Creation Logic (`batch_utils.py`)
- `create_batch()` function updated to:
  - Accept optional `batch_number` parameter
  - Accept optional `ownership_type` parameter
  - Accept custom `cost_per_unit` in kwargs
  - Auto-generate batch number only if not provided
  - Handle mixed batch numbering schemes gracefully

### 3. Receipt Form Updates (`templates/receipts/new.html`)
New columns added to receipt item table:
- **Batch Number**: Text input with placeholder "Auto-gen if blank"
- **Cost/Unit**: Number input with placeholder "Blank = item cost"
- **Ownership**: Dropdown with options (Owned/Consignment/Lohn)

### 4. Receipt Processing (`routes/receipts.py`)
Enhanced to:
- Collect batch_number, cost_per_unit, and ownership_type from form
- Pass all parameters to `create_batch()`
- Use item master cost as fallback if cost not provided
- Default ownership to 'owned' if not specified

### 5. Inventory Valuation Updates

#### Dashboard (`routes/dashboard.py`)
```python
# Only counts owned batches
inventory_value = db.session.query(
    func.sum(Batch.quantity_available * Batch.cost_per_unit)
).filter(
    Batch.status == 'active',
    Batch.ownership_type == 'owned'  # Excludes consignment/lohn
).scalar() or 0
```

#### Inventory Valuation Report (`routes/reports.py`)
- Primary calculation excludes consignment/lohn materials
- Separate query shows consignment/lohn quantities (for visibility)
- Total value only includes owned materials

## Migration

### Running the Migration

```bash
python migrate_add_batch_ownership.py
```

The migration script will:
1. Check if batches table exists
2. Add ownership_type column if not present
3. Set all existing batches to 'owned'
4. Verify the migration succeeded

### Safe to Run
- ✓ Idempotent (can run multiple times)
- ✓ Won't affect existing data
- ✓ Backward compatible (existing batches default to 'owned')

## Usage Examples

### Example 1: Standard Purchase Order Receipt
```
Item: Steel Bar 10mm
Batch Number: [blank] → Auto-generates BATCH-000123
Cost/Unit: [blank] → Uses item master cost
Ownership: Owned → Counts in inventory value
```

### Example 2: Consignment Material Receipt
```
Item: Special Alloy Wire
Batch Number: SUPPLIER-2024-ABC → Custom batch number
Cost/Unit: 0.00 → Zero value (or leave blank)
Ownership: Consignment → Does NOT count in inventory value
```

### Example 3: Lohn (Customer Material) Receipt
```
Item: Customer Provided Parts
Batch Number: CUST-ORDER-789 → Customer's reference
Cost/Unit: 0.00 → Zero value (customer owns it)
Ownership: Lohn → Does NOT count in inventory value
```

### Example 4: Price Variation
```
Item: Copper Wire
Batch Number: [blank] → Auto-generates
Cost/Unit: 2.85 → This shipment's actual cost
Ownership: Owned → Counts in inventory at $2.85/unit
```

## Impact on Existing Functionality

### ✓ Compatible
- **FIFO consumption**: Works normally for all ownership types
- **Batch tracking**: All batches tracked regardless of ownership
- **Production orders**: Can consume any batch type
- **Shipments**: Can ship any batch type
- **Traceability**: Full traceability for all ownership types

### ✓ Enhanced
- **Inventory valuation**: Now accurately excludes non-owned materials
- **Dashboard**: Shows true owned inventory value
- **Reports**: Separate visibility of owned vs consignment/lohn

### No Breaking Changes
- Existing batches automatically set to 'owned'
- Existing code continues to work
- New fields have sensible defaults

## Financial Impact

### Before Implementation
```
Total Inventory Value = All Batches × Cost Per Unit
```

### After Implementation
```
Total Inventory Value = (Owned Batches Only) × Cost Per Unit
```

**Consignment and Lohn materials are excluded from inventory value calculations.**

## User Workflow Changes

### Receipt Creation
1. Select source (PO, Production, External Process)
2. Add items as before
3. **NEW**: Optionally enter batch number for each item
4. **NEW**: Optionally enter cost per unit for each item
5. **NEW**: Select ownership type (defaults to Owned)
6. Submit receipt

### Reporting
- Dashboard shows only owned inventory value
- Inventory valuation report separates owned vs consignment/lohn
- Batch list shows ownership type for each batch

## Testing Checklist

- [ ] Create receipt with auto-generated batch number (leave blank)
- [ ] Create receipt with manual batch number
- [ ] Create receipt with custom cost per unit
- [ ] Create receipt with ownership = Owned
- [ ] Create receipt with ownership = Consignment
- [ ] Create receipt with ownership = Lohn
- [ ] Verify dashboard inventory value excludes consignment/lohn
- [ ] Verify inventory valuation report excludes consignment/lohn
- [ ] Verify FIFO consumption works for all ownership types
- [ ] Verify batch traceability for all ownership types

## Files Modified

1. `models.py` - Added ownership_type field to Batch model
2. `batch_utils.py` - Updated create_batch() function
3. `routes/receipts.py` - Enhanced receipt processing
4. `templates/receipts/new.html` - Added form fields
5. `routes/reports.py` - Updated inventory valuation logic
6. `routes/dashboard.py` - Updated inventory value calculation

## Files Created

1. `migrate_add_batch_ownership.py` - Database migration script
2. `BATCH_OWNERSHIP_IMPLEMENTATION.md` - This documentation

## Benefits

### Accounting
- ✓ Accurate inventory valuation
- ✓ Consignment materials don't inflate asset value
- ✓ Lohn materials properly tracked but not valued
- ✓ Better financial reporting

### Operations
- ✓ Track customer-owned materials separately
- ✓ Match supplier batch numbering
- ✓ Handle price variations between shipments
- ✓ Maintain full traceability for all material types

### Compliance
- ✓ Proper accounting for consignment inventory
- ✓ Clear separation of owned vs non-owned materials
- ✓ Audit trail for all materials
- ✓ Support for toll manufacturing workflows

## Future Enhancements

Potential additions for future releases:
- Automatic consignment invoicing when consumed
- Consignment liability tracking
- Lohn processing cost tracking
- Ownership transfer workflows
- Consignment return processing
- Advanced ownership reports

## Support

For questions or issues, refer to:
- Batch tracking documentation: `FIFO_SYSTEM_COMPLETE.md`
- Production FIFO documentation (existing)
- Inventory management documentation (existing)
