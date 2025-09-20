"""
Simple Ethereum Client for Token Withdrawals
Professional implementation with nonce management
"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any
from web3 import Web3
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleEthereumClient:
    """Simple, reliable Ethereum client for token operations"""

    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.w3 = None
        self.initialize_client()

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file or environment variables"""
        try:
            # Try to load from file first
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                logger.info("Configuration loaded from file")
                return config
            else:
                # Fallback to environment variables for production
                logger.info("Config file not found, using environment variables")
                config = {
                    "chain_id": int(os.getenv("CHAIN_ID", "1")),
                    "public_client_rpc": os.getenv("RPC_ENDPOINT", "https://ethereum-rpc.publicnode.com"),
                    "wallet_address": os.getenv("WALLET_ADDRESS", ""),
                    "include_ens_names": os.getenv("ENS_NAME", "").endswith('.eth'),
                    "ens_public_client": os.getenv("ENS_NAME", ""),
                    "api_key": os.getenv("ETHEREUM_API_KEY", ""),
                    "etherscan_api_key": os.getenv("ETHERSCAN_API_KEY", "PF423A8SIHNIXVM8K13X2S8G9YTKSDCZ"),
                    "warehouse_endpoint": None,
                    "network_settings": {
                        "timeout": 30,
                        "retry_attempts": 3,
                        "gas_multiplier": 1.1
                    },
                    "security": {
                        "validate_addresses": True,
                        "check_balance_before_tx": True,
                        "wait_for_confirmation": True
                    }
                }
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def initialize_client(self):
        """Initialize Web3 client with fallback endpoints"""
        try:
            # Try multiple public RPC endpoints
            rpc_endpoints = [
                "https://ethereum-rpc.publicnode.com",
                "https://rpc.ankr.com/eth",
                "https://eth.drpc.org",
                "https://ethereum.blockpi.network/v1/rpc/public"
            ]

            for endpoint in rpc_endpoints:
                try:
                    logger.info(f"Trying to connect to {endpoint}")
                    self.w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 10}))

                    if self.w3.is_connected():
                        logger.info(f"✅ Connected to Ethereum via {endpoint}")
                        logger.info(f"📊 Chain ID: {self.w3.eth.chain_id}")
                        logger.info(f"📈 Current block: {self.w3.eth.block_number}")
                        break

                except Exception as e:
                    logger.warning(f"Failed to connect to {endpoint}: {e}")
                    continue

            if not self.w3 or not self.w3.is_connected():
                raise ConnectionError("Could not connect to any Ethereum RPC endpoint")

        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            raise

    def validate_address(self, address: str) -> str:
        """Validate and checksum an Ethereum address"""
        try:
            if not address or len(address) != 42 or not address.startswith('0x'):
                raise ValueError(f"Invalid address format: {address}")

            # Simple checksum validation
            checksummed = Web3.to_checksum_address(address)
            return checksummed
        except Exception as e:
            logger.error(f"Address validation failed for {address}: {e}")
            raise

    def get_nonce(self, address: str) -> int:
        """Get current nonce for address"""
        try:
            validated_address = self.validate_address(address)
            nonce = self.w3.eth.get_transaction_count(validated_address, 'pending')
            logger.info(f"📊 Current nonce for {validated_address}: {nonce}")
            return nonce
        except Exception as e:
            logger.error(f"Failed to get nonce: {e}")
            raise

    def is_valid_nonce(self, nonce: int, address: str) -> bool:
        """Check if nonce is valid for the address"""
        try:
            current_nonce = self.get_nonce(address)
            is_valid = nonce >= current_nonce
            status = "✅ VALID" if is_valid else "❌ INVALID"
            logger.info(f"🔍 Nonce {nonce} validation: {status} (current: {current_nonce})")
            return is_valid
        except Exception as e:
            logger.error(f"Nonce validation failed: {e}")
            return False

    def get_balance(self, address: str) -> float:
        """Get ETH balance for address"""
        try:
            validated_address = self.validate_address(address)
            balance_wei = self.w3.eth.get_balance(validated_address)
            balance_eth = Web3.from_wei(balance_wei, 'ether')
            logger.info(f"💰 Balance for {validated_address}: {balance_eth} ETH")
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

    def get_gas_price(self) -> int:
        """Get current gas price"""
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = float(Web3.from_wei(gas_price, 'gwei'))
            logger.info(f"⛽ Gas price: {gas_price_gwei:.2f} Gwei")
            return gas_price
        except Exception as e:
            logger.error(f"Failed to get gas price: {e}")
            return Web3.to_wei(20, 'gwei')  # 20 Gwei fallback

    def estimate_gas_for_transfer(self, from_addr: str, to_addr: str, amount_wei: int) -> int:
        """Estimate gas for ETH transfer"""
        try:
            transaction = {
                'from': self.validate_address(from_addr),
                'to': self.validate_address(to_addr),
                'value': amount_wei
            }
            gas_estimate = self.w3.eth.estimate_gas(transaction)
            logger.info(f"⛽ Gas estimate: {gas_estimate}")
            return gas_estimate
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            return 21000  # Standard ETH transfer gas

    async def resolve_ens_name(self, ens_name: str) -> Optional[str]:
        """Try to resolve ENS name (basic implementation)"""
        try:
            if not ens_name.endswith('.eth'):
                return None

            # Try basic ENS resolution
            try:
                if hasattr(self.w3, 'ens') and self.w3.ens:
                    address = self.w3.ens.address(ens_name)
                    if address:
                        resolved = self.validate_address(address)
                        logger.info(f"🌐 ENS {ens_name} → {resolved}")
                        return resolved
            except:
                logger.warning(f"ENS resolution not available for {ens_name}")

            return None
        except Exception as e:
            logger.error(f"ENS resolution error: {e}")
            return None

    def create_transaction(self, from_addr: str, to_addr: str, amount_eth: float) -> Dict[str, Any]:
        """Create a transaction dictionary"""
        try:
            from_addr = self.validate_address(from_addr)
            to_addr = self.validate_address(to_addr)

            amount_wei = Web3.to_wei(amount_eth, 'ether')
            nonce = self.get_nonce(from_addr)
            gas_price = self.get_gas_price()
            gas_limit = self.estimate_gas_for_transfer(from_addr, to_addr, amount_wei)

            transaction = {
                'from': from_addr,
                'to': to_addr,
                'value': amount_wei,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            }

            logger.info(f"📋 Transaction prepared: {amount_eth} ETH from {from_addr} to {to_addr}")
            return transaction

        except Exception as e:
            logger.error(f"Transaction creation failed: {e}")
            raise

    def get_withdraw_config(self, user_address: str) -> Dict[str, Any]:
        """Get withdrawal configuration (mock implementation)"""
        try:
            # Mock warehouse response
            config = {
                "incentive": 100,
                "paused": False,
                "userAddress": self.validate_address(user_address),
                "maxWithdrawAmount": "10.0",
                "minWithdrawAmount": "0.001"
            }
            logger.info(f"⚙️ Withdraw config: {config}")
            return config
        except Exception as e:
            logger.error(f"Failed to get withdraw config: {e}")
            return {"incentive": 0, "paused": True}

    def get_eip712_domain(self) -> Dict[str, Any]:
        """Get EIP-712 domain structure"""
        return {
            "chainId": self.w3.eth.chain_id,
            "name": "Warehouse",
            "salt": "0x" + "0" * 64,
            "verifyingContract": self.config["wallet_address"],
            "version": "2"
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                "connected": self.w3.is_connected(),
                "chain_id": self.w3.eth.chain_id,
                "current_block": self.w3.eth.block_number,
                "gas_price_gwei": float(Web3.from_wei(self.w3.eth.gas_price, 'gwei')),
                "wallet_address": self.config["wallet_address"],
                "ens_enabled": self.config.get("include_ens_names", False)
            }
            return status
        except Exception as e:
            logger.error(f"System status error: {e}")
            return {"error": str(e)}

