"""
Database Migration Script: Add Batch Tracking Tables

This script adds the batch tracking functionality to an existing database.

Run this script to upgrade your database with:
- batches table (for FIFO inventory tracking)
- batch_transactions table (for batch movement audit trail)

Usage:
    python migrate_add_batches.py
"""

from app import create_app
from extensions import db
from models import Batch, BatchTransaction
from sqlalchemy import inspect

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def migrate_database():
    """Run the migration"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Database Migration: Add Batch Tracking")
        print("=" * 60)
        print()

        # Check current state
        print("Checking database state...")
        batches_exists = check_table_exists('batches')
        batch_transactions_exists = check_table_exists('batch_transactions')

        if batches_exists and batch_transactions_exists:
            print("✓ Batch tables already exist. No migration needed.")
            return

        print()
        print("Tables to create:")
        if not batches_exists:
            print("  - batches")
        if not batch_transactions_exists:
            print("  - batch_transactions")
        print()

        # Confirm before proceeding
        response = input("Proceed with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            return

        print()
        print("Running migration...")

        try:
            # Create tables
            db.create_all()

            print("✓ Migration completed successfully!")
            print()
            print("New features enabled:")
            print("  - Batch/lot tracking for all received items")
            print("  - FIFO (First In, First Out) inventory consumption")
            print("  - Batch-level cost tracking")
            print("  - Full audit trail for batch movements")
            print("  - Support for supplier batch numbers")
            print("  - Expiry date tracking (optional)")
            print()
            print("Next steps:")
            print("  1. All new receipts will automatically create batches")
            print("  2. Shipments will consume batches using FIFO logic")
            print("  3. View batch details at /batches")
            print("  4. Use batch API endpoints for advanced queries")
            print()
            print("Note: Existing inventory will not have batch data.")
            print("New batches will be created as you receive new items.")

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

        batches_exists = check_table_exists('batches')
        batch_transactions_exists = check_table_exists('batch_transactions')

        if batches_exists and batch_transactions_exists:
            print("✓ All batch tables present")

            # Check columns
            inspector = inspect(db.engine)

            batches_columns = [col['name'] for col in inspector.get_columns('batches')]
            expected_batches_columns = [
                'id', 'batch_number', 'item_id', 'receipt_id', 'location_id',
                'quantity_original', 'quantity_available', 'received_date',
                'expiry_date', 'supplier_batch_number', 'po_id',
                'internal_order_number', 'external_process_id', 'cost_per_unit',
                'status', 'notes', 'created_by', 'created_at', 'updated_at'
            ]

            missing_columns = [col for col in expected_batches_columns if col not in batches_columns]
            if missing_columns:
                print(f"⚠ Warning: Missing columns in batches table: {missing_columns}")
            else:
                print("✓ All batches table columns present")

            batch_trans_columns = [col['name'] for col in inspector.get_columns('batch_transactions')]
            expected_trans_columns = [
                'id', 'batch_id', 'transaction_type', 'quantity',
                'reference_type', 'reference_id', 'from_location_id',
                'to_location_id', 'notes', 'created_by', 'created_at'
            ]

            missing_trans_columns = [col for col in expected_trans_columns if col not in batch_trans_columns]
            if missing_trans_columns:
                print(f"⚠ Warning: Missing columns in batch_transactions table: {missing_trans_columns}")
            else:
                print("✓ All batch_transactions table columns present")

            print()
            print("Migration verification complete!")
        else:
            print("✗ Migration verification failed")
            if not batches_exists:
                print("  - batches table not found")
            if not batch_transactions_exists:
                print("  - batch_transactions table not found")

if __name__ == '__main__':
    try:
        migrate_database()
        verify_migration()
    except KeyboardInterrupt:
        print()
        print("Migration cancelled by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
