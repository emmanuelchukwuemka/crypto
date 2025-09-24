# 🚀 Ethereum Withdrawal API with Warehouse Integration

**Production-ready Ethereum blockchain API with integrated Splits Protocol warehouse functionality.**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## ✨ Features

- ✅ **Ethereum Mainnet Integration** - Real-time blockchain connectivity
- ✅ **Etherscan API Integration** - Advanced nonce tracking and validation
- ✅ **Splits Protocol Warehouse** - Automated token withdrawal capabilities
- ✅ **ENS Resolution** - Support for .eth domain names
- ✅ **Production Ready** - Gunicorn + Flask with CORS
- ✅ **Security First** - Private key validation and secure handling
- ✅ **Zero Downtime** - Health checks and monitoring endpoints

## 🔧 API Endpoints

### Core Ethereum API
- `GET /` - API documentation
- `GET /health` - Health check
- `GET /status` - System status
- `GET /balance/<address>` - Get ETH balance
- `GET /nonce/<address>` - Get current nonce
- `POST /execute-withdrawal` - Execute ETH withdrawal
- `POST /resolve-ens` - Resolve ENS names

### Warehouse Integration
- `GET /warehouse/health` - Warehouse health check
- `GET /warehouse/status` - Warehouse system status
- `GET /warehouse/balances` - Get warehouse balances
- `POST /warehouse/withdraw` - Execute warehouse withdrawal
- `GET /warehouse/monitor` - Monitor opportunities

## 🚀 Deploy to Render

### One-Click Deploy
1. Click the "Deploy to Render" button above
2. Connect your GitHub repository
3. Render will auto-detect `render.yaml` configuration
4. Your API will be live in minutes!

### Manual Deploy
1. Fork this repository
2. Connect to Render.com
3. Select "Web Service"
4. Your app will be deployed automatically

## 🔐 Environment Variables

All sensitive data is configured via environment variables:

```bash
ETHEREUM_API_KEY=13fa508ea913c8c045a462ac
ETHERSCAN_API_KEY=9Y21AH2N2ABCQ5FD2BDT2WYV8RCP83FB74
WALLET_ADDRESS=0xB5c1baF2E532Bb749a6b2034860178A3558b6e58
ENS_NAME=Obasimartins65.eth
CHAIN_ID=1
RPC_ENDPOINT=https://ethereum-rpc.publicnode.com
```

## 🛠️ Troubleshooting Etherscan Integration Issues

If you're experiencing issues with Etherscan integration (showing as "not running"), follow these steps:

### 1. Diagnose the Issue
Run the diagnostic script to identify connection problems:
```bash
python diagnose_ethereum_connection.py
```

### 2. Common Issues and Solutions

#### Ethereum Connection Failure
- **Issue**: `connected: false` in status endpoint
- **Solution**: 
  1. Check network connectivity from your deployment environment
  2. Try different RPC endpoints (Infura, Alchemy, etc.)
  3. Verify firewall settings allow outbound HTTPS connections

#### Etherscan API Key Issues
- **Issue**: Etherscan API key not configured or invalid
- **Solution**:
  1. Verify `ETHERSCAN_API_KEY` environment variable is set
  2. Check that your API key is valid on Etherscan.io
  3. Ensure you haven't exceeded daily request limits

#### Render Deployment Issues
- **Issue**: Connection works locally but fails on Render
- **Solution**:
  1. Check Render environment variables match your local config
  2. Verify Render can access external RPC endpoints
  3. Consider using dedicated node services (Infura/Alchemy)

### 3. Fix Etherscan Integration
Run the fix script to automatically resolve common issues:
```bash
python fix_etherscan_integration.py
```

## 🛡️ Security Features

- **Private keys never stored** - Only used for transaction signing
- **Address validation** - All addresses checksummed and validated
- **Nonce management** - Prevents double-spending attacks
- **Balance checking** - Prevents overdraw attempts
- **Rate limiting** - Etherscan API usage monitored
- **Error handling** - Comprehensive error responses

## 📊 Production Monitoring

- **Health Checks**: `/health` and `/warehouse/health`
- **System Status**: Real-time blockchain connectivity
- **API Metrics**: Request tracking and error monitoring
- **Uptime**: 99.9%+ availability target

## 🎯 Supported Networks

- **Ethereum Mainnet** (Chain ID: 1)
- **ENS Resolution** (.eth domains)
- **Splits Protocol** (Warehouse integration)

## 💡 Usage Examples

### Check Balance
```bash
curl https://your-app.onrender.com/balance/0xB5c1baF2E532Bb749a6b2034860178A3558b6e58
```

### Execute Withdrawal
```bash
curl -X POST https://your-app.onrender.com/execute-withdrawal \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58",
    "to_address": "0x...",
    "amount_eth": 0.001,
    "private_key": "your_private_key"
  }'
```

### Check Warehouse Status
```bash
curl https://your-app.onrender.com/warehouse/status
```

## 🔄 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Server will start on http://localhost:5000
```

## 📈 Performance

- **Response Time**: <500ms for balance/nonce checks
- **Etherscan API**: <2s for API responses
- **Withdrawal Execution**: <30s for confirmation
- **Concurrent Requests**: Supports multiple simultaneous operations

## 🆘 Support

For issues or questions:
1. Check the API documentation at `/`
2. Monitor health endpoints
3. Review logs for error details
4. Run diagnostic scripts to identify connection issues

---

**Built with ❤️ for the Ethereum ecosystem**