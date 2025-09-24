"""
Automatic Token Withdrawal Monitor
Continuously monitors for pending tokens and executes automatic withdrawals
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import signal
import sys
from etherscan_nonce_tracker import EtherscanNonceTracker
from splits_warehouse_client import SplitsWarehouseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auto_withdrawal.log')
    ]
)
logger = logging.getLogger(__name__)

class AutoWithdrawalMonitor:
    """Automatic monitoring and withdrawal system for Etherscan and Warehouse"""
    
    def __init__(self):
        self.running = False
        self.etherscan_tracker = None
        self.warehouse_client = None
        self.config = self.load_config()
        self.last_check = datetime.now()
        self.withdrawal_count = 0
        
        # Monitoring settings
        self.check_interval = self.config.get('monitor_interval_minutes', 5) * 60  # Convert to seconds
        self.auto_withdraw_enabled = self.config.get('auto_withdraw_enabled', True)
        self.min_threshold = self.config.get('min_withdraw_threshold', 0.001)
        
        logger.info("🤖 Auto Withdrawal Monitor initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from files"""
        try:
            # Load warehouse config
            if os.path.exists('warehouse_config.json'):
                with open('warehouse_config.json', 'r') as f:
                    warehouse_config = json.load(f)
                    config = warehouse_config.get('warehouse_config', {})
                    config.update(warehouse_config.get('monitoring', {}))
            else:
                config = {}
            
            # Load main config
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    main_config = json.load(f)
                    config.update(main_config)
            
            # Set defaults
            config.setdefault('wallet_address', '0xB5c1baF2E532Bb749a6b2034860178A3558b6e58')
            config.setdefault('monitor_interval_minutes', 5)
            config.setdefault('auto_withdraw_enabled', True)
            config.setdefault('min_withdraw_threshold', 0.001)
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {
                'wallet_address': '0xB5c1baF2E532Bb749a6b2034860178A3558b6e58',
                'monitor_interval_minutes': 5,
                'auto_withdraw_enabled': True,
                'min_withdraw_threshold': 0.001
            }
    
    def initialize_clients(self):
        """Initialize Etherscan and Warehouse clients"""
        try:
            # Initialize Etherscan tracker
            logger.info("🔄 Initializing Etherscan nonce tracker...")
            self.etherscan_tracker = EtherscanNonceTracker()
            logger.info("✅ Etherscan tracker initialized")
            
            # Initialize Warehouse client
            logger.info("🔄 Initializing Warehouse client...")
            self.warehouse_client = SplitsWarehouseClient()
            logger.info("✅ Warehouse client initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Client initialization failed: {e}")
            return False
    
    def check_etherscan_status(self) -> Dict[str, Any]:
        """Check Etherscan API status and nonce tracking"""
        try:
            if not self.etherscan_tracker:
                return {"status": "not_initialized", "ready": False}
            
            address = self.config['wallet_address']
            validation = self.etherscan_tracker.validate_nonce_tracking(address)
            
            status = {
                "status": "active",
                "ready": validation['can_communicate'],
                "nonce_consistent": validation['nonce_consistency'],
                "api_calls": validation['api_calls_tracked'],
                "last_check": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Etherscan status: {status['status']} | Ready: {status['ready']}")
            return status
            
        except Exception as e:
            logger.error(f"Etherscan status check failed: {e}")
            return {"status": "error", "ready": False, "error": str(e)}
    
    def check_warehouse_status(self) -> Dict[str, Any]:
        """Check warehouse status and pending withdrawals"""
        try:
            if not self.warehouse_client:
                return {"status": "not_initialized", "ready": False}
            
            address = self.config['wallet_address']
            
            # Get warehouse balances
            balances = self.warehouse_client.get_warehouse_balances(address)
            has_funds = any(balance > self.min_threshold for balance in balances.values())
            
            # Validate nonce
            nonce_validation = self.warehouse_client.validate_nonce_for_warehouse(address)
            
            # Check pending distributions
            pending = self.warehouse_client.check_pending_distributions(address)
            
            status = {
                "status": "active",
                "ready": nonce_validation['warehouse_ready'],
                "has_claimable_funds": has_funds,
                "balances": balances,
                "pending_distributions": len(pending),
                "total_value": sum(balances.values()),
                "last_check": datetime.now().isoformat()
            }
            
            logger.info(f"🏭 Warehouse status: {status['status']} | Ready: {status['ready']} | Funds: {status['has_claimable_funds']}")
            return status
            
        except Exception as e:
            logger.error(f"Warehouse status check failed: {e}")
            return {"status": "error", "ready": False, "error": str(e)}
    
    async def execute_automatic_withdrawal(self) -> Optional[Dict[str, Any]]:
        """Execute complete automatic two-step withdrawal if conditions are met"""
        try:
            if not self.auto_withdraw_enabled:
                logger.info("⏸️ Auto withdrawal disabled in config")
                return None
            
            # Check if we have the private key (for security, we'd get this from environment)
            private_key = os.getenv('WALLET_PRIVATE_KEY')
            if not private_key:
                logger.warning("🔑 Private key not found in environment - manual withdrawal required")
                return None
            
            address = self.config['wallet_address']
            
            # Check if warehouse client is available
            if not self.warehouse_client:
                logger.error("❌ WarehouseClient not initialized")
                return None
            
            # Execute complete warehouse withdrawal (2-step process)
            logger.info("🚀 Executing complete two-step withdrawal process...")
            result = await self.warehouse_client.execute_complete_withdrawal(
                address, 
                private_key, 
                auto_detect_amounts=True
            )
            
            if result['status'] == 'complete_success':
                self.withdrawal_count += 1
                logger.info(f"🎉 Complete automatic withdrawal #{self.withdrawal_count} successful!")
                logger.info(f"   Step 1 TX: {result['step1_withdrawal']['transaction_hash']}")
                logger.info(f"   Step 2 TX: {result['step2_release']['transaction_hash']}")
                logger.info(f"   ETH to Wallet: {result['step2_release']['released_eth']}")
                logger.info(f"   Tokens to Wallet: {result['step2_release']['released_tokens']}")
                logger.info(f"   🎯 Tokens are now in your wallet!")
                
                return result
            elif result['status'] == 'step1_failed':
                logger.warning(f"⚠️ Step 1 (source->WarehouseClient) failed: {result.get('message', 'Unknown error')}")
                return result
            elif result['status'] == 'step2_failed':
                logger.warning(f"⚠️ Step 2 (WarehouseClient->wallet) failed: Tokens in WarehouseClient")
                logger.warning(f"   Step 1 Success: {result['step1_withdrawal']['transaction_hash']}")
                logger.warning(f"   Step 2 Error: {result['step2_release'].get('error', 'Unknown')}")
                logger.warning(f"   💡 Tokens are in WarehouseClient - will retry next cycle")
                return result
            else:
                logger.warning(f"⚠️ Withdrawal failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Complete automatic withdrawal execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def monitoring_cycle(self):
        """Single monitoring cycle"""
        try:
            logger.info("🔍 Starting monitoring cycle...")
            
            # Check Etherscan status
            etherscan_status = self.check_etherscan_status()
            
            # Check Warehouse status
            warehouse_status = self.check_warehouse_status()
            
            # Log summary
            logger.info(f"📊 Monitor Summary:")
            logger.info(f"   Etherscan Ready: {'✅' if etherscan_status['ready'] else '❌'}")
            logger.info(f"   Warehouse Ready: {'✅' if warehouse_status['ready'] else '❌'}")
            logger.info(f"   Claimable Funds: {'✅' if warehouse_status.get('has_claimable_funds') else '❌'}")
            
            # Execute withdrawal if conditions are met
            withdrawal_result = None
            if (warehouse_status['ready'] and 
                warehouse_status.get('has_claimable_funds', False) and
                etherscan_status['ready']):
                
                logger.info("🚀 Conditions met for automatic withdrawal!")
                withdrawal_result = await self.execute_automatic_withdrawal()
            
            # Update last check time
            self.last_check = datetime.now()
            
            return {
                "etherscan_status": etherscan_status,
                "warehouse_status": warehouse_status,
                "withdrawal_result": withdrawal_result,
                "check_time": self.last_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Monitoring cycle failed: {e}")
            return {"error": str(e), "check_time": datetime.now().isoformat()}
    
    async def start_monitoring(self):
        """Start the continuous monitoring loop"""
        logger.info("🚀 Starting Automatic Withdrawal Monitor")
        logger.info("=" * 60)
        
        # Initialize clients
        if not self.initialize_clients():
            logger.error("❌ Failed to initialize clients - exiting")
            return
        
        # Set running flag
        self.running = True
        
        logger.info(f"⚙️ Configuration:")
        logger.info(f"   Wallet: {self.config['wallet_address']}")
        logger.info(f"   Check Interval: {self.check_interval // 60} minutes")
        logger.info(f"   Auto Withdraw: {'✅ Enabled' if self.auto_withdraw_enabled else '❌ Disabled'}")
        logger.info(f"   Min Threshold: {self.min_threshold} ETH")
        
        logger.info(f"\n🔄 Starting monitoring loop...")
        
        try:
            while self.running:
                # Run monitoring cycle
                result = await self.monitoring_cycle()
                
                if 'error' not in result:
                    logger.info(f"✅ Monitoring cycle completed")
                else:
                    logger.error(f"❌ Monitoring cycle failed: {result['error']}")
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {self.check_interval // 60} minutes until next check...")
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Monitoring loop failed: {e}")
        finally:
            self.running = False
            logger.info("🔚 Monitoring stopped")
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        logger.info("🛑 Stopping monitoring...")
        self.running = False
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        etherscan_status = self.check_etherscan_status() if self.etherscan_tracker else {"status": "not_initialized"}
        warehouse_status = self.check_warehouse_status() if self.warehouse_client else {"status": "not_initialized"}
        
        return {
            "monitor_status": {
                "running": self.running,
                "last_check": self.last_check.isoformat(),
                "withdrawal_count": self.withdrawal_count,
                "next_check": (self.last_check + timedelta(seconds=self.check_interval)).isoformat()
            },
            "etherscan_status": etherscan_status,
            "warehouse_status": warehouse_status,
            "configuration": {
                "wallet_address": self.config['wallet_address'],
                "check_interval_minutes": self.check_interval // 60,
                "auto_withdraw_enabled": self.auto_withdraw_enabled,
                "min_threshold": self.min_threshold
            }
        }

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("🔔 Received shutdown signal")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start monitor
    monitor = AutoWithdrawalMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 Monitor stopped by user")
    except Exception as e:
        logger.error(f"❌ Monitor failed: {e}")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    print("🤖 Automatic Token Withdrawal Monitor")
    print("=====================================")
    print("This service monitors for pending tokens and executes automatic withdrawals")
    print("Press Ctrl+C to stop")
    print()
    
    asyncio.run(main())