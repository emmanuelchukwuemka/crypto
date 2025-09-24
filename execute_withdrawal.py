"""
Manual Withdrawal Execution Script
Execute pending token withdrawals from Splits Warehouse
"""

import asyncio
import os
import sys
from splits_warehouse_client import SplitsWarehouseClient

async def main():
    print("🚀 Manual Withdrawal Execution")
    print("=" * 40)
    
    try:
        # Initialize warehouse client
        print("🔄 Initializing warehouse client...")
        client = SplitsWarehouseClient()
        
        # Your wallet address
        address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"
        
        # Check current status
        print(f"\n📊 Checking current status for {address[:10]}...")
        status = client.get_system_status()
        
        # Display warehouse status
        warehouse_status = status['warehouse_status']
        print(f"\n🏭 Warehouse Status:")
        print(f"   Has Claimable Funds: {'✅' if warehouse_status['has_claimable_funds'] else '❌'}")
        print(f"   Total Value: {warehouse_status['total_value']} ETH")
        
        if warehouse_status['balances']:
            print(f"   Available tokens:")
            for token, balance in warehouse_status['balances'].items():
                if balance > 0:
                    print(f"     {token}: {balance}")
        
        # Check nonce status
        nonce_status = status['nonce_status']
        print(f"\n🔢 Nonce Status:")
        print(f"   Warehouse Ready: {'✅' if nonce_status['warehouse_ready'] else '❌'}")
        print(f"   Current Nonce: {nonce_status['current_nonce']}")
        
        # Check if ready for withdrawal
        if not warehouse_status['has_claimable_funds']:
            print("\n❌ No claimable funds available. Nothing to withdraw.")
            return
        
        if not nonce_status['warehouse_ready']:
            print("\n❌ Warehouse not ready for communication. Please check network status.")
            return
        
        print("\n✅ Ready for withdrawal!")
        
        # Get private key securely
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            print("\n🔑 Private key required for withdrawal.")
            print("Options:")
            print("1. Set environment variable: set WALLET_PRIVATE_KEY=your_private_key")
            print("2. Enter it manually (less secure)")
            
            choice = input("\nChoose option (1 or 2): ").strip()
            
            if choice == "1":
                print("Please set the environment variable and run the script again.")
                print("Example: set WALLET_PRIVATE_KEY=0x1234567890abcdef...")
                return
            elif choice == "2":
                private_key = input("Enter your private key (0x...): ").strip()
                if not private_key:
                    print("❌ No private key provided. Exiting.")
                    return
            else:
                print("❌ Invalid choice. Exiting.")
                return
        
        # Confirm withdrawal
        print(f"\n⚠️ COMPLETE WITHDRAWAL CONFIRMATION")
        print(f"This will execute a TWO-STEP process:")
        print(f"  Step 1: Withdraw from source to Splits Warehouse")
        print(f"  Step 2: Release from Warehouse to your wallet")
        print(f"\nAddress: {address}")
        print(f"Tokens to withdraw: {list(warehouse_status['balances'].keys())}")
        print(f"\n⏱️ This process takes 2-5 minutes to complete both steps.")
        
        confirm = input("Do you want to proceed with withdrawal? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("❌ Withdrawal cancelled by user.")
            return
        
        # Execute complete two-step withdrawal
        print(f"\n🚀 Executing complete withdrawal process...")
        print(f"   Step 1: Withdraw from source to WarehouseClient")
        print(f"   Step 2: Release from WarehouseClient to your wallet")
        
        result = await client.execute_complete_withdrawal(
            address=address,
            private_key=private_key,
            auto_detect_amounts=True
        )
        
        # Display results
        print(f"\n📊 Withdrawal Results:")
        print(f"Status: {result['status']}")
        
        if result['status'] == 'complete_success':
            print(f"✅ Complete withdrawal successful!")
            print(f"\n🔄 Step 1 (Source → Warehouse):")
            step1 = result['step1_withdrawal']
            print(f"   Transaction Hash: {step1['transaction_hash']}")
            print(f"   ETH Withdrawn: {step1['withdrawn_eth']}")
            print(f"   Tokens Withdrawn: {step1['withdrawn_tokens']}")
            print(f"   Explorer: {step1['explorer_url']}")
            
            print(f"\n🔄 Step 2 (Warehouse → Your Wallet):")
            step2 = result['step2_release']
            print(f"   Transaction Hash: {step2['transaction_hash']}")
            print(f"   ETH Released: {step2['released_eth']}")
            print(f"   Tokens Released: {step2['released_tokens']}")
            print(f"   Explorer: {step2['explorer_url']}")
            
            print(f"\n🎉 {result['final_status']}")
            print(f"⏱️ Total Process Time: {result['total_process_time']}")
            
        elif result['status'] == 'step1_failed':
            print(f"❌ Step 1 failed: {result['message']}")
            print(f"   Error: {result['step1_result'].get('error', 'Unknown error')}")
            
        elif result['status'] == 'step2_failed':
            print(f"⚠️ Step 2 failed: Tokens are in warehouse but not released")
            step1 = result['step1_withdrawal']
            print(f"   Step 1 Success: {step1['transaction_hash']}")
            print(f"   Step 2 Error: {result['step2_release'].get('error', 'Unknown error')}")
            print(f"\n💡 Your tokens are in the warehouse. You can try manual release later.")
            
        elif result['status'] == 'no_warehouse_funds':
            print(f"❌ {result['message']}")
            print(f"   This might indicate a timing issue. Please wait and try again.")
            
        else:
            print(f"❌ Withdrawal failed: {result.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n🛑 Withdrawal cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("To set your private key securely:")
    print("set WALLET_PRIVATE_KEY=0x1234567890abcdef...")
    print()
    
    asyncio.run(main())