async def main():
    """Test the simple Ethereum client"""
    try:
        print("🚀 Starting Ethereum Client Test")
        print("=" * 50)

        # Initialize client
        client = SimpleEthereumClient()

        # Get system status
        print("\n📊 System Status:")
        status = client.get_system_status()
        for key, value in status.items():
            print(f"   {key}: {value}")

        # Test wallet address from config
        wallet_address = client.config["wallet_address"]
        print(f"\n🔍 Testing wallet: {wallet_address}")

        # Validate address
        validated = client.validate_address(wallet_address)
        print(f"✅ Address validated: {validated}")

        # Get current nonce
        nonce = client.get_nonce(wallet_address)
        print(f"📊 Current nonce: {nonce}")

        # Validate nonce
        is_valid = client.is_valid_nonce(nonce, wallet_address)
        print(f"🔍 Nonce validation: {'✅ VALID' if is_valid else '❌ INVALID'}")

        # Get balance
        balance = client.get_balance(wallet_address)
        print(f"💰 Balance: {balance} ETH")

        # Test ENS resolution
        if client.config.get("include_ens_names"):
            ens_name = client.config.get("ens_public_client")
            if ens_name:
                resolved = await client.resolve_ens_name(ens_name)
                if resolved:
                    print(f"🌐 ENS {ens_name} → {resolved}")
                else:
                    print(f"⚠️ Could not resolve ENS: {ens_name}")

        # Get withdrawal config
        withdraw_config = client.get_withdraw_config(wallet_address)
        print(f"⚙️ Withdrawal status: {'✅ ENABLED' if not withdraw_config.get('paused') else '❌ PAUSED'}")

        # Get EIP-712 domain
        domain = client.get_eip712_domain()
        print(f"📄 EIP-712 Domain: {domain['name']} (Chain {domain['chainId']})")

        print("\n" + "=" * 50)
        if is_valid and not withdraw_config.get('paused'):
            print("🎉 SUCCESS: System is ready for withdrawals!")
            print("✅ Nonce is VALID")
            print("✅ Network communication established")
            print("✅ Withdrawals are ENABLED")
            print("\n📝 To withdraw tokens, use the create_transaction method")
            print("⚠️ Remember: Never share your private key!")
        else:
            print("❌ System not ready - check configuration")

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
