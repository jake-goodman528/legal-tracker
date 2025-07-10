#!/usr/bin/env python3
"""
Main entry point for the STR Compliance Toolkit Flask application.
"""

import os
import sys

# Add the current directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.application import create_app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration from environment variables
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.environ.get("PORT", 9000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    if debug_mode:
        print(f"Starting STR Compliance Toolkit on {host}:{port}")
        print(f"Debug mode: {debug_mode}")
        print(f"Admin username: {os.environ.get('ADMIN_USERNAME', 'admin')}")
    else:
        print(f"Starting STR Compliance Toolkit on {host}:{port}")
    
    app.run(host=host, port=port, debug=debug_mode) 