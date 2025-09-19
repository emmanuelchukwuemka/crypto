"""
Token Withdrawal Handler with Nonce Management
Professional implementation for secure blockchain transactions
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any
from ethereum_client import EthereumClient, TokenWithdrawalManager, ClientConfig
import logging

logger = logging.getLogger(__name__)

class SecureWithdrawalHandler:
    """
    Secure handler for token withdrawals with comprehensive validation
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.client = EthereumClient(self.config)
        self.withdrawal_manager = TokenWithdrawalManager(self.client)
    
    def load_config(self, config_path: str) -> ClientConfig:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            return ClientConfig(
                chain_id=config_data['chain_id'],
                public_client_rpc=config_data['public_client_rpc'],
                wallet_address=config_data['wallet_address'],
                include_ens_names=config_data['include_ens_names'],
                ens_public_client=config_data['ens_public_client'],
                api_key=config_data['api_key'],
                warehouse_endpoint=config_data.get('warehouse_endpoint')
            )
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    async def validate_nonce_and_communicate(self) -> bool:
        """
        Validate nonce and establish communication with the network
        Returns True if nonce is valid and can communicate
        """
        try:
            print("🔍 Validating nonce and network communication...")
            
            # Get current nonce
            current_nonce = self.client.get_nonce()
            print(f"📊 Current nonce: {current_nonce}")
            
            # Validate nonce
            is_valid = self.client.is_valid_nonce(current_nonce)
            print(f"✅ Nonce validation: {'VALID' if is_valid else 'INVALID'}")
            
            if not is_valid:
                print("❌ Nonce is invalid - cannot proceed with transactions")
                return False
            
            # Test network connectivity
            balance = self.client.get_balance()
            print(f"💰 Current balance: {balance} ETH")
            
            # Test ENS resolution if enabled
            if self.config.include_ens_names:
                ens_address = await self.client.resolve_ens_name(self.config.ens_public_client)
                if ens_address:
                    print(f"🌐 ENS {self.config.ens_public_client} → {ens_address}")
                else:
                    print(f"⚠️  Could not resolve ENS: {self.config.ens_public_client}")
            
            # Get withdrawal configuration
            withdraw_config = await self.client.get_withdraw_config(self.config.wallet_address)
            print(f"⚙️  Withdrawal config: {withdraw_config}")
            
            if withdraw_config.get('paused', True):
                print("⏸️  Withdrawals are currently paused")
                return False
            
            print("✅ Nonce is VALID and ready for communication!")
            print("✅ Network connection established!")
            print("✅ Ready to withdraw tokens!")
            
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            print(f"❌ Validation error: {e}")
            return False
    
    async def execute_secure_withdrawal(
        self, 
        to_address: str, 
        amount_eth: float,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Execute a secure withdrawal with all validations
        """
        try:
            print(f"\n🚀 Initiating withdrawal: {amount_eth} ETH → {to_address}")
            
            # Pre-withdrawal validation
            if not await self.validate_nonce_and_communicate():
                raise Exception("Pre-withdrawal validation failed")
            
            # Execute withdrawal
            result = await self.withdrawal_manager.execute_withdrawal(
                to_address=to_address,
                amount_eth=amount_eth,
                private_key=private_key,
                wait_for_confirmation=True
            )
            
            print(f"✅ Withdrawal successful!")
            print(f"📋 Transaction Hash: {result['transaction_hash']}")
            print(f"🔢 Nonce Used: {result['nonce']}")
            print(f"💰 Amount: {result['amount']} ETH")
            print(f"📍 To: {result['to_address']}")
            print(f"📊 Status: {result['status']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Withdrawal failed: {e}")
            print(f"❌ Withdrawal failed: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                "network_connected": self.client.w3.is_connected(),
                "chain_id": self.client.w3.eth.chain_id,
                "wallet_address": self.config.wallet_address,
                "ens_enabled": self.config.include_ens_names,
                "api_configured": bool(self.config.api_key),
                "current_block": self.client.w3.eth.block_number,
                "gas_price_gwei": float(self.client.w3.from_wei(self.client.w3.eth.gas_price, 'gwei'))
            }
            return status
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

async def main():
    """Main function for testing and demonstration"""
    
    try:
        # Initialize withdrawal handler
        handler = SecureWithdrawalHandler()
        
        print("🔧 Ethereum Withdrawal System Initialized")
        print("=" * 50)
        
        # Get system status
        status = handler.get_system_status()
        print("\n📊 System Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n" + "=" * 50)
        
        # Validate nonce and communication
        is_ready = await handler.validate_nonce_and_communicate()
        
        if is_ready:
            print("\n🎉 SYSTEM READY FOR WITHDRAWALS!")
            print("📝 To perform a withdrawal, call:")
            print("   await handler.execute_secure_withdrawal(")
            print("       to_address='0x...',")  
            print("       amount_eth=0.01,")
            print("       private_key='your_private_key'")
            print("   )")
            print("\n⚠️  WARNING: Never share your private key!")
        else:
            print("\n❌ SYSTEM NOT READY - Please check configuration")
        
        # Example withdrawal (commented out for security)
        """
        # UNCOMMENT AND PROVIDE REAL VALUES TO TEST WITHDRAWAL
        private_key = "YOUR_PRIVATE_KEY_HERE"  # Replace with actual private key
        to_address = "0x742d35Cc6634C0532925a3b8D18F29C6c8aaF"  # Replace with target address
        amount = 0.001  # Amount in ETH
        
        result = await handler.execute_secure_withdrawal(
            to_address=to_address,
            amount_eth=amount,
            private_key=private_key
        )
        """
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main execution failed: {e}")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())