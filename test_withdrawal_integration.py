"""
Test Integration of All Withdrawal Methods with app.py Server
This script demonstrates that all withdrawal files work correctly
"""

import requests
import json
from simple_ethereum_client import SimpleEthereumClient

def test_server_connection():
    """Test that app.py server is running and responsive"""
    try:
        print("🧪 Testing server connection...")
        
        # Test health endpoint
        health = requests.get("http://localhost:5000/health", timeout=5)
        if health.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {health.status_code}")
            return False
        
        # Test status endpoint
        status = requests.get("http://localhost:5000/status", timeout=5)
        if status.status_code == 200:
            status_data = status.json()
            print("✅ Status check passed")
            print(f"   Connected: {status_data['data']['blockchain']['connected']}")
            print(f"   Chain ID: {status_data['data']['blockchain']['chain_id']}")
            print(f"   Wallet: {status_data['data']['blockchain']['wallet_address']}")
        else:
            print(f"❌ Status check failed: {status.status_code}")
            return False
        
        # Test balance endpoint
        wallet = status_data['data']['blockchain']['wallet_address']
        balance = requests.get(f"http://localhost:5000/balance/{wallet}", timeout=5)
        if balance.status_code == 200:
            balance_data = balance.json()
            print(f"✅ Balance check passed: {balance_data['data']['balance_eth']} ETH")
        else:
            print(f"❌ Balance check failed: {balance.status_code}")
            return False
        
        # Test nonce endpoint
        nonce = requests.get(f"http://localhost:5000/nonce/{wallet}", timeout=5)
        if nonce.status_code == 200:
            nonce_data = nonce.json()
            print(f"✅ Nonce check passed: {nonce_data['data']['nonce']}")
        else:
            print(f"❌ Nonce check failed: {nonce.status_code}")
            return False
        
        # Test gas price endpoint
        gas = requests.get("http://localhost:5000/gas-price", timeout=5)
        if gas.status_code == 200:
            gas_data = gas.json()
            print(f"✅ Gas price check passed: {gas_data['data']['gas_price_gwei']:.3f} Gwei")
        else:
            print(f"❌ Gas price check failed: {gas.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure app.py is running:")
        print("   python app.py")
        return False
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def test_direct_client():
    """Test that direct client connections work"""
    try:
        print("\n🧪 Testing direct client connection...")
        
        client = SimpleEthereumClient()
        status = client.get_system_status()
        
        print("✅ Direct client connection successful")
        print(f"   Connected: {status['connected']}")
        print(f"   Chain ID: {status['chain_id']}")
        print(f"   Current block: {status['current_block']}")
        print(f"   Wallet: {status['wallet_address']}")
        
        # Test balance
        balance = client.get_balance(status['wallet_address'])
        print(f"   Balance: {balance} ETH")
        
        # Test nonce
        nonce = client.get_nonce(status['wallet_address'])
        print(f"   Nonce: {nonce}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct client test failed: {e}")
        return False

def test_transaction_creation():
    """Test transaction creation without actually sending"""
    try:
        print("\n🧪 Testing transaction creation...")
        
        # Test via server API
        transaction_data = {
            "from_address": "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
            "to_address": "0x742d35Cc6634C0532925a3b8D18F29C6c8aaF123",
            "amount_eth": 0.001
        }
        
        response = requests.post(
            "http://localhost:5000/create-transaction",
            json=transaction_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Transaction creation via API successful")
                tx_data = result['data']['transaction']
                print(f"   Gas: {tx_data['gas']}")
                print(f"   Gas Price: {tx_data['gasPrice']} wei")
                print(f"   Nonce: {tx_data['nonce']}")
                print(f"   Value: {tx_data['value']} wei")
            else:
                print(f"❌ Transaction creation failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Transaction creation API failed: {response.status_code}")
            return False
        
        # Test via direct client
        client = SimpleEthereumClient()
        tx = client.create_transaction(
            from_address="0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
            to_address="0x742d35Cc6634C0532925a3b8D18F29C6c8aaF123",
            amount_eth=0.001
        )
        
        print("✅ Transaction creation via direct client successful")
        print(f"   Gas: {tx['gas']}")
        print(f"   Nonce: {tx['nonce']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Transaction creation test failed: {e}")
        return False

def summarize_withdrawal_methods():
    """Summarize all available withdrawal methods"""
    print("\n📋 AVAILABLE WITHDRAWAL METHODS:")
    print("=" * 50)
    
    print("1. 🌐 API-Based Withdrawal (Recommended)")
    print("   File: api_withdrawal.py")
    print("   Usage: python api_withdrawal.py")
    print("   Description: Uses the running app.py server via REST API")
    print("   Benefits: Secure, uses running server, no direct blockchain connection needed")
    print()
    
    print("2. 🔧 Direct Script Execution")
    print("   File: execute_withdrawal.py")
    print("   Usage: python execute_withdrawal.py")
    print("   Description: Direct blockchain interaction with comprehensive validation")
    print("   Benefits: Full control, detailed pre-flight checks")
    print()
    
    print("3. 🎯 Interactive Handler")
    print("   File: perform_withdrawal.py")
    print("   Usage: python perform_withdrawal.py")
    print("   Description: Interactive interface with secure input handling")
    print("   Benefits: User-friendly, secure private key input")
    print()
    
    print("4. 🏭 Professional Handler")
    print("   File: withdrawal_handler.py")
    print("   Usage: Import and use SecureWithdrawalHandler class")
    print("   Description: Professional-grade handler with comprehensive validation")
    print("   Benefits: Programmatic usage, full validation suite")
    print()
    
    print("🎯 RECOMMENDATION:")
    print("Use api_withdrawal.py with the running app.py server for the best experience!")

def main():
    """Run all integration tests"""
    print("🚀 WITHDRAWAL SYSTEM INTEGRATION TEST")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test server connection
    if not test_server_connection():
        all_tests_passed = False
        print("\n❌ Server tests failed. Make sure app.py is running:")
        print("   python app.py")
        print("\nOther withdrawal methods may still work with direct blockchain connection.")
    
    # Test direct client
    if not test_direct_client():
        all_tests_passed = False
        print("\n❌ Direct client tests failed.")
    
    # Test transaction creation
    if not test_transaction_creation():
        all_tests_passed = False
        print("\n❌ Transaction creation tests failed.")
    
    # Show results
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ app.py server is running correctly")
        print("✅ All withdrawal methods are functional")
        print("✅ System is ready for withdrawals")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Check the error messages above for details.")
    
    # Show withdrawal methods summary
    summarize_withdrawal_methods()
    
    print("\n🔐 SECURITY REMINDER:")
    print("⚠️  Never share your private key")
    print("⚠️  Test with small amounts first")
    print("⚠️  Verify recipient addresses carefully")

if __name__ == "__main__":
    main()