"""
Interactive Withdrawal Script
Securely perform ETH withdrawals
"""

import asyncio
import getpass
from withdrawal_handler import SecureWithdrawalHandler

async def interactive_withdrawal():
    """Interactive withdrawal with secure input"""
    
    try:
        # Initialize handler
        handler = SecureWithdrawalHandler()
        
        print("🔐 SECURE WITHDRAWAL INTERFACE")
        print("=" * 40)
        
        # Get system status first
        status = handler.get_system_status()
        balance = handler.client.get_balance()
        
        print(f"💰 Available balance: {balance} ETH")
        print(f"🔗 Network: Chain ID {status['chain_id']}")
        print(f"📍 From: {status['wallet_address']}")
        print()
        
        # Get withdrawal details
        to_address = input("📍 Enter recipient address: ").strip()
        if not to_address.startswith('0x') or len(to_address) != 42:
            print("❌ Invalid address format")
            return
        
        # Get amount
        try:
            amount_str = input("💰 Enter amount in ETH: ").strip()
            amount_eth = float(amount_str)
            
            if amount_eth <= 0:
                print("❌ Amount must be positive")
                return
            
            if amount_eth > float(balance):
                print(f"❌ Insufficient balance. Available: {balance} ETH")
                return
                
        except ValueError:
            print("❌ Invalid amount format")
            return
        
        # Get private key securely
        print("\n🔑 Enter your private key:")
        print("⚠️  This will be hidden for security")
        private_key = getpass.getpass("Private key: ").strip()
        
        if not private_key:
            print("❌ Private key is required")
            return
        
        # Confirm withdrawal
        print(f"\n📋 WITHDRAWAL CONFIRMATION:")
        print(f"   From: {status['wallet_address']}")
        print(f"   To: {to_address}")
        print(f"   Amount: {amount_eth} ETH")
        print(f"   Available: {balance} ETH")
        
        confirm = input("\n❓ Confirm withdrawal? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Withdrawal cancelled")
            return
        
        # Execute withdrawal
        print("\n🚀 Executing withdrawal...")
        result = await handler.execute_secure_withdrawal(
            to_address=to_address,
            amount_eth=amount_eth,
            private_key=private_key
        )
        
        print("\n🎉 WITHDRAWAL COMPLETED!")
        print(f"📋 Transaction Hash: {result['transaction_hash']}")
        print(f"🔍 View on Etherscan: https://etherscan.io/tx/{result['transaction_hash']}")
        
    except KeyboardInterrupt:
        print("\n❌ Withdrawal cancelled by user")
    except Exception as e:
        print(f"\n❌ Withdrawal failed: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_withdrawal())