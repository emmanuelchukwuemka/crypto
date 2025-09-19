"""
Ethereum Address Security Analyzer
Comprehensive security analysis for wallet addresses
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityRisk:
    """Security risk assessment"""
    category: str
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    recommendation: str
    evidence: List[str]

@dataclass
class TransactionPattern:
    """Transaction pattern analysis"""
    total_transactions: int
    incoming_count: int
    outgoing_count: int
    average_gas_price: float
    max_value: float
    min_value: float
    frequent_addresses: List[str]
    suspicious_patterns: List[str]

@dataclass
class SecurityReport:
    """Complete security assessment report"""
    address: str
    analysis_timestamp: str
    overall_risk_level: str
    balance_eth: float
    nonce: int
    risks: List[SecurityRisk]
    transaction_patterns: TransactionPattern
    recommendations: List[str]
    vulnerability_score: int  # 0-100

class EthereumSecurityAnalyzer:
    """Comprehensive Ethereum address security analyzer"""
    
    def __init__(self, rpc_endpoint: str = "https://ethereum-rpc.publicnode.com"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        self.etherscan_api = "https://api.etherscan.io/api"
        self.risks = []
        
    def validate_connection(self) -> bool:
        """Validate blockchain connection"""
        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def analyze_address_format(self, address: str) -> List[SecurityRisk]:
        """Analyze address format for potential issues"""
        risks = []
        
        try:
            # Check address format
            if not address.startswith('0x'):
                risks.append(SecurityRisk(
                    category="Address Format",
                    level="HIGH",
                    description="Address doesn't start with 0x prefix",
                    recommendation="Verify address format before use",
                    evidence=[f"Address: {address}"]
                ))
            
            # Check address length
            if len(address) != 42:
                risks.append(SecurityRisk(
                    category="Address Format",
                    level="CRITICAL",
                    description="Invalid address length",
                    recommendation="Use only valid 42-character addresses",
                    evidence=[f"Length: {len(address)} (expected: 42)"]
                ))
            
            # Check checksum
            try:
                checksummed = Web3.to_checksum_address(address)
                if address != checksummed:
                    risks.append(SecurityRisk(
                        category="Address Format",
                        level="MEDIUM",
                        description="Address is not checksummed",
                        recommendation="Always use checksummed addresses",
                        evidence=[f"Original: {address}", f"Checksummed: {checksummed}"]
                    ))
            except Exception as e:
                risks.append(SecurityRisk(
                    category="Address Format",
                    level="CRITICAL",
                    description="Invalid address format",
                    recommendation="Verify address is valid Ethereum address",
                    evidence=[f"Error: {str(e)}"]
                ))
                
        except Exception as e:
            risks.append(SecurityRisk(
                category="Address Format",
                level="HIGH",
                description="Address validation failed",
                recommendation="Manually verify address format",
                evidence=[f"Error: {str(e)}"]
            ))
        
        return risks
    
    def analyze_balance_security(self, address: str) -> List[SecurityRisk]:
        """Analyze balance-related security risks"""
        risks = []
        
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = float(Web3.from_wei(balance_wei, 'ether'))
            
            # Low balance risks
            if balance_eth < 0.001:
                risks.append(SecurityRisk(
                    category="Balance Security",
                    level="HIGH",
                    description="Very low ETH balance for gas fees",
                    recommendation="Maintain minimum balance for transaction fees",
                    evidence=[f"Balance: {balance_eth} ETH"]
                ))
            
            # High balance risks
            if balance_eth > 100:
                risks.append(SecurityRisk(
                    category="Balance Security",
                    level="MEDIUM",
                    description="High balance may attract attackers",
                    recommendation="Consider using multi-sig or hardware wallet",
                    evidence=[f"Balance: {balance_eth} ETH"]
                ))
            
            # Dust balance pattern
            if 0 < balance_eth < 0.0001:
                risks.append(SecurityRisk(
                    category="Balance Security",
                    level="LOW",
                    description="Dust balance may indicate testing or spam",
                    recommendation="Monitor for unusual activity",
                    evidence=[f"Balance: {balance_eth} ETH"]
                ))
                
        except Exception as e:
            risks.append(SecurityRisk(
                category="Balance Security",
                level="MEDIUM",
                description="Could not retrieve balance information",
                recommendation="Verify network connectivity and address",
                evidence=[f"Error: {str(e)}"]
            ))
        
        return risks
    
    def analyze_nonce_security(self, address: str) -> List[SecurityRisk]:
        """Analyze nonce-related security issues"""
        risks = []
        
        try:
            nonce = self.w3.eth.get_transaction_count(address, 'latest')
            pending_nonce = self.w3.eth.get_transaction_count(address, 'pending')
            
            # Nonce gap analysis
            if pending_nonce > nonce:
                risks.append(SecurityRisk(
                    category="Nonce Security",
                    level="MEDIUM",
                    description="Pending transactions detected",
                    recommendation="Monitor pending transactions for completion",
                    evidence=[f"Current nonce: {nonce}", f"Pending nonce: {pending_nonce}"]
                ))
            
            # High nonce may indicate high activity
            if nonce > 1000:
                risks.append(SecurityRisk(
                    category="Nonce Security",
                    level="LOW",
                    description="High transaction count may indicate automated activity",
                    recommendation="Review transaction patterns for legitimacy",
                    evidence=[f"Transaction count: {nonce}"]
                ))
                
        except Exception as e:
            risks.append(SecurityRisk(
                category="Nonce Security",
                level="MEDIUM",
                description="Could not retrieve nonce information",
                recommendation="Verify network connectivity",
                evidence=[f"Error: {str(e)}"]
            ))
        
        return risks
    
    def get_transaction_history(self, address: str, limit: int = 100) -> List[Dict]:
        """Get transaction history using Etherscan API"""
        try:
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': limit,
                'sort': 'desc'
            }
            
            response = requests.get(self.etherscan_api, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    return data.get('result', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Transaction history fetch failed: {e}")
            return []
    
    def analyze_transaction_patterns(self, address: str) -> TransactionPattern:
        """Analyze transaction patterns for security risks"""
        transactions = self.get_transaction_history(address)
        
        if not transactions:
            return TransactionPattern(
                total_transactions=0,
                incoming_count=0,
                outgoing_count=0,
                average_gas_price=0,
                max_value=0,
                min_value=0,
                frequent_addresses=[],
                suspicious_patterns=["No transaction history available"]
            )
        
        # Analyze patterns
        incoming = [tx for tx in transactions if tx['to'].lower() == address.lower()]
        outgoing = [tx for tx in transactions if tx['from'].lower() == address.lower()]
        
        values = [float(Web3.from_wei(int(tx['value']), 'ether')) for tx in transactions if tx['value'] != '0']
        gas_prices = [int(tx['gasPrice']) for tx in transactions if 'gasPrice' in tx]
        
        # Find frequent addresses
        address_counts = {}
        for tx in transactions:
            other_addr = tx['to'] if tx['from'].lower() == address.lower() else tx['from']
            address_counts[other_addr] = address_counts.get(other_addr, 0) + 1
        
        frequent_addresses = sorted(address_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Identify suspicious patterns
        suspicious_patterns = []
        
        # Pattern: Many small transactions
        small_tx_count = len([v for v in values if 0 < v < 0.01])
        if small_tx_count > 20:
            suspicious_patterns.append(f"High number of small transactions: {small_tx_count}")
        
        # Pattern: Rapid transactions
        if len(transactions) > 50:
            timestamps = [int(tx['timeStamp']) for tx in transactions[:10]]
            if len(set(timestamps)) < 3:  # Many transactions in same timeframe
                suspicious_patterns.append("Rapid transaction pattern detected")
        
        # Pattern: Round number transactions
        round_values = [v for v in values if v in [0.1, 0.5, 1.0, 5.0, 10.0]]
        if len(round_values) > 5:
            suspicious_patterns.append("Many round-number transactions")
        
        return TransactionPattern(
            total_transactions=len(transactions),
            incoming_count=len(incoming),
            outgoing_count=len(outgoing),
            average_gas_price=sum(gas_prices) / len(gas_prices) if gas_prices else 0,
            max_value=max(values) if values else 0,
            min_value=min([v for v in values if v > 0]) if values else 0,
            frequent_addresses=[addr for addr, count in frequent_addresses],
            suspicious_patterns=suspicious_patterns
        )
    
    def analyze_contract_interactions(self, address: str) -> List[SecurityRisk]:
        """Analyze smart contract interaction risks"""
        risks = []
        transactions = self.get_transaction_history(address)
        
        contract_interactions = []
        for tx in transactions:
            if tx.get('input', '0x') != '0x':  # Has input data
                contract_interactions.append(tx)
        
        if contract_interactions:
            risks.append(SecurityRisk(
                category="Contract Security",
                level="MEDIUM",
                description="Address has interacted with smart contracts",
                recommendation="Verify contract security before interactions",
                evidence=[f"Contract interactions: {len(contract_interactions)}"]
            ))
            
            # Check for failed transactions
            failed_tx = [tx for tx in contract_interactions if tx.get('isError') == '1']
            if failed_tx:
                risks.append(SecurityRisk(
                    category="Contract Security",
                    level="HIGH",
                    description="Failed contract interactions detected",
                    recommendation="Review failed transactions for potential issues",
                    evidence=[f"Failed transactions: {len(failed_tx)}"]
                ))
        
        return risks
    
    def check_known_risks(self, address: str) -> List[SecurityRisk]:
        """Check against known security risks"""
        risks = []
        
        # Check if address is a known exchange/service
        known_services = {
            "0xdac17f958d2ee523a2206206994597c13d831ec7": "Tether (USDT) Contract",
            "0xa0b86a33e6bcc14f4b3b0d5a9b0f1a6d3b4e5c6d": "Example Exchange",
        }
        
        if address.lower() in [k.lower() for k in known_services.keys()]:
            risks.append(SecurityRisk(
                category="Address Type",
                level="LOW",
                description="Address is a known service/contract",
                recommendation="Verify legitimacy of service",
                evidence=[f"Identified as: {known_services.get(address.lower(), 'Unknown service')}"]
            ))
        
        # Check address age
        try:
            transactions = self.get_transaction_history(address, limit=1)
            if transactions:
                first_tx_time = int(transactions[-1]['timeStamp'])
                current_time = int(time.time())
                age_days = (current_time - first_tx_time) / (24 * 3600)
                
                if age_days < 30:
                    risks.append(SecurityRisk(
                        category="Address Age",
                        level="MEDIUM",
                        description="Very new address (less than 30 days)",
                        recommendation="Exercise caution with new addresses",
                        evidence=[f"Address age: {age_days:.1f} days"]
                    ))
        except Exception as e:
            logger.warning(f"Could not determine address age: {e}")
        
        return risks
    
    def calculate_vulnerability_score(self, all_risks: List[SecurityRisk]) -> int:
        """Calculate overall vulnerability score (0-100)"""
        score = 0
        
        for risk in all_risks:
            if risk.level == "LOW":
                score += 10
            elif risk.level == "MEDIUM":
                score += 25
            elif risk.level == "HIGH":
                score += 50
            elif risk.level == "CRITICAL":
                score += 100
        
        return min(score, 100)  # Cap at 100
    
    def generate_recommendations(self, all_risks: List[SecurityRisk], patterns: TransactionPattern) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Based on risk levels
        critical_risks = [r for r in all_risks if r.level == "CRITICAL"]
        high_risks = [r for r in all_risks if r.level == "HIGH"]
        
        if critical_risks:
            recommendations.append("🚨 URGENT: Address critical security issues immediately")
            recommendations.append("⚠️ Do not use this address until critical issues are resolved")
        
        if high_risks:
            recommendations.append("🔴 Address high-risk issues before proceeding")
        
        # Transaction pattern recommendations
        if patterns.total_transactions > 100:
            recommendations.append("📊 Consider using fresh addresses for new activities")
        
        if len(patterns.suspicious_patterns) > 0:
            recommendations.append("🔍 Investigate suspicious transaction patterns")
        
        # General recommendations
        recommendations.extend([
            "🔐 Always use hardware wallets for large amounts",
            "✅ Verify all addresses with checksums",
            "📝 Keep detailed transaction records",
            "🛡️ Monitor address activity regularly",
            "🔒 Never share private keys or seed phrases",
            "💰 Use multi-signature wallets for business use"
        ])
        
        return recommendations
    
    async def analyze_address(self, address: str) -> SecurityReport:
        """Perform comprehensive security analysis"""
        logger.info(f"Starting security analysis for address: {address}")
        
        if not self.validate_connection():
            raise Exception("Cannot connect to Ethereum network")
        
        # Perform all security checks
        all_risks = []
        
        # Address format analysis
        all_risks.extend(self.analyze_address_format(address))
        
        # Balance security
        all_risks.extend(self.analyze_balance_security(address))
        
        # Nonce security
        all_risks.extend(self.analyze_nonce_security(address))
        
        # Contract interaction risks
        all_risks.extend(self.analyze_contract_interactions(address))
        
        # Known risks
        all_risks.extend(self.check_known_risks(address))
        
        # Transaction pattern analysis
        patterns = self.analyze_transaction_patterns(address)
        
        # Get current state
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = float(Web3.from_wei(balance_wei, 'ether'))
            nonce = self.w3.eth.get_transaction_count(address)
        except Exception as e:
            balance_eth = 0
            nonce = 0
            logger.error(f"Could not get current state: {e}")
        
        # Calculate vulnerability score
        vulnerability_score = self.calculate_vulnerability_score(all_risks)
        
        # Determine overall risk level
        if vulnerability_score >= 80:
            overall_risk = "CRITICAL"
        elif vulnerability_score >= 50:
            overall_risk = "HIGH"
        elif vulnerability_score >= 25:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Generate recommendations
        recommendations = self.generate_recommendations(all_risks, patterns)
        
        return SecurityReport(
            address=address,
            analysis_timestamp=datetime.now().isoformat(),
            overall_risk_level=overall_risk,
            balance_eth=balance_eth,
            nonce=nonce,
            risks=all_risks,
            transaction_patterns=patterns,
            recommendations=recommendations,
            vulnerability_score=vulnerability_score
        )
    
    def export_report(self, report: SecurityReport, filename: str = None) -> str:
        """Export security report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_report_{report.address[:8]}_{timestamp}.json"
        
        # Convert dataclasses to dict
        report_dict = asdict(report)
        
        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        return filename

