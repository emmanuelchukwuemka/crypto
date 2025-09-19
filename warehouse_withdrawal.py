"""
WarehouseClient Withdrawal Script
Execute automatic withdrawal from Splits Warehouse
"""

import asyncio
import getpass
from splits_warehouse_client import SplitsWarehouseClient

async def execute_warehouse_withdrawal():
    """Execute withdrawal from warehouse with WarehouseClient"""
    
    try:
        print("🏭 WAREHOUSECLIENT - SPLITS WAREHOUSE WITHDRAWAL")
        print("=" * 50)
        
        # Initialize WarehouseClient
        client = SplitsWarehouseClient()
        
        # Show current status
        status = client.get_system_status()
        warehouse = status['warehouse_status']
        
        print(f"💰 Claimable Funds in Warehouse:")
        for token, balance in warehouse['balances'].items():
            if balance > 0:
                print(f"   {token}: {balance}")
        
        print(f"\n🔢 Nonce Status: {status['nonce_status']['warehouse_ready']}")
        print(f"📍 Address: {status['address_info']['address']}")
        
        if not warehouse['has_claimable_funds']:
            print("❌ No claimable funds in warehouse")
            return
        
        if not status['nonce_status']['warehouse_ready']:
            print("❌ Nonce not ready for warehouse communication")
            return
        
        # Get private key
        print(f"\n🔑 Enter your private key to withdraw from warehouse:")
        print("⚠️  This will be hidden for security")
        private_key = getpass.getpass("Private key: ").strip()
        
        if not private_key:
            print("❌ Private key is required")
            return
        
        # Confirm withdrawal
        print(f"\n📋 WAREHOUSE WITHDRAWAL CONFIRMATION:")
        print(f"   Using WarehouseClient for Splits Protocol")
        print(f"   Address: {status['address_info']['address']}")
        print(f"   Available Tokens:")
        for token, balance in warehouse['balances'].items():
            if balance > 0:
                print(f"     - {token}: {balance}")
        
        confirm = input(f"\n❓ Confirm WarehouseClient withdrawal? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Warehouse withdrawal cancelled")
            return
        
        # Execute warehouse withdrawal
        print(f"\n🚀 Executing WarehouseClient withdrawal from Splits Warehouse...")
        
        result = await client.execute_automatic_withdrawal(
            address=status['address_info']['address'],
            private_key=private_key,
            auto_detect_amounts=True
        )
        
        if result['status'] == 'success':
            print(f"\n🎉 WAREHOUSE WITHDRAWAL COMPLETED!")
            print(f"📋 Transaction Hash: {result['transaction_hash']}")
            print(f"🔍 View on Etherscan: {result['explorer_url']}")
            print(f"💰 Withdrawn ETH: {result['withdrawn_eth']}")
            print(f"🎯 Withdrawn Tokens: {result['withdrawn_tokens']}")
            print(f"⛽ Gas Used: {result['gas_used']}")
        elif result['status'] == 'no_funds':
            print(f"\n📊 {result['message']}")
            print(f"💰 Current balances: {result['balances']}")
        else:
            print(f"\n❌ Warehouse withdrawal failed: {result.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n❌ Warehouse withdrawal cancelled by user")
    except Exception as e:
        print(f"\n❌ WarehouseClient withdrawal failed: {e}")

if __name__ == "__main__":
    asyncio.run(execute_warehouse_withdrawal())