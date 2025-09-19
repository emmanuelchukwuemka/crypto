"""
Production Server Startup Script
Run the Ethereum server with proper configuration
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import flask_cors
        import web3
        import eth_account
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install -r requirements.txt")
        return False

def start_development_server():
    """Start the Flask development server"""
    print("🚀 Starting Development Server")
    print("=" * 40)
    
    if not check_dependencies():
        return False
    
    try:
        # Import and run the server
        from app import run_server
        run_server()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False
    
    return True

def start_production_server(host="0.0.0.0", port=5000, workers=4):
    """Start the production server with Gunicorn"""
    print("🏭 Starting Production Server with Gunicorn")
    print("=" * 40)
    
    if not check_dependencies():
        return False
    
    try:
        # Check if gunicorn is available
        subprocess.run(["gunicorn", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Gunicorn not found. Install with: pip install gunicorn")
        return False
    
    # Gunicorn configuration
    cmd = [
        "gunicorn",
        "--bind", f"{host}:{port}",
        "--workers", str(workers),
        "--worker-class", "sync",
        "--timeout", "120",
        "--keep-alive", "5",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--preload",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "app:app"
    ]
    
    print(f"📍 Server will run on http://{host}:{port}")
    print(f"👥 Workers: {workers}")
    print(f"📝 Command: {' '.join(cmd)}")
    print("\n🎯 Press Ctrl+C to stop")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server error: {e}")
        return False
    
    return True

def show_usage():
    """Show usage information"""
    print("Ethereum Token Withdrawal Server")
    print("=" * 40)
    print("Usage:")
    print("  python start_server.py [mode] [options]")
    print("")
    print("Modes:")
    print("  dev        Start development server (default)")
    print("  prod       Start production server with Gunicorn")
    print("  test       Test server connectivity")
    print("")
    print("Options for production mode:")
    print("  --host HOST     Bind to host (default: 0.0.0.0)")
    print("  --port PORT     Bind to port (default: 5000)")
    print("  --workers N     Number of worker processes (default: 4)")
    print("")
    print("Examples:")
    print("  python start_server.py")
    print("  python start_server.py dev")
    print("  python start_server.py prod")
    print("  python start_server.py prod --port 8080 --workers 8")
    print("  python start_server.py test")

def test_server():
    """Test server connectivity"""
    print("🧪 Testing Server Connectivity")
    print("=" * 40)
    
    try:
        from server_client_example import EthereumServerClient
        import time
        
        # Try to connect to server
        client = EthereumServerClient()
        
        print("🔍 Checking if server is running...")
        health = client.get_health()
        
        if health.get('status') == 'healthy':
            print("✅ Server is running and healthy")
            
            # Test basic endpoints
            print("🧪 Testing endpoints...")
            
            status = client.get_system_status()
            if status.get('success'):
                print("✅ System status endpoint working")
            
            info = client.get_server_info()
            if info.get('name'):
                print("✅ Server info endpoint working")
            
            print("🎉 All tests passed!")
            return True
            
        else:
            print("❌ Server is not responding correctly")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure the server is running:")
        print("   python start_server.py dev")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) == 1 or sys.argv[1] == "dev":
        # Default: development mode
        start_development_server()
        
    elif sys.argv[1] == "prod":
        # Production mode
        host = "0.0.0.0"
        port = 5000
        workers = 4
        
        # Parse additional arguments
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--workers" and i + 1 < len(sys.argv):
                workers = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        start_production_server(host, port, workers)
        
    elif sys.argv[1] == "test":
        # Test mode
        success = test_server()
        sys.exit(0 if success else 1)
        
    elif sys.argv[1] in ["-h", "--help", "help"]:
        # Help
        show_usage()
        
    else:
        print(f"❌ Unknown mode: {sys.argv[1]}")
        show_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()