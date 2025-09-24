from splits_warehouse_client import SplitsWarehouseClient

def test_warehouse():
    try:
        print("Initializing Warehouse client...")
        client = SplitsWarehouseClient()
        print("✅ Warehouse client initialized successfully")
        
        print("\nGetting system status...")
        status = client.get_system_status()
        
        print(f"Web3 connected: {status['connection']['web3_connected']}")
        print(f"Warehouse ready: {status['nonce_status']['warehouse_ready']}")
        print(f"Claimable funds: {status['warehouse_status']['has_claimable_funds']}")
        
        # Check balances for the configured address
        address = client.config["wallet_address"]
        print(f"\nChecking balances for address: {address}")
        balances = client.get_warehouse_balances(address)
        print(f"Balances: {balances}")
        
        if any(balance > 0 for balance in balances.values()):
            print("💰 Found claimable funds in warehouse!")
            for token, balance in balances.items():
                if balance > 0:
                    print(f"  {token}: {balance}")
        else:
            print("📭 No claimable funds in warehouse")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_warehouse()