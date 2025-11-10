"""
Migration Script: Add bin_location column to batches table

This script adds the bin_location column to the batches table to support
warehouse bin tracking for FIFO inventory management.

Run this script once to update your database:
    python add_bin_location_migration.py
"""

from app import app
from extensions import db

def add_bin_location_column():
    """Add bin_location column to batches table"""
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('batches')]

            if 'bin_location' in columns:
                print("✓ bin_location column already exists in batches table")
                return

            # Add the column
            print("Adding bin_location column to batches table...")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    "ALTER TABLE batches ADD COLUMN bin_location VARCHAR(50)"
                ))
                conn.commit()

            print("✓ Successfully added bin_location column to batches table")
            print("\nNote: Existing batches will have NULL bin_location.")
            print("You can update them manually through the inventory interface.")

        except Exception as e:
            print(f"✗ Error adding bin_location column: {str(e)}")
            print("\nIf the column already exists, you can ignore this error.")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add bin_location to batches")
    print("=" * 60)
    add_bin_location_column()
    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)
