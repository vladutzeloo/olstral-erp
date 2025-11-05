#!/bin/bash

echo "=========================================="
echo "  Starting Inventory ERP System..."
echo "=========================================="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found!"
    echo "Please run setup.sh first"
    exit 1
fi

# Start the application
echo "Starting server on http://localhost:5000"
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python app.py
