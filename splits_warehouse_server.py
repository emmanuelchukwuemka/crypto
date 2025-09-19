"""
Splits Warehouse API Server
REST API for automated Splits Protocol warehouse interactions
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
from splits_warehouse_client import SplitsWarehouseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global warehouse client
warehouse_client: SplitsWarehouseClient = None

def init_warehouse_client():
    """Initialize the Splits Warehouse client"""
    global warehouse_client
    try:
        warehouse_client = SplitsWarehouseClient()
        logger.info("✅ Splits Warehouse client initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize warehouse client: {e}")
        return False

def create_response(success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
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

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with Splits Warehouse API documentation"""
    return jsonify({
        "name": "Splits Warehouse API Server",
        "version": "2.0.0",
        "status": "running",
        "description": "Automated Splits Protocol warehouse token withdrawal API",
        "endpoints": {
            "GET /": "This documentation",
            "GET /warehouse/status": "Get warehouse and system status",
            "GET /warehouse/balances": "Get warehouse balances for address",
            "POST /warehouse/validate-nonce": "Validate nonce for warehouse communication",
            "GET /warehouse/pending": "Get pending distributions",
            "POST /warehouse/withdraw": "Execute automatic withdrawal",
            "POST /warehouse/create-transaction": "Create withdrawal transaction",
            "GET /warehouse/health": "Health check for warehouse operations"
        },
        "target_address": "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
        "splits_protocol": "Integrated with 0xSplits protocol for automated withdrawals"
    })

@app.route('/warehouse/health', methods=['GET'])
def warehouse_health():
    """Health check for warehouse operations"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        # Test basic connectivity
        status = warehouse_client.get_system_status()
        
        health_status = {
            "warehouse_service": "online",
            "web3_connected": status['connection']['web3_connected'],
            "chain_id": status['connection']['chain_id'],
            "warehouse_ready": status['nonce_status']['warehouse_ready'],
            "has_claimable_funds": status['warehouse_status']['has_claimable_funds']
        }
        
        return jsonify(create_response(True, health_status))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/status', methods=['GET'])
def get_warehouse_status():
    """Get comprehensive warehouse status"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        status = warehouse_client.get_system_status()
        return jsonify(create_response(True, status))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/balances', methods=['GET'])
def get_warehouse_balances():
    """Get warehouse balances for the configured address"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        address = warehouse_client.config["wallet_address"]
        balances = warehouse_client.get_warehouse_balances(address)
        
        result = {
            "address": address,
            "balances": balances,
            "total_value": sum(balances.values()),
            "has_funds": any(balance > 0 for balance in balances.values()),
            "claimable_tokens": [token for token, balance in balances.items() if balance > 0]
        }
        
        return jsonify(create_response(True, result))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/validate-nonce', methods=['POST'])
def validate_warehouse_nonce():
    """Validate nonce for warehouse communication"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        data = request.get_json() or {}
        address = data.get('address', warehouse_client.config["wallet_address"])
        
        validation = warehouse_client.validate_nonce_for_warehouse(address)
        return jsonify(create_response(True, validation))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/pending', methods=['GET'])
def get_pending_distributions():
    """Get pending distributions for the address"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        address = warehouse_client.config["wallet_address"]
        pending = warehouse_client.check_pending_distributions(address)
        
        result = {
            "address": address,
            "pending_distributions": pending,
            "total_pending": len(pending),
            "claimable_count": len([p for p in pending if p['claimable']])
        }
        
        return jsonify(create_response(True, result))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/create-transaction', methods=['POST'])
def create_withdrawal_transaction():
    """Create a withdrawal transaction for Splits Warehouse"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400
        
        address = data.get('address', warehouse_client.config["wallet_address"])
        withdraw_eth = float(data.get('withdraw_eth', 0))
        tokens = data.get('tokens', [])
        
        # Create transaction
        transaction = warehouse_client.create_withdrawal_transaction(
            address, withdraw_eth, tokens
        )
        
        # Calculate cost estimate
        gas_cost_wei = transaction['gas'] * transaction['gasPrice']
        gas_cost_eth = float(Web3.from_wei(gas_cost_wei, 'ether'))
        
        result = {
            "transaction": transaction,
            "withdrawal_details": {
                "address": address,
                "eth_amount": withdraw_eth,
                "tokens": tokens,
                "gas_estimate": transaction['gas'],
                "gas_cost_eth": gas_cost_eth
            },
            "ready_to_sign": True
        }
        
        return jsonify(create_response(True, result))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/warehouse/withdraw', methods=['POST'])
