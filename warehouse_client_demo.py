"""WarehouseClient Demo
Demonstrates the proper WarehouseClient naming and usage
"""

import asyncio
from warehouse_force_release import WarehouseClient

def main():
    """Demo showing WarehouseClient usage"""
    print("🏭 WarehouseClient Demo")
    print("=" * 30)
    
    try:
        # Initialize WarehouseClient (not just warehouse)
        warehouse_client = WarehouseClient()
        
        # Show the class name
        print(f"✅ Initialized: {warehouse_client.__class__.__name__}")
        print(f"📍 Target Address: {warehouse_client.config['wallet_address']}")
        print(f"🔗 ENS: {warehouse_client.config['ens_public_client']}")
        
        # Get status using WarehouseClient
        address = warehouse_client.config["wallet_address"]
        status = warehouse_client.get_release_status(address)
        
        print(f"\n📊 WarehouseClient Status:")
        print(f"   Wallet Balance: {status['wallet_balance_eth']} ETH")
        print(f"   Can Force Release: {'✅' if status['can_force_release'] else '❌'}")
        print(f"   Ready for Release: {'✅' if status['nonce_status']['ready_for_release'] else '❌'}")
        
        held_funds = status['held_funds']
        if held_funds.get('release_ready'):
            print(f"\n💰 Held Funds (via WarehouseClient):")
            for token_name, token_info in held_funds.get('token_balances', {}).items():
                if token_info.get('balance', 0) > 0:
                    print(f"   {token_name}: {token_info['balance']}")
        
        print(f"\n🎯 WarehouseClient is properly named and functional!")
        
    except Exception as e:
        print(f"❌ WarehouseClient demo failed: {e}")

if __name__ == "__main__":
    main()