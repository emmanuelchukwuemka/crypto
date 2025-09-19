"""
Splits Warehouse Auto-Withdrawal Demo
Demonstrates automatic token withdrawal from Splits warehouse using the API
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class SplitsWarehouseAPI:
    """Client for the Splits WarehouseClient API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_warehouse_status(self) -> Dict[str, Any]:
        """Get comprehensive warehouse status"""
        response = self.session.get(f"{self.base_url}/warehouseclient/status")
        return response.json()
    
    def get_warehouse_balances(self) -> Dict[str, Any]:
        """Get warehouse balances"""
        response = self.session.get(f"{self.base_url}/warehouseclient/balances")
        return response.json()
    
    def validate_nonce(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Validate nonce for warehouse communication"""
        payload = {}
        if address:
            payload['address'] = address
        
        response = self.session.post(f"{self.base_url}/warehouseclient/validate-nonce", json=payload)
        return response.json()
    
    def get_pending_distributions(self) -> Dict[str, Any]:
        """Get pending distributions"""
        response = self.session.get(f"{self.base_url}/warehouseclient/pending")
        return response.json()
    
    def execute_withdrawal(self, private_key: str, address: Optional[str] = None, auto_detect: bool = True) -> Dict[str, Any]:
        """Execute automatic withdrawal from warehouse"""
        payload = {
            'private_key': private_key, 
            'auto_detect_amounts': auto_detect
        }
        if address:
            payload['address'] = address
        
        response = self.session.post(f"{self.base_url}/warehouseclient/withdraw", json=payload)
        return response.json()
    
    def monitor_warehouse(self) -> Dict[str, Any]:
        """Monitor warehouse for withdrawal opportunities"""
        response = self.session.get(f"{self.base_url}/warehouseclient/monitor")
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check warehouse service health"""
        response = self.session.get(f"{self.base_url}/warehouseclient/health")
        return response.json()

def main():
    """Demonstrate Splits WarehouseClient auto-withdrawal"""
    print("🏭 Splits WarehouseClient Auto-Withdrawal Demo")
    print("=" * 50)
    
    api = SplitsWarehouseAPI()
    
    try:
        # Step 1: Health Check
        print("🔍 Step 1: Checking warehouse service health...")
        health = api.health_check()
        
        if not health.get('success'):
            print(f"❌ Warehouse service not healthy: {health.get('error')}")
            return
        
        health_data = health['data']
        print(f"✅ Service Online: Web3={'✅' if health_data['web3_connected'] else '❌'}")
        print(f"✅ Warehouse Ready: {'✅' if health_data['warehouse_ready'] else '❌'}")
        print(f"✅ Has Claimable Funds: {'✅' if health_data['has_claimable_funds'] else '❌'}")
        
        # Step 2: Get Warehouse Status  
        print(f"\n📊 Step 2: Getting warehouse status...")
        status = api.get_warehouse_status()
        
        if status.get('success'):
            status_data = status['data']
            connection = status_data['connection']
            address_info = status_data['address_info']
            warehouse_status = status_data['warehouse_status']
            nonce_status = status_data['nonce_status']
            
            print(f"🔗 Connection: Chain {connection['chain_id']}, Block {connection['current_block']}")
            print(f"👤 Address: {address_info['address']} ({address_info['ens_name']})")
            print(f"💰 Wallet Balance: {address_info['balance_eth']} ETH")
            print(f"🏭 Warehouse Funds: {warehouse_status['total_value']} ETH equivalent")
            print(f"🔢 Nonce: {nonce_status['current_nonce']} (Ready: {'✅' if nonce_status['warehouse_ready'] else '❌'})")
        
        # Step 3: Check Balances
        print(f"\n💰 Step 3: Checking warehouse balances...")
        balances = api.get_warehouse_balances()
        
        if balances.get('success'):
            balance_data = balances['data']
            print(f"📊 Total Value: {balance_data['total_value']} ETH")
            print(f"🪙 Claimable Tokens: {len(balance_data['claimable_tokens'])}")
            
            for token in balance_data['claimable_tokens']:
                amount = balance_data['balances'][token]
                print(f"   {token}: {amount}")
        
        # Step 4: Check Pending Distributions
        print(f"\n📋 Step 4: Checking pending distributions...")
        pending = api.get_pending_distributions()
        
        if pending.get('success'):
            pending_data = pending['data']
            print(f"📈 Pending Distributions: {pending_data['total_pending']}")
            print(f"✅ Claimable: {pending_data['claimable_count']}")
            
            for dist in pending_data['pending_distributions']:
                status_icon = '✅' if dist['claimable'] else '❌'
                print(f"   {status_icon} {dist['token']}: {dist['amount']}")
        
        # Step 5: Validate Nonce
        print(f"\n🔢 Step 5: Validating nonce for warehouse communication...")
        nonce_validation = api.validate_nonce()
        
        if nonce_validation.get('success'):
            nonce_data = nonce_validation['data']
            print(f"✅ Current Nonce: {nonce_data['current_nonce']}")
            print(f"✅ Pending Nonce: {nonce_data['pending_nonce']}")
            print(f"✅ Warehouse Ready: {'✅' if nonce_data['warehouse_ready'] else '❌'}")
            print(f"✅ Can Communicate: {'✅' if nonce_data['can_communicate'] else '❌'}")
        
        # Step 6: Monitor for Auto-Withdrawal Opportunities
        print(f"\n🔍 Step 6: Monitoring for auto-withdrawal opportunities...")
        monitor = api.monitor_warehouse()
        monitor_data = {}  # Initialize with default value
        
        if monitor.get('success'):
            monitor_data = monitor['data']
            should_withdraw = monitor_data['auto_withdraw_recommended']
            
            print(f"🎯 Auto-Withdrawal Recommended: {'✅ YES' if should_withdraw else '❌ NO'}")
            
            if should_withdraw:
                print(f"\n🚀 READY FOR AUTOMATIC WITHDRAWAL!")
                print(f"   • Claimable funds detected")
                print(f"   • Nonce is valid for communication")
                print(f"   • System is properly configured")
                
                # Step 7: Execute Withdrawal (Example - DO NOT USE WITH REAL PRIVATE KEYS)
                print(f"\n💡 To execute withdrawal, call:")
                print(f"   result = api.execute_withdrawal('YOUR_PRIVATE_KEY_HERE')")
                print(f"")
                print(f"⚠️  WARNING: Never share or hardcode private keys!")
                print(f"   Use environment variables or secure key management")
                
                # Example of what the withdrawal call would look like:
                print(f"\n📝 Example withdrawal call:")
                print(f"   POST /warehouse/withdraw")
                print(f"   {{")
                print(f"     \"private_key\": \"0x...\",")
                print(f"     \"auto_detect_amounts\": true")
                print(f"   }}")
                
            else:
                print(f"\n⚠️ Auto-withdrawal not recommended:")
                if not monitor_data.get('balances'):
                    print(f"   • No claimable balances found")
                if not monitor_data['nonce_status']['warehouse_ready']:
                    print(f"   • Nonce not ready for communication")
        
        print(f"\n🎉 Warehouse analysis complete!")
        print(f"📄 Summary:")
        print(f"   • Service Status: {'✅ Online' if health['success'] else '❌ Offline'}")
        print(f"   • Funds Available: {'✅ Yes' if health_data.get('has_claimable_funds') else '❌ No'}")
        print(f"   • Ready to Withdraw: {'✅ Yes' if monitor_data.get('auto_withdraw_recommended') else '❌ No'}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to warehouse API server")
        print("💡 Make sure the server is running: python splits_warehouse_server.py")
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demonstrate_withdrawal_with_private_key():
    """
    EXAMPLE FUNCTION - DO NOT USE WITH REAL PRIVATE KEYS
    This shows how to execute withdrawal when you have a private key
    """
    print("\n" + "="*50)
    print("🔐 WITHDRAWAL EXECUTION EXAMPLE")
    print("⚠️  THIS IS FOR DEMONSTRATION ONLY")
    print("="*50)
    
    api = SplitsWarehouseAPI()
    
    # NEVER DO THIS IN PRODUCTION - This is just an example
    example_private_key = "0x0000000000000000000000000000000000000000000000000000000000000000"
    
    print("📝 To execute a real withdrawal:")
    print("1. Securely obtain your private key")
    print("2. Call the withdrawal API:")
    print(f"   result = api.execute_withdrawal(private_key)")
    print("3. Check the result status")
    print("4. Monitor transaction on Etherscan")
    print("")
    print("⚠️  SECURITY REMINDERS:")
    print("• Never share your private key")
    print("• Use environment variables for keys")
    print("• Test with small amounts first")
    print("• Verify all addresses before withdrawal")
    
    # Uncomment the line below ONLY if you want to test with a real private key
    # result = api.execute_withdrawal(your_actual_private_key_here)

if __name__ == "__main__":
    main()
    
    # Uncomment to see withdrawal execution example
    # demonstrate_withdrawal_with_private_key()