"""
API-Based Withdrawal Using Deployed Server
Use the running server to execute withdrawals
"""

import requests
import json
import getpass

def execute_api_withdrawal():
    """Execute withdrawal via the deployed API server"""
    
    print("🌐 API-BASED WITHDRAWAL (Using Deployed Server)")
    print("=" * 50)
    print("Server URL: http://localhost:5000")
    print()
    
    try:
        # Check server health
        health_response = requests.get("http://localhost:5000/health")
        if health_response.status_code != 200:
            print("❌ Server is not running. Start it with: python start_server.py dev")
            return
        
        print("✅ Server is running and healthy")
        
        # Get system status
        status_response = requests.get("http://localhost:5000/status")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"📊 Current Balance: {status['data']['balance_eth']} ETH")
            print(f"🔢 Current Nonce: {status['data']['nonce']}")
            print()
        
        # Get withdrawal details
        to_address = input("📍 Enter recipient address: ").strip()
        if not to_address or not to_address.startswith('0x'):
            print("❌ Invalid address format")
            return
        
        amount_str = input("💰 Enter amount in ETH: ").strip()
        try:
            amount_eth = float(amount_str)
            if amount_eth <= 0:
                print("❌ Amount must be positive")
                return
        except ValueError:
            print("❌ Invalid amount format")
            return
        
        # Get private key
        print("\n🔑 Enter your private key:")
        private_key = getpass.getpass("Private key: ").strip()
        if not private_key:
            print("❌ Private key is required")
            return
        
        # Prepare withdrawal request
        withdrawal_data = {
            "to_address": to_address,
            "amount_eth": amount_eth,
            "private_key": private_key,
            "wait_for_confirmation": True
        }
        
        print(f"\n📋 WITHDRAWAL CONFIRMATION:")
        print(f"   To: {to_address}")
        print(f"   Amount: {amount_eth} ETH")
        print(f"   Via API: http://localhost:5000/execute-withdrawal")
        
        confirm = input("\n❓ Confirm API withdrawal? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Withdrawal cancelled")
            return
        
        # Execute withdrawal via API
        print("\n🚀 Executing withdrawal via deployed server...")
        
        response = requests.post(
            "http://localhost:5000/execute-withdrawal",
            json=withdrawal_data,
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                data = result['data']
                print(f"\n🎉 WITHDRAWAL SUCCESSFUL!")
                print(f"📋 Transaction Hash: {data['transaction_hash']}")
                print(f"🔍 Explorer: https://etherscan.io/tx/{data['transaction_hash']}")
                print(f"💰 Amount: {data['amount_eth']} ETH")
                print(f"📍 To: {data['to_address']}")
                print(f"🔢 Nonce: {data['nonce']}")
                print(f"📊 Status: {data['status']}")
            else:
                print(f"\n❌ Withdrawal failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running:")
        print("   python start_server.py dev")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    execute_api_withdrawal()