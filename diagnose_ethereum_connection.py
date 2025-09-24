"""
Diagnostic script to check Ethereum RPC connection issues
"""

import json
import logging
import os
from web3 import Web3
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from file or environment variables"""
    config_file = "config.json"
    
    # Try to load from file first
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info("Configuration loaded from file")
        return config
    else:
        # Fallback to environment variables for production
        logger.info("Config file not found, using environment variables")
        config = {
            "chain_id": int(os.getenv("CHAIN_ID", "1")),
            "public_client_rpc": os.getenv("RPC_ENDPOINT", "https://ethereum-rpc.publicnode.com"),
            "wallet_address": os.getenv("WALLET_ADDRESS", ""),
            "api_key": os.getenv("ETHEREUM_API_KEY", ""),
            "etherscan_api_key": os.getenv("ETHERSCAN_API_KEY", ""),
        }
        return config

def test_rpc_endpoints(config):
    """Test multiple RPC endpoints to identify connection issues"""
    print("🔍 Testing Ethereum RPC Endpoints...")
    print("=" * 50)
    
    # List of RPC endpoints to test
    rpc_endpoints = [
        {"name": "PublicNode", "url": "https://ethereum-rpc.publicnode.com"},
        {"name": "Ankr", "url": "https://rpc.ankr.com/eth"},
        {"name": "drpc", "url": "https://eth.drpc.org"},
        {"name": "BlockPI", "url": "https://ethereum.blockpi.network/v1/rpc/public"},
        {"name": "Cloudflare", "url": "https://cloudflare-eth.com"},
        {"name": "Infura", "url": f"https://mainnet.infura.io/v3/{config.get('api_key', '')}"}
    ]
    
    results = []
    
    for endpoint in rpc_endpoints:
        try:
            print(f"\nTesting {endpoint['name']}: {endpoint['url']}")
            
            # Create Web3 instance
            w3 = Web3(Web3.HTTPProvider(endpoint['url'], request_kwargs={'timeout': 10}))
            
            # Test connection
            is_connected = w3.is_connected()
            print(f"  Connected: {'✅' if is_connected else '❌'}")
            
            if is_connected:
                # Test basic functionality
                chain_id = w3.eth.chain_id
                block_number = w3.eth.block_number
                print(f"  Chain ID: {chain_id}")
                print(f"  Current Block: {block_number}")
                
                # Test account functionality if wallet address is provided
                if config.get("wallet_address"):
                    try:
                        balance_wei = w3.eth.get_balance(config["wallet_address"])
                        balance_eth = float(w3.from_wei(balance_wei, 'ether'))
                        print(f"  Wallet Balance: {balance_eth} ETH")
                    except Exception as e:
                        print(f"  Wallet Balance: Error - {e}")
                
                results.append({
                    "name": endpoint['name'],
                    "url": endpoint['url'],
                    "status": "success",
                    "chain_id": chain_id,
                    "block_number": block_number
                })
            else:
                results.append({
                    "name": endpoint['name'],
                    "url": endpoint['url'],
                    "status": "failed",
                    "error": "Not connected"
                })
                
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "name": endpoint['name'],
                "url": endpoint['url'],
                "status": "failed",
                "error": str(e)
            })
    
    return results

def test_etherscan_api(config):
    """Test Etherscan API connectivity"""
    print("\n🔍 Testing Etherscan API...")
    print("=" * 50)
    
    etherscan_api_key = config.get("etherscan_api_key")
    if not etherscan_api_key:
        print("❌ Etherscan API key not found in configuration")
        return False
    
    try:
        # Test basic API connectivity
        url = "https://api.etherscan.io/api"
        params = {
            'module': 'account',
            'action': 'balance',
            'address': config.get("wallet_address", "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"),
            'tag': 'latest',
            'apikey': etherscan_api_key
        }
        
        print(f"Testing Etherscan API with key: {etherscan_api_key[:8]}...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                balance = int(data.get('result', 0))
                balance_eth = balance / 10**18
                print(f"✅ Etherscan API working correctly")
                print(f"  Wallet Balance: {balance_eth} ETH")
                return True
            else:
                print(f"❌ Etherscan API error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Etherscan API request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Etherscan API test failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Ethereum Connection Diagnostic Tool")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    print(f"Wallet Address: {config.get('wallet_address', 'Not set')}")
    print(f"Etherscan API Key: {'✅ Configured' if config.get('etherscan_api_key') else '❌ Not configured'}")
    
    # Test RPC endpoints
    rpc_results = test_rpc_endpoints(config)
    
    # Test Etherscan API
    etherscan_working = test_etherscan_api(config)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    working_endpoints = [r for r in rpc_results if r['status'] == 'success']
    if working_endpoints:
        print(f"✅ Working RPC Endpoints: {len(working_endpoints)}")
        for endpoint in working_endpoints:
            print(f"  - {endpoint['name']}: {endpoint['url']}")
    else:
        print("❌ No working RPC endpoints found")
    
    print(f"🔍 Etherscan API: {'✅ Working' if etherscan_working else '❌ Not working'}")
    
    if not working_endpoints:
        print("\n💡 RECOMMENDATIONS:")
        print("  1. Check your network connectivity")
        print("  2. Verify that your hosting environment allows outbound HTTPS connections")
        print("  3. Consider using a dedicated Ethereum node service like Infura")
        print("  4. Check if your IP address is rate-limited by public RPC providers")
    elif not etherscan_working:
        print("\n💡 Etherscan API Recommendations:")
        print("  1. Verify your Etherscan API key is correct")
        print("  2. Check if you've exceeded the daily request limit")
        print("  3. Ensure your server can make outbound HTTPS requests to api.etherscan.io")
    else:
        print("\n🎉 All systems are working correctly!")

if __name__ == "__main__":
    main()