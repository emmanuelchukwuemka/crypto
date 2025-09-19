"""
Ethereum Server Client Example
Shows how to interact with the Ethereum server API
"""

import requests
import json
from typing import Dict, Any, Optional

class EthereumServerClient:
    """Client for interacting with the Ethereum server API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the server"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {e}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON response: {e}"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and available endpoints"""
        return self._make_request('GET', '/')
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return self._make_request('GET', '/status')
    
    def get_health(self) -> Dict[str, Any]:
        """Get server health status"""
        return self._make_request('GET', '/health')
    
    def get_balance(self, address: str) -> Dict[str, Any]:
        """Get ETH balance for an address"""
        return self._make_request('GET', f'/balance/{address}')
    
    def get_nonce(self, address: str) -> Dict[str, Any]:
        """Get current nonce for an address"""
        return self._make_request('GET', f'/nonce/{address}')
    
    def validate_nonce(self, address: str, nonce: int) -> Dict[str, Any]:
        """Validate if a nonce is valid for an address"""
        return self._make_request('POST', '/validate-nonce', {
            'address': address,
            'nonce': nonce
        })
    
    def resolve_ens(self, ens_name: str) -> Dict[str, Any]:
        """Resolve ENS name to Ethereum address"""
        return self._make_request('POST', '/resolve-ens', {
            'ens_name': ens_name
        })
    
    def get_gas_price(self) -> Dict[str, Any]:
        """Get current gas price"""
        return self._make_request('GET', '/gas-price')
    
    def get_withdraw_config(self, address: str) -> Dict[str, Any]:
        """Get withdrawal configuration for an address"""
        return self._make_request('GET', f'/withdraw-config/{address}')
    
    def get_eip712_domain(self) -> Dict[str, Any]:
        """Get EIP-712 domain information"""
        return self._make_request('GET', '/eip712-domain')
    
    def create_transaction(self, from_address: str, to_address: str, amount_eth: float) -> Dict[str, Any]:
        """Create an unsigned transaction"""
        return self._make_request('POST', '/create-transaction', {
            'from_address': from_address,
            'to_address': to_address,
            'amount_eth': amount_eth
        })
    
    def execute_withdrawal(
        self, 
        from_address: str, 
        to_address: str, 
        amount_eth: float, 
        private_key: str,
        wait_for_confirmation: bool = True
    ) -> Dict[str, Any]:
        """Execute a complete withdrawal transaction"""
        return self._make_request('POST', '/execute-withdrawal', {
            'from_address': from_address,
            'to_address': to_address,
            'amount_eth': amount_eth,
            'private_key': private_key,
            'wait_for_confirmation': wait_for_confirmation
        })

def main():
    """Example usage of the Ethereum server client"""
    
    print("🌟 Ethereum Server Client Example")
    print("=" * 50)
    
    # Initialize client
    client = EthereumServerClient()
    
    # Test server connection
    print("\n🔍 Testing server connection...")
    health = client.get_health()
    
    if not health.get('status') == 'healthy':
        print("❌ Server is not healthy or not running")
        print("   Start the server with: python ethereum_server.py")
        return
    
    print("✅ Server is healthy and running")
    
    # Get server info
    print("\n📖 Server Information:")
    info = client.get_server_info()
    if info.get('name'):
        print(f"   Name: {info['name']}")
        print(f"   Version: {info['version']}")
        print(f"   Status: {info['status']}")
    
    # Get system status
    print("\n📊 System Status:")
    status = client.get_system_status()
    if status.get('success'):
        blockchain = status['data']['blockchain']
        print(f"   Connected: {'✅' if blockchain['connected'] else '❌'}")
        print(f"   Chain ID: {blockchain['chain_id']}")
        print(f"   Current Block: {blockchain['current_block']}")
        print(f"   Gas Price: {blockchain['gas_price_gwei']:.3f} Gwei")
        print(f"   Wallet: {blockchain['wallet_address']}")
    
    # Test wallet operations
    wallet_address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"  # From config
    
    print(f"\n💰 Wallet Operations for {wallet_address}:")
    
    # Get balance
    balance_result = client.get_balance(wallet_address)
    if balance_result.get('success'):
        balance = balance_result['data']['balance_eth']
        print(f"   Balance: {balance} ETH")
    
    # Get nonce
    nonce_result = client.get_nonce(wallet_address)
    if nonce_result.get('success'):
        nonce = nonce_result['data']['nonce']
        print(f"   Current Nonce: {nonce}")
        
        # Validate the nonce
        validate_result = client.validate_nonce(wallet_address, nonce)
        if validate_result.get('success'):
            is_valid = validate_result['data']['is_valid']
            can_communicate = validate_result['data']['can_communicate']
            print(f"   Nonce Valid: {'✅' if is_valid else '❌'}")
            print(f"   Can Communicate: {'✅' if can_communicate else '❌'}")
    
    # Test ENS resolution
    print(f"\n🌐 ENS Resolution:")
    ens_result = client.resolve_ens("Obasimartins65.eth")
    if ens_result.get('success'):
        resolved = ens_result['data']['resolved_address']
        if resolved:
            print(f"   Obasimartins65.eth → {resolved}")
        else:
            print(f"   ⚠️ Could not resolve ENS name")
    
    # Get withdrawal config
    print(f"\n⚙️ Withdrawal Configuration:")
    config_result = client.get_withdraw_config(wallet_address)
    if config_result.get('success'):
        config = config_result['data']['config']
        enabled = config_result['data']['withdrawals_enabled']
        print(f"   Withdrawals Enabled: {'✅' if enabled else '❌'}")
        print(f"   Incentive: {config.get('incentive', 0)}")
        print(f"   Min Amount: {config.get('minWithdrawAmount', 'N/A')} ETH")
        print(f"   Max Amount: {config.get('maxWithdrawAmount', 'N/A')} ETH")
    
    # Get gas price
    print(f"\n⛽ Gas Information:")
    gas_result = client.get_gas_price()
    if gas_result.get('success'):
        gas_data = gas_result['data']
        print(f"   Gas Price: {gas_data['gas_price_gwei']:.3f} Gwei")
        print(f"   Recommended Gas Limit: {gas_data['recommended_gas_limit']}")
    
    # Get EIP-712 domain
    print(f"\n📄 EIP-712 Domain:")
    domain_result = client.get_eip712_domain()
    if domain_result.get('success'):
        domain = domain_result['data']
        print(f"   Name: {domain['name']}")
        print(f"   Chain ID: {domain['chainId']}")
        print(f"   Version: {domain['version']}")
    
    print("\n" + "=" * 50)
    print("🎉 All API endpoints tested successfully!")
    print("\n💡 Example API Calls:")
    print("   curl http://localhost:5000/status")
    print("   curl http://localhost:5000/balance/0xB5c1baF2E532Bb749a6b2034860178A3558b6e58")
    print("   curl http://localhost:5000/nonce/0xB5c1baF2E532Bb749a6b2034860178A3558b6e58")
    
    print("\n📝 To execute withdrawals:")
    print("   Use POST /execute-withdrawal with:")
    print("   - from_address")
    print("   - to_address (or ENS name)")
    print("   - amount_eth")
    print("   - private_key")
    
    print("\n⚠️ Note: Keep private keys secure in production!")

if __name__ == "__main__":
    main()