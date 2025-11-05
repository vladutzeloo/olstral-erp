# Inventory ERP System

A comprehensive Flask-based inventory management and ERP system for tracking items, inventory across multiple locations, purchase orders, shipments, and external treatments.

## Features

- **SKU Management**: Automatic SKU generation using Category-Type-Material pattern
- **Multi-Location Inventory**: Track stock across warehouses, production facilities, and other locations
- **Purchase Orders**: Create and manage POs with partial receiving capability
- **Receipts**: Process incoming inventory with automatic stock updates
- **Shipments**: Track outgoing inventory and customer orders
- **Treatment Tracking**: Send items for external processing and track returns
- **Comprehensive Reporting**: Inventory valuation, low stock alerts, transaction history
- **User Authentication**: Role-based access control with secure login
- **Audit Trail**: Complete transaction history for all inventory movements

## Quick Start

### Requirements

- Python 3.11 or higher
- Windows 10/11 (batch files included for easy setup)

### Installation

1. **Extract the files** to a folder on your computer

2. **Run setup**:
   - Double-click `setup.bat`
   - This will create a virtual environment and install all dependencies

3. **Start the server**:
   - Double-click `start_server.bat`
   - Wait for "Running on http://localhost:5000" message
   - Open your web browser and go to: http://localhost:5000

4. **Login**:
   - Username: `admin`
   - Password: `admin123`

### Stopping the Server

- Press `Ctrl+C` in the command window, or
- Double-click `stop_server.bat`

## System Architecture

### Database Tables

1. **Users** - System users with role-based permissions
2. **Categories** - Item categories (e.g., RAW, FIN, PKG)
3. **ItemTypes** - Types within categories (e.g., SHT, BAR, BOX)
4. **Materials** - Material specifications (e.g., SS304, AL6061)
5. **Items** - Master item records with SKU
6. **Locations** - Physical locations/warehouses
7. **InventoryLocations** - Stock levels at each location
8. **Suppliers** - Vendor information
9. **PurchaseOrders** - PO headers
10. **PurchaseOrderItems** - PO line items
11. **Receipts** - Incoming inventory records
12. **ReceiptItems** - Receipt line items
13. **Shipments** - Outgoing shipments
14. **ShipmentItems** - Shipment line items
15. **Treatments** - External processing records
16. **InventoryTransactions** - Complete audit trail
17. **AuditLog** - System-wide audit log

### SKU Generation

SKUs are automatically generated using the pattern:
```
{CATEGORY}-{TYPE}-{MATERIAL}-{SEQUENCE}
```

Example: `RAW-SHT-SS304-0001`

- **RAW**: Raw Material category
- **SHT**: Sheet type
- **SS304**: Stainless Steel 304 material
- **0001**: Auto-incremented sequence number

## Main Features

### Dashboard
- Total items count
- Inventory valuation
- Low stock alerts
- Pending purchase orders
- Active treatments
- Recent activity feed

### Item Management
- Create new items with automatic SKU generation
- Manage categories, types, and materials
- Set reorder levels and quantities
- Track cost and selling price

### Inventory Control
- View stock levels across all locations
- Adjust inventory quantities
- Transfer stock between locations
- Complete transaction history

### Purchase Order Management
- Create POs with multiple line items
- Submit POs to suppliers
- Track PO status (draft, submitted, partial, received)
- Partial receiving capability

### Receipt Processing
- Receive inventory from POs or other sources
- Automatic inventory updates
- Link receipts to purchase orders
- Update PO status automatically

### Shipment Management
- Create outgoing shipments
- Track shipping status
- Automatic inventory deduction
- Customer information tracking

### Treatment Tracking
- Send items for external processing (plating, heat treatment, etc.)
- Track quantities sent and returned
- Monitor treatment status
- Calculate treatment costs

### Reporting
- Inventory valuation by item
- Low stock report with reorder suggestions
- Transaction history
- Purchase order status report
- Treatment status report

## Default Login Credentials

**Important**: Change these immediately after first login!

- Username: `admin`
- Password: `admin123`

## Troubleshooting

### Python Version Issues
If you encounter errors during setup:
1. Check Python version: `python --version`
2. Must be Python 3.11 or higher
3. Download from: https://www.python.org/downloads/

### Port Already in Use
If port 5000 is already in use:
1. Stop other applications using port 5000
2. Or edit `app.py` and change the port number

### Database Issues
If you need to reset the database:
1. Stop the server
2. Delete the file `inventory.db`
3. Restart the server (database will be recreated)

## File Structure

```
inventory_erp_complete/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── extensions.py         # Flask extensions
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── setup.bat            # Setup script
├── start_server.bat     # Start server script
├── stop_server.bat      # Stop server script
├── routes/              # Route handlers
│   ├── auth.py          # Authentication
│   ├── dashboard.py     # Dashboard
│   ├── items.py         # Item management
│   ├── inventory.py     # Inventory control
│   ├── purchase_orders.py
│   ├── receipts.py
│   ├── shipments.py
│   ├── treatments.py
│   └── reports.py
├── templates/           # HTML templates
│   └── base.html
└── static/             # CSS, JS, images
    └── css/
        └── style.css
```

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review error messages in the command window
3. Check that all files are present and not corrupted

## Security Notes

- Change default admin password immediately
- Use strong passwords for all users
- Keep Python and dependencies updated
- Back up the database regularly
- Secure the server if deploying to production

## License

This software is provided as-is for internal use.