def execute_automatic_withdrawal():
    """Execute automatic withdrawal from Splits Warehouse"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400
        
        address = data.get('address', warehouse_client.config["wallet_address"])
        private_key = data.get('private_key')
        auto_detect = data.get('auto_detect_amounts', True)
        
        if not private_key:
            return jsonify(create_response(False, error="private_key required")), 400
        
        # Validate private key format
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        # Execute withdrawal in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                warehouse_client.execute_automatic_withdrawal(
                    address, private_key, auto_detect
                )
            )
        finally:
            loop.close()
        
        if result['status'] == 'success':
            return jsonify(create_response(True, result))
        elif result['status'] == 'no_funds':
            return jsonify(create_response(False, error=result['message'], data=result)), 400
        else:
            return jsonify(create_response(False, error=result.get('error', 'Withdrawal failed'), data=result)), 400
        
    except Exception as e:
        logger.error(f"Withdrawal execution failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/monitor', methods=['GET'])
def monitor_warehouse():
    """Monitor warehouse for automatic withdrawal opportunities"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        address = warehouse_client.config["wallet_address"]
        
        # Get current status
        balances = warehouse_client.get_warehouse_balances(address)
        nonce_status = warehouse_client.validate_nonce_for_warehouse(address)
        pending = warehouse_client.check_pending_distributions(address)
        
        # Determine if automatic withdrawal should be triggered
        has_funds = any(balance > 0 for balance in balances.values())
        is_ready = nonce_status['warehouse_ready']
        
        monitoring_result = {
            "address": address,
            "balances": balances,
            "nonce_status": nonce_status,
            "pending_distributions": pending,
            "auto_withdraw_recommended": has_funds and is_ready,
            "monitoring_timestamp": datetime.now().isoformat(),
            "next_check_recommended": datetime.now().isoformat()  # Could add scheduling logic
        }
        
        return jsonify(create_response(True, monitoring_result))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify(create_response(False, error="Endpoint not found")), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify(create_response(False, error="Internal server error")), 500

def main():
    """Run the Splits Warehouse API server"""
    print("🏭 Starting Splits Warehouse API Server")
    print("=" * 50)
    
    # Initialize warehouse client
    if not init_warehouse_client():
        print("❌ Failed to initialize warehouse client")
        return
    
    try:
        # Get initial status
        status = warehouse_client.get_system_status()
        
        print("✅ Warehouse client initialized")
        print(f"\n📊 System Status:")
        print(f"   Connected: {'✅' if status['connection']['web3_connected'] else '❌'}")
        print(f"   Chain ID: {status['connection']['chain_id']}")
        print(f"   Target Address: {status['address_info']['address']}")
        print(f"   ENS: {status['address_info']['ens_name']}")
        print(f"   Warehouse Ready: {'✅' if status['nonce_status']['warehouse_ready'] else '❌'}")
        print(f"   Has Claimable Funds: {'✅' if status['warehouse_status']['has_claimable_funds'] else '❌'}")
        
        if status['warehouse_status']['has_claimable_funds']:
            print(f"\n💰 Warehouse Balances:")
            for token, balance in status['warehouse_status']['balances'].items():
                if balance > 0:
                    print(f"   {token}: {balance}")
        
    except Exception as e:
        print(f"⚠️ Status check failed: {e}")
    
    print(f"\n🌐 API Endpoints:")
    print(f"   📍 Base URL: http://localhost:5000")
    print(f"   📖 Documentation: GET /")
    print(f"   💚 Health Check: GET /warehouse/health")
    print(f"   📊 Warehouse Status: GET /warehouse/status")
    print(f"   💰 Check Balances: GET /warehouse/balances")
    print(f"   🔢 Validate Nonce: POST /warehouse/validate-nonce")
    print(f"   📋 Pending Distributions: GET /warehouse/pending")
    print(f"   🚀 Auto Withdraw: POST /warehouse/withdraw")
    print(f"   📊 Monitor: GET /warehouse/monitor")
    
    print(f"\n🎯 Ready to handle Splits Warehouse operations!")
    print("=" * 50)
    
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()