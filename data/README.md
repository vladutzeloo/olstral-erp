# Database Folder

This folder contains the SQLite database file for the ERP system.

## Database Location

**Current database:** `data/inventory.db`

This file is gitignored, so your local database changes won't be committed to the repository.

## How to Replace with Demo/Sample Database

To reset your database or use the sample database:

1. **Stop the application** if it's running
2. **Delete the current database:**
   ```bash
   # On Windows (PowerShell)
   Remove-Item data\inventory.db

   # On Linux/Mac
   rm data/inventory.db
   ```

3. **Copy the sample database:**
   ```bash
   # On Windows (PowerShell)
   Copy-Item sample_inventory.db data\inventory.db

   # On Linux/Mac
   cp sample_inventory.db data/inventory.db
   ```

4. **Run the schema fix script** (if needed):
   ```bash
   python fix_database_schema.py data/inventory.db
   ```

5. **Start the application**

## Database Schema

The database includes all necessary tables:
- Users
- Items, Categories, Materials
- Inventory locations and transactions
- Purchase Orders
- Receipts
- Shipments
- External Processes
- Scraps
- Clients and Suppliers

## Default Credentials

When using the sample database:
- **Username:** admin
- **Password:** admin123

## Troubleshooting

If you get "unable to open database file" error:
- Make sure the `data/` folder exists
- Check file permissions
- Ensure SQLite can write to this directory
