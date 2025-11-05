#!/bin/bash

echo "Stopping Inventory ERP System..."

# Find and kill the Flask process
pkill -f "python app.py"
pkill -f "flask run"

echo "Server stopped."
