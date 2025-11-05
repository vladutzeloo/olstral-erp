# Inventory ERP - Changes Summary

## Major Changes Implemented

### 1. **Material Series Management**
- ✅ Added `MaterialSeries` model for grouping materials (e.g., Stainless Steel series, Aluminum series)
- ✅ Materials can now be assigned to a series for better organization
- ✅ Material series is **only** a field in materials (NOT in items)
- ✅ New routes: `/items/series`, `/items/series/new`

### 2. **Renamed Treatments to External Processes**
- ✅ Complete rename from "Treatments" to "External Processes" throughout the system
- ✅ Table renamed: `treatments` → `external_processes`
- ✅ Column renamed: `treatment_type` → `process_type`
- ✅ Number format changed: `TRT-000001` → `EXT-000001`
- ✅ All references updated in:
  - Models
  - Routes
  - Templates
  - Navigation
  - Dashboard

### 3. **Client Management System**
- ✅ Added `Client` model with full CRUD operations
- ✅ Clients can be linked to shipments
- ✅ Client management routes: `/clients/`, `/clients/new`, `/clients/edit`
- ✅ Client code auto-generation: `CLI-0001`, `CLI-0002`, etc.
- ✅ View client history with recent shipments
- ✅ Edit functionality for updating client information

### 4. **Excel Import for Items**
- ✅ Changed from CSV to Excel (.xlsx, .xls) import
- ✅ Added `openpyxl` library for Excel support
- ✅ Template download button for easy import
- ✅ Generates Excel template with proper headers
- ✅ Import route: `/items/import`
- ✅ Template download route: `/items/template`

### 5. **Internal Order Number Tracking**
- ✅ Added `internal_order_number` field to `Receipt` model
- ✅ Useful for tracking items received from production
- ✅ Field appears in receipt creation form
- ✅ Provides traceability for production-based receipts

### 6. **Purchase Orders Enhancement**
- ✅ Added `po_type` field to PurchaseOrder model
- ✅ Can now create POs for: `items`, `materials`, or `external_process`
- ✅ Supports purchasing raw materials directly
- ✅ Supports POs for external processing services

### 7. **CNC-Specific Dimensional Fields**
All items now have these fields:
- ✅ Diameter (mm)
- ✅ Length (mm)
- ✅ Width (mm)
- ✅ Height (mm)
- ✅ Weight (kg)

These fields appear in:
- Item creation form
- Item edit form
- Item view page with dedicated "Dimensions & Weight" section

### 8. **Edit Functionality Added**
Added edit routes and templates for:
- ✅ Items
- ✅ Materials
- ✅ Clients
- ✅ External Processes
- ✅ Suppliers (existing)

### 9. **Currency Changed to EUR**
- ✅ All $ symbols replaced with €
- ✅ All price/cost labels show "(EUR)"
- ✅ Updated in all templates

### 10. **Navigation Updates**
New menu structure:
- Items → includes "Material Series" and "Import Items"
- Shipping → includes "Clients" link
- External Processes → replaces Treatments menu

## Database Schema Changes

### New Tables:
1. **material_series** - Groups materials by series
2. **clients** - Customer management
3. **external_processes** - Renamed from treatments

### Modified Tables:
1. **materials** - Added `series_id` foreign key
2. **items** - Added dimensional fields (diameter, length, width, height, weight_kg)
3. **receipts** - Added `internal_order_number` field
4. **purchase_orders** - Added `po_type` field
5. **shipments** - Added `client_id` foreign key

### Renamed Tables:
- `treatments` → `external_processes`

## Important Notes

### ⚠️ Breaking Changes
- **Database must be deleted and recreated** due to schema changes
- Old treatments data will need to be migrated manually if needed

### Migration Steps:
1. Delete existing `inventory.db`
2. Extract new ZIP file
3. Delete `venv` folder
4. Run `setup.bat`
5. Run `start_server.bat`
6. Database will be recreated automatically

## New Dependencies
- `openpyxl==3.1.2` - For Excel file handling

## File Changes Summary
- **Models**: Updated models.py with new tables and relationships
- **Routes**: Added clients.py, renamed treatments.py → external_processes.py
- **Templates**: 
  - Added `/clients/` folder with 4 templates
  - Renamed `/treatments/` → `/external_processes/`
  - Updated 20+ existing templates for EUR and new features
- **Requirements**: Added openpyxl

## Testing Checklist

After installation, test:
- [ ] Create Material Series
- [ ] Create Material with Series
- [ ] Import Items via Excel
- [ ] Create Client
- [ ] Edit Client
- [ ] Create External Process
- [ ] Edit External Process
- [ ] Create Receipt with Internal Order Number
- [ ] View dimensional fields on items
- [ ] Verify EUR currency throughout
