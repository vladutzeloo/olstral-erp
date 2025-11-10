# Production Order FIFO Requirements

## Overview

This document outlines the requirements and implementation plan for linking FIFO batch tracking to internal production orders.

## Current State

### What We Have ✓
- **Batch Tracking System**: Full batch/lot tracking for received items
- **FIFO Implementation**: consume_batches_fifo() function in batch_utils.py
- **BOM (Bill of Materials)**: Defines components needed for finished items
- **Production Receipts**: Can receive finished goods with internal_order_number
- **Batch Creation on Receipt**: Batches are automatically created when receiving items

### What's Missing ✗
- **Production Order Module**: No formal production order system
- **Component Consumption Tracking**: No tracking of components consumed during production
- **Work-in-Progress (WIP) Tracking**: No WIP inventory tracking
- **Production Scheduling**: No production order scheduling
- **Labor/Machine Time**: No tracking of production resources

## Requirements for Full Production Order FIFO

### 1. Production Order Model

Create a new `ProductionOrder` model:

```python
class ProductionOrder(db.Model):
    id
    order_number (e.g., "PROD-000001")
    finished_item_id
    bom_id
    quantity_ordered
    quantity_produced
    status ('draft', 'released', 'in_progress', 'completed', 'cancelled')
    start_date
    due_date
    actual_start_date
    actual_completion_date
    location_id (production location)
    created_by
    created_at
    updated_at
```

### 2. Production Order Component Consumption

Create a new `ProductionConsumption` model:

```python
class ProductionConsumption(db.Model):
    id
    production_order_id
    component_item_id
    quantity_consumed
    batch_id (consumed batch - for FIFO tracking)
    cost_per_unit (from batch)
    consumed_date
    consumed_by
    notes
```

### 3. FIFO Component Consumption Workflow

When a production order starts:

1. **Load BOM**: Get components required from BOM
2. **Calculate Requirements**: quantity_needed = bom_component_quantity * production_quantity
3. **FIFO Consumption**: For each component:
   ```python
   consumed_batches = consume_batches_fifo(
       item_id=component_item_id,
       quantity_needed=required_quantity,
       location_id=production_location_id,
       reference_type='production_order',
       reference_id=production_order_id,
       notes=f"Production Order {order_number}",
       created_by=current_user.id
   )
   ```
4. **Track Consumption**: Create ProductionConsumption records linking batches to production order
5. **Cost Calculation**: Calculate production cost based on FIFO batch costs

### 4. Finished Goods Receipt with Batch Creation

When production completes:

1. **Create Receipt**: Generate receipt with source_type='production'
2. **Create Batch**: Automatically create batch for finished goods
3. **Link to Production Order**: batch.internal_order_number = production_order_number
4. **Cost Tracking**: batch.cost_per_unit = total_component_cost / quantity_produced
5. **Traceability**: Link finished goods batch to consumed component batches

## Implementation Steps

### Phase 1: Production Order Module (Essential)
- [ ] Create ProductionOrder model
- [ ] Create ProductionConsumption model
- [ ] Create production order creation form
- [ ] Implement production order list/view
- [ ] Add production order status workflow

### Phase 2: FIFO Component Consumption (Critical for Requirement)
- [ ] Implement component picking/consumption function
- [ ] Integrate consume_batches_fifo() for component consumption
- [ ] Create consumption transaction records
- [ ] Update inventory after consumption
- [ ] Display consumed batches in production order view

### Phase 3: Finished Goods Production Receipt
- [ ] Link production receipts to production orders
- [ ] Calculate FIFO cost for finished goods
- [ ] Create batches for produced items with cost tracking
- [ ] Link finished goods batches to production order

### Phase 4: Reporting & Analytics
- [ ] Production cost reports (FIFO-based)
- [ ] Component consumption reports
- [ ] Batch traceability reports (forward and backward)
- [ ] Production efficiency metrics

## Example Workflow

### Scenario: Produce 100 units of Finished Part "FIN-BAR-SS304-00001"

**BOM Components:**
- RAW-SHT-SS304-00001: 2 units per finished part
- PKG-BOX-CARD-00001: 1 unit per finished part

**Step 1: Create Production Order**
```
Order: PROD-000045
Item: FIN-BAR-SS304-00001
Quantity: 100
Status: Released
```

**Step 2: Start Production - Consume Components (FIFO)**

For RAW-SHT-SS304-00001 (need 200 units):
```python
consumed = consume_batches_fifo(
    item_id=raw_sheet_id,
    quantity_needed=200,
    location_id=production_location,
    reference_type='production_order',
    reference_id=45
)
# Result: Consumes from oldest batches first
# BATCH-000123: 150 units @ $10/unit = $1,500
# BATCH-000156: 50 units @ $12/unit = $600
# Total cost: $2,100
```

For PKG-BOX-CARD-00001 (need 100 units):
```python
consumed = consume_batches_fifo(
    item_id=box_id,
    quantity_needed=100,
    location_id=production_location,
    reference_type='production_order',
    reference_id=45
)
# BATCH-000089: 100 units @ $0.50/unit = $50
# Total cost: $50
```

**Total Component Cost: $2,150**

**Step 3: Complete Production - Create Finished Goods Receipt**
```
Receipt: RCV-001234
Source: Production
Internal Order: PROD-000045
Quantity: 100
```

**Step 4: Create Batch for Finished Goods**
```
Batch: BATCH-001500
Item: FIN-BAR-SS304-00001
Quantity: 100
Cost per unit: $2,150 / 100 = $21.50
Internal Order: PROD-000045
```

**Step 5: Traceability**
- Finished goods batch BATCH-001500 can be traced back to:
  - BATCH-000123 (raw material)
  - BATCH-000156 (raw material)
  - BATCH-000089 (packaging)

## Benefits of Production FIFO

1. **Accurate Costing**: True cost of production based on actual materials consumed
2. **Traceability**: Full forward/backward traceability from raw materials to finished goods
3. **Compliance**: Meets quality and regulatory traceability requirements
4. **Inventory Valuation**: Accurate FIFO-based inventory valuation
5. **Quality Control**: Can identify batches if quality issues arise

## API Endpoints Needed

- `POST /production-orders/new` - Create production order
- `GET /production-orders/<id>` - View production order details
- `POST /production-orders/<id>/start` - Start production (consume components)
- `POST /production-orders/<id>/complete` - Complete production (create receipt)
- `GET /production-orders/<id>/consumed-batches` - View consumed batches
- `GET /production-orders/<id>/cost-breakdown` - FIFO cost breakdown

## Database Changes

Run migration to add:
- production_orders table
- production_consumption table
- Update batches table (already has internal_order_number field)

## Notes

- The current system is **ready for FIFO production** from a technical standpoint
- The batch_utils.py module has all necessary FIFO functions
- Only need to create the Production Order UI and workflow
- All batch tracking and FIFO consumption logic is already implemented

## Timeline Estimate

- **Phase 1**: 2-3 days (Production Order Module)
- **Phase 2**: 1-2 days (FIFO Component Consumption)
- **Phase 3**: 1 day (Finished Goods Receipt Integration)
- **Phase 4**: 2-3 days (Reporting)

**Total**: 6-9 days for complete production FIFO system
