# Enhanced Inventory ERP System - Setup Guide

## 🚀 Quick Start

### Option 1: Fresh Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will:
- Automatically create the database with all tables
- Create a default admin user (username: admin, password: admin123)
- Start on http://localhost:5000

### Option 2: Upgrading Existing Database
```bash
# Install dependencies
pip install -r requirements.txt

# Run migration script
python migrate_database.py your_database.db

# Start the application
python app.py
```

## 📋 System Requirements

- Python 3.7 or higher
- Flask 2.x
- SQLite 3
- Modern web browser (Chrome, Firefox, Edge, Safari)

## 🎯 New Features Overview

### 1. Advanced Reception System

#### Multiple Reception Sources
- **Purchase Orders**: Receive items from suppliers via POs
- **Production**: Track items manufactured internally with order numbers
- **External Processes**: Receive items returning from external processing

#### Smart Item Search
- Real-time search as you type
- Search by SKU or item name
- Instant results (minimum 2 characters)
- Auto-complete selection

#### Scrap During Reception
- Mark damaged/defective items during receiving
- Automatic separation of good vs. scrap quantities
- Creates scrap records automatically
- Only good items added to inventory

### 2. Scrap Management Module

#### Track Scrapped Inventory
- Record scraps from warehouse operations
- Multiple scrap reasons (Damaged, Defective, Expired, etc.)
- Location-based item search
- Automatic inventory deduction
- Full audit trail

#### Scrap Sources
- **Receipt**: Damaged items found during receiving
- **Warehouse**: Items scrapped from warehouse inventory
- **Production**: Manufacturing defects or rejects

### 3. External Process Reception (Fixed)

- Direct reception from external processes
- Automatic status updates
- Quantity validation
- Supplier tracking

## 📖 User Guide

### Creating a Receipt from Purchase Order

1. Navigate to **Receipts → New Receipt**
2. Select "Purchase Order" as source type
3. Choose a PO from the dropdown (or leave blank for manual entry)
   - If PO selected: Items auto-populate
   - If blank: Manually search and add items
4. For each item:
   - **Qty Received**: Total quantity received
   - **Qty Scrap**: How many are damaged/defective
   - **Good Qty**: Automatically calculated (Received - Scrap)
5. Add notes if needed
6. Click "Create Receipt"

**Result:**
- Good quantity added to inventory
- Scrap record created for damaged items
- PO status updated
- Transaction history logged

### Creating a Receipt from Production

1. Navigate to **Receipts → New Receipt**
2. Select "Production (Internal Order)" as source type
3. Enter your internal order number (e.g., PROD-2024-001)
4. Select the receiving location
5. Search and add items:
   - Type part of SKU or name
   - Select from search results
   - Enter quantities
6. Mark any scrap if applicable
7. Click "Create Receipt"

**Result:**
- Production items added to inventory
- Internal order number tracked
- Scrap handled if any

### Creating a Receipt from External Process

1. Navigate to **Receipts → New Receipt**
2. Select "External Process Return" as source type
3. Choose the external process from dropdown
   - Shows remaining quantity to receive
   - Item auto-populates
4. Enter quantity received
5. Mark any scrap (damaged during processing)
6. Click "Create Receipt"

**Result:**
- Items returned to inventory
- External process status updated
- Supplier reference maintained
- Scrap tracked if any

### Creating a Warehouse Scrap Record

1. Navigate to **Inventory → New Scrap**
2. Select the location where items are scrapped
3. Search for the item:
   - Only shows items available at selected location
   - Displays available quantity
4. Enter quantity to scrap (max = available)
5. Select scrap reason:
   - Damaged
   - Defective
   - Expired
   - Quality Issue
   - Contaminated
   - Obsolete
   - Other
6. Add notes with details
7. Click "Create Scrap Record"

**Result:**
- Inventory deducted
- Scrap record created
- Transaction logged
- Audit trail maintained

## 🔍 Search Functionality

### How Item Search Works

**In Receipts:**
- Type 2+ characters of SKU or name
- See instant results
- Click to select
- Works for all reception types

**In Scraps:**
- Must select location first
- Only shows items available at that location
- Displays current available quantity
- Prevents selecting unavailable items

### Search Tips
- Use partial matches: "BRG" finds "BRG-001", "BRG-002", etc.
- Case insensitive: "bearing" = "BEARING" = "Bearing"
- Searches both SKU and name fields
- Results limited to 20 items for performance

## 📊 Understanding the Data

### Receipt View Details

When viewing a receipt, you'll see:
- **Source Type**: How items were received
- **Total Received**: All items including scrap
- **Scrap Qty**: Items that were damaged
- **Good Qty**: Items added to inventory
- **Status**: Visual indicator of scrap percentage

