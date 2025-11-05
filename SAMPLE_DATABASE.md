# Sample Database - Quick Start Guide

This file contains a pre-populated database with sample data to demonstrate the ERP system.

## What's Included

### Items (10 total):
- **Raw Materials**:
  - SS304 Sheet (1mm x 1000mm x 2000mm)
  - AL6061 Bar (25mm x 3000mm)
  - ST1018 Tube (50mm OD x 6000mm)

- **Components**:
  - Mounting Bracket - Stainless Steel
  - Support Bracket - Aluminum
  - Side Panel - Stainless Steel
  - Front Panel - Aluminum

- **Finished Goods**:
  - Industrial Equipment Cabinet - Stainless Steel
  - Aluminum Panel Assembly

- **Packaging**:
  - Cardboard Box - Large

### Bill of Materials (2 BOMs):
- **BOM-00001**: Industrial Equipment Cabinet
  - 4x Mounting Brackets
  - 2x Side Panels
  - 0.5x SS304 Sheet (for door)
  - 1x Packaging Box
  - Production Time: 180 minutes
  - Material Cost: ~$90

- **BOM-00002**: Aluminum Panel Assembly
  - 2x Support Brackets
  - 1x Front Panel
  - 0.3x AL6061 Bar (for frame)
  - 1x Packaging Box
  - Production Time: 90 minutes
  - Material Cost: ~$45

### Inventory Locations (3):
- **WH-01**: Main Warehouse (primary stock)
- **PROD-01**: Production Floor (work in progress)
- **SHIP-01**: Shipping Area

### Suppliers (2):
- Metal Supply Co. - Raw materials supplier
- Aluminum Warehouse - Aluminum products supplier

### Clients (2):
- Manufacturing Solutions Inc.
- Equipment Distributors Ltd.

### Sample Transactions:
- 1 Purchase Order (partially received)
- 1 Shipment (shipped status)
- Inventory distributed across locations

## How to Use This Sample Database

### Option 1: Quick Replace (Recommended)

**Windows:**
```cmd
cd olstral-erp
copy sample_inventory.db inventory.db
```

**Mac/Linux:**
```bash
cd olstral-erp
cp sample_inventory.db inventory.db
```

Then start the server and login:
- Username: `admin`
- Password: `admin123`

### Option 2: First-Time Setup

If you haven't run the ERP yet:

1. Download the repository
2. Copy `sample_inventory.db` to `inventory.db`
3. Run setup script
4. Start the server

### What to Show Your Colleagues

1. **Dashboard** - Overview of system
   - Total items, inventory value, low stock alerts

2. **Items** - Navigate to Items → All Items
   - See raw materials, components, finished goods
   - Check SKU structure (e.g., RAW-SHT-SS304-0001)

3. **Bill of Materials** - Navigate to Production → Bill of Materials
   - View BOM-00001 (Industrial Cabinet)
   - See component breakdown and costs
   - Show production time estimates

4. **Inventory** - Navigate to Inventory → Stock Levels
   - See stock across multiple locations
   - Check quantities in Warehouse vs Production

5. **Purchase Orders** - Navigate to Purchasing → Purchase Orders
   - View PO-00001 (partial receipt example)

6. **Shipments** - Navigate to Shipping → Shipments
   - View SHIP-00001 (completed shipment)

## Resetting to Sample Data

If you modify the database and want to reset to original sample data:

**Windows:**
```cmd
del inventory.db
copy sample_inventory.db inventory.db
```

**Mac/Linux:**
```bash
rm inventory.db
cp sample_inventory.db inventory.db
```

## Login Credentials

- **Username**: admin
- **Password**: admin123

**Important**: Change the password after demonstrating!

## Notes

- The sample database is read-only in the repository
- Your `inventory.db` is git-ignored, so your changes won't be committed
- You can safely experiment - just reset using the steps above
- All inventory quantities are randomly generated (50-200 in warehouse, 10-50 in production)

## Support

If you need to regenerate the sample data:
```bash
python populate_sample_data.py
cp inventory.db sample_inventory.db
```

This will create fresh sample data with different random quantities.
