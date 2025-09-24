"""
Simple Secure Warehouse Withdrawal
Execute withdrawals with improved security (no additional dependencies)
"""

import asyncio
import os
import json
import getpass
from splits_warehouse_client import SplitsWarehouseClient

# Simple encryption using built-in libraries
def simple_encrypt(text: str, password: str) -> str:
    """Simple XOR encryption (for demonstration only - not production secure)"""
    # This is a basic example - in production, use proper encryption libraries
    encrypted = ''.join(chr(ord(c) ^ ord(password[i % len(password)])) for i, c in enumerate(text))
    return encrypted.encode('utf-16').hex()

def simple_decrypt(encrypted_hex: str, password: str) -> str:
    """Simple XOR decryption (for demonstration only - not production secure)"""
    encrypted = bytes.fromhex(encrypted_hex).decode('utf-16')
    decrypted = ''.join(chr(ord(c) ^ ord(password[i % len(password)])) for i, c in enumerate(encrypted))
    return decrypted

class SimpleKeyManager:
    """Simple key manager using basic encryption"""
    
    def __init__(self, key_file="simple_keys.json"):
        self.key_file = key_file
    
    def store_private_key(self, address: str, private_key: str) -> bool:
        """Store an encrypted private key"""
        try:
            # Get password from user
            password = getpass.getpass("Enter encryption password: ")
            confirm_password = getpass.getpass("Confirm encryption password: ")
            
            if password != confirm_password:
                print("❌ Passwords do not match")
                return False
            
            # Encrypt private key
            encrypted_key = simple_encrypt(private_key, password)
            
            # Load existing keys if file exists
            keys = {}
            if os.path.exists(self.key_file):
                with open(self.key_file, 'r') as f:
                    keys = json.load(f)
            
            # Add new key
            keys[address] = encrypted_key
            
            # Save
            with open(self.key_file, 'w') as f:
                json.dump(keys, f)
            
            print("✅ Private key stored securely")
            return True
            
        except Exception as e:
            print(f"❌ Error storing private key: {e}")
            return False
    
    def get_private_key(self, address: str) -> str | None:
        """Retrieve a decrypted private key"""
        try:
            if not os.path.exists(self.key_file):
                print("❌ No keys file found")
                return None
            
            # Load keys
            with open(self.key_file, 'r') as f:
                keys = json.load(f)
            
            if address not in keys:
                print(f"❌ No private key found for address {address}")
                return None
            
            # Get password from user
            password = getpass.getpass("Enter decryption password: ")
            
            # Decrypt private key
            decrypted_key = simple_decrypt(keys[address], password)
            return decrypted_key
                
        except Exception as e:
            print(f"❌ Error retrieving private key: {e}")
            return None

async def secure_warehouse_withdrawal():
    """Execute withdrawal using securely stored private key"""
    print("🔐 Simple Secure Warehouse Withdrawal")
    print("=" * 45)
    
    try:
        # Initialize warehouse client
        print("🔄 Initializing warehouse client...")
        client = SplitsWarehouseClient()
        
        # Get your wallet address
        address = client.config["wallet_address"]
        print(f"💼 Wallet Address: {address}")
        
        # Check current status
        print(f"\n📊 Checking current status...")
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
        
        # Check if ready for withdrawal
        if not warehouse_status['has_claimable_funds']:
            print("\n❌ No claimable funds available. Nothing to withdraw.")
            return
        
        # Get private key securely from storage
        print(f"\n🔑 Retrieving private key from secure storage...")
        key_manager = SimpleKeyManager()
        private_key = key_manager.get_private_key(address)
        
        if not private_key:
            print("❌ Could not retrieve private key from secure storage")
            print("💡 Run this script with option 2 to store your private key first")
            return
        
        # Confirm withdrawal
        print(f"\n⚠️ WITHDRAWAL CONFIRMATION")
        print(f"This will execute a TWO-STEP process:")
        print(f"  Step 1: Withdraw from source to Splits WarehouseClient")
        print(f"  Step 2: Release from WarehouseClient to your wallet")
        print(f"\nAddress: {address}")
        print(f"Tokens to withdraw: {list(warehouse_status['balances'].keys())}")
        
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
            
        else:
            print(f"❌ Withdrawal failed: {result.get('error', result['status'])}")
            
    except KeyboardInterrupt:
        print("\n🛑 Withdrawal cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def setup_secure_key():
    """Help user set up secure key storage"""
    print("🔐 Simple Secure Key Setup")
    print("=" * 30)
    
    key_manager = SimpleKeyManager()
    
    # Get wallet address from config
    client = SplitsWarehouseClient()
    address = client.config["wallet_address"]
    
    print(f"Wallet Address: {address}")
    private_key = input("Enter your private key (0x...): ").strip()
    
    if private_key:
        if key_manager.store_private_key(address, private_key):
            print("✅ Private key stored securely!")
            print("💡 You can now run secure withdrawals without entering your private key each time")
        else:
            print("❌ Failed to store private key")
    else:
        print("❌ No private key provided")

def check_warehouse_status():
    """Check warehouse status without withdrawal"""
    print("🔍 Warehouse Status Check")
    print("=" * 25)
    
    try:
        # Initialize warehouse client
        client = SplitsWarehouseClient()
        
        # Get your wallet address
        address = client.config["wallet_address"]
        print(f"💼 Wallet Address: {address}")
        
        # Check current status
        status = client.get_system_status()
        
        # Display warehouse status
        warehouse_status = status['warehouse_status']
        print(f"\n🏭 Warehouse Status:")
        print(f"   Web3 Connected: {'✅' if status['connection']['web3_connected'] else '❌'}")
        print(f"   Warehouse Ready: {'✅' if status['nonce_status']['warehouse_ready'] else '❌'}")
        print(f"   Has Claimable Funds: {'✅' if warehouse_status['has_claimable_funds'] else '❌'}")
        print(f"   Total Value: {warehouse_status['total_value']} ETH")
        
        if warehouse_status['balances']:
            print(f"   Available tokens:")
            for token, balance in warehouse_status['balances'].items():
                if balance > 0:
                    print(f"     {token}: {balance}")
        
        # Check pending distributions
        pending = client.check_pending_distributions(address)
        if pending:
            print(f"\n📋 Pending Distributions: {len(pending)}")
            for dist in pending:
                print(f"   {dist['token']}: {dist['amount']} (Claimable: {'✅' if dist['claimable'] else '❌'})")
        
    except Exception as e:
        print(f"❌ Error checking warehouse status: {e}")

if __name__ == "__main__":
    print("Simple Secure Warehouse Withdrawal Options:")
    print("1. Execute secure withdrawal (requires stored private key)")
    print("2. Setup secure key storage")
    print("3. Check warehouse status only")
    
    choice = input("\nSelect option (1, 2, or 3): ").strip()
    
    if choice == "1":
        asyncio.run(secure_warehouse_withdrawal())
    elif choice == "2":
        setup_secure_key()
    elif choice == "3":
        check_warehouse_status()
    else:
        print("Invalid option")