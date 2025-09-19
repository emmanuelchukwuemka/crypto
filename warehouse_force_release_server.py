"""
Warehouse Force Release API Server
REST API for forcing release of held funds from Splits Warehouse
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
from warehouse_force_release import WarehouseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global WarehouseClient
warehouse_client: WarehouseClient = None

def init_warehouse_client():
    """Initialize the WarehouseClient"""
    global warehouse_client
    try:
        warehouse_client = WarehouseClient()
        logger.info("✅ WarehouseClient initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize WarehouseClient: {e}")
        return False

def create_response(success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
    """Create standardized API response"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "api_version": "2.0.0"  # Following API versioning convention
    }
    
    if success:
        response["data"] = data
    else:
        response["error"] = error
        
    return response

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with Force Release API documentation"""
    return jsonify({
        "name": "Warehouse Force Release API Server",
        "version": "2.0.0",  # Following API versioning convention
        "status": "running",
        "description": "Force release held funds from Splits Protocol warehouse",
        "endpoints": {
            "GET /": "This documentation",
            "GET /release/status": "Get held funds and release status",
            "GET /release/held-funds": "Detailed held funds analysis",
            "POST /release/force": "Execute force release of held funds",
            "GET /release/health": "Health check for release operations",
            "POST /release/validate-nonce": "Validate nonce for release command"
        },
        "target_address": "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
        "warehouse_protocol": "Integrated with Splits Protocol for forced fund release",
        "important_note": "This API forces release of funds held in warehouse without code command"
    })

@app.route('/release/health', methods=['GET'])
def release_health():
    """Health check for force release operations"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="WarehouseClient not initialized")), 500
        
        # Test basic connectivity and get status
        address = warehouse_client.config["wallet_address"]
        status = warehouse_client.get_release_status(address)
        
        health_status = {
            "service": "online",
            "web3_connected": warehouse_client.w3.is_connected(),
            "chain_id": warehouse_client.w3.eth.chain_id,
            "target_address": address,
            "can_force_release": status.get('can_force_release', False),
            "nonce_ready": status.get('nonce_status', {}).get('ready_for_release', False),
            "held_funds_detected": status.get('held_funds', {}).get('release_ready', False)
        }
        
        return jsonify(create_response(True, health_status))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/release/status', methods=['GET'])
def get_release_status():
    """Get comprehensive release status and held funds information"""
    try:
        if not force_releaser:
            return jsonify(create_response(False, error="Force releaser not initialized")), 500
        
        address = force_releaser.config["wallet_address"]
        status = force_releaser.get_release_status(address)
        
        return jsonify(create_response(True, status))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/release/held-funds', methods=['GET'])
def get_held_funds_detailed():
    """Get detailed analysis of held funds in warehouse"""
    try:
        if not force_releaser:
            return jsonify(create_response(False, error="Force releaser not initialized")), 500
        
        address = force_releaser.config["wallet_address"]
        held_funds = force_releaser.get_held_funds_detailed(address)
        
        analysis = {
            "address": address,
            "held_funds": held_funds,
            "analysis_summary": {
                "total_eth_held": held_funds.get("eth_balance", 0),
                "total_tokens_held": len([t for t in held_funds.get("token_balances", {}).values() if t["balance"] > 0]),
                "total_value_eth": held_funds.get("total_held_value", 0),
                "release_ready": held_funds.get("release_ready", False),
                "needs_force_release": held_funds.get("release_ready", False)
            }
        }
        
        return jsonify(create_response(True, analysis))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/release/validate-nonce', methods=['POST'])
def validate_nonce_for_release():
    """Validate nonce for force release command"""
    try:
        if not force_releaser:
            return jsonify(create_response(False, error="Force releaser not initialized")), 500
        
        data = request.get_json() or {}
        address = data.get('address', force_releaser.config["wallet_address"])
        
        # Get nonce information following nonce management requirement
        current_nonce = force_releaser.w3.eth.get_transaction_count(address, 'latest')
        pending_nonce = force_releaser.w3.eth.get_transaction_count(address, 'pending')
        
        validation = {
            "address": address,
            "current_nonce": current_nonce,
            "pending_nonce": pending_nonce,
            "is_valid": current_nonce >= 0,
            "ready_for_release": pending_nonce == current_nonce,
            "can_execute_command": pending_nonce == current_nonce and current_nonce >= 0,
            "next_nonce": pending_nonce,
            "validation_timestamp": datetime.now().isoformat()
        }
        
        return jsonify(create_response(True, validation))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/release/force', methods=['POST'])
