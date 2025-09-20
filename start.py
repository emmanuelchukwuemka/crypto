"""
Production startup script for Ethereum Withdrawal API
"""

import os
import sys
from app import run_server

if __name__ == "__main__":
    # Set production environment
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('FLASK_DEBUG', 'False')

    print("🚀 Starting Ethereum Token Withdrawal Server (Production)")
    print("=" * 60)

    try:
        run_server()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)
