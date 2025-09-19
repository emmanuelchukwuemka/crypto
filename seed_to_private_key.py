"""
Seed Phrase to Private Key Converter
For recovering YOUR private key from YOUR seed phrase
"""

import getpass
from mnemonic import Mnemonic
from eth_account import Account

def seed_to_private_key():
    """Convert your seed phrase to private key"""
    
    print("🌱 SEED PHRASE TO PRIVATE KEY")
    print("=" * 40)
    print("This will derive your private key from your seed phrase")
    print("⚠️  Only use YOUR OWN seed phrase!")
    print()
    
    try:
        # Get seed phrase
        print("📝 Enter your seed phrase (12 or 24 words):")
        seed_phrase = input("Seed phrase: ").strip()
        
        if not seed_phrase:
            print("❌ Seed phrase is required")
            return None
        
        # Validate seed phrase
        mnemo = Mnemonic("english")
        if not mnemo.check(seed_phrase):
            print("❌ Invalid seed phrase")
            return None
        
        # Derive private key for first account (index 0)
        Account.enable_unaudited_hdwallet_features()
        account = Account.from_mnemonic(seed_phrase)
        
        private_key = account.key.hex()
        derived_address = account.address
        
        print(f"\n✅ Private key derived successfully!")
        print(f"🔑 Private Key: {private_key}")
        print(f"📍 Address: {derived_address}")
        
        # Check if this matches your expected address
        expected_address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"
        if derived_address.lower() == expected_address.lower():
            print(f"✅ Address matches your wallet!")
        else:
            print(f"⚠️  Address doesn't match. Expected: {expected_address}")
            print(f"   This might be a different derivation path.")
        
        return private_key
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def try_different_derivation_paths(seed_phrase):
    """Try different derivation paths to find your address"""
    
    print(f"\n🔍 Trying different derivation paths...")
    expected_address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"
    
    # Common derivation paths
    paths = [
        "m/44'/60'/0'/0/0",  # Standard Ethereum path
        "m/44'/60'/0'/0/1",  # Second account
        "m/44'/60'/0'/0/2",  # Third account
        "m/44'/60'/0'/1/0",  # Different change path
    ]
    
    mnemo = Mnemonic("english")
    
    for i, path in enumerate(paths):
        try:
            Account.enable_unaudited_hdwallet_features()
            account = Account.from_mnemonic(seed_phrase, account_path=path)
            
            if account.address.lower() == expected_address.lower():
                print(f"✅ FOUND! Path: {path}")
                print(f"🔑 Private Key: {account.key.hex()}")
                print(f"📍 Address: {account.address}")
                return account.key.hex()
            else:
                print(f"   Path {path}: {account.address}")
                
        except Exception as e:
            print(f"   Path {path}: Error - {e}")
    
    print(f"❌ Your address not found in common derivation paths")
    return None

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Convert seed phrase to private key")
    print("2. Try different derivation paths")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        private_key = seed_to_private_key()
        if private_key:
            print(f"\n🎯 You can now use this private key for your warehouse withdrawal!")
    elif choice == "2":
        seed_phrase = input("Enter your seed phrase: ").strip()
        if seed_phrase:
            private_key = try_different_derivation_paths(seed_phrase)
            if private_key:
                print(f"\n🎯 Found your private key! Use it for withdrawal.")
    else:
        print("❌ Invalid choice")