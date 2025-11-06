# WINDOWS FIX - Database Schema Error

If you're getting `no such column: locations.zone` error on Windows, follow these steps **EXACTLY**:

## Step 1: Close Everything
- Close your browser
- Stop the Flask app (Ctrl+C)
- Close any Python processes

## Step 2: Pull Latest Changes
```powershell
git pull origin claude/locate-database-file-011CUqHNZwEVSN5ErRZrSK2c
```

## Step 3: Verify data folder exists
```powershell
# Check if data folder exists
Test-Path data
```
If it says `False`, create it:
```powershell
mkdir data
```

## Step 4: Delete Old Database (IMPORTANT!)
```powershell
# Force delete the old database
Remove-Item -Force data\inventory.db
```

## Step 5: Copy Fixed Sample Database
```powershell
Copy-Item sample_inventory.db data\inventory.db
```

## Step 6: Verify Database Schema (Optional)
```powershell
python -c "import sqlite3; conn = sqlite3.connect('data/inventory.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(locations)'); columns = [row[1] for row in cursor.fetchall()]; print('Columns:', columns); print('Has zone?', 'zone' in columns); print('Has capacity?', 'capacity' in columns)"
```

This should print:
```
Has zone? True
Has capacity? True
```

## Step 7: Start App
```powershell
python app.py
```

## If It STILL Doesn't Work

Your browser might be showing a cached error. Do this:
1. Close ALL browser tabs with the app
2. Clear browser cache (Ctrl+Shift+Delete)
3. Open a NEW incognito/private window
4. Go to http://localhost:5000

---

## Alternative: Manual Database Fix

If copying doesn't work, run this:
```powershell
python fix_database_schema.py data\inventory.db
```

Then restart the app.
