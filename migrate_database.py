"""
Database Migration Script for Enhanced Inventory ERP
Adds new columns and tables for scrap management and enhanced reception system
"""

import sqlite3
import sys
from datetime import datetime

def migrate_database(db_path='inventory.db'):
    """
    Migrate existing database to support new features:
    1. Add source_type and external_process_id to receipts
    2. Add scrap_quantity to receipt_items
    3. Create scraps table
    """
    
    print(f"Starting database migration for: {db_path}")
    print("-" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migrations are needed
        print("\n1. Checking receipts table...")
        cursor.execute("PRAGMA table_info(receipts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'source_type' not in columns:
            print("   Adding source_type column to receipts...")
            cursor.execute("""
                ALTER TABLE receipts 
                ADD COLUMN source_type VARCHAR(30) DEFAULT 'purchase_order'
            """)
            print("   ✓ Added source_type column")
        else:
            print("   ✓ source_type column already exists")
        
        if 'external_process_id' not in columns:
            print("   Adding external_process_id column to receipts...")
            cursor.execute("""
                ALTER TABLE receipts 
                ADD COLUMN external_process_id INTEGER
            """)
            # Add foreign key constraint (note: SQLite doesn't enforce FK on ALTER TABLE)
            print("   ✓ Added external_process_id column")
        else:
            print("   ✓ external_process_id column already exists")
        
        # Check receipt_items table
        print("\n2. Checking receipt_items table...")
        cursor.execute("PRAGMA table_info(receipt_items)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'scrap_quantity' not in columns:
            print("   Adding scrap_quantity column to receipt_items...")
            cursor.execute("""
                ALTER TABLE receipt_items 
                ADD COLUMN scrap_quantity INTEGER DEFAULT 0
            """)
            print("   ✓ Added scrap_quantity column")
        else:
            print("   ✓ scrap_quantity column already exists")
        
        # Check if scraps table exists
        print("\n3. Checking for scraps table...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scraps'
        """)
        
        if cursor.fetchone() is None:
            print("   Creating scraps table...")
            cursor.execute("""
                CREATE TABLE scraps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scrap_number VARCHAR(50) UNIQUE NOT NULL,
                    item_id INTEGER NOT NULL,
                    location_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    reason VARCHAR(200),
                    source_type VARCHAR(30),
                    source_id INTEGER,
                    scrap_date DATETIME NOT NULL,
                    scrapped_by INTEGER,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES items(id),
                    FOREIGN KEY (location_id) REFERENCES locations(id),
                    FOREIGN KEY (scrapped_by) REFERENCES users(id)
                )
            """)
            print("   ✓ Created scraps table")
        else:
            print("   ✓ scraps table already exists")
        
        # Update existing receipts to have source_type if NULL
        print("\n4. Updating existing receipts...")
        cursor.execute("""
            UPDATE receipts 
            SET source_type = 'purchase_order' 
            WHERE source_type IS NULL
        """)
        updated = cursor.rowcount
        print(f"   ✓ Updated {updated} receipts with default source_type")
        
        # Commit all changes
        conn.commit()
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        
        # Show summary
        print("\nSummary of changes:")
        print("  - Added source_type to receipts table")
        print("  - Added external_process_id to receipts table")
        print("  - Added scrap_quantity to receipt_items table")
        print("  - Created scraps table")
        print(f"  - Updated {updated} existing receipts")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Error during migration: {e}")
        conn.rollback()
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_migration(db_path='inventory.db'):
    """Verify that migration was successful"""
    print("\n" + "=" * 60)
    print("Verifying migration...")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check receipts table
        cursor.execute("PRAGMA table_info(receipts)")
        receipts_cols = [col[1] for col in cursor.fetchall()]
        
        checks = {
            'receipts.source_type': 'source_type' in receipts_cols,
            'receipts.external_process_id': 'external_process_id' in receipts_cols
        }
        
        # Check receipt_items table
        cursor.execute("PRAGMA table_info(receipt_items)")
        receipt_items_cols = [col[1] for col in cursor.fetchall()]
        checks['receipt_items.scrap_quantity'] = 'scrap_quantity' in receipt_items_cols
        
        # Check scraps table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scraps'
        """)
        checks['scraps table exists'] = cursor.fetchone() is not None
        
        # Print verification results
        print("\nVerification Results:")
        all_passed = True
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✓ All checks passed! Migration successful.")
        else:
            print("\n✗ Some checks failed. Please review the migration.")
        
        conn.close()
        return all_passed
        
    except Exception as e:
        print(f"✗ Error during verification: {e}")
        return False

if __name__ == '__main__':
    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'inventory.db'
    
    print("Enhanced Inventory ERP - Database Migration Tool")
    print("=" * 60)
    print(f"Target database: {db_path}")
    print("=" * 60)
    
    # Run migration
    success = migrate_database(db_path)
    
    if success:
        # Verify migration
        verify_migration(db_path)
        print("\n" + "=" * 60)
        print("Migration process completed!")
        print("You can now use the enhanced features:")
        print("  - Multiple reception sources (PO, Production, External Process)")
        print("  - Scrap tracking during reception")
        print("  - Warehouse scrap management")
        print("  - Item search functionality")
        print("=" * 60)
    else:
        print("\n✗ Migration failed. Please check the error messages above.")
        sys.exit(1)
