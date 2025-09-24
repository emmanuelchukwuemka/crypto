"""
Complete System Startup Script
Starts both app.py and auto_withdrawal_monitor.py with complete 2-step withdrawal
"""

import subprocess
import sys
import os
import time
from threading import Thread
import signal

def run_app_server():
    """Run the Flask app server"""
    print("🚀 Starting Flask API server...")
    try:
        subprocess.run([sys.executable, "app.py"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("🛑 Flask server stopped")

def run_auto_monitor():
    """Run the automatic withdrawal monitor"""
    print("🤖 Starting automatic withdrawal monitor...")
    time.sleep(5)  # Wait for Flask server to start
    try:
        subprocess.run([sys.executable, "auto_withdrawal_monitor.py"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("🛑 Auto monitor stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🔔 Received shutdown signal - stopping all services...")
    sys.exit(0)

def main():
    """Main startup function"""
    print("🎯 Complete Ethereum Withdrawal System")
    print("=" * 50)
    print("This starts both services:")
    print("✅ Flask API Server (app.py)")
    print("✅ Auto Withdrawal Monitor (auto_withdrawal_monitor.py)")
    print("🔄 Complete 2-step withdrawal process enabled")
    print("=" * 50)
    
    # Check for private key
    if not os.getenv('WALLET_PRIVATE_KEY'):
        print("⚠️  WARNING: WALLET_PRIVATE_KEY environment variable not set")
        print("   Auto withdrawals will require manual intervention")
        print("   To enable full automation, run:")
        print("   set WALLET_PRIVATE_KEY=0x1234567890abcdef...")
        print()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start Flask server in a separate thread
        flask_thread = Thread(target=run_app_server, daemon=True)
        flask_thread.start()
        
        print("⏳ Waiting 5 seconds for Flask server to initialize...")
        time.sleep(5)
        
        # Start auto monitor (this will block)
        run_auto_monitor()
        
    except KeyboardInterrupt:
        print("\n🛑 System shutdown requested")
    except Exception as e:
        print(f"\n❌ System error: {e}")
    finally:
        print("🔚 Complete system stopped")

if __name__ == "__main__":
    print("🎯 COMPLETE WITHDRAWAL SYSTEM")
    print("=============================")
    print("✅ Automatic 2-step withdrawal process")
    print("✅ Source → WarehouseClient → Your Wallet")
    print("✅ No manual intervention required")
    print("✅ Continuous monitoring enabled")
    print()
    print("Press Ctrl+C to stop all services")
    print()
    
    main()