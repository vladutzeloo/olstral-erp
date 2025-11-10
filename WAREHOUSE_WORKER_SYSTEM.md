# Warehouse Worker System

## Overview

The Warehouse Worker system provides a simplified, focused interface for warehouse staff who handle day-to-day inventory operations without needing access to purchasing, production planning, or administrative functions.

---

## User Account

### Default Warehouse Worker

**Username:** WHM
**Password:** WHM123
**Role:** warehouse_worker
**Email:** whm@warehouse.com

---

## Permissions

### ✅ Warehouse Worker CAN:

**Core Tasks:**
- ✅ Receive materials from:
  - Purchase Orders (PO)
  - Production (internal orders)
  - External Processes
- ✅ Create shipments to customers
- ✅ Move stock between locations
- ✅ View inventory levels and batches
- ✅ View items and locations
- ✅ Track FIFO batch information
- ✅ View reports (read-only)
- ✅ See their own activity history

### ❌ Warehouse Worker CANNOT:

**Restricted Functions:**
- ❌ Create Purchase Orders (POs)
- ❌ Create Production Orders
- ❌ Create/Edit BOMs (Bill of Materials)
- ❌ Manage users or permissions
- ❌ Manage suppliers or clients
- ❌ Create/delete items
- ❌ Configure system settings

---

## Simplified Dashboard

### Access
Navigate to: `/warehouse/dashboard`
Or login with WHM account (automatic redirect)

### Dashboard Features

**Quick Stats:**
- Today's receipts count
- Today's shipments count
- Pending POs to receive
- Pending external processes
- Low stock alerts
- Total active locations

**Today's Activity:**
- Recent receipts (last 10)
- Recent shipments (last 10)
- Recent stock movements (last 10)

**Pending Tasks:**
- POs waiting to be received
- External processes waiting for return
- Low stock items requiring attention

**Quick Actions:**
- Quick Receive
- Quick Ship
- Stock Lookup
- View My Activity

---

## Key Features

### 1. Quick Receive Interface

**Purpose:** Simplified receiving process

**Access:** `/warehouse/quick-receive`

**Features:**
- See all pending POs at a glance
- See all pending external processes
- One-click access to receive materials
- Auto-populated item lists
- Batch tracking automatic

**Workflow:**
```
1. Select reception source:
   - Purchase Order (shows pending POs)
   - Production (enter internal order number)
   - External Process (shows pending returns)

2. Select location

3. Add items:
   - Type/search item name or SKU
   - Enter supplier batch number (optional)
   - Enter quantity received
   - Enter scrap quantity (if damaged)

4. Submit → Automatically creates:
   - Receipt with unique number (RCV-XXXXXX)
   - Batches for FIFO tracking (BATCH-XXXXXX)
   - Inventory updates
   - Transaction audit trail
```

### 2. Quick Ship Interface

**Purpose:** Simplified shipping process

**Access:** `/warehouse/quick-ship`

**Features:**
- Quick item search
- Automatic FIFO batch consumption
- Real-time stock availability
- Location-based shipping

**Workflow:**
```
1. Select from location

2. Add items to ship:
   - Search by SKU or name
   - Enter quantity
   - System shows available stock

3. Enter customer details:
   - Customer name
   - Shipping address
   - Tracking number (optional)

4. Submit → Automatically:
   - Consumes oldest batches (FIFO)
   - Creates shipment (SHP-XXXXXX)
   - Updates inventory
   - Records FIFO cost
```

### 3. Stock Lookup

**Purpose:** Quick inventory checking

**Access:** `/warehouse/stock-lookup`

**Features:**
- Search any item by SKU, name, or neo_code
- Filter by location
- See batch details (FIFO order)
- View available quantities
- Check multiple locations

**Information Displayed:**
```
For each item:
- Total quantity across locations
- Quantity per location
- Available batches (oldest first)
- Batch numbers and quantities
- Received dates (for FIFO)
- Supplier batch numbers
```

### 4. My Activity

**Purpose:** Track personal work history

**Access:** `/warehouse/my-activity`

