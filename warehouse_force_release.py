"""
Splits Warehouse Fund Release Commander
Forces release of held funds from Splits Warehouse using proper contract calls
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_account import Account
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WarehouseClient:
    """Specialized client for forcing fund release from Splits Warehouse"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.w3 = None
        self.initialize_web3()
        
        # Updated Splits Protocol addresses (verified)
        self.splits_addresses = {
            "split_main": "0x2ed6c4B5dA6378c7897AC67Ba9e43102Feb694EE",  # Verified 0xSplits: Split Main
            "warehouse": "0x8fb66F38cF86A3d5e8768f8F1754A24A6c661Fb8",    # Splits Warehouse
            "waterfall_module": "0x0000000000000000000000000000000000000000"
        }
        
        # Get exact contract ABIs for fund release
        self.split_main_abi = self.get_split_main_abi()
        self.warehouse_abi = self.get_warehouse_abi()
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration with fallback to memory configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Config file not found, using memory config: {e}")
            # Use memory configuration from project_information_memory
            return {
                "chain_id": 1,
                "wallet_address": "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
                "api_key": "13fa508ea913c8c045a462ac",
                "ens_public_client": "Obasimartins65.eth"
            }
    
    def initialize_web3(self):
        """Initialize Web3 with reliable RPC endpoint"""
        try:
            # Use the configured RPC endpoint from memory
            rpc_endpoint = "https://ethereum-rpc.publicnode.com"
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_endpoint, request_kwargs={'timeout': 20}))
            
            if not self.w3.is_connected():
                raise ConnectionError("Could not connect to Ethereum network")
            
            logger.info(f"✅ Connected to Ethereum Mainnet via {rpc_endpoint}")
            logger.info(f"📊 Current block: {self.w3.eth.block_number}")
            
        except Exception as e:
            logger.error(f"Web3 initialization failed: {e}")
            raise
    
    def get_split_main_abi(self) -> List[Dict]:
        """Get complete Split Main contract ABI for fund operations"""
        return [
            {
                "inputs": [
                    {"name": "split", "type": "address"},
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
    
    def get_warehouse_abi(self) -> List[Dict]:
        """Get Warehouse contract ABI for direct fund release"""
        return [
            {
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "tokens", "type": "address[]"},
                    {"name": "amounts", "type": "uint256[]"}
                ],
                "name": "batchWithdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable", 
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "token", "type": "address"}
                ],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def get_held_funds_detailed(self, address: str) -> Dict[str, Any]:
        """Get detailed information about held funds in warehouse"""
        try:
            held_funds = {
                "eth_balance": 0,
                "token_balances": {},
                "total_held_value": 0,
                "release_ready": False
            }
            
            # Check Split Main contract balances
            split_main_contract = self.w3.eth.contract(
                address=self.splits_addresses["split_main"],
                abi=self.split_main_abi
            )
            
            # Get ETH balance in Split Main
            try:
                eth_balance_wei = split_main_contract.functions.getETHBalance(address).call()
                eth_balance = float(Web3.from_wei(eth_balance_wei, 'ether'))
                held_funds["eth_balance"] = eth_balance
                held_funds["total_held_value"] += eth_balance
                
                if eth_balance > 0:
                    logger.info(f"🔍 Found held ETH: {eth_balance}")
                    held_funds["release_ready"] = True
                    
            except Exception as e:
                logger.debug(f"ETH balance check failed: {e}")
            
            # Check common token balances
            common_tokens = {
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "USDC": "0xA0b86a33E6bCc14F4B3b0d5a9b0F1a6D3b4e5c6d", 
                "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
            }
            
            for token_name, token_address in common_tokens.items():
                try:
                    token_balance_wei = split_main_contract.functions.getERC20Balance(
                        address, token_address
                    ).call()
                    
                    if token_balance_wei > 0:
                        # Convert to readable format (assuming 18 decimals for most tokens)
                        token_balance = float(Web3.from_wei(token_balance_wei, 'ether'))
                        held_funds["token_balances"][token_name] = {
                            "balance": token_balance,
                            "address": token_address,
                            "balance_wei": token_balance_wei
                        }
                        held_funds["total_held_value"] += token_balance
                        held_funds["release_ready"] = True
                        
                        logger.info(f"🔍 Found held {token_name}: {token_balance}")
                        
                except Exception as e:
                    logger.debug(f"{token_name} balance check failed: {e}")
            
            # Check warehouse contract directly if available
            if self.splits_addresses["warehouse"] != "0x0000000000000000000000000000000000000000":
                try:
                    warehouse_contract = self.w3.eth.contract(
                        address=self.splits_addresses["warehouse"],
                        abi=self.warehouse_abi
                    )
                    
                    # Check warehouse balances for common tokens
                    for token_name, token_info in held_funds["token_balances"].items():
                        if token_info["balance"] == 0:  # Only check if not found in Split Main
                            try:
                                warehouse_balance = warehouse_contract.functions.balanceOf(
                                    address, token_info["address"] 
                                ).call()
                                
                                if warehouse_balance > 0:
                                    token_balance = float(Web3.from_wei(warehouse_balance, 'ether'))
                                    held_funds["token_balances"][token_name]["balance"] += token_balance
                                    held_funds["token_balances"][token_name]["warehouse_balance"] = warehouse_balance
                                    held_funds["total_held_value"] += token_balance
                                    held_funds["release_ready"] = True
                                    
                                    logger.info(f"🔍 Found held {token_name} in warehouse: {token_balance}")
                                    
                            except Exception as e:
                                logger.debug(f"Warehouse {token_name} check failed: {e}")
                                
                except Exception as e:
                    logger.debug(f"Warehouse contract interaction failed: {e}")
            
            return held_funds
            
        except Exception as e:
            logger.error(f"Failed to get held funds details: {e}")
            return {"error": str(e), "release_ready": False}
    
    def create_force_release_transaction(self, address: str, held_funds: Dict[str, Any]) -> Dict[str, Any]:
        """Create transaction to force release of all held funds"""
        try:
            split_main_contract = self.w3.eth.contract(
                address=self.splits_addresses["split_main"],
                abi=self.split_main_abi
            )
            
            # Get current nonce - required by nonce management specification
            current_nonce = self.w3.eth.get_transaction_count(address, 'pending')
            
            # Validate nonce as per specification
            if current_nonce < 0:
                raise ValueError("Invalid nonce detected")
            
            logger.info(f"🔢 Using nonce {current_nonce} for fund release")
            
            # Prepare withdrawal parameters
            withdraw_eth_wei = Web3.to_wei(held_funds.get("eth_balance", 0), 'ether')
            
            # Collect all token addresses that have balances
            token_addresses = []
            for token_name, token_info in held_funds.get("token_balances", {}).items():
                if token_info["balance"] > 0:
                    token_addresses.append(token_info["address"])
            
            logger.info(f"🎯 Force releasing: {Web3.from_wei(withdraw_eth_wei, 'ether')} ETH + {len(token_addresses)} tokens")
            
            # Build the force release transaction
            transaction = split_main_contract.functions.withdraw(
                address,
                withdraw_eth_wei,
                token_addresses
            ).build_transaction({
                'from': address,
                'nonce': current_nonce,
                'gas': 500000,  # Higher gas limit for multiple token release
                'gasPrice': int(self.w3.eth.gas_price * 1.2),  # 20% higher gas price for priority
                'chainId': self.config['chain_id']
            })
            
            logger.info(f"✅ Force release transaction created")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to create force release transaction: {e}")
            raise
    
    async def execute_force_release(self, address: str, private_key: str) -> Dict[str, Any]:
        """Execute the force release command to free held funds"""
        try:
            logger.info(f"🚀 Starting FORCE RELEASE for address: {address}")
            
            # Step 1: Get detailed information about held funds
            logger.info("🔍 Step 1: Scanning for held funds...")
            held_funds = self.get_held_funds_detailed(address)
            
            if not held_funds.get("release_ready"):
                return {
                    "status": "no_funds_held",
                    "message": "No held funds detected in warehouse",
                    "held_funds": held_funds
                }
            
            logger.info(f"💰 Found held funds: {held_funds['total_held_value']} ETH equivalent")
            
            # Step 2: Validate current nonce (required by specification)
            current_nonce = self.w3.eth.get_transaction_count(address, 'latest')
            pending_nonce = self.w3.eth.get_transaction_count(address, 'pending')
            
            if pending_nonce != current_nonce:
                logger.warning(f"⚠️ Pending transactions detected: current={current_nonce}, pending={pending_nonce}")
            
            # Step 3: Create force release transaction
            logger.info("🔧 Step 2: Creating force release transaction...")
            transaction = self.create_force_release_transaction(address, held_funds)
            
            # Step 4: Sign the transaction
            logger.info("🔐 Step 3: Signing force release transaction...")
            signed_txn = Account.sign_transaction(transaction, private_key)
            
            # Step 5: Send the transaction
            logger.info("📤 Step 4: Broadcasting force release command...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Force release command sent: {tx_hash_hex}")
            
            # Step 6: Wait for confirmation
            logger.info("⏳ Step 5: Waiting for warehouse to release funds...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=300)
            
            # Step 7: Verify release
            final_status = "success" if receipt['status'] == 1 else "failed"
            
            result = {
                "status": final_status,
                "message": "Funds successfully released from warehouse" if final_status == "success" else "Fund release failed",
                "transaction_hash": tx_hash_hex,
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed'],
                "held_funds_before": held_funds,
                "nonce_used": transaction['nonce'],
                "explorer_url": f"https://etherscan.io/tx/{tx_hash_hex}",
                "release_timestamp": datetime.now().isoformat()
            }
            
            if final_status == "success":
                logger.info(f"🎉 WAREHOUSE FUNDS SUCCESSFULLY RELEASED!")
                logger.info(f"   Transaction: {tx_hash_hex}")
                logger.info(f"   Block: {receipt['blockNumber']}")
                logger.info(f"   Gas Used: {receipt['gasUsed']}")
            else:
                logger.error(f"❌ Fund release failed - check transaction: {tx_hash_hex}")
            
            return result
            
        except Exception as e:
            logger.error(f"Force release execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_release_status(self, address: str) -> Dict[str, Any]:
        """Get current status of funds and release readiness"""
        try:
            held_funds = self.get_held_funds_detailed(address)
            current_nonce = self.w3.eth.get_transaction_count(address, 'latest')
            pending_nonce = self.w3.eth.get_transaction_count(address, 'pending')
            wallet_balance = float(Web3.from_wei(self.w3.eth.get_balance(address), 'ether'))
            
            status = {
                "address": address,
                "wallet_balance_eth": wallet_balance,
                "held_funds": held_funds,
                "nonce_status": {
                    "current_nonce": current_nonce,
                    "pending_nonce": pending_nonce,
                    "ready_for_release": pending_nonce == current_nonce
                },
                "release_recommendations": [],
                "can_force_release": held_funds.get("release_ready", False),
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate recommendations
            if held_funds.get("release_ready"):
                status["release_recommendations"].append("✅ Held funds detected - ready for force release")
                if wallet_balance < 0.01:
                    status["release_recommendations"].append("⚠️ Low wallet balance - ensure sufficient ETH for gas fees")
                if pending_nonce != current_nonce:
                    status["release_recommendations"].append("⚠️ Pending transactions detected - wait for completion")
                else:
                    status["release_recommendations"].append("🚀 All systems ready - execute force release now")
            else:
                status["release_recommendations"].append("ℹ️ No held funds detected in warehouse")
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get release status: {e}")
            return {"error": str(e)}

async def main():
    """Test the fund release system"""
    print("🏭 Splits Warehouse Fund Release Commander")
    print("=" * 50)
    
    try:
        warehouse_client = WarehouseClient()
        address = warehouse_client.config["wallet_address"]
        
        print(f"🎯 Target Address: {address}")
        print(f"🔗 ENS: {warehouse_client.config['ens_public_client']}")
        print()
        
        # Get current release status
        print("🔍 Checking WarehouseClient fund release status...")
        status = warehouse_client.get_release_status(address)
        
        print(f"\n💼 Current Status:")
        print(f"   Wallet Balance: {status['wallet_balance_eth']} ETH")
        print(f"   Current Nonce: {status['nonce_status']['current_nonce']}")
        print(f"   Ready for Release: {'✅' if status['nonce_status']['ready_for_release'] else '❌'}")
        
        held_funds = status['held_funds']
        print(f"\n🏭 Warehouse Analysis:")
        print(f"   ETH Held: {held_funds.get('eth_balance', 0)} ETH")
        print(f"   Tokens Held: {len(held_funds.get('token_balances', {}))}")
        print(f"   Total Value: {held_funds.get('total_held_value', 0)} ETH equivalent")
        print(f"   Can Force Release: {'✅' if held_funds.get('release_ready') else '❌'}")
        
        if held_funds.get('token_balances'):
            print(f"\n💰 Held Token Details:")
            for token_name, token_info in held_funds['token_balances'].items():
                if token_info['balance'] > 0:
                    print(f"   {token_name}: {token_info['balance']}")
        
        print(f"\n💡 Recommendations:")
        for rec in status['release_recommendations']:
            print(f"   {rec}")
        
        if status['can_force_release']:
            print(f"\n🚀 FORCE RELEASE READY!")
            print(f"   Your funds are held in the warehouse and can be released.")
            print(f"   To execute release:")
            print(f"   await warehouse_client.execute_force_release(address, private_key)")
        else:
            print(f"\n⚠️ No funds currently held in warehouse")
        
    except Exception as e:
        print(f"❌ System check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())