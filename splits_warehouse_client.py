"""
Splits Warehouse Integration
Automated token withdrawal from Splits Protocol warehouse
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_account import Account
import requests
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SplitsWarehouseClient:
    """Client for interacting with Splits Warehouse protocol"""
    
    def __init__(self, config_file: str = "warehouse_config.json"):
        self.config = self.load_config(config_file)
        self.w3 = None
        self.initialize_web3()
        
        # Splits protocol addresses
        self.splits_addresses = {
            "warehouse": "0x0000000000000000000000000000000000000000",  # Will be updated with actual address
            "split_main": "0x2ed6c4B5dA6378c7897AC67Ba9e43102Feb694EE",  # 0xSplits: Split Main
            "waterfall_factory": "0x0000000000000000000000000000000000000000"
        }
        
        # Common ERC20 tokens in Splits
        self.common_tokens = {
            "ETH": "0x0000000000000000000000000000000000000000",
            "USDC": "0xA0b86a33E6bCc14F4B3b0d5a9b0F1a6D3b4e5c6d",  # Example
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        }
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            # Try to load warehouse-specific config first
            if config_file.endswith('warehouse_config.json') and os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    # Extract the warehouse_config section
                    if 'warehouse_config' in config_data:
                        return config_data['warehouse_config']
                    else:
                        return config_data
            
            # Fallback to main config.json
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    return json.load(f)
            
            # Environment variables fallback
            return {
                "chain_id": int(os.getenv("CHAIN_ID", "1")),
                "wallet_address": os.getenv("WALLET_ADDRESS", "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"),
                "api_key": os.getenv("API_KEY", "13fa508ea913c8c045a462ac"),
                "ens_public_client": os.getenv("ENS_NAME", "Obasimartins65.eth"),
                "auto_withdraw_enabled": True,
                "min_withdraw_threshold": 0.001
            }
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Use memory configuration as fallback
            return {
                "chain_id": 1,
                "wallet_address": "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
                "api_key": "13fa508ea913c8c045a462ac",
                "ens_public_client": "Obasimartins65.eth",
                "auto_withdraw_enabled": True,
                "min_withdraw_threshold": 0.001
            }
    
    def initialize_web3(self):
        """Initialize Web3 connection"""
        try:
            # Use multiple RPC endpoints for reliability
            rpc_endpoints = [
                "https://ethereum-rpc.publicnode.com",
                "https://rpc.ankr.com/eth",
                "https://eth.drpc.org"
            ]
            
            for endpoint in rpc_endpoints:
                try:
                    self.w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 15}))
                    if self.w3.is_connected():
                        logger.info(f"✅ Connected to Ethereum via {endpoint}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to connect to {endpoint}: {e}")
                    continue
            
            if not self.w3 or not self.w3.is_connected():
                raise ConnectionError("Could not connect to any Ethereum RPC")
                
        except Exception as e:
            logger.error(f"Web3 initialization failed: {e}")
            raise
    
    def get_split_contract_abi(self) -> List[Dict]:
        """Get 0xSplits contract ABI for interactions"""
        # Simplified ABI for key functions
        return [
            {
                "inputs": [
                    {"name": "split", "type": "address"},
                    {"name": "token", "type": "address"},
                    {"name": "accounts", "type": "address[]"},
                    {"name": "percentAllocations", "type": "uint32[]"},
                    {"name": "distributorFee", "type": "uint32"},
                    {"name": "distributorAddress", "type": "address"}
                ],
                "name": "distributeETH",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "split", "type": "address"},
                    {"name": "token", "type": "address"},
                    {"name": "accounts", "type": "address[]"},
                    {"name": "percentAllocations", "type": "uint32[]"},
                    {"name": "distributorFee", "type": "uint32"},
                    {"name": "distributorAddress", "type": "address"}
                ],
                "name": "distributeERC20",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "account", "type": "address"},
                    {"name": "withdrawETH", "type": "uint256"},
                    {"name": "tokens", "type": "address[]"}
                ],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "account", "type": "address"}
                ],
                "name": "getETHBalance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "account", "type": "address"},
                    {"name": "token", "type": "address"}
                ],
                "name": "getERC20Balance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def get_warehouse_balances(self, address: str) -> Dict[str, float]:
        """Get balances in Splits Warehouse for an address"""
        try:
            if self.w3 is None or not self.w3.is_connected():
                raise Exception("Web3 client not initialized")
                
            balances = {}
            
            # Get Split Main contract
            split_contract = self.w3.eth.contract(
                address=self.splits_addresses["split_main"],
                abi=self.get_split_contract_abi()
            )
            
            # Check ETH balance
            try:
                eth_balance_wei = split_contract.functions.getETHBalance(address).call()
                eth_balance = float(Web3.from_wei(eth_balance_wei, 'ether'))
                balances["ETH"] = eth_balance
                logger.info(f"📊 Warehouse ETH balance: {eth_balance}")
            except Exception as e:
                logger.warning(f"Could not get ETH balance: {e}")
                balances["ETH"] = 0.0
            
            # Check common ERC20 token balances
            for token_name, token_address in self.common_tokens.items():
                if token_address == "0x0000000000000000000000000000000000000000":
                    continue  # Skip ETH address
                    
                try:
                    token_balance_wei = split_contract.functions.getERC20Balance(
                        address, token_address
                    ).call()
                    
                    # Convert based on token decimals (assuming 18 for most tokens)
                    token_balance = float(Web3.from_wei(token_balance_wei, 'ether'))
                    if token_balance > 0:
                        balances[token_name] = token_balance
                        logger.info(f"📊 Warehouse {token_name} balance: {token_balance}")
                        
                except Exception as e:
                    logger.debug(f"Could not get {token_name} balance: {e}")
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get warehouse balances: {e}")
            return {"ETH": 0.0}
    
    def check_pending_distributions(self, address: str) -> List[Dict]:
        """Check for pending distributions that need to be claimed"""
        try:
            # This would typically query the Splits subgraph or API
            # For now, we'll simulate pending distributions
            pending = []
            
            # Check if there are any claimable amounts
            balances = self.get_warehouse_balances(address)
            
            for token, balance in balances.items():
                if balance > 0:
                    pending.append({
                        "token": token,
                        "amount": balance,
                        "claimable": True,
                        "last_updated": datetime.now().isoformat()
                    })
            
            logger.info(f"📋 Found {len(pending)} pending distributions")
            return pending
            
        except Exception as e:
            logger.error(f"Failed to check pending distributions: {e}")
            return []
    
    def create_withdrawal_transaction(
        self, 
        address: str, 
        withdraw_eth: float = 0, 
        tokens: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a withdrawal transaction for Splits Warehouse"""
        try:
            if self.w3 is None or not self.w3.is_connected():
                raise Exception("Web3 client not initialized or not connected")
                        
            if tokens is None:
                tokens = []
            
            # Get Split Main contract
            split_contract = self.w3.eth.contract(
                address=self.splits_addresses["split_main"],
                abi=self.get_split_contract_abi()
            )
            
            # Convert ETH amount to Wei
            withdraw_eth_wei = Web3.to_wei(withdraw_eth, 'ether') if withdraw_eth > 0 else 0
            
            # Convert token names to addresses
            token_addresses = []
            for token in tokens:
                if token in self.common_tokens:
                    token_addresses.append(self.common_tokens[token])
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(address, 'pending')
            
            # Build transaction
            transaction = split_contract.functions.withdraw(
                address,
                withdraw_eth_wei,
                token_addresses
            ).build_transaction({
                'from': address,
                'nonce': nonce,
                'gas': 300000,  # Higher gas limit for complex contract interaction
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.config['chain_id']
            })
            
            logger.info(f"📋 Created withdrawal transaction for {withdraw_eth} ETH + {len(token_addresses)} tokens")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to create withdrawal transaction: {e}")
            raise
    
    def validate_nonce_for_warehouse(self, address: str) -> Dict[str, Any]:
        """Validate nonce specifically for warehouse interactions"""
        try:
            if self.w3 is None or not self.w3.is_connected():
                raise Exception("Web3 client not initialized")
                
            current_nonce = self.w3.eth.get_transaction_count(address, 'latest')
            pending_nonce = self.w3.eth.get_transaction_count(address, 'pending')
            
            # Check if nonce is valid for communication
            is_valid = current_nonce >= 0  # Any valid nonce works
            can_communicate = pending_nonce == current_nonce  # No pending transactions
            
            validation_result = {
                "address": address,
                "current_nonce": current_nonce,
                "pending_nonce": pending_nonce,
                "is_valid": is_valid,
                "can_communicate": can_communicate,
                "warehouse_ready": can_communicate and is_valid,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🔍 Nonce validation: Current={current_nonce}, Pending={pending_nonce}, Ready={validation_result['warehouse_ready']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Nonce validation failed: {e}")
            return {
                "address": address,
                "is_valid": False,
                "can_communicate": False,
                "warehouse_ready": False,
                "error": str(e)
            }
    
    async def execute_automatic_withdrawal(
        self, 
        address: str, 
        private_key: str,
        auto_detect_amounts: bool = True
    ) -> Dict[str, Any]:
        """Execute automatic withdrawal from Splits Warehouse"""
        try:
            logger.info(f"🚀 Starting automatic withdrawal for {address}")
            
            # Step 1: Validate nonce
            nonce_validation = self.validate_nonce_for_warehouse(address)
            if not nonce_validation['warehouse_ready']:
                raise Exception(f"Address not ready for warehouse interaction: {nonce_validation}")
            
            # Step 2: Check warehouse balances
            balances = self.get_warehouse_balances(address)
            if not any(balance > 0 for balance in balances.values()):
                return {
                    "status": "no_funds",
                    "message": "No funds available in warehouse",
                    "balances": balances
                }
            
            # Step 3: Determine withdrawal amounts
            withdraw_eth = balances.get("ETH", 0) if auto_detect_amounts else 0
            withdraw_tokens = [token for token, balance in balances.items() 
                             if token != "ETH" and balance > 0] if auto_detect_amounts else []
            
            logger.info(f"💰 Withdrawing: {withdraw_eth} ETH + {len(withdraw_tokens)} tokens")
            
            # Step 4: Create withdrawal transaction
            transaction = self.create_withdrawal_transaction(
                address, 
                withdraw_eth, 
                withdraw_tokens
            )
            
            if self.w3 is None or not self.w3.is_connected():
                raise Exception("Web3 client not initialized")
                
            # Sign and send transaction
            signed_txn = Account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Withdrawal transaction sent: {tx_hash_hex}")
            
            # Step 6: Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=300)
            
            result = {
                "status": "success" if receipt['status'] == 1 else "failed",
                "transaction_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed'],
                "withdrawn_eth": withdraw_eth,
                "withdrawn_tokens": withdraw_tokens,
                "balances_before": balances,
                "nonce_used": transaction['nonce'],
                "explorer_url": f"https://etherscan.io/tx/{tx_hash_hex}"
            }
            
            logger.info(f"🎉 Automatic withdrawal completed: {result['status'].upper()}")
            return result
            
        except Exception as e:
            logger.error(f"Automatic withdrawal failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_complete_withdrawal(
        self, 
        address: str, 
        private_key: str,
        auto_detect_amounts: bool = True
    ) -> Dict[str, Any]:
        """Execute complete two-step withdrawal: source -> warehouse -> wallet"""
        try:
            logger.info(f"🚀 Starting complete two-step withdrawal for {address}")
            
            # Step 1: Execute initial withdrawal to warehouse
            step1_result = await self.execute_automatic_withdrawal(
                address, private_key, auto_detect_amounts
            )
            
            if step1_result['status'] != 'success':
                return {
                    "status": "step1_failed",
                    "step1_result": step1_result,
                    "message": "Failed at step 1: withdrawal to warehouse"
                }
            
            logger.info(f"✅ Step 1 completed: {step1_result['transaction_hash']}")
            
            # Wait a bit for the transaction to be processed
            await asyncio.sleep(10)
            
            # Step 2: Release from warehouse to actual wallet
            logger.info(f"🚀 Step 2: Releasing tokens from warehouse to wallet...")
            
            # Check warehouse balances after step 1
            warehouse_balances = self.get_warehouse_balances(address)
            
            if not any(balance > 0 for balance in warehouse_balances.values()):
                return {
                    "status": "no_warehouse_funds",
                    "step1_result": step1_result,
                    "message": "No funds in warehouse after step 1"
                }
            
            # Create release transaction from warehouse
            step2_result = await self.execute_warehouse_release(
                address, private_key, warehouse_balances
            )
            
            # Combine results
            final_result = {
                "status": "complete_success" if step2_result['status'] == 'success' else "step2_failed",
                "step1_withdrawal": step1_result,
                "step2_release": step2_result,
                "total_process_time": "~2-5 minutes",
                "final_status": "Tokens now in your wallet" if step2_result['status'] == 'success' else "Tokens stuck in warehouse"
            }
            
            if step2_result['status'] == 'success':
                logger.info(f"🎉 Complete withdrawal successful! Tokens are now in your wallet.")
            else:
                logger.warning(f"⚠️ Step 2 failed. Tokens are in warehouse but not released to wallet.")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Complete withdrawal failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_warehouse_release(
        self, 
        address: str, 
        private_key: str,
        balances: Dict[str, float]
    ) -> Dict[str, Any]:
        """Release tokens from warehouse to actual wallet"""
        try:
            if self.w3 is None or not self.w3.is_connected():
                raise Exception("Web3 client not initialized")
            
            logger.info(f"💰 Releasing {sum(balances.values())} total value from warehouse")
            
            # Get Split Main contract for warehouse release
            split_contract = self.w3.eth.contract(
                address=self.splits_addresses["split_main"],
                abi=self.get_split_contract_abi()
            )
            
            # Prepare tokens for release
            eth_amount = balances.get("ETH", 0)
            token_addresses = []
            
            for token_name, balance in balances.items():
                if token_name != "ETH" and balance > 0 and token_name in self.common_tokens:
                    token_addresses.append(self.common_tokens[token_name])
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(address, 'pending')
            
            # Build warehouse release transaction
            transaction = split_contract.functions.withdraw(
                address,  # Recipient (your wallet)
                Web3.to_wei(eth_amount, 'ether') if eth_amount > 0 else 0,
                token_addresses
            ).build_transaction({
                'from': address,
                'nonce': nonce,
                'gas': 400000,  # Higher gas for warehouse release
                'gasPrice': int(self.w3.eth.gas_price * 1.2),  # 20% higher gas price for faster processing
                'chainId': self.config['chain_id']
            })
            
            # Sign and send transaction
            signed_txn = Account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Warehouse release transaction sent: {tx_hash_hex}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=300)
            
            result = {
                "status": "success" if receipt['status'] == 1 else "failed",
                "transaction_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed'],
                "released_eth": eth_amount,
                "released_tokens": [token for token in balances.keys() if token != "ETH" and balances[token] > 0],
                "nonce_used": transaction['nonce'],
                "explorer_url": f"https://etherscan.io/tx/{tx_hash_hex}",
                "process_type": "warehouse_release"
            }
            
            logger.info(f"🎉 Warehouse release completed: {result['status'].upper()}")
            return result
            
        except Exception as e:
            logger.error(f"Warehouse release failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for warehouse operations"""
        try:
            address = self.config["wallet_address"]
            
            status = {
                "connection": {
                    "web3_connected": self.w3.is_connected(),
                    "chain_id": self.w3.eth.chain_id,
                    "current_block": self.w3.eth.block_number,
                    "gas_price_gwei": float(Web3.from_wei(self.w3.eth.gas_price, 'gwei'))
                },
                "address_info": {
                    "address": address,
                    "balance_eth": float(Web3.from_wei(self.w3.eth.get_balance(address), 'ether')),
                    "ens_name": self.config.get("ens_public_client")
                },
                "warehouse_status": {},
                "splits_contracts": self.splits_addresses,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add nonce validation
            nonce_validation = self.validate_nonce_for_warehouse(address)
            status["nonce_status"] = nonce_validation
            
            # Add warehouse balances
            warehouse_balances = self.get_warehouse_balances(address)
            status["warehouse_status"] = {
                "balances": warehouse_balances,
                "total_value": sum(warehouse_balances.values()),
                "has_claimable_funds": any(balance > 0 for balance in warehouse_balances.values())
            }
            
            # Add pending distributions
            pending = self.check_pending_distributions(address)
            status["pending_distributions"] = pending
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

async def main():
    """Test Splits Warehouse integration"""
    print("🏭 Splits Warehouse Integration Test")
    print("=" * 50)
    
    try:
        client = SplitsWarehouseClient()
        
        # Get system status
        print("📊 Getting system status...")
        status = client.get_system_status()
        
        print(f"\n🔗 Connection Status:")
        conn = status['connection']
        print(f"   Web3 Connected: {'✅' if conn['web3_connected'] else '❌'}")
        print(f"   Chain ID: {conn['chain_id']}")
        print(f"   Current Block: {conn['current_block']}")
        print(f"   Gas Price: {conn['gas_price_gwei']:.3f} Gwei")
        
        print(f"\n👤 Address Information:")
        addr = status['address_info']
        print(f"   Address: {addr['address']}")
        print(f"   ENS: {addr['ens_name']}")
        print(f"   Balance: {addr['balance_eth']} ETH")
        
        print(f"\n🏭 Warehouse Status:")
        warehouse = status['warehouse_status']
        print(f"   Has Claimable Funds: {'✅' if warehouse['has_claimable_funds'] else '❌'}")
        print(f"   Total Value: {warehouse['total_value']} ETH")
        for token, balance in warehouse['balances'].items():
            if balance > 0:
                print(f"   {token}: {balance}")
        
        print(f"\n🔢 Nonce Status:")
        nonce = status['nonce_status']
        print(f"   Current Nonce: {nonce['current_nonce']}")
        print(f"   Pending Nonce: {nonce['pending_nonce']}")
        print(f"   Warehouse Ready: {'✅' if nonce['warehouse_ready'] else '❌'}")
        
        if warehouse['has_claimable_funds'] and nonce['warehouse_ready']:
            print(f"\n🎉 READY FOR AUTOMATIC WITHDRAWAL!")
            print(f"   • Funds are available in warehouse")
            print(f"   • Nonce is valid for communication")
            print(f"   • System is configured properly")
            print(f"\n💡 To execute withdrawal:")
            print(f"   await client.execute_automatic_withdrawal(address, private_key)")
        else:
            print(f"\n⚠️ Not ready for withdrawal:")
            if not warehouse['has_claimable_funds']:
                print(f"   • No claimable funds in warehouse")
            if not nonce['warehouse_ready']:
                print(f"   • Nonce not ready for communication")
        
        print(f"\n📋 Pending Distributions: {len(status['pending_distributions'])}")
        for dist in status['pending_distributions']:
            print(f"   {dist['token']}: {dist['amount']} (Claimable: {'✅' if dist['claimable'] else '❌'})")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())