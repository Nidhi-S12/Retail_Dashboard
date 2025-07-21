#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask server for serving the Indian Retail Trends Dashboard
"""

from flask import Flask, send_from_directory
import os
import sys

# Get the project root directory (parent of 'src')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)  # Change to project root directory

app = Flask(__name__, static_folder=ROOT_DIR)

@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory(ROOT_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(ROOT_DIR, path)

if __name__ == '__main__':
    # Check if data directory exists, create if not
    data_dir = os.path.join(ROOT_DIR, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Check if the JSON data file exists, if not, suggest generating it
    json_path = os.path.join(data_dir, 'retail_trends_data.json')
    if not os.path.exists(json_path):
        print("Warning: Data file not found. Please run 'python src/generate_data.py' first.")
    
    print("Starting server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
