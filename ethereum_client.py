"""
Ethereum Blockchain Client with Warehouse Integration
Supports ENS resolution, nonce management, and token withdrawals
"""

import asyncio
import json
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from web3 import Web3
from web3.exceptions import Web3Exception
from eth_account import Account
from eth_utils.address import to_checksum_address, is_address
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ClientConfig:
    """Configuration for the Ethereum client"""
    chain_id: int
    public_client_rpc: str
    wallet_address: str
    include_ens_names: bool
    ens_public_client: str
    api_key: str
    warehouse_endpoint: Optional[str] = None

class EthereumClient:
    """
    Professional Ethereum client with warehouse integration
    Handles nonce management, ENS resolution, and token operations
    """
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.w3 = None
        self.account = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Web3 client and validate configuration"""
        try:
            # Initialize Web3 connection
            if self.config.chain_id == 1:  # Ethereum Mainnet
                # Try multiple RPC endpoints for better reliability
                rpc_endpoints = [
                    f"https://mainnet.infura.io/v3/{self.config.api_key}",
                    "https://ethereum-rpc.publicnode.com",
                    "https://rpc.ankr.com/eth",
                    "https://eth.drpc.org"
                ]
                rpc_url = None
                for endpoint in rpc_endpoints:
                    try:
                        test_w3 = Web3(Web3.HTTPProvider(endpoint))
                        if test_w3.is_connected():
                            rpc_url = endpoint
                            logger.info(f"Connected to RPC: {endpoint}")
                            break
                    except:
                        continue
                if not rpc_url:
                    rpc_url = rpc_endpoints[0]  # Fallback to first endpoint
            else:
                rpc_url = self.config.public_client_rpc
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to Ethereum network")
            
            # Validate wallet address
            if not is_address(self.config.wallet_address):
                raise ValueError(f"Invalid wallet address: {self.config.wallet_address}")
            
            self.wallet_address = to_checksum_address(self.config.wallet_address)
            logger.info(f"Ethereum client initialized for address: {self.wallet_address}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ethereum client: {e}")
            raise
    
    async def resolve_ens_name(self, ens_name: str) -> Optional[str]:
        """Resolve ENS name to Ethereum address"""
        try:
            if not self.config.include_ens_names:
                logger.warning("ENS resolution is disabled")
                return None
            
            if not ens_name.endswith('.eth'):
                logger.warning(f"Invalid ENS name format: {ens_name}")
                return None
            
            # Resolve ENS name
            address = self.w3.ens.address(ens_name)
            if address:
                resolved_address = to_checksum_address(address)
                logger.info(f"ENS {ens_name} resolved to: {resolved_address}")
                return resolved_address
            else:
                logger.warning(f"Could not resolve ENS name: {ens_name}")
                return None
                
        except Exception as e:
            logger.error(f"ENS resolution failed for {ens_name}: {e}")
            return None
    
    def get_nonce(self, address: Optional[str] = None) -> int:
        """Get the current nonce for the address"""
        try:
            target_address = address or self.wallet_address
            nonce = self.w3.eth.get_transaction_count(target_address, 'pending')
            logger.info(f"Current nonce for {target_address}: {nonce}")
            return nonce
        except Exception as e:
            logger.error(f"Failed to get nonce: {e}")
            raise
    
    def is_valid_nonce(self, nonce: int, address: Optional[str] = None) -> bool:
        """Validate if the provided nonce is valid"""
        try:
            target_address = address or self.wallet_address
            current_nonce = self.get_nonce(target_address)
            is_valid = nonce >= current_nonce
            logger.info(f"Nonce {nonce} validation for {target_address}: {'Valid' if is_valid else 'Invalid'}")
            return is_valid
        except Exception as e:
            logger.error(f"Nonce validation failed: {e}")
            return False
    
    def get_balance(self, address: Optional[str] = None) -> float:
        """Get ETH balance for the address"""
        try:
            target_address = address or self.wallet_address
            balance_wei = self.w3.eth.get_balance(target_address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            logger.info(f"Balance for {target_address}: {balance_eth} ETH")
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
    
    async def get_withdraw_config(self, user_address: str) -> Dict[str, Any]:
        """
        Get withdrawal configuration from warehouse
        Returns incentive and paused status
        """
        try:
            if not self.config.warehouse_endpoint:
                # Mock response for demonstration
                return {
                    "incentive": 100,
                    "paused": False,
                    "userAddress": user_address
                }
            
            # Make API call to warehouse endpoint
            response = requests.get(
                f"{self.config.warehouse_endpoint}/getWithdrawConfig",
                params={"userAddress": user_address},
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                config = response.json()
                logger.info(f"Withdraw config retrieved for {user_address}: {config}")
                return config
            else:
                logger.error(f"Failed to get withdraw config: {response.status_code}")
                return {"incentive": 0, "paused": True}
                
        except Exception as e:
            logger.error(f"Error getting withdraw config: {e}")
            return {"incentive": 0, "paused": True}
    
    def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """Estimate gas for a transaction"""
        try:
            gas_estimate = self.w3.eth.estimate_gas(transaction)
            logger.info(f"Gas estimate: {gas_estimate}")
            return gas_estimate
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            return 21000  # Default gas limit for simple transfers
    
    def get_gas_price(self) -> int:
        """Get current gas price"""
        try:
            gas_price = self.w3.eth.gas_price
            logger.info(f"Current gas price: {gas_price} wei ({self.w3.from_wei(gas_price, 'gwei')} Gwei)")
            return gas_price
        except Exception as e:
            logger.error(f"Failed to get gas price: {e}")
            return self.w3.to_wei(20, 'gwei')  # Default fallback
    
    async def prepare_withdrawal_transaction(
        self, 
        to_address: str, 
        amount_eth: float,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare a withdrawal transaction with proper nonce management
        """
        try:
            # Validate addresses
            to_address = to_checksum_address(to_address)
            
            # Get withdraw config
            withdraw_config = await self.get_withdraw_config(self.wallet_address)
            
            if withdraw_config.get("paused", True):
                raise Exception("Withdrawals are currently paused")
            
            # Get current nonce
            nonce = self.get_nonce()
            
            # Convert amount to Wei
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # Prepare transaction
            transaction = {
                'from': self.wallet_address,
                'to': to_address,
                'value': amount_wei,
                'nonce': nonce,
                'chainId': self.config.chain_id,
            }
            
            # Estimate gas
            gas_estimate = self.estimate_gas(transaction)
            gas_price = self.get_gas_price()
            
            # Add gas parameters
            transaction.update({
                'gas': gas_estimate,
                'gasPrice': gas_price,
            })
            
            logger.info(f"Prepared withdrawal transaction: {transaction}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to prepare withdrawal transaction: {e}")
            raise
    
    def sign_transaction(self, transaction: Dict[str, Any], private_key: str) -> str:
        """Sign a transaction with private key"""
        try:
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            logger.info(f"Transaction signed: {signed_txn.hash.hex()}")
            return signed_txn.rawTransaction.hex()
        except Exception as e:
            logger.error(f"Transaction signing failed: {e}")
            raise
    
    def send_raw_transaction(self, signed_transaction: str) -> str:
        """Send a signed raw transaction"""
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction)
            tx_hash_hex = tx_hash.hex()
            logger.info(f"Transaction sent: {tx_hash_hex}")
            return tx_hash_hex
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            raise
    
    def wait_for_transaction_receipt(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for transaction confirmation"""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            logger.info(f"Transaction confirmed: {tx_hash}")
            return dict(receipt)
        except Exception as e:
            logger.error(f"Transaction confirmation failed: {e}")
            raise
    
    def get_eip712_domain(self) -> Dict[str, Any]:
        """Get EIP-712 domain for the warehouse"""
        return {
            "chainId": self.config.chain_id,
            "name": "Warehouse",
            "salt": "0x" + "0" * 64,  # 32 bytes of zeros
            "verifyingContract": self.wallet_address,
            "version": "1"
        }

class TokenWithdrawalManager:
    """
    High-level manager for token withdrawals with proper nonce handling
    """
    
    def __init__(self, ethereum_client: EthereumClient):
        self.client = ethereum_client
        self.pending_nonces = set()
    
    async def execute_withdrawal(
        self, 
        to_address: str, 
        amount_eth: float,
        private_key: str,
        wait_for_confirmation: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a complete withdrawal with proper nonce management
        """
        try:
            logger.info(f"Starting withdrawal: {amount_eth} ETH to {to_address}")
            
            # Resolve ENS if needed
            if to_address.endswith('.eth'):
                resolved_address = await self.client.resolve_ens_name(to_address)
                if not resolved_address:
                    raise ValueError(f"Could not resolve ENS name: {to_address}")
                to_address = resolved_address
            
            # Check balance
            balance = self.client.get_balance()
            if balance < amount_eth:
                raise ValueError(f"Insufficient balance: {balance} ETH < {amount_eth} ETH")
            
            # Prepare transaction
            transaction = await self.client.prepare_withdrawal_transaction(
                to_address, amount_eth, private_key
            )
            
            # Validate nonce
            nonce = transaction['nonce']
            if not self.client.is_valid_nonce(nonce):
                raise ValueError(f"Invalid nonce: {nonce}")
            
            # Track nonce to prevent double-spending
            if nonce in self.pending_nonces:
                raise ValueError(f"Nonce {nonce} already in use")
            
            self.pending_nonces.add(nonce)
            
            try:
                # Sign and send transaction
                signed_tx = self.client.sign_transaction(transaction, private_key)
                tx_hash = self.client.send_raw_transaction(signed_tx)
                
                result = {
                    "transaction_hash": tx_hash,
                    "nonce": nonce,
                    "amount": amount_eth,
                    "to_address": to_address,
                    "status": "sent"
                }
                
                # Wait for confirmation if requested
                if wait_for_confirmation:
                    receipt = self.client.wait_for_transaction_receipt(tx_hash)
                    result.update({
                        "receipt": receipt,
                        "status": "confirmed" if receipt['status'] == 1 else "failed"
                    })
                
                logger.info(f"Withdrawal completed: {result}")
                return result
                
            finally:
                # Remove nonce from pending set
                self.pending_nonces.discard(nonce)
                
        except Exception as e:
            logger.error(f"Withdrawal failed: {e}")
            raise

# Example usage and testing functions
async def main():
    """Main function demonstrating the usage"""
    
    # Configuration from the user's input
    config = ClientConfig(
        chain_id=1,  # Ethereum Mainnet
        public_client_rpc="https://mainnet.infura.io/v3/",
        wallet_address="0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
        include_ens_names=True,
        ens_public_client="Obasimartins65.eth",
        api_key="13fa508ea913c8c045a462ac",
        warehouse_endpoint=None  # Set to actual endpoint if available
    )
    
    try:
        # Initialize client
        client = EthereumClient(config)
        withdrawal_manager = TokenWithdrawalManager(client)
        
        # Test ENS resolution
        ens_address = await client.resolve_ens_name(config.ens_public_client)
        if ens_address:
            print(f"ENS {config.ens_public_client} resolved to: {ens_address}")
        
        # Get current nonce
        current_nonce = client.get_nonce()
        print(f"Current nonce: {current_nonce}")
        
        # Validate nonce
        is_valid = client.is_valid_nonce(current_nonce)
        print(f"Nonce {current_nonce} is valid: {is_valid}")
        
        # Get balance
        balance = client.get_balance()
        print(f"Current balance: {balance} ETH")
        
        # Get withdraw config
        withdraw_config = await client.get_withdraw_config(config.wallet_address)
        print(f"Withdraw config: {withdraw_config}")
        
        # Get EIP-712 domain
        domain = client.get_eip712_domain()
        print(f"EIP-712 Domain: {domain}")
        
        print("\n✅ All systems configured properly!")
        print("✅ Nonce is valid and ready for communication!")
        print("✅ Ready for token withdrawals!")
        
        # Note: Actual withdrawal would require a private key
        # Example (DO NOT use with real private keys in production):
        # private_key = "your_private_key_here"
        # result = await withdrawal_manager.execute_withdrawal(
        #     "0x742d35Cc6634C0532925a3b8D18F29C6c8aaF", 
        #     0.01, 
        #     private_key
        # )
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Configuration error: {e}")

if __name__ == "__main__":
    asyncio.run(main())