async def main():
    """Example usage"""
    # Target address from configuration
    target_address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"
    
    print("🔍 Ethereum Address Security Analyzer")
    print("=" * 50)
    print(f"🎯 Analyzing address: {target_address}")
    print()
    
    analyzer = EthereumSecurityAnalyzer()
    
    try:
        # Perform comprehensive analysis
        report = await analyzer.analyze_address(target_address)
        
        # Display results
        print(f"📊 SECURITY ANALYSIS REPORT")
        print(f"🕒 Analysis Time: {report.analysis_timestamp}")
        print(f"📍 Address: {report.address}")
        print(f"💰 Balance: {report.balance_eth} ETH")
        print(f"🔢 Nonce: {report.nonce}")
        print(f"⚠️ Overall Risk Level: {report.overall_risk_level}")
        print(f"📈 Vulnerability Score: {report.vulnerability_score}/100")
        print()
        
        # Show risks
        if report.risks:
            print("🚨 IDENTIFIED RISKS:")
            for i, risk in enumerate(report.risks, 1):
                print(f"{i}. [{risk.level}] {risk.category}")
                print(f"   Description: {risk.description}")
                print(f"   Recommendation: {risk.recommendation}")
                if risk.evidence:
                    print(f"   Evidence: {', '.join(risk.evidence)}")
                print()
        
        # Show transaction patterns
        patterns = report.transaction_patterns
        print("📊 TRANSACTION PATTERNS:")
        print(f"   Total Transactions: {patterns.total_transactions}")
        print(f"   Incoming: {patterns.incoming_count}")
        print(f"   Outgoing: {patterns.outgoing_count}")
        print(f"   Max Value: {patterns.max_value} ETH")
        if patterns.suspicious_patterns:
            print(f"   Suspicious Patterns: {len(patterns.suspicious_patterns)}")
            for pattern in patterns.suspicious_patterns:
                print(f"     - {pattern}")
        print()
        
        # Show recommendations
        print("💡 SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i:2d}. {rec}")
        print()
        
        # Export report
        filename = analyzer.export_report(report)
        print(f"📄 Report exported to: {filename}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())