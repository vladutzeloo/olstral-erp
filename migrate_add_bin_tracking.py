"""
Migration Script: Add bin_location fields to stock_movements and batch_transactions tables

This script adds bin tracking fields to support tracking bin locations during
transfers and batch transactions.

Run this script once to update your database:
    python migrate_add_bin_tracking.py
"""

from app import app
from extensions import db

def add_bin_tracking_columns():
    """Add bin_location columns to stock_movements and batch_transactions tables"""
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)

            # Check stock_movements table
            print("\nChecking stock_movements table...")
            stock_movement_columns = [col['name'] for col in inspector.get_columns('stock_movements')]

            needs_update = False

            if 'from_bin_location' not in stock_movement_columns:
                print("  Adding from_bin_location column to stock_movements...")
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE stock_movements ADD COLUMN from_bin_location VARCHAR(50)"
                    ))
                    conn.commit()
                print("  ✓ Added from_bin_location column")
                needs_update = True
            else:
                print("  ✓ from_bin_location column already exists")

            if 'to_bin_location' not in stock_movement_columns:
                print("  Adding to_bin_location column to stock_movements...")
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE stock_movements ADD COLUMN to_bin_location VARCHAR(50)"
                    ))
                    conn.commit()
                print("  ✓ Added to_bin_location column")
                needs_update = True
            else:
                print("  ✓ to_bin_location column already exists")

            # Check batch_transactions table
            print("\nChecking batch_transactions table...")
            batch_transaction_columns = [col['name'] for col in inspector.get_columns('batch_transactions')]

            if 'from_bin_location' not in batch_transaction_columns:
                print("  Adding from_bin_location column to batch_transactions...")
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE batch_transactions ADD COLUMN from_bin_location VARCHAR(50)"
                    ))
                    conn.commit()
                print("  ✓ Added from_bin_location column")
                needs_update = True
            else:
                print("  ✓ from_bin_location column already exists")

            if 'to_bin_location' not in batch_transaction_columns:
                print("  Adding to_bin_location column to batch_transactions...")
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE batch_transactions ADD COLUMN to_bin_location VARCHAR(50)"
                    ))
                    conn.commit()
                print("  ✓ Added to_bin_location column")
                needs_update = True
            else:
                print("  ✓ to_bin_location column already exists")

            if needs_update:
                print("\n✓ Successfully added bin tracking columns")
                print("\nNote: Existing records will have NULL bin locations.")
                print("New transfers and movements will track bin locations.")
            else:
                print("\n✓ All bin tracking columns already exist - no changes needed")

        except Exception as e:
            print(f"\n✗ Error adding bin tracking columns: {str(e)}")
            print("\nIf the columns already exist, you can ignore this error.")
            raise

if __name__ == '__main__':
    print("=" * 70)
    print("Database Migration: Add Bin Tracking to Movements and Transactions")
    print("=" * 70)
    add_bin_tracking_columns()
    print("=" * 70)
    print("Migration complete!")
    print("=" * 70)