def execute_force_release():
    """Execute force release command to free held funds from warehouse"""
    try:
        if not force_releaser:
            return jsonify(create_response(False, error="Force releaser not initialized")), 500
        
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400
        
        address = data.get('address', force_releaser.config["wallet_address"])
        private_key = data.get('private_key')
        
        if not private_key:
            return jsonify(create_response(False, error="private_key required for force release")), 400
        
        # Validate private key format
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        # Validate private key matches address
        try:
            from eth_account import Account
            account = Account.from_key(private_key)
            if account.address.lower() != address.lower():
                return jsonify(create_response(False, error="Private key doesn't match address")), 400
        except Exception as e:
            return jsonify(create_response(False, error=f"Invalid private key: {e}")), 400
        
        logger.info(f"🚀 Executing force release for {address}")
        
        # Execute force release in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                force_releaser.execute_force_release(address, private_key)
            )
        finally:
            loop.close()
        
        if result['status'] == 'success':
            logger.info(f"✅ Force release successful: {result['transaction_hash']}")
            return jsonify(create_response(True, result))
        elif result['status'] == 'no_funds_held':
            return jsonify(create_response(False, error=result['message'], data=result)), 400
        else:
            logger.error(f"❌ Force release failed: {result.get('error', 'Unknown error')}")
            return jsonify(create_response(False, error=result.get('error', 'Force release failed'), data=result)), 400
        
    except Exception as e:
        logger.error(f"Force release execution failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/release/simulate', methods=['POST'])
def simulate_force_release():
    """Simulate force release without executing (for testing)"""
    try:
        if not force_releaser:
            return jsonify(create_response(False, error="Force releaser not initialized")), 500
        
        data = request.get_json() or {}
        address = data.get('address', force_releaser.config["wallet_address"])
        
        # Get held funds information
        held_funds = force_releaser.get_held_funds_detailed(address)
        
        if not held_funds.get("release_ready"):
            return jsonify(create_response(False, error="No funds to release", data=held_funds)), 400
        
        # Simulate transaction creation
        try:
            transaction = force_releaser.create_force_release_transaction(address, held_funds)
            
            simulation = {
                "address": address,
                "held_funds": held_funds,
                "simulated_transaction": {
                    "to": transaction['to'],
                    "value": transaction['value'],
                    "gas": transaction['gas'],
                    "gasPrice": transaction['gasPrice'],
                    "nonce": transaction['nonce'],
                    "estimated_gas_cost_eth": float(force_releaser.w3.from_wei(
                        transaction['gas'] * transaction['gasPrice'], 'ether'
                    ))
                },
                "would_release": {
                    "eth_amount": held_funds.get("eth_balance", 0),
                    "token_count": len([t for t in held_funds.get("token_balances", {}).values() if t["balance"] > 0]),
                    "total_value": held_funds.get("total_held_value", 0)
                },
                "simulation_note": "This is a simulation - no actual transaction was sent"
            }
            
            return jsonify(create_response(True, simulation))
            
        except Exception as e:
            return jsonify(create_response(False, error=f"Simulation failed: {e}")), 400
        
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
    """Run the Warehouse Force Release API server"""
    print("🚀 Starting Warehouse Force Release API Server")
    print("=" * 50)
    
    # Initialize force releaser
    if not init_force_releaser():
        print("❌ Failed to initialize force releaser")
        return
    
    try:
        # Get initial status
        address = force_releaser.config["wallet_address"]
        status = force_releaser.get_release_status(address)
        
        print("✅ Force releaser initialized")
        print(f"\n📊 Current Status:")
        print(f"   Target Address: {address}")
        print(f"   ENS: {force_releaser.config['ens_public_client']}")
        print(f"   Wallet Balance: {status['wallet_balance_eth']} ETH")
        print(f"   Current Nonce: {status['nonce_status']['current_nonce']}")
        print(f"   Ready for Release: {'✅' if status['nonce_status']['ready_for_release'] else '❌'}")
        
        held_funds = status['held_funds']
        print(f"\n🏭 Warehouse Fund Analysis:")
        print(f"   Can Force Release: {'✅' if held_funds.get('release_ready') else '❌'}")
        print(f"   ETH Held: {held_funds.get('eth_balance', 0)} ETH")
        print(f"   Tokens Held: {len(held_funds.get('token_balances', {}))}")
        print(f"   Total Value: {held_funds.get('total_held_value', 0)} ETH equivalent")
        
        if held_funds.get('token_balances'):
            print(f"\n💰 Held Funds Details:")
            for token_name, token_info in held_funds['token_balances'].items():
                if token_info['balance'] > 0:
                    print(f"   {token_name}: {token_info['balance']}")
        
        if held_funds.get('release_ready'):
            print(f"\n🚨 HELD FUNDS DETECTED!")
            print(f"   Your funds are being held in the warehouse")
            print(f"   Force release is available and ready")
            
    except Exception as e:
        print(f"⚠️ Status check failed: {e}")
    
    print(f"\n🌐 Force Release API Endpoints:")
    print(f"   📍 Base URL: http://localhost:5000")
    print(f"   📖 Documentation: GET /")
    print(f"   💚 Health Check: GET /release/health")
    print(f"   📊 Release Status: GET /release/status")
    print(f"   💰 Held Funds: GET /release/held-funds")
    print(f"   🔢 Validate Nonce: POST /release/validate-nonce")
    print(f"   🚀 FORCE RELEASE: POST /release/force")
    print(f"   🧪 Simulate Release: POST /release/simulate")
    
    print(f"\n🎯 Ready to force release held warehouse funds!")
    print("=" * 50)
    
    # Run the Flask server using specified web framework
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()