# Splits Warehouse Withdrawal Guide

This guide explains how to use the Splits WarehouseClient to withdraw funds through the batching mechanism.

## Overview

The WarehouseClient is designed to batch operations for the Splits protocol. Instead of calling distributeToken on each of your splits individually (and paying gas for each one), you can provide the WarehouseClient with a list of your splits and the tokens they hold. It will then loop through them and trigger the distribution for each one in a single transaction.

## Current Setup

Your wallet address is configured as: `0xB5c1baF2E532Bb749a6b2034860178A3558b6e58`

## How to Withdraw Funds Through WarehouseClient

### 1. Check Warehouse Status

First, check if there are any funds available in the WarehouseClient:

```bash
# Using the API
curl http://localhost:3000/warehouse/balances

# Or using the test script
python test_warehouse.py
```

### 2. Execute Complete Withdrawal

To execute a complete two-step withdrawal (source → warehouse → wallet):

#### Option A: Using the API

```bash
curl -X POST http://localhost:3000/warehouse/complete-withdraw \
  -H "Content-Type: application/json" \
  -d '{
    "private_key": "YOUR_PRIVATE_KEY"
  }'
```

#### Option B: Using the Command Line Script

```bash
# Set your private key as an environment variable
set WALLET_PRIVATE_KEY=your_private_key_here

# Run the withdrawal script
python execute_warehouse_withdrawal.py
```

### 3. Automatic Monitoring

To automatically monitor for funds and withdraw them:

```bash
# Set your private key
set WALLET_PRIVATE_KEY=your_private_key_here

# Run the monitor
python monitor_and_withdraw.py
```

## Secure Alternatives (No Direct Private Key Input)

### 1. Environment Variable Approach
Set your private key once as an environment variable:

```bash
# Windows
set WALLET_PRIVATE_KEY=your_private_key_here

# Linux/Mac
export WALLET_PRIVATE_KEY=your_private_key_here

# Then run withdrawals without entering private key each time
python execute_warehouse_withdrawal.py
```

### 2. Simple Encrypted Key Storage (No Additional Dependencies)
Store your private key in an encrypted file using built-in Python libraries:

```bash
# First, store your private key securely
python simple_secure_withdrawal.py
# Select option 2 for setup

# Then run secure withdrawals
python simple_secure_withdrawal.py
# Select option 1 for withdrawal
```

### 3. Hardware Wallet Integration (Coming Soon)
Future versions will support hardware wallet integration for maximum security.

## Two-Step Withdrawal Process

The system executes a complete two-step withdrawal:

1. **Step 1**: Withdraw from source to Splits WarehouseClient
   - This batches your operations to save on gas costs
   - Funds are held temporarily in the WarehouseClient

2. **Step 2**: Release from WarehouseClient to your wallet
   - This moves the funds from the WarehouseClient to your actual wallet
   - Completes the withdrawal process

## Security Notes

1. **Private Key Storage**: Never share your private key. Use secure storage methods.
2. **Gas Costs**: The two-step process is designed to minimize overall gas costs.
3. **Nonce Management**: The system handles nonce validation automatically.

## Troubleshooting

### No Funds Detected

If no funds are showing in the warehouse:
1. Ensure your address is correctly configured in `warehouse_config.json`
2. Check that funds have been sent to the Splits protocol
3. Verify network connectivity with `python test_warehouse.py`

### Withdrawal Fails

If a withdrawal fails:
1. Check your private key is correct
2. Ensure sufficient ETH for gas fees
3. Verify nonce status with `/warehouse/validate-nonce`

## API Endpoints

- `GET /warehouse/balances` - Check warehouse balances
- `GET /warehouse/status` - Get comprehensive warehouse status
- `POST /warehouse/complete-withdraw` - Execute complete two-step withdrawal
- `POST /warehouse/trigger-withdrawal` - Trigger withdrawal from warehouse to wallet

## Example Response

When a withdrawal is successful, you'll receive a response like:

```json
{
  "success": true,
  "data": {
    "message": "Complete withdrawal successful! Tokens are now in your wallet.",
    "step1": {
      "transaction_hash": "0x...",
      "withdrawn_eth": 19.665,
      "withdrawn_tokens": ["ETH"]
    },
    "step2": {
      "transaction_hash": "0x...",
      "released_eth": 19.665,
      "released_tokens": ["ETH"]
    },
    "final_status": "Tokens now in your wallet",
    "process_time": "~2-5 minutes"
  }
}
```
