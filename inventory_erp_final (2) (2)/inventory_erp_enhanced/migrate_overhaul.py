"""
Database Migration for Overhauled External Processes & Reception System
Adds support for:
- Item transformation tracking (different SKU after processing)
- External processor supplier designation
- Process result tracking
- Shipping and pickup details
"""

import sqlite3
import sys

def migrate_database(db_path='inventory.db'):
    print(f"Starting migration for: {db_path}")
    print("="*60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Add new fields to external_processes table
        print("\n1. Updating external_processes table...")
        cursor.execute("PRAGMA table_info(external_processes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        new_fields = {
            'returned_item_id': "ALTER TABLE external_processes ADD COLUMN returned_item_id INTEGER",
            'process_result': "ALTER TABLE external_processes ADD COLUMN process_result VARCHAR(200)",
            'creates_new_sku': "ALTER TABLE external_processes ADD COLUMN creates_new_sku BOOLEAN DEFAULT 0",
            'updated_at': "ALTER TABLE external_processes ADD COLUMN updated_at DATETIME"
        }
        
        for field, sql in new_fields.items():
            if field not in columns:
                print(f"   Adding {field}...")
                cursor.execute(sql)
        
        # 2. Add new fields to suppliers table
        print("\n2. Updating suppliers table...")
        cursor.execute("PRAGMA table_info(suppliers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        supplier_fields = {
            'is_external_processor': "ALTER TABLE suppliers ADD COLUMN is_external_processor BOOLEAN DEFAULT 0",
            'typical_process_types': "ALTER TABLE suppliers ADD COLUMN typical_process_types TEXT",
            'typical_lead_time_days': "ALTER TABLE suppliers ADD COLUMN typical_lead_time_days INTEGER",
            'shipping_account': "ALTER TABLE suppliers ADD COLUMN shipping_account VARCHAR(100)",
            'pickup_instructions': "ALTER TABLE suppliers ADD COLUMN pickup_instructions TEXT"
        }
        
        for field, sql in supplier_fields.items():
            if field not in columns:
                print(f"   Adding {field}...")
                cursor.execute(sql)
        
        # 3. Initialize updated_at for existing records
        print("\n3. Initializing timestamps...")
        cursor.execute("""
            UPDATE external_processes 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        """)
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✓ Migration completed successfully!")
        print("="*60)
        
        print("\nSummary:")
        print("  External Processes now support:")
        print("    - Item transformation (different SKU after processing)")
        print("    - Process result tracking")
        print("    - Creates new SKU flag")
        print("\n  Suppliers now support:")
        print("    - External processor designation")
        print("    - Typical process types")
        print("    - Lead time tracking")
        print("    - Shipping account info")
        print("    - Pickup instructions")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Error: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_migration(db_path='inventory.db'):
    print("\n" + "="*60)
    print("Verifying migration...")
    print("="*60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check external_processes
        cursor.execute("PRAGMA table_info(external_processes)")
        ext_cols = [col[1] for col in cursor.fetchall()]
        
        # Check suppliers
        cursor.execute("PRAGMA table_info(suppliers)")
        sup_cols = [col[1] for col in cursor.fetchall()]
        
        checks = {
            'external_processes.returned_item_id': 'returned_item_id' in ext_cols,
            'external_processes.process_result': 'process_result' in ext_cols,
            'external_processes.creates_new_sku': 'creates_new_sku' in ext_cols,
            'external_processes.updated_at': 'updated_at' in ext_cols,
            'suppliers.is_external_processor': 'is_external_processor' in sup_cols,
            'suppliers.typical_process_types': 'typical_process_types' in sup_cols,
            'suppliers.typical_lead_time_days': 'typical_lead_time_days' in sup_cols,
            'suppliers.shipping_account': 'shipping_account' in sup_cols,
            'suppliers.pickup_instructions': 'pickup_instructions' in sup_cols
        }
        
        print("\nVerification:")
        all_passed = True
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✓ All checks passed!")
        else:
            print("\n✗ Some checks failed!")
        
        conn.close()
        return all_passed
        
    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'inventory.db'
    
    print("OVERHAULED EXTERNAL PROCESSES & RECEPTION MIGRATION")
    print("="*60)
    print(f"Database: {db_path}")
    print("="*60)
    
    success = migrate_database(db_path)
    
    if success:
        verify_migration(db_path)
        print("\n" + "="*60)
        print("MIGRATION COMPLETE!")
        print("\nNew Features Available:")
        print("  1. Item Transformation Tracking")
        print("     - Track when processing creates different SKU")
        print("     - E.g., 'Shaft' → 'Shaft-Painted-Red'")
        print("\n  2. External Processor Management")
        print("     - Designate suppliers as external processors")
        print("     - Pre-configure typical processes")
        print("     - Set typical lead times")
        print("     - Store shipping details")
        print("\n  3. Enhanced Reception")
        print("     - Receive transformed items correctly")
        print("     - Track what was sent vs. what returned")
        print("     - Proper inventory management")
        print("="*60)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
