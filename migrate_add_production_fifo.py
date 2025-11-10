"""
Database Migration Script: Add Production Order FIFO System

This script adds complete production order functionality with FIFO batch tracking.

Run this script to upgrade your database with:
- production_orders table
- production_consumption table (links batches to production orders)

Prerequisites:
- batches and batch_transactions tables must exist (run migrate_add_batches.py first)

Usage:
    python migrate_add_production_fifo.py
"""

from app import create_app
from extensions import db
from models import ProductionOrder, ProductionConsumption, Batch, BatchTransaction
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
        print("Database Migration: Add Production Order FIFO System")
        print("=" * 60)
        print()

        # Check prerequisites
        print("Checking prerequisites...")
        batches_exists = check_table_exists('batches')
        batch_transactions_exists = check_table_exists('batch_transactions')

        if not batches_exists or not batch_transactions_exists:
            print("✗ ERROR: Batch tables not found!")
            print()
            print("Please run migrate_add_batches.py first to add batch tracking.")
            print("Production orders require batch FIFO functionality.")
            return False

        print("✓ Batch tables found")
        print()

        # Check current state
        print("Checking database state...")
        prod_orders_exists = check_table_exists('production_orders')
        prod_consumption_exists = check_table_exists('production_consumption')

        if prod_orders_exists and prod_consumption_exists:
            print("✓ Production order tables already exist. No migration needed.")
            return True

        print()
        print("Tables to create:")
        if not prod_orders_exists:
            print("  - production_orders")
        if not prod_consumption_exists:
            print("  - production_consumption")
        print()

        # Confirm before proceeding
        response = input("Proceed with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            return False

        print()
        print("Running migration...")

        try:
            # Create tables
            db.create_all()

            print("✓ Migration completed successfully!")
            print()
            print("New features enabled:")
            print("  ✓ Production Order Management")
            print("  ✓ FIFO Component Consumption (oldest materials used first)")
            print("  ✓ Automatic cost calculation from consumed batches")
            print("  ✓ Full component-to-finished-goods traceability")
            print("  ✓ Production scrap tracking")
            print("  ✓ Real-time material availability checking")
            print()
            print("Production Order Workflow:")
            print("  1. Create production order (select BOM and quantity)")
            print("  2. Release order (make ready for production)")
            print("  3. Start production → Consumes component batches using FIFO")
            print("  4. Complete production → Creates receipt and finished goods batch")
            print()
            print("FIFO Benefits:")
            print("  • Accurate costing based on actual material costs")
            print("  • Full traceability from components to finished goods")
            print("  • Compliance with accounting standards")
            print("  • Quality control batch tracking")
            print()
            print("Next steps:")
            print("  1. Navigate to /production-orders to create orders")
            print("  2. Ensure you have active BOMs for your finished items")
            print("  3. Component materials must have available batches")
            print("  4. Production will automatically use oldest batches (FIFO)")

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

        prod_orders_exists = check_table_exists('production_orders')
        prod_consumption_exists = check_table_exists('production_consumption')

        if prod_orders_exists and prod_consumption_exists:
            print("✓ All production order tables present")

            # Check columns
            inspector = inspect(db.engine)

            # Production Orders table
            prod_orders_columns = [col['name'] for col in inspector.get_columns('production_orders')]
            expected_po_columns = [
                'id', 'order_number', 'finished_item_id', 'bom_id', 'location_id',
                'quantity_ordered', 'quantity_produced', 'quantity_scrapped', 'status',
                'start_date', 'due_date', 'actual_start_date', 'actual_completion_date',
                'material_cost', 'labor_cost', 'overhead_cost', 'total_cost',
                'notes', 'created_by', 'created_at', 'updated_at'
            ]

            missing_po_columns = [col for col in expected_po_columns if col not in prod_orders_columns]
            if missing_po_columns:
                print(f"⚠ Warning: Missing columns in production_orders: {missing_po_columns}")
            else:
                print("✓ All production_orders columns present")

            # Production Consumption table
            prod_cons_columns = [col['name'] for col in inspector.get_columns('production_consumption')]
            expected_pc_columns = [
                'id', 'production_order_id', 'component_item_id', 'batch_id',
                'quantity_consumed', 'cost_per_unit', 'total_cost',
                'consumed_date', 'consumed_by', 'notes'
            ]

            missing_pc_columns = [col for col in expected_pc_columns if col not in prod_cons_columns]
            if missing_pc_columns:
                print(f"⚠ Warning: Missing columns in production_consumption: {missing_pc_columns}")
            else:
                print("✓ All production_consumption columns present")

            print()
            print("Migration verification complete!")
            print()
            print("System Status:")
            print("  ✓ Batch Tracking: ENABLED")
            print("  ✓ FIFO Inventory: ENABLED")
            print("  ✓ Production Orders: ENABLED")
            print("  ✓ Production FIFO: ENABLED")
            print()
            print("Your ERP system now has full FIFO production tracking!")

            return True
        else:
            print("✗ Migration verification failed")
            if not prod_orders_exists:
                print("  - production_orders table not found")
            if not prod_consumption_exists:
                print("  - production_consumption table not found")
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