**Shows:**
- My receipts (last 20)
- My stock movements (last 20)
- My shipments (last 20)
- My transactions (last 30)

**Use Cases:**
- Review today's work
- Verify completed tasks
- Track productivity
- Audit trail for accountability

---

## Role-Based Access Control

### Technical Implementation

**Role Decorators:**
```python
@role_required('warehouse_worker', 'user', 'manager', 'admin')
def warehouse_function():
    # This function allows warehouse workers and up
    ...

@min_role_required('manager')
def manager_only_function():
    # This function requires manager or admin
    ...
```

**Permission Checking in Templates:**
```html
{% if can_user('create_po') %}
    <a href="/purchase-orders/new">Create PO</a>
{% endif %}
```

**Available Permissions:**
- `view_inventory`
- `receive_materials`
- `ship_materials`
- `move_stock`
- `view_batches`
- `create_po`
- `create_production_order`
- `create_bom`
- `manage_users`
- `view_reports`
- `create_reports`

---

## Navigation for Warehouse Workers

### Simplified Menu Structure

**Main Menu:**
```
📦 Warehouse Dashboard
   ├─ 📥 Quick Receive
   ├─ 📤 Quick Ship
   ├─ 📊 Stock Lookup
   └─ 📋 My Activity

📦 Inventory
   ├─ View Inventory
   ├─ Stock Movements
   └─ Batches (FIFO)

📦 Operations
   ├─ Receipts (History)
   ├─ Shipments (History)
   └─ Scraps

📦 Reference
   ├─ Items (Read-only)
   ├─ Locations (Read-only)
   └─ Reports (View-only)
```

### Hidden from Warehouse Workers

**Menu items NOT shown:**
- Purchase Orders (Create/Edit)
- Production Orders (Create/Edit)
- BOMs (Create/Edit)
- User Management
- Supplier Management
- Client Management
- System Configuration

---

## Automatic Features

### 1. Auto-Redirect on Login

When WHM logs in:
```
Login → Detect role → Redirect to /warehouse/dashboard
```

### 2. Auto-Batch Creation

When receiving materials:
```
Receive 100 units → Automatically creates:
- Receipt: RCV-000123
- Batch: BATCH-000456
  * Quantity: 100
  * Cost: $10/unit (from item master)
  * Supplier Batch: SS-2024-A-123
  * Received Date: 2024-01-15 (for FIFO)
```

### 3. Auto-FIFO Consumption

When shipping:
```
Ship 50 units → System automatically:
1. Finds oldest batches (FIFO)
2. Consumes BATCH-000001: 30 units @ $10 = $300
3. Consumes BATCH-000005: 20 units @ $12 = $240
4. Total cost: $540
5. Updates inventory
6. Creates audit trail
```

---

## Benefits for Warehouse Staff

### 1. Simplified Interface
- No clutter from purchasing/production features
- Focus on core warehouse tasks
- Faster task completion

### 2. Clear Workflow
- Step-by-step processes
- Visual guides
- Clear error messages

### 3. Automatic Compliance
- FIFO enforced automatically
- Batch tracking automatic
- Audit trail automatic

### 4. Accountability
- All actions tracked
- "My Activity" shows personal history
- Complete traceability

### 5. Real-time Information
- Live stock levels
- Pending PO list
- Low stock alerts

---

## Example Workflows

### Workflow 1: Receive from Purchase Order

```
Scenario: Receive 500 units of stainless steel sheet

Steps for WHM:
1. Login → Auto-redirect to warehouse dashboard
2. Click "Quick Receive"
3. Select "Purchase Order" → See PO-000123 in list
4. Click PO-000123 → Items auto-populate
5. Confirm quantities:
   - RAW-SHT-SS304-00001: 500 units
   - Supplier batch: SS-2024-A-123
6. Select location: WAREHOUSE-MAIN
7. Submit

Result:
✓ Receipt RCV-000234 created
✓ Batch BATCH-001234 created (FIFO tracking)
✓ Inventory updated (+500 units)
✓ PO status updated
✓ Audit trail created
✓ Ready for production use
```

