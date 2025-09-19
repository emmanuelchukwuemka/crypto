"""
Token Withdrawal Execution Script
Use this script to perform actual token withdrawals
"""

import asyncio
import getpass
from simple_ethereum_client import SimpleEthereumClient
from eth_account import Account
import logging

logger = logging.getLogger(__name__)

class WithdrawalExecutor:
    """Execute secure token withdrawals"""
    
    def __init__(self):
        self.client = SimpleEthereumClient()
    
    def sign_and_send_transaction(self, transaction: dict, private_key: str) -> str:
        """Sign and send a transaction"""
        try:
            # Sign the transaction
            signed_txn = Account.sign_transaction(transaction, private_key)
            
            # Send the transaction
            tx_hash = self.client.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Transaction sent: {tx_hash_hex}")
            return tx_hash_hex
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
    
    def wait_for_confirmation(self, tx_hash: str, timeout: int = 120) -> dict:
        """Wait for transaction confirmation"""
        try:
            print(f"⏳ Waiting for transaction confirmation...")
            receipt = self.client.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            if receipt['status'] == 1:
                print(f"✅ Transaction confirmed!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas used: {receipt['gasUsed']}")
            else:
                print(f"❌ Transaction failed!")
                
            return dict(receipt)
            
        except Exception as e:
            logger.error(f"Confirmation failed: {e}")
            raise
    
    async def execute_withdrawal(self, to_address: str, amount_eth: float, private_key: str) -> dict:
        """Execute complete withdrawal process"""
        try:
            print(f"\n🚀 Executing withdrawal:")
            print(f"   To: {to_address}")
            print(f"   Amount: {amount_eth} ETH")
            
            from_address = self.client.config["wallet_address"]
            
            # Validate system first
            print("\n🔍 Pre-flight checks...")
            
            # Check balance
            balance = self.client.get_balance(from_address)
            if balance < amount_eth:
                raise ValueError(f"Insufficient balance: {balance} ETH < {amount_eth} ETH")
            
            # Check withdrawal config
            withdraw_config = self.client.get_withdraw_config(from_address)
            if withdraw_config.get('paused'):
                raise ValueError("Withdrawals are currently paused")
            
            # Check min/max limits
            min_amount = float(withdraw_config.get('minWithdrawAmount', '0'))
            max_amount = float(withdraw_config.get('maxWithdrawAmount', '999999'))
            
            if amount_eth < min_amount:
                raise ValueError(f"Amount below minimum: {amount_eth} < {min_amount}")
            if amount_eth > max_amount:
                raise ValueError(f"Amount above maximum: {amount_eth} > {max_amount}")
            
            print("✅ All pre-flight checks passed")
            
            # Resolve ENS if needed
            if to_address.endswith('.eth'):
                print(f"🌐 Resolving ENS name: {to_address}")
                resolved = await self.client.resolve_ens_name(to_address)
                if not resolved:
                    raise ValueError(f"Could not resolve ENS: {to_address}")
                to_address = resolved
                print(f"✅ ENS resolved to: {to_address}")
            
            # Create transaction
            print("\n📋 Creating transaction...")
            transaction = self.client.create_transaction(from_address, to_address, amount_eth)
            
            print("📊 Transaction details:")
            print(f"   From: {transaction['from']}")
            print(f"   To: {transaction['to']}")
            print(f"   Value: {amount_eth} ETH")
            print(f"   Nonce: {transaction['nonce']}")
            print(f"   Gas: {transaction['gas']}")
            print(f"   Gas Price: {self.client.w3.from_wei(transaction['gasPrice'], 'gwei')} Gwei")
            
            # Confirm transaction
            confirm = input("\n❓ Proceed with transaction? (yes/no): ").lower().strip()
            if confirm != 'yes':
                print("❌ Transaction cancelled by user")
                return {"status": "cancelled"}
            
            # Sign and send
            print("\n🔐 Signing and sending transaction...")
            tx_hash = self.sign_and_send_transaction(transaction, private_key)
            
            print(f"📤 Transaction sent!")
            print(f"   Hash: {tx_hash}")
            print(f"   Explorer: https://etherscan.io/tx/{tx_hash}")
            
            # Wait for confirmation
            receipt = self.wait_for_confirmation(tx_hash)
            
            result = {
                "status": "confirmed" if receipt['status'] == 1 else "failed",
                "transaction_hash": tx_hash,
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed'],
                "amount": amount_eth,
                "from": from_address,
                "to": to_address,
                "nonce": transaction['nonce']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Withdrawal failed: {e}")
            print(f"❌ Withdrawal failed: {e}")
            raise

def main():
    """Interactive withdrawal interface"""
    try:
        print("🌟 Ethereum Token Withdrawal System")
        print("=" * 50)
        
        executor = WithdrawalExecutor()
        
        # Get system status
        status = executor.client.get_system_status()
        print(f"\n📊 Network Status:")
        print(f"   Connected: {'✅' if status['connected'] else '❌'}")
        print(f"   Chain ID: {status['chain_id']}")
        print(f"   Block: {status['current_block']}")
        print(f"   Gas Price: {status['gas_price_gwei']:.3f} Gwei")
        
        wallet = status['wallet_address']
        balance = executor.client.get_balance(wallet)
        nonce = executor.client.get_nonce(wallet)
        
        print(f"\n💼 Wallet Status:")
        print(f"   Address: {wallet}")
        print(f"   Balance: {balance} ETH")
        print(f"   Nonce: {nonce}")
        
        if not status['connected']:
            print("❌ Not connected to network")
            return
        
        if balance <= 0:
            print("❌ Insufficient balance for withdrawal")
            return
        
        print("\n" + "=" * 50)
        print("✅ System ready for withdrawal!")
        
        # Get withdrawal parameters
        print("\n📝 Enter withdrawal details:")
        
        to_address = input("To address (or ENS name): ").strip()
        if not to_address:
            print("❌ Address required")
            return
        
        try:
            amount_str = input(f"Amount in ETH (max: {balance:.6f}): ").strip()
            amount_eth = float(amount_str)
        except ValueError:
            print("❌ Invalid amount")
            return
        
        if amount_eth <= 0 or amount_eth > balance:
            print("❌ Invalid amount")
            return
        
        # Get private key securely
        print("\n🔐 Private key required for signing:")
        print("⚠️  Your private key will NOT be stored or logged")
        private_key = getpass.getpass("Enter private key: ").strip()
        
        if not private_key:
            print("❌ Private key required")
            return
        
        # Validate private key format
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        try:
            # Test private key by creating account
            account = Account.from_key(private_key)
            if account.address.lower() != wallet.lower():
                print(f"❌ Private key doesn't match wallet address")
                print(f"   Expected: {wallet}")
                print(f"   Got: {account.address}")
                return
        except Exception as e:
            print(f"❌ Invalid private key: {e}")
            return
        
        print("✅ Private key validated")
        
        # Execute withdrawal
        print("\n🚀 Starting withdrawal process...")
        
        async def run_withdrawal():
            return await executor.execute_withdrawal(to_address, amount_eth, private_key)
        
        result = asyncio.run(run_withdrawal())
        
        if result['status'] == 'confirmed':
            print(f"\n🎉 WITHDRAWAL SUCCESSFUL!")
            print(f"   Transaction: {result['transaction_hash']}")
            print(f"   Amount: {result['amount']} ETH")
            print(f"   Block: {result['block_number']}")
            print(f"   Gas Used: {result['gas_used']}")
        else:
            print(f"\n❌ WITHDRAWAL FAILED!")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Main execution failed: {e}")

if __name__ == "__main__":
    main()