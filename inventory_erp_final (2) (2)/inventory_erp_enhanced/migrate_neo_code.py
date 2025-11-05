import sqlite3
import sys

def migrate(db_path='inventory.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add neo_code to materials
    cursor.execute("PRAGMA table_info(materials)")
    cols = [col[1] for col in cursor.fetchall()]
    if 'neo_code' not in cols:
        cursor.execute("ALTER TABLE materials ADD COLUMN neo_code VARCHAR(50)")
        print("✓ Added neo_code to materials")
    
    # Add neo_code to items
    cursor.execute("PRAGMA table_info(items)")
    cols = [col[1] for col in cursor.fetchall()]
    if 'neo_code' not in cols:
        cursor.execute("ALTER TABLE items ADD COLUMN neo_code VARCHAR(50)")
        print("✓ Added neo_code to items")
    
    conn.commit()
    conn.close()
    print("✓ Migration complete")

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'inventory.db'
    migrate(db_path)