### Scrap Record Details

Each scrap record shows:
- Unique scrap number (SCRAP-XXXXXX)
- Item details
- Location where scrapped
- Quantity scrapped
- Reason for scrap
- Source (receipt, warehouse, production)
- Date and user who created it

### Inventory Transactions

All operations create transactions:
- **receipt**: Items received (good quantity)
- **scrap**: Items scrapped (negative quantity)
- **process_out**: Sent for external processing
- **process_in**: Returned from external processing

## 🔐 User Roles & Permissions

All users with login access can:
- Create receipts
- Create scrap records
- View all records
- Search items

Admin users additionally can:
- Manage users
- Configure locations
- Set up items and categories
- Access all reports

## 📈 Reports & Analytics

Enhanced data available for:
- Scrap rate analysis by item/location/reason
- Reception quality metrics
- External process turnaround
- Source-specific performance
- Cost impact of scraps

## 🗃️ Database Schema

### New/Modified Tables

**receipts** (enhanced):
- `source_type`: purchase_order | production | external_process
- `external_process_id`: Link to external process (if applicable)
- `internal_order_number`: Production order number

**receipt_items** (enhanced):
- `scrap_quantity`: Quantity marked as scrap

**scraps** (new):
- Complete scrap tracking with reason, source, and audit info

## 🔧 Troubleshooting

### Migration Issues

**Problem**: "table already exists" error
```bash
# Check if tables exist
sqlite3 inventory.db ".tables"

# If tables exist, migration should skip them automatically
# Re-run migration:
python migrate_database.py inventory.db
```

**Problem**: Old receipts show no source type
- This is normal! Default value is "purchase_order"
- Migration automatically sets this for existing records

### Search Not Working

**Problem**: Search doesn't show results
- Check you've typed at least 2 characters
- For scraps: Ensure location is selected first
- Check items are marked as active (is_active = True)

**Problem**: Search is slow
- Normal for first search (database warm-up)
- Subsequent searches should be fast (<300ms)

### Scrap Creation Fails

**Problem**: "Insufficient quantity" error
- Check item is actually at selected location
- Verify available quantity is sufficient
- Check for pending transactions

## 🔄 Data Migration

### Backing Up Before Migration

```bash
# Create backup
cp inventory.db inventory.db.backup

# Run migration
python migrate_database.py inventory.db

# If issues occur, restore:
mv inventory.db.backup inventory.db
```

### What Gets Migrated

✓ All existing receipts preserved
✓ All existing inventory preserved
✓ All existing transactions preserved
✓ New columns added with safe defaults
✓ No data loss

### Post-Migration Verification

```bash
# Run verification
python migrate_database.py inventory.db

# Check for "All checks passed" message
# Review any failed checks
```

## 📞 Support

### Common Questions

**Q: Can I edit a receipt after creation?**
A: Receipts are immutable for audit purposes. Create an adjustment if needed.

**Q: Can I reverse a scrap?**
A: Scrap records are permanent. Use inventory adjustment to add items back if needed.

**Q: What happens to scrap quantity?**
A: Scrap quantity is NOT added to inventory. It's tracked separately for reporting.

**Q: Can I receive partial quantities?**
A: Yes! The system tracks received vs. ordered quantities. PO status updates automatically.

**Q: How do I handle returns from customers?**
A: Use a new receipt with "Production" source or create a shipment reversal.

## 🚦 Best Practices

### Reception Best Practices
1. Always inspect items before marking quantity
2. Separate damaged items immediately
3. Document scrap reasons clearly in notes
4. Take photos for high-value scraps (future feature)
5. Process receipts same day when possible

### Scrap Management Best Practices
1. Scrap items as soon as damage is identified
2. Use specific scrap reasons (not just "Damaged")
3. Add detailed notes for quality analysis
4. Review scrap reports weekly
5. Investigate high scrap rates

### Search Tips
1. Use partial SKUs for faster search
2. For similar items, search by name
3. Recent items appear in search faster
4. Keep item names descriptive

## 📝 Version History

- **v2.0** (November 2025): Enhanced reception with scrap tracking
- **v1.0** (October 2024): Initial release

## 🎓 Training Resources

### Video Tutorials (Coming Soon)
- Creating Different Types of Receipts
- Scrap Management Workflow
- Using Advanced Search Features
- Running Reports on Scraps

### Quick Reference Guides
See `ENHANCEMENTS.md` for detailed technical documentation

---

## 🎉 You're Ready!

The system is now fully configured with:
✓ Multiple reception sources
✓ Scrap tracking
✓ Smart item search
✓ External process reception
✓ Complete audit trails

Start by creating your first enhanced receipt or scrap record!
