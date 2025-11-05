# Local ERP Setup Guide

Follow these simple steps to run the Inventory ERP system on your local computer.

## Quick Start

### For Windows:

1. **Install Python 3.11 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Download the project**
   ```bash
   git clone https://github.com/vladutzeloo/olstral-erp.git
   cd olstral-erp
   ```

3. **Run the setup script**
   - Double-click `setup.bat`
   - Wait for it to complete

4. **Start the server**
   - Double-click `start_server.bat`
   - Open your browser to: http://localhost:5000

### For Mac/Linux:

1. **Install Python 3.11 or higher**
   ```bash
   # Mac (using Homebrew)
   brew install python@3.11

   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv
   ```

2. **Download the project**
   ```bash
   git clone https://github.com/vladutzeloo/olstral-erp.git
   cd olstral-erp
   ```

3. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Start the server**
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

   Open your browser to: http://localhost:5000

## Login Credentials

- **Username:** admin
- **Password:** admin123

**IMPORTANT:** Change the password after first login!

## Manual Setup (If scripts don't work)

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

## Stopping the Server

- Press `Ctrl+C` in the terminal window, or
- On Windows: Double-click `stop_server.bat`

## Troubleshooting

### Port 5000 Already in Use

Edit `app.py` line 80 and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Changed from 5000 to 8080
```

### Python Version Issues

Check your Python version:
```bash
python --version  # or python3 --version
```

Must be 3.11 or higher.

### Database Issues

If you need to reset the database:
1. Stop the server
2. Delete `inventory.db` file
3. Restart the server (database will be recreated)

## Features Available

Once running, you can:
- ✅ Manage inventory across multiple locations
- ✅ Create and track purchase orders
- ✅ Process receipts and shipments
- ✅ Manage clients and suppliers
- ✅ Track external processing/treatments
- ✅ Generate comprehensive reports
- ✅ Full audit trail of all transactions

## Accessing from Other Devices on Your Network

To access the ERP from other computers/tablets/phones on your network:

1. Find your computer's local IP address:
   ```bash
   # Windows
   ipconfig
   # Mac/Linux
   ifconfig
   ```

2. Look for something like `192.168.1.xxx`

3. On other devices, visit: `http://192.168.1.xxx:5000`

## Need Help?

- Check the main README.md for feature documentation
- Review SETUP_GUIDE.md for detailed information
- Check TROUBLESHOOTING section above
