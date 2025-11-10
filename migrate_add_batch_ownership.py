"""
Database Migration Script: Add Batch Ownership Type

This script adds ownership tracking to batches to support:
- Owned materials (counted in inventory value)
- Consignment materials (not counted in inventory value)
- Lohn materials (customer-owned, not counted in inventory value)

Run this script to upgrade your database with:
- ownership_type column in batches table

Prerequisites:
- batches table must exist (run migrate_add_batches.py first)

Usage:
    python migrate_add_batch_ownership.py
"""

from app import create_app
from extensions import db
from models import Batch
from sqlalchemy import inspect, text

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Run the migration"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Database Migration: Add Batch Ownership Type")
        print("=" * 60)
        print()

        # Check prerequisites
        print("Checking prerequisites...")
        batches_exists = check_table_exists('batches')

        if not batches_exists:
            print("✗ ERROR: Batches table not found!")
            print()
            print("Please run migrate_add_batches.py first to add batch tracking.")
            return False

        print("✓ Batches table found")
        print()

        # Check if column already exists
        print("Checking current state...")
        ownership_exists = check_column_exists('batches', 'ownership_type')

        if ownership_exists:
            print("✓ ownership_type column already exists. No migration needed.")
            return True

        print()
        print("Changes to apply:")
        print("  - Add ownership_type column to batches table")
        print("    (owned, consignment, lohn)")
        print()
        print("Impact:")
        print("  - Existing batches will default to 'owned'")
        print("  - Inventory valuation will exclude consignment/lohn materials")
        print()

        # Confirm before proceeding
        response = input("Proceed with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            return False

        print()
        print("Running migration...")

        try:
            # Add ownership_type column
            with db.engine.connect() as conn:
                # Add column with default value
                conn.execute(text("""
                    ALTER TABLE batches
                    ADD COLUMN ownership_type VARCHAR(20) DEFAULT 'owned'
                """))
                conn.commit()

            print("✓ Added ownership_type column")
            print()

            # Update existing batches to 'owned'
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    UPDATE batches
                    SET ownership_type = 'owned'
                    WHERE ownership_type IS NULL
                """))
                conn.commit()
                print(f"✓ Updated {result.rowcount} existing batches to 'owned' status")

            print()
            print("✓ Migration completed successfully!")
            print()
            print("New features enabled:")
            print("  ✓ Batch ownership tracking")
            print("  ✓ Consignment material support")
            print("  ✓ Lohn/customer-owned material support")
            print("  ✓ Accurate inventory valuation (excludes non-owned materials)")
            print()
            print("Ownership Types:")
            print("  • owned - Your company owns the material (counted in inventory value)")
            print("  • consignment - Supplier-owned material at your location (not valued)")
            print("  • lohn - Customer-owned material for processing (not valued)")
            print()
            print("How it works:")
            print("  1. When creating receipts, select ownership type for each batch")
            print("  2. Manual batch numbers are now supported (auto-generated if blank)")
            print("  3. Cost per unit can be manually entered (uses item cost if blank)")
            print("  4. Inventory valuation reports exclude consignment/lohn materials")
            print("  5. Dashboard value shows only owned materials")
            print()
            print("Next steps:")
            print("  1. Create new receipts and assign ownership types")
            print("  2. Review inventory valuation reports")
            print("  3. Consignment/lohn materials won't affect your inventory value")

            return True

        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            print()
            print("Please check your database configuration and try again.")
            raise

def verify_migration():
    """Verify the migration was successful"""
    app = create_app()

    with app.app_context():
        print()
        print("Verifying migration...")

        # Check column exists
        ownership_exists = check_column_exists('batches', 'ownership_type')

        if ownership_exists:
            print("✓ ownership_type column present in batches table")

            # Count batches by ownership type
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT ownership_type, COUNT(*) as count
                    FROM batches
                    GROUP BY ownership_type
                """))
                rows = result.fetchall()

            print()
            print("Batch ownership distribution:")
            for row in rows:
                print(f"  - {row[0]}: {row[1]} batches")

            print()
            print("Migration verification complete!")
            print()
            print("System Status:")
            print("  ✓ Batch Tracking: ENABLED")
            print("  ✓ FIFO Inventory: ENABLED")
            print("  ✓ Ownership Tracking: ENABLED")
            print("  ✓ Consignment Support: ENABLED")
            print("  ✓ Lohn Support: ENABLED")
            print()
            print("Your ERP system now supports material ownership tracking!")

            return True
        else:
            print("✗ Migration verification failed")
            print("  - ownership_type column not found in batches table")
            return False

if __name__ == '__main__':
    try:
        success = migrate_database()
        if success:
            verify_migration()
    except KeyboardInterrupt:
        print()
        print("Migration cancelled by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
