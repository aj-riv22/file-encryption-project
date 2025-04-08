#!/usr/bin/env python3
"""
Start script for the Encrip server.
"""

from server import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting Encrip server...")
    print("Server running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 