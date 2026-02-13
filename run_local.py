#!/usr/bin/env python3
"""Run the yt-dlp-host server locally without Docker"""
import os
import sys

# Set the download directory to local path before importing config
os.environ['DOWNLOAD_DIR'] = os.path.join(os.getcwd(), 'downloads')

# Import and patch the config
from config import storage
storage.DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')

# Now import and start the server
from src.server import app

if __name__ == '__main__':
    print(f"Starting yt-dlp-host server...")
    print(f"Download directory: {storage.DOWNLOAD_DIR}")
    print(f"API endpoint: http://localhost:5050")
    print(f"Health check: http://localhost:5050/health")
    print(f"\nAPI Key (admin): HbbRxQNiz3py27wRvyb-e9LSmFYIImMs0murWGNB1HE")
    print(f"\nPress Ctrl+C to stop the server\n")

    # Ensure directories exist
    os.makedirs(storage.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs('jsons', exist_ok=True)

    # Start the Flask app
    app.run(host='0.0.0.0', port=5050, debug=True)
