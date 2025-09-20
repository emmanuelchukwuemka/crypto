"""
Etherscan API Integration Routes
Enhanced nonce tracking with Etherscan API
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime
from etherscan_nonce_tracker import EtherscanNonceTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app for Etherscan API integration
etherscan_app = Flask(__name__)
CORS(etherscan_app)

# Global tracker instance
etherscan_tracker = None

def init_etherscan_tracker():
    """Initialize Etherscan tracker"""
    global etherscan_tracker
    try:
        etherscan_tracker = EtherscanNonceTracker()
        logger.info("✅ Etherscan tracker initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Etherscan tracker: {e}")
        return False

def get_tracker():
    """Get Etherscan tracker instance"""
    global etherscan_tracker
    if etherscan_tracker is None:
        if not init_etherscan_tracker():
            raise Exception("Etherscan tracker not initialized")
    return etherscan_tracker

def create_response(success: bool, data=None, error=None):
    """Create standardized API response"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
    }
    
    if success:
        response["data"] = data
    else:
        response["error"] = error
        
    return response

@etherscan_app.route('/', methods=['GET'])
def etherscan_home():
    """Etherscan API integration documentation"""
    return jsonify({
        "name": "Etherscan API Integration Server",
        "version": "1.0.0",
        "status": "running",
        "api_key": "9Y21AH2N2ABCQ5FD2BDT2WYV8RCP83FB74",
        "endpoints": {
            "GET /": "This documentation",
            "GET /etherscan-status": "Etherscan API status and tracking info",
            "GET /enhanced-nonce/<address>": "Get nonce via Etherscan API (tracked)",
            "GET /validate-nonce-tracking/<address>": "Comprehensive nonce validation",
            "GET /transaction-history/<address>": "Get transaction history via Etherscan",
            "GET /api-usage": "Check API usage statistics"
        },
        "description": "Enhanced nonce tracking using Etherscan API for precise transaction management"
    })

