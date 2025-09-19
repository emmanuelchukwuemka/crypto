"""
Test script to verify the Ethereum withdrawal system
"""

import asyncio
import sys
from withdrawal_handler import SecureWithdrawalHandler

async def test_system():
    """Test the system configuration and nonce validation"""
    
    print("🧪 Testing Ethereum Withdrawal System")
    print("=" * 40)
    
    try:
        # Initialize the handler
        handler = SecureWithdrawalHandler()
        print("✅ Handler initialized successfully")
        
        # Test system status
        status = handler.get_system_status()
        print(f"✅ System status retrieved: {len(status)} parameters")
        
        # Test nonce validation and communication
        is_ready = await handler.validate_nonce_and_communicate()
        
        if is_ready:
            print("\n🎉 SUCCESS: System is properly configured!")
            print("✅ Nonce is valid")
            print("✅ Network communication established")
            print("✅ Ready for token withdrawals")
            return True
        else:
            print("\n❌ FAILURE: System configuration issues detected")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)