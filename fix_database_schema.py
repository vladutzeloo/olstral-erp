#!/usr/bin/env python3
"""
Fix database schema to match current models
Adds missing columns to the locations table
"""
import sqlite3
import sys

def fix_database(db_path):
    """Add missing columns to the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Fixing database schema in {db_path}...")

    # Check current columns in locations table
    cursor.execute("PRAGMA table_info(locations)")
    columns = {row[1] for row in cursor.fetchall()}
    print(f"Current columns in locations: {columns}")

    # Add missing columns if they don't exist
    changes_made = False

    if 'zone' not in columns:
        print("Adding 'zone' column to locations table...")
        cursor.execute("ALTER TABLE locations ADD COLUMN zone VARCHAR(50)")
        changes_made = True
        print("✓ Added 'zone' column")
    else:
        print("✓ 'zone' column already exists")

    if 'capacity' not in columns:
        print("Adding 'capacity' column to locations table...")
        cursor.execute("ALTER TABLE locations ADD COLUMN capacity INTEGER")
        changes_made = True
        print("✓ Added 'capacity' column")
    else:
        print("✓ 'capacity' column already exists")

    if changes_made:
        conn.commit()
        print("\n✓ Database schema fixed successfully!")
    else:
        print("\n✓ Database schema is already up to date!")

    conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'instance/inventory.db'
    fix_database(db_path)