@etherscan_app.route('/etherscan-status', methods=['GET'])
def etherscan_status():
    """Get Etherscan API integration status"""
    try:
        tracker = get_tracker()
        
        status_data = {
            "etherscan_integration": {
                "api_key": "9Y21AH2N2ABCQ5FD2BDT2WYV8RCP83FB74",
                "api_key_configured": True,
                "tracking_active": True,
                "api_calls_today": tracker.api_call_count,
                "last_reset": tracker.last_api_reset.isoformat(),
                "base_url": tracker.etherscan_base_url
            },
            "client_status": {
                "web3_connected": tracker.w3.is_connected(),
                "chain_id": tracker.w3.eth.chain_id,
                "current_block": tracker.w3.eth.block_number
            }
        }
        
        return jsonify(create_response(True, status_data))
        
    except Exception as e:
        logger.error(f"Etherscan status check failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@etherscan_app.route('/enhanced-nonce/<address>', methods=['GET'])
def get_enhanced_nonce(address: str):
    """Get nonce using Etherscan API (counts towards daily limit)"""
    try:
        tracker = get_tracker()
        
        # Get nonce via Etherscan API (this will be tracked)
        etherscan_nonce = tracker.get_nonce_via_etherscan(address)
        web3_nonce = tracker.get_nonce_via_web3(address)
        
        response_data = {
            "address": address,
            "etherscan_nonce": etherscan_nonce,
            "web3_nonce": web3_nonce,
            "recommended_nonce": etherscan_nonce,
            "sources_match": etherscan_nonce == web3_nonce,
            "api_calls_today": tracker.api_call_count,
            "tracking_active": True
        }
        
        return jsonify(create_response(True, response_data))
        
    except Exception as e:
        logger.error(f"Enhanced nonce check failed for {address}: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@etherscan_app.route('/validate-nonce-tracking/<address>', methods=['GET'])
def validate_nonce_tracking(address: str):
    """Comprehensive nonce validation using Etherscan API"""
    try:
        tracker = get_tracker()
        
        # Perform comprehensive validation
        validation_result = tracker.validate_nonce_tracking(address)
        
        return jsonify(create_response(True, validation_result))
        
    except Exception as e:
        logger.error(f"Nonce validation failed for {address}: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@etherscan_app.route('/transaction-history/<address>', methods=['GET'])
def get_transaction_history(address: str):
    """Get transaction history via Etherscan API"""
    try:
        tracker = get_tracker()
        
        # Get limit from query parameter
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Max 100 transactions
        
        # Get transaction history via Etherscan API
        transactions = tracker.get_transaction_history_via_etherscan(address, limit)
        
        response_data = {
            "address": address,
            "transaction_count": len(transactions),
            "limit": limit,
            "transactions": transactions,
            "api_calls_today": tracker.api_call_count
        }
        
        return jsonify(create_response(True, response_data))
        
    except Exception as e:
        logger.error(f"Transaction history failed for {address}: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@etherscan_app.route('/api-usage', methods=['GET'])
def get_api_usage():
    """Get Etherscan API usage statistics"""
    try:
        tracker = get_tracker()
        
        usage_data = {
            "api_key": "9Y21AH2N2ABCQ5FD2BDT2WYV8RCP83FB74",
            "calls_today": tracker.api_call_count,
            "last_reset": tracker.last_api_reset.isoformat(),
            "daily_limit": 100000,  # Etherscan free tier limit
            "calls_remaining": 100000 - tracker.api_call_count,
            "usage_percentage": (tracker.api_call_count / 100000) * 100,
            "tracking_active": True,
            "status": "healthy" if tracker.api_call_count < 90000 else "approaching_limit"
        }
        
        return jsonify(create_response(True, usage_data))
        
    except Exception as e:
        logger.error(f"API usage check failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@etherscan_app.route('/health', methods=['GET'])
def health_check():
    """Health check for Etherscan integration"""
    try:
        tracker = get_tracker()
        connected = tracker.w3.is_connected()
        
        return jsonify({
            "status": "healthy" if connected else "unhealthy",
            "etherscan_integration": "active",
            "api_key": "configured",
            "connected": connected,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def run_etherscan_server():
    """Run the Etherscan integration server"""
    print("🚀 Starting Etherscan API Integration Server")
    print("=" * 60)
    
    # Initialize Etherscan tracker
    if not init_etherscan_tracker():
        print("❌ Failed to initialize Etherscan tracker")
        return
        
    print("✅ Etherscan tracker initialized")
    print(f"🔑 API Key: PF423A8SIHNIXVM8K13X2S8G9YTKSDCZ")
    
    # Test the tracker
    try:
        wallet_address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"
        validation = etherscan_tracker.validate_nonce_tracking(wallet_address)
        print(f"\n📊 Nonce Tracking Test:")
        print(f"   Wallet: {wallet_address}")
        print(f"   Etherscan Nonce: {validation['etherscan_nonce']}")
        print(f"   Web3 Nonce: {validation['web3_nonce']}")
        print(f"   Tracking Active: {validation['tracking_active']}")
        print(f"   API Calls: {validation['api_calls_tracked']}")
    except Exception as e:
        print(f"⚠️ Tracker test failed: {e}")
    
    print("\n🌐 Etherscan API Endpoints:")
    print(f"   📍 Base URL: http://localhost:5001")
    print(f"   📖 Documentation: GET /")
    print(f"   💚 Health Check: GET /health")
    print(f"   📊 Etherscan Status: GET /etherscan-status")
    print(f"   🔢 Enhanced Nonce: GET /enhanced-nonce/<address>")
    print(f"   ✅ Validate Tracking: GET /validate-nonce-tracking/<address>")
    print(f"   📋 Transaction History: GET /transaction-history/<address>")
    print(f"   📈 API Usage: GET /api-usage")
    
    print(f"\n🎯 Etherscan API Integration Ready!")
    print("🔄 All API calls will be tracked and counted")
    print("=" * 60)
    
    # Run the Flask server on port 5001
    etherscan_app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == "__main__":
    run_etherscan_server()