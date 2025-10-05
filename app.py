"""
Main Flask application for Ethereum Token Withdrawal System
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
from simple_ethereum_client import SimpleEthereumClient
from etherscan_nonce_tracker import EtherscanNonceTracker
from splits_warehouse_client import SplitsWarehouseClient
from eth_account import Account
import traceback
from datetime import datetime

# Configure logging for production
if os.getenv('FLASK_ENV') == 'production':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/app.log')
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Production configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Global client instances
ethereum_client: Optional[SimpleEthereumClient] = None
warehouse_client: Optional[SplitsWarehouseClient] = None


def init_client():
    """Initialize the Ethereum client"""
    global ethereum_client
    try:
        ethereum_client = SimpleEthereumClient()
        logger.info("✅ Ethereum client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Ethereum client: {e}")
        return False

def init_warehouse_client():
    """Initialize the Splits Warehouse client"""
    global warehouse_client
    try:
        # Ensure config files exist
        if not os.path.exists('warehouse_config.json'):
            logger.warning("warehouse_config.json not found, using config.json")
        
        warehouse_client = SplitsWarehouseClient()
        
        # Test the client connection
        test_address = warehouse_client.config["wallet_address"]
        nonce_validation = warehouse_client.validate_nonce_for_warehouse(test_address)
        
        if nonce_validation['warehouse_ready']:
            logger.info("✅ Splits Warehouse client initialized and ready")
        else:
            logger.warning("⚠️ Warehouse client initialized but not ready for operations")
            
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize warehouse client: {e}")
        warehouse_client = None
        return False

def get_client() -> SimpleEthereumClient:
    """Get the Ethereum client instance"""
    global ethereum_client
    if ethereum_client is None:
        if not init_client():
            raise Exception("Ethereum client not initialized")
    return ethereum_client  # type: ignore

def create_response(success: bool, data: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
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
    """Home endpoint with API documentation"""
    return jsonify({
        "name": "Ethereum Token Withdrawal Server",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "GET /": "This documentation",
            "GET /status": "System status and health check",
            "GET /balance/<address>": "Get ETH balance for address",
            "GET /nonce/<address>": "Get current nonce for address",
            "POST /validate-nonce": "Validate nonce for address",
            "POST /resolve-ens": "Resolve ENS name to address",
            "POST /create-transaction": "Create unsigned transaction",
            "POST /execute-withdrawal": "Execute complete withdrawal",
            "GET /withdraw-config/<address>": "Get withdrawal configuration",
            "GET /gas-price": "Get current gas price",
            "GET /eip712-domain": "Get EIP-712 domain",
            "GET /warehouse/health": "Warehouse health check",
            "GET /warehouse/status": "Warehouse system status",
            "GET /warehouse/balances": "Get warehouse balances",
            "POST /warehouse/validate-nonce": "Validate nonce for warehouse",
            "GET /warehouse/pending": "Get pending distributions",
            "POST /warehouse/create-transaction": "Create warehouse transaction",
            "POST /warehouse/withdraw": "Execute warehouse withdrawal",
            "POST /warehouse/complete-withdraw": "Execute complete 2-step withdrawal (source->warehouse->wallet)",
            "GET /warehouse/monitor": "Monitor warehouse opportunities"
        },
        "documentation": "Send requests to individual endpoints for functionality"
    })

@app.route('/status', methods=['GET'])
def system_status():
    """Get comprehensive system status"""
    try:
        client = get_client()
        status = client.get_system_status()

        # Add server-specific status
        server_status = {
            "server": "online",
            "client_initialized": ethereum_client is not None,
            "blockchain": status
        }

        return jsonify(create_response(True, server_status))

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address: str):
    """Get ETH balance for an address"""
    try:
        client = get_client()
        balance = client.get_balance(address)

        # Only try to convert to wei if client is properly initialized
        balance_wei = 0
        if hasattr(client, 'w3') and client.w3:
            try:
                balance_wei = client.w3.to_wei(balance, 'ether')
            except:
                # Fallback if there's an issue with the conversion
                balance_wei = int(balance * 10**18)

        return jsonify(create_response(True, {
            "address": address,
            "balance_eth": balance,
            "balance_wei": balance_wei
        }))

    except Exception as e:
        logger.error(f"Balance check failed for {address}: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/nonce/<address>', methods=['GET'])
def get_nonce(address: str):
    """Get current nonce for an address"""
    try:
        client = get_client()
        nonce = client.get_nonce(address)

        return jsonify(create_response(True, {
            "address": address,
            "nonce": nonce,
            "is_valid": True
        }))

    except Exception as e:
        logger.error(f"Nonce check failed for {address}: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/validate-nonce', methods=['POST'])
def validate_nonce():
    """Validate if a nonce is valid for an address"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400

        address = data.get('address')
        nonce = data.get('nonce')

        if not address or nonce is None:
            return jsonify(create_response(False, error="address and nonce required")), 400

        client = get_client()
        is_valid = client.is_valid_nonce(int(nonce), address)
        current_nonce = client.get_nonce(address)

        return jsonify(create_response(True, {
            "address": address,
            "requested_nonce": nonce,
            "current_nonce": current_nonce,
            "is_valid": is_valid,
            "can_communicate": is_valid
        }))

    except Exception as e:
        logger.error(f"Nonce validation failed: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/resolve-ens', methods=['POST'])
def resolve_ens():
    """Resolve ENS name to Ethereum address"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400

        ens_name = data.get('ens_name')
        if not ens_name:
            return jsonify(create_response(False, error="ens_name required")), 400

        client = get_client()

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            resolved_address = loop.run_until_complete(client.resolve_ens_name(ens_name))
        finally:
            loop.close()

        return jsonify(create_response(True, {
            "ens_name": ens_name,
            "resolved_address": resolved_address,
            "resolved": resolved_address is not None
        }))

    except Exception as e:
        logger.error(f"ENS resolution failed: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/gas-price', methods=['GET'])
def get_gas_price():
    """Get current gas price"""
    try:
        client = get_client()
        gas_price_wei = client.get_gas_price()
        
        # Only try to convert if client is properly initialized
        gas_price_gwei = 0
        if hasattr(client, 'w3') and client.w3:
            try:
                gas_price_gwei = float(client.w3.from_wei(gas_price_wei, 'gwei'))
            except:
                # Fallback calculation
                gas_price_gwei = gas_price_wei / 10**9

        return jsonify(create_response(True, {
            "gas_price_wei": gas_price_wei,
            "gas_price_gwei": gas_price_gwei,
            "recommended_gas_limit": 21000
        }))

    except Exception as e:
        logger.error(f"Gas price check failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/withdraw-config/<address>', methods=['GET'])
def get_withdraw_config(address: str):
    """Get withdrawal configuration for an address"""
    try:
        client = get_client()
        config = client.get_withdraw_config(address)

        return jsonify(create_response(True, {
            "address": address,
            "config": config,
            "withdrawals_enabled": not config.get('paused', True)
        }))

    except Exception as e:
        logger.error(f"Withdraw config failed for {address}: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/eip712-domain', methods=['GET'])
def get_eip712_domain():
    """Get EIP-712 domain information"""
    try:
        client = get_client()
        domain = client.get_eip712_domain()

        return jsonify(create_response(True, domain))

    except Exception as e:
        logger.error(f"EIP-712 domain failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/create-transaction', methods=['POST'])
def create_transaction():
    """Create an unsigned transaction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400

        from_address = data.get('from_address')
        to_address = data.get('to_address')
        amount_eth = data.get('amount_eth')

        if not all([from_address, to_address, amount_eth]):
            return jsonify(create_response(False, error="from_address, to_address, and amount_eth required")), 400

        client = get_client()

        # Resolve ENS if needed
        if to_address.endswith('.eth'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                resolved = loop.run_until_complete(client.resolve_ens_name(to_address))
                if resolved:
                    to_address = resolved
                else:
                    return jsonify(create_response(False, error=f"Could not resolve ENS: {to_address}")), 400
            finally:
                loop.close()

        transaction = client.create_transaction(from_address, to_address, float(amount_eth))

        # Add transaction cost estimate
        total_cost_wei = transaction['value'] + (transaction['gas'] * transaction['gasPrice'])
        
        # Only try to convert if client is properly initialized
        total_cost_eth = 0
        gas_cost_eth = 0
        if hasattr(client, 'w3') and client.w3:
            try:
                total_cost_eth = float(client.w3.from_wei(total_cost_wei, 'ether'))
                gas_cost_eth = float(client.w3.from_wei(transaction['gas'] * transaction['gasPrice'], 'ether'))
            except:
                # Fallback calculations
                total_cost_eth = total_cost_wei / 10**18
                gas_cost_eth = (transaction['gas'] * transaction['gasPrice']) / 10**18

        response_data = {
            "transaction": transaction,
            "cost_estimate": {
                "amount_eth": amount_eth,
                "gas_cost_eth": gas_cost_eth,
                "total_cost_eth": total_cost_eth
            },
            "ready_to_sign": True
        }

        return jsonify(create_response(True, response_data))

    except Exception as e:
        logger.error(f"Transaction creation failed: {e}")
        return jsonify(create_response(False, error=str(e))), 400

@app.route('/execute-withdrawal', methods=['POST'])
def execute_withdrawal():
    """Execute a complete withdrawal transaction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400

        from_address = data.get('from_address') or os.getenv('WALLET_ADDRESS')
        to_address = data.get('to_address')
        amount_eth = data.get('amount_eth')
        private_key = data.get('private_key')
        wait_for_confirmation = data.get('wait_for_confirmation', True)

        if not all([from_address, to_address, amount_eth, private_key]):
            return jsonify(create_response(False, error="from_address, to_address, amount_eth, and private_key required")), 400

        client = get_client()

        # Validate private key
        try:
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            account = Account.from_key(private_key)
            if account.address.lower() != from_address.lower():
                return jsonify(create_response(False, error="Private key doesn't match from_address")), 400
        except Exception as e:
            return jsonify(create_response(False, error=f"Invalid private key: {e}")), 400

        # Pre-flight checks
        balance = client.get_balance(from_address)
        if balance < float(amount_eth):
            return jsonify(create_response(False, error=f"Insufficient balance: {balance} < {amount_eth}")), 400

        # Resolve ENS if needed
        original_to = to_address
        if to_address.endswith('.eth'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                resolved = loop.run_until_complete(client.resolve_ens_name(to_address))
                if resolved:
                    to_address = resolved
                else:
                    return jsonify(create_response(False, error=f"Could not resolve ENS: {to_address}")), 400
            finally:
                loop.close()

        # Create and sign transaction
        transaction = client.create_transaction(from_address, to_address, float(amount_eth))

        # Sign transaction
        signed_txn = Account.sign_transaction(transaction, private_key)

        # Send transaction
        # Only try to send if client is properly initialized
        tx_hash_hex = ""
        if hasattr(client, 'w3') and client.w3:
            try:
                tx_hash = client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                tx_hash_hex = tx_hash.hex()
                logger.info(f"✅ Transaction sent: {tx_hash_hex}")
            except Exception as e:
                return jsonify(create_response(False, error=f"Failed to send transaction: {e}")), 400
        else:
            return jsonify(create_response(False, error="Ethereum client not properly initialized")), 400

        response_data = {
            "transaction_hash": tx_hash_hex,
            "from_address": from_address,
            "to_address": to_address,
            "original_to": original_to,
            "amount_eth": amount_eth,
            "nonce": transaction['nonce'],
            "gas_used": transaction['gas'],
            "gas_price_gwei": 0,  # Default value
            "status": "sent",
            "explorer_url": f"https://etherscan.io/tx/{tx_hash_hex}"
        }

        # Try to get gas price in gwei if client is properly initialized
        if hasattr(client, 'w3') and client.w3:
            try:
                response_data["gas_price_gwei"] = float(client.w3.from_wei(transaction['gasPrice'], 'gwei'))
            except:
                # Fallback calculation
                response_data["gas_price_gwei"] = transaction['gasPrice'] / 10**9

        # Wait for confirmation if requested
        if wait_for_confirmation:
            try:
                logger.info("⏳ Waiting for transaction confirmation...")
                if hasattr(client, 'w3') and client.w3:
                    receipt = client.w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=120)
                    response_data.update({
                        "status": "confirmed" if receipt['status'] == 1 else "failed",
                        "block_number": receipt['blockNumber'],
                        "actual_gas_used": receipt['gasUsed'],
                        "confirmation_time": datetime.now().isoformat()
                    })
                    logger.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
                else:
                    response_data["status"] = "sent_pending"
                    response_data["confirmation_error"] = "Ethereum client not properly initialized"
            except Exception as e:
                logger.warning(f"Confirmation timeout: {e}")
                response_data["status"] = "sent_pending"
                response_data["confirmation_error"] = str(e)

        return jsonify(create_response(True, response_data))

    except Exception as e:
        logger.error(f"Withdrawal execution failed: {e}")
        return jsonify(create_response(False, error=str(e))), 400

# Warehouse Integration Endpoints
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

@app.route('/warehouse/trigger-withdrawal', methods=['POST'])
def trigger_warehouse_withdrawal():
    """Trigger withdrawal from WarehouseClient to wallet"""
    try:
        if not warehouse_client:
            return jsonify(create_response(False, error="Warehouse client not initialized")), 500
        
        data = request.get_json()
        if not data:
            return jsonify(create_response(False, error="JSON body required")), 400
        
        address = data.get('address', warehouse_client.config["wallet_address"])
        private_key = data.get('private_key')
        
        if not private_key:
            return jsonify(create_response(False, error="private_key required")), 400
        
        # Validate private key format
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        # Check if there are funds available
        balances = warehouse_client.get_warehouse_balances(address)
        has_funds = any(balance > 0 for balance in balances.values())
        
        if not has_funds:
            return jsonify(create_response(False, error="No funds available in warehouse", data={
                "balances": balances
            })), 400
        
        # Execute complete withdrawal in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                warehouse_client.execute_complete_withdrawal(
                    address, private_key, True
                )
            )
        finally:
            loop.close()
        
        if result['status'] == 'complete_success':
            return jsonify(create_response(True, {
                "message": "Withdrawal successful! Tokens are now in your wallet.",
                "step1": result['step1_withdrawal'],
                "step2": result['step2_release'],
                "final_status": result['final_status'],
                "process_time": result['total_process_time']
            }))
        else:
            return jsonify(create_response(False, 
                error=f"Withdrawal failed: {result.get('error', result['status'])}",
                data=result
            )), 400
        
    except Exception as e:
        logger.error(f"Warehouse withdrawal trigger failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/complete-withdraw', methods=['POST'])
def execute_complete_warehouse_withdrawal():
    """Execute complete two-step withdrawal from Splits Warehouse to wallet"""
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
        
        # Execute complete withdrawal in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                warehouse_client.execute_complete_withdrawal(
                    address, private_key, auto_detect
                )
            )
        finally:
            loop.close()
        
        if result['status'] == 'complete_success':
            return jsonify(create_response(True, {
                "message": "Complete withdrawal successful! Tokens are now in your wallet.",
                "step1": result['step1_withdrawal'],
                "step2": result['step2_release'],
                "final_status": result['final_status'],
                "process_time": result['total_process_time']
            }))
        elif result['status'] == 'step1_failed':
            return jsonify(create_response(False, 
                error="Step 1 failed: Could not withdraw from source to warehouse",
                data=result
            )), 400
        elif result['status'] == 'step2_failed':
            return jsonify(create_response(False, 
                error="Step 2 failed: Tokens in warehouse but not released to wallet",
                data=result
            )), 400
        elif result['status'] == 'no_warehouse_funds':
            return jsonify(create_response(False, 
                error="No funds found in warehouse after step 1",
                data=result
            )), 400
        else:
            return jsonify(create_response(False, 
                error=result.get('error', 'Complete withdrawal failed'),
                data=result
            )), 400
        
    except Exception as e:
        logger.error(f"Complete warehouse withdrawal execution failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/withdraw', methods=['POST'])
def execute_warehouse_withdrawal():
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
        
        # Execute complete withdrawal in async context (2-step process by default)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Use complete withdrawal by default for better user experience
            use_complete_process = data.get('use_complete_process', True)
            
            if use_complete_process:
                result = loop.run_until_complete(
                    warehouse_client.execute_complete_withdrawal(
                        address, private_key, auto_detect
                    )
                )
            else:
                # Legacy single-step withdrawal
                result = loop.run_until_complete(
                    warehouse_client.execute_automatic_withdrawal(
                        address, private_key, auto_detect
                    )
                )
        finally:
            loop.close()
        
        # Handle different result types
        if use_complete_process:
            # Complete withdrawal process results
            if result['status'] == 'complete_success':
                return jsonify(create_response(True, {
                    "message": "Complete withdrawal successful! Tokens are now in your wallet.",
                    "step1": result['step1_withdrawal'],
                    "step2": result['step2_release'],
                    "final_status": result['final_status'],
                    "process_time": result['total_process_time'],
                    "process_type": "complete_two_step"
                }))
            elif result['status'] == 'step1_failed':
                return jsonify(create_response(False, 
                    error="Step 1 failed: Could not withdraw from source to WarehouseClient",
                    data=result
                )), 400
            elif result['status'] == 'step2_failed':
                return jsonify(create_response(False, 
                    error="Step 2 failed: Tokens in WarehouseClient but not released to wallet",
                    data=result
                )), 400
            else:
                return jsonify(create_response(False, 
                    error=result.get('error', 'Complete withdrawal failed'),
                    data=result
                )), 400
        else:
            # Legacy single-step withdrawal results
            if result['status'] == 'success':
                return jsonify(create_response(True, result))
            elif result['status'] == 'no_funds':
                return jsonify(create_response(False, error=result['message'], data=result)), 400
            else:
                return jsonify(create_response(False, error=result.get('error', 'Withdrawal failed'), data=result)), 400
        
    except Exception as e:
        logger.error(f"Warehouse withdrawal execution failed: {e}")
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/warehouse/create-transaction', methods=['POST'])
def create_warehouse_transaction():
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
        
        # Only try to convert if warehouse_client is properly initialized
        gas_cost_eth = 0
        if hasattr(warehouse_client, 'w3') and warehouse_client.w3:
            try:
                gas_cost_eth = float(warehouse_client.w3.from_wei(gas_cost_wei, 'ether'))
            except:
                # Fallback calculation
                gas_cost_eth = gas_cost_wei / 10**18
        else:
            # Fallback calculation
            gas_cost_eth = gas_cost_wei / 10**18
        
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
            "next_check_recommended": datetime.now().isoformat()
        }
        
        return jsonify(create_response(True, monitoring_result))
        
    except Exception as e:
        return jsonify(create_response(False, error=str(e))), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        client = get_client()
        # Check if client is properly initialized before checking connection
        connected = False
        if hasattr(client, 'w3') and client.w3:
            try:
                connected = client.w3.is_connected()
            except:
                connected = False

        return jsonify({
            "status": "healthy" if connected else "unhealthy",
            "connected": connected,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify(create_response(False, error="Endpoint not found")), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify(create_response(False, error="Internal server error")), 500

def run_server():
    """Run the Flask application"""
    print("🚀 Starting Ethereum Token Withdrawal Server with Warehouse Integration")
    print("=" * 70)

    # Initialize the Ethereum client
    if not init_client():
        print("❌ Failed to initialize Ethereum client")
        return

    print("✅ Ethereum client initialized")
    
    # Initialize the Warehouse client with better error handling
    warehouse_init = init_warehouse_client()
    if warehouse_init:
        print("✅ Warehouse client initialized")
        
        # Test warehouse connectivity
        try:
            if warehouse_client is not None:
                test_address = warehouse_client.config["wallet_address"]
                warehouse_status = warehouse_client.get_system_status()
                
                print(f"🏭 Warehouse System Check:")
                print(f"   Web3 Connected: {'✅' if warehouse_status['connection']['web3_connected'] else '❌'}")
                print(f"   Warehouse Ready: {'✅' if warehouse_status['nonce_status']['warehouse_ready'] else '❌'}")
                print(f"   Claimable Funds: {'✅' if warehouse_status['warehouse_status']['has_claimable_funds'] else '❌'}")
                
                if warehouse_status['warehouse_status']['has_claimable_funds']:
                    print(f"💰 Available balances:")
                    for token, balance in warehouse_status['warehouse_status']['balances'].items():
                        if balance > 0:
                            print(f"     {token}: {balance}")
                    
                    print(f"\n🤖 TIP: You can start automatic monitoring with:")
                    print(f"   python auto_withdrawal_monitor.py")
                    
        except Exception as e:
            print(f"⚠️ Warehouse connectivity test failed: {e}")
    else:
        print("⚠️ Warehouse client failed to initialize (will continue without warehouse features)")
        print("   Check your warehouse_config.json and ensure all dependencies are installed")

    # Get system status
    status = {}
    try:
        if ethereum_client is not None:
            status = ethereum_client.get_system_status()
            print(f"\n📊 Ethereum System Status:")
            print(f"   Connected: {'✅' if status['connected'] else '❌'}")
            print(f"   Chain ID: {status['chain_id']}")
            print(f"   Block: {status['current_block']}")
            
            # Enhanced Etherscan integration check
            etherscan_status = status.get('etherscan_integration', {})
            if etherscan_status:
                print(f"\n🔍 Etherscan Integration:")
                print(f"   API Key: {'✅ Configured' if etherscan_status.get('api_key_configured') else '❌ Missing'}")
                print(f"   Tracking Active: {'✅' if etherscan_status.get('tracking_active') else '❌'}")
                if status.get('connected'):
                    print(f"   Note: Full Etherscan features available")
                else:
                    print(f"   Note: Etherscan API key configured but Ethereum connection unavailable")
                    print(f"   To enable full features: Check network connectivity to Ethereum RPC endpoints")
            
            # Test nonce if connected
            if ethereum_client is not None and status.get('connected'):
                nonce = ethereum_client.get_nonce(status['wallet_address'])
                print(f"   Current Nonce: {nonce} ✅")
            elif ethereum_client is not None:
                print(f"   Current Nonce: ❌ Unavailable (Ethereum connection failed)")

    except Exception as e:
        print(f"⚠️ Status check failed: {e}")

    print("\n🌐 Server Endpoints:")
    print(f"   📍 Base URL: http://localhost:5000")
    print(f"   📖 Documentation: GET /")
    print(f"   💚 Health Check: GET /health")
    print(f"   📊 System Status: GET /status")
    print(f"   💰 Balance: GET /balance/<address>")
    print(f"   🔢 Nonce: GET /nonce/<address>")
    print(f"   ✅ Validate Nonce: POST /validate-nonce")
    print(f"   🌐 Resolve ENS: POST /resolve-ens")
    print(f"   📋 Create TX: POST /create-transaction")
    print(f"   🚀 Execute Withdrawal: POST /execute-withdrawal")
    
    if warehouse_init:
        print(f"\n🏭 Warehouse Endpoints:")
        print(f"   💚 Warehouse Health: GET /warehouse/health")
        print(f"   📊 Warehouse Status: GET /warehouse/status")
        print(f"   💰 Warehouse Balances: GET /warehouse/balances")
        print(f"   🔢 Validate Warehouse Nonce: POST /warehouse/validate-nonce")
        print(f"   📋 Pending Distributions: GET /warehouse/pending")
        print(f"   📋 Create Warehouse Transaction: POST /warehouse/create-transaction")
        print(f"   🚀 Execute Warehouse Withdrawal: POST /warehouse/withdraw")
        print(f"   🎆 Complete Withdrawal (2-Step): POST /warehouse/complete-withdraw")
        print(f"   📊 Monitor Warehouse: GET /warehouse/monitor")

    print(f"\n🎯 Service Status Summary:")
    ethereum_ready = ethereum_client is not None
    warehouse_ready = warehouse_client is not None
    ethereum_connected = status.get('connected', False) if status else False
    
    if ethereum_ready and warehouse_ready and ethereum_connected:
        print("✅ FULLY OPERATIONAL - Both Ethereum and Warehouse services are running!")
        print("✅ Ethereum API: Ready for basic operations")
        print("✅ Warehouse API: Ready for automatic token withdrawals")
        print("\n💡 NEXT STEPS:")
        print("   1. For full Etherscan integration, start: python auto_withdrawal_monitor.py")
        print("   2. Monitor pending tokens via: GET /warehouse/pending")
        print("   3. Check system health via: GET /warehouse/health")
    elif ethereum_ready and warehouse_ready:
        print("⚠️ PARTIALLY OPERATIONAL - Services initialized but Ethereum connection unavailable")
        print("✅ Etherscan API Key: Configured")
        print("✅ Warehouse API: Ready for automatic token withdrawals")
        print("❌ Ethereum Connection: Failed - Check network connectivity")
        print("\n💡 TROUBLESHOOTING:")
        print("   1. Verify RPC endpoints are accessible from your deployment environment")
        print("   2. Check firewall settings if deploying on restricted networks")
        print("   3. Consider using a dedicated Ethereum node service like Infura")
    elif ethereum_ready:
        print("⚠️ PARTIALLY OPERATIONAL - Ethereum service initialized but Warehouse unavailable")
        print("✅ Ethereum API: Ready")
        print("❌ Warehouse API: Not available")
    else:
        print("❌ SERVICE ISSUES - Please check configuration and dependencies")

    print("=" * 70)

    # Run the Flask server
    port = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Production server entry point for gunicorn
if __name__ == "__main__":
    run_server()
