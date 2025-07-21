#!/bin/bash

# Setup and run script for Indian Retail Trends Dashboard

# Print colorful messages
function print_message() {
    echo -e "\033[1;36m>> $1\033[0m"
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"  # Change to the script directory

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

print_message "Setting up Indian Retail Trends Dashboard..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_message "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source venv/bin/activate

# Install requirements
print_message "Installing required packages..."
pip install -r requirements.txt

# Generate data if it doesn't exist
if [ ! -f "data/retail_trends_data.json" ]; then
    print_message "Generating synthetic data (this may take a few minutes)..."
    python src/generate_data.py
fi

# Run the server
print_message "Starting the dashboard server..."
print_message "Access the dashboard at http://localhost:5000"
python src/app.py

# Deactivate virtual environment on exit
deactivate
