"""
Monitor Splits Warehouse and Automatically Withdraw Funds
This script continuously monitors the Splits Warehouse for available funds
and automatically executes withdrawals when funds are detected.
"""

import asyncio
import os
import time
from datetime import datetime
from splits_warehouse_client import SplitsWarehouseClient

class WarehouseMonitor:
    """Monitor Splits Warehouse and execute automatic withdrawals"""
    
    def __init__(self, check_interval_minutes=5):
        self.client = SplitsWarehouseClient()
        self.address = self.client.config["wallet_address"]
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.last_withdrawal_time = None
        self.withdrawal_count = 0
        
    def check_warehouse(self):
        """Check warehouse for available funds"""
        try:
            print(f"\n🔍 Checking warehouse at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get warehouse balances
            balances = self.client.get_warehouse_balances(self.address)
            has_funds = any(balance > 0.0001 for balance in balances.values())  # Threshold to avoid dust
            
            if has_funds:
                print("💰 Found claimable funds in warehouse:")
                total_value = 0
                for token, balance in balances.items():
                    if balance > 0:
                        print(f"   {token}: {balance}")
                        total_value += balance
                print(f"   Total Value: {total_value} ETH equivalent")
                return True, balances
            else:
                print("📭 No significant funds in warehouse")
                return False, {}
                
        except Exception as e:
            print(f"❌ Error checking warehouse: {e}")
            return False, {}
    
    async def execute_withdrawal(self, balances):
        """Execute withdrawal from warehouse to wallet"""
        try:
            print("🚀 Executing withdrawal from WarehouseClient...")
            
            # Get private key
            private_key = os.getenv('WALLET_PRIVATE_KEY')
            if not private_key:
                print("❌ Private key not found in environment variables")
                print("💡 Set WALLET_PRIVATE_KEY environment variable to enable automatic withdrawals")
                return False
            
            # Execute complete two-step withdrawal
            result = await self.client.execute_complete_withdrawal(
                self.address,
                private_key,
                auto_detect_amounts=True
            )
            
            if result['status'] == 'complete_success':
                self.withdrawal_count += 1
                self.last_withdrawal_time = datetime.now()
                
                print("✅ Withdrawal successful!")
                print(f"   Transaction 1 (to warehouse): {result['step1_withdrawal']['transaction_hash']}")
                print(f"   Transaction 2 (to wallet): {result['step2_release']['transaction_hash']}")
                print(f"   ETH released: {result['step2_release']['released_eth']}")
                print(f"   Tokens released: {result['step2_release']['released_tokens']}")
                return True
            else:
                print(f"❌ Withdrawal failed: {result.get('error', result['status'])}")
                return False
                
        except Exception as e:
            print(f"❌ Error executing withdrawal: {e}")
            return False
    
    async def monitor(self):
        """Main monitoring loop"""
        print("🤖 Starting Warehouse Monitor")
        print(f"   Wallet Address: {self.address}")
        print(f"   Check Interval: {self.check_interval} seconds")
        print(f"   Auto Withdrawal: {'Enabled' if os.getenv('WALLET_PRIVATE_KEY') else 'Disabled (no private key)'}")
        print("\n" + "="*50)
        
        while True:
            try:
                # Check warehouse
                has_funds, balances = self.check_warehouse()
                
                if has_funds:
                    print("🎉 Funds detected! Initiating withdrawal process...")
                    
                    # Execute withdrawal
                    success = await self.execute_withdrawal(balances)
                    
                    if success:
                        print("✅ Withdrawal completed successfully")
                        # Wait longer after successful withdrawal
                        await asyncio.sleep(self.check_interval * 2)
                    else:
                        print("❌ Withdrawal failed, will retry in regular interval")
                        await asyncio.sleep(self.check_interval)
                else:
                    # No funds, wait for next check
                    await asyncio.sleep(self.check_interval)
                    
            except KeyboardInterrupt:
                print("\n🛑 Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(self.check_interval)

async def main():
    """Main function"""
    print("🏭 Splits Warehouse Monitor & Auto-Withdrawal")
    print("=" * 50)
    
    # Check if private key is available
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        print("⚠️  WARNING: No private key found in environment variables")
        print("   Automatic withdrawals will be disabled")
        print("   To enable automatic withdrawals, set:")
        print("   set WALLET_PRIVATE_KEY=your_private_key_here")
        print()
    
    # Initialize monitor
    monitor = WarehouseMonitor(check_interval_minutes=5)
    
    # Run monitoring
    await monitor.monitor()

if __name__ == "__main__":
    print("Splits Warehouse Monitor")
    print("Press Ctrl+C to stop")
    print()
    asyncio.run(main())