### Workflow 2: Receive from Production

```
Scenario: Receive 100 finished parts from production

Steps for WHM:
1. Go to Quick Receive
2. Select "Production"
3. Enter internal order: PROD-000045
4. Search/add item: FIN-BAR-SS304-00001
5. Enter quantity: 100
6. Select location: WAREHOUSE-FINISHED
7. Submit

Result:
✓ Receipt RCV-000235 created
✓ Batch BATCH-001235 created with FIFO cost
✓ Linked to production order PROD-000045
✓ Full traceability to component batches
✓ Inventory updated
```

### Workflow 3: Ship to Customer

```
Scenario: Ship 75 units to customer

Steps for WHM:
1. Go to Quick Ship
2. Select from location: WAREHOUSE-FINISHED
3. Search item: FIN-BAR-SS304-00001
4. Enter quantity: 75
5. Enter customer: ABC Manufacturing
6. Enter address
7. Enter tracking number (optional)
8. Submit

Result:
✓ Shipment SHP-000156 created
✓ System automatically uses FIFO:
  - Consumed BATCH-001235: 75 units @ $21.50
✓ Inventory updated (-75 units)
✓ True FIFO cost calculated: $1,612.50
✓ Full traceability maintained
```

### Workflow 4: Check Stock

```
Scenario: Customer calls asking about availability

Steps for WHM:
1. Go to Stock Lookup
2. Type item: "SS304" or "stainless"
3. See results:
   - RAW-SHT-SS304-00001
   - Total: 425 units
   - Locations:
     * WAREHOUSE-MAIN: 400 units
     * PRODUCTION-FLOOR: 25 units
   - Batches (oldest first):
     * BATCH-000123: 150 units (Received 2024-01-15)
     * BATCH-000156: 275 units (Received 2024-01-20)

Answer customer immediately with accurate info!
```

---

## Security & Audit

### All Actions Tracked

Every warehouse action creates audit records:
- **Who:** User ID (WHM)
- **What:** Action type (receipt, shipment, movement)
- **When:** Timestamp
- **Where:** Location
- **Details:** Reference numbers, quantities

### Read-Only Restrictions

Warehouse workers can **VIEW** but not **MODIFY:**
- Purchase Orders
- Production Orders
- BOMs
- Items (master data)
- Suppliers
- Clients

### Session Security

- Auto-logout after inactivity
- Password requirements
- Login history tracked

---

## Training Guide

### For New Warehouse Staff

**Day 1:**
1. Login with WHM credentials
2. Tour of dashboard
3. Practice receiving from PO
4. Practice stock lookup

**Day 2:**
1. Practice shipping
2. Practice stock movements
3. Review "My Activity"

**Day 3:**
1. Handle real receipts
2. Handle real shipments
3. Supervised work

**Week 1:**
- Independent work
- Questions answered
- Best practices

---

## Troubleshooting

### Common Issues

**Q: Cannot create Purchase Order**
A: Warehouse workers don't have this permission. Contact purchasing department.

**Q: Item not found in stock lookup**
A: Check spelling. Item may be inactive. Contact admin.

**Q: Cannot receive - location not found**
A: Location may be inactive. Contact supervisor.

**Q: Batch number not showing**
A: Supplier batch is optional. System creates internal batch automatically.

**Q: FIFO cost seems wrong**
A: FIFO uses oldest batch costs. This is correct and automatic.

---

## Summary

The Warehouse Worker system provides:

✅ **Simplified Interface** - Only what warehouse staff need
✅ **Automatic FIFO** - No manual batch selection
✅ **Full Traceability** - Every action tracked
✅ **Role Security** - Restricted access to appropriate functions
✅ **Real-time Data** - Always up-to-date stock levels
✅ **Easy Training** - Intuitive workflows
✅ **Accountability** - Complete audit trail

**Perfect for warehouse staff who need to:**
- Receive materials efficiently
- Ship orders accurately
- Track inventory in real-time
- Maintain FIFO compliance

**Without complexity of:**
- Production planning
- Purchasing decisions
- BOM management
- System administration
