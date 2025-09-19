"""
Comprehensive Security Analysis Runner
Combines all security analysis tools for complete assessment
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from ethereum_security_analyzer import EthereumSecurityAnalyzer, SecurityReport
from vulnerability_scanner import AdvancedVulnerabilityScanner, Vulnerability

class ComprehensiveSecurityAnalysis:
    """Complete security analysis combining all tools"""
    
    def __init__(self):
        self.analyzer = EthereumSecurityAnalyzer()
        self.scanner = AdvancedVulnerabilityScanner()
        
    async def run_complete_analysis(self, address: str) -> Dict[str, Any]:
        """Run complete security analysis"""
        print("🔍 COMPREHENSIVE SECURITY ANALYSIS")
        print("=" * 60)
        print(f"🎯 Target Address: {address}")
        print(f"🕒 Analysis Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Basic Security Analysis
        print("📊 Step 1: Basic Security Analysis...")
        security_report = await self.analyzer.analyze_address(address)
        print(f"✅ Found {len(security_report.risks)} security risks")
        
        # Step 2: Advanced Vulnerability Scanning
        print("🔍 Step 2: Advanced Vulnerability Scanning...")
        vulnerabilities = await self.scanner.comprehensive_scan(address)
        vuln_report = self.scanner.generate_vulnerability_report(vulnerabilities, address)
        print(f"✅ Found {len(vulnerabilities)} vulnerabilities")
        
        # Step 3: Combined Analysis
        print("🔄 Step 3: Combining Results...")
        combined_report = self.combine_reports(security_report, vuln_report, address)
        print("✅ Analysis Complete")
        
        return combined_report
    
    def combine_reports(self, security_report: SecurityReport, vuln_report: Dict, address: str) -> Dict[str, Any]:
        """Combine security and vulnerability reports"""
        
        # Calculate combined risk score
        security_score = security_report.vulnerability_score
        vuln_score = vuln_report['risk_score']
        combined_score = min((security_score + vuln_score), 100)
        
        # Determine combined risk level
        if combined_score >= 80:
            combined_risk = "CRITICAL"
        elif combined_score >= 60:
            combined_risk = "HIGH"
        elif combined_score >= 30:
            combined_risk = "MEDIUM"
        else:
            combined_risk = "LOW"
        
        # Combine all risks and vulnerabilities
        all_issues = []
        
        # Add security risks
        for risk in security_report.risks:
            all_issues.append({
                "type": "Security Risk",
                "name": f"{risk.category}: {risk.level}",
                "severity": risk.level,
                "description": risk.description,
                "recommendation": risk.recommendation,
                "evidence": risk.evidence
            })
        
        # Add vulnerabilities
        for vuln in vuln_report['vulnerabilities']:
            all_issues.append({
                "type": "Vulnerability",
                "name": vuln['name'],
                "severity": vuln['severity'],
                "description": vuln['description'],
                "recommendation": vuln['mitigation'],
                "attack_vector": vuln['attack_vector'],
                "affected_assets": vuln['affected_assets']
            })
        
        # Sort issues by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        all_issues.sort(key=lambda x: severity_order.get(x['severity'], 5))
        
        # Generate comprehensive recommendations
        recommendations = self.generate_comprehensive_recommendations(all_issues, security_report, vuln_report)
        
        combined_report = {
            "analysis_metadata": {
                "address": address,
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_type": "Comprehensive Security Analysis",
                "tools_used": ["EthereumSecurityAnalyzer", "AdvancedVulnerabilityScanner"]
            },
            "executive_summary": {
                "overall_risk_level": combined_risk,
                "combined_risk_score": combined_score,
                "total_issues": len(all_issues),
                "critical_issues": len([i for i in all_issues if i['severity'] == 'CRITICAL']),
                "high_issues": len([i for i in all_issues if i['severity'] == 'HIGH']),
                "address_safe_to_use": combined_risk in ["LOW", "MEDIUM"]
            },
            "address_information": {
                "address": security_report.address,
                "balance_eth": security_report.balance_eth,
                "nonce": security_report.nonce,
                "transaction_count": security_report.transaction_patterns.total_transactions
            },
            "detailed_findings": {
                "security_analysis": {
                    "vulnerability_score": security_report.vulnerability_score,
                    "risk_level": security_report.overall_risk_level,
                    "issues_found": len(security_report.risks),
                    "transaction_patterns": {
                        "total_transactions": security_report.transaction_patterns.total_transactions,
                        "suspicious_patterns": security_report.transaction_patterns.suspicious_patterns
                    }
                },
                "vulnerability_scan": {
                    "risk_score": vuln_report['risk_score'],
                    "risk_level": vuln_report['overall_risk_level'],
                    "vulnerabilities_found": vuln_report['total_vulnerabilities'],
                    "severity_breakdown": vuln_report['severity_breakdown']
                }
            },
            "all_issues": all_issues,
            "recommendations": recommendations,
            "next_steps": self.generate_next_steps(combined_risk, all_issues)
        }
        
        return combined_report
    
    def generate_comprehensive_recommendations(self, all_issues: List[Dict], security_report: SecurityReport, vuln_report: Dict) -> List[str]:
        """Generate comprehensive security recommendations"""
        recommendations = []
        
        # Critical issues
        critical_issues = [i for i in all_issues if i['severity'] == 'CRITICAL']
        if critical_issues:
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED:")
            recommendations.append("   • Stop using this address immediately until critical issues are resolved")
            recommendations.append("   • Do not send funds to or from this address")
            recommendations.append("   • Investigate the source of critical vulnerabilities")
        
        # High-priority issues
        high_issues = [i for i in all_issues if i['severity'] == 'HIGH']
        if high_issues:
            recommendations.append("🔴 HIGH PRIORITY:")
            recommendations.append("   • Address high-severity issues before any major transactions")
            recommendations.append("   • Consider migrating to a new address if risks cannot be mitigated")
            recommendations.append("   • Implement additional security measures")
        
        # Transaction patterns
        if security_report.transaction_patterns.suspicious_patterns:
            recommendations.append("📊 TRANSACTION PATTERNS:")
            recommendations.append("   • Review and modify suspicious transaction patterns")
            recommendations.append("   • Implement transaction timing randomization")
            recommendations.append("   • Consider using multiple addresses for different purposes")
        
        # Balance-related recommendations
        if security_report.balance_eth > 1:
            recommendations.append("💰 BALANCE SECURITY:")
            recommendations.append("   • Consider using a hardware wallet for large balances")
            recommendations.append("   • Implement multi-signature security")
            recommendations.append("   • Keep only operational amounts in hot wallets")
        elif security_report.balance_eth < 0.001:
            recommendations.append("⛽ GAS CONSIDERATIONS:")
            recommendations.append("   • Ensure sufficient balance for transaction fees")
            recommendations.append("   • Monitor gas price fluctuations")
        
        # General security recommendations
        recommendations.extend([
            "🛡️ GENERAL SECURITY:",
            "   • Use hardware wallets for long-term storage",
            "   • Enable 2FA on all related accounts",
            "   • Regularly audit address activity",
            "   • Keep software and security tools updated",
            "   • Never share private keys or seed phrases",
            "   • Use checksummed addresses only",
            "   • Verify all transaction details before signing",
            "   • Consider using fresh addresses for new activities"
        ])
        
        return recommendations
    
    def generate_next_steps(self, risk_level: str, all_issues: List[Dict]) -> List[str]:
        """Generate actionable next steps based on risk level"""
        next_steps = []
        
        if risk_level == "CRITICAL":
            next_steps = [
                "1. 🚨 STOP all activity on this address immediately",
                "2. 🔍 Investigate the source of critical vulnerabilities",
                "3. 💰 Move funds to a secure address if possible",
                "4. 🛡️ Implement emergency security measures",
                "5. 📞 Consider consulting security experts",
                "6. 📝 Document the incident for future reference"
            ]
        elif risk_level == "HIGH":
            next_steps = [
                "1. ⚠️ Limit address usage until issues are resolved",
                "2. 🔧 Address high-severity vulnerabilities first",
                "3. 🔄 Consider migrating to a new, secure address",
                "4. 📊 Monitor address activity closely",
                "5. 🛡️ Implement additional security measures",
                "6. 📈 Re-scan after implementing fixes"
            ]
        elif risk_level == "MEDIUM":
            next_steps = [
                "1. 📋 Review and prioritize medium-risk issues",
                "2. 🔧 Implement recommended security improvements",
                "3. 📊 Monitor transaction patterns",
                "4. 🔄 Perform regular security audits",
                "5. 📚 Stay updated on security best practices",
                "6. 🛡️ Consider preventive security measures"
            ]
        else:  # LOW
            next_steps = [
                "1. ✅ Address any remaining low-risk issues",
                "2. 🔄 Maintain regular security monitoring",
                "3. 📚 Stay informed about new threats",
                "4. 🛡️ Continue following security best practices",
                "5. 📈 Perform periodic security reviews",
                "6. 📝 Keep security documentation updated"
            ]
        
        return next_steps
    
    def export_comprehensive_report(self, report: Dict, filename: str = None) -> str:
        """Export comprehensive report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            address_short = report['analysis_metadata']['address'][:8]
            filename = f"comprehensive_security_report_{address_short}_{timestamp}.json"
        
        filepath = os.path.join("security_analysis", filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filepath
    
    def print_executive_summary(self, report: Dict):
        """Print executive summary of the analysis"""
        summary = report['executive_summary']
        metadata = report['analysis_metadata']
        
        print("\n" + "🔍 EXECUTIVE SUMMARY".center(60, "="))
        print(f"📍 Address: {metadata['address']}")
        print(f"🕒 Analysis Date: {metadata['analysis_timestamp']}")
        print(f"⚠️ Overall Risk Level: {summary['overall_risk_level']}")
        print(f"📊 Combined Risk Score: {summary['combined_risk_score']}/100")
        print(f"🔍 Total Issues Found: {summary['total_issues']}")
        print(f"🚨 Critical Issues: {summary['critical_issues']}")
        print(f"🔴 High-Risk Issues: {summary['high_issues']}")
        print(f"✅ Safe to Use: {'YES' if summary['address_safe_to_use'] else 'NO'}")
        print("=" * 60)

async def main():
    """Run comprehensive security analysis"""
    target_address = "0xB5c1baF2E532Bb749a6b2034860178A3558b6e58"
    
    analysis = ComprehensiveSecurityAnalysis()
    
    try:  
        # Run complete analysis
        report = await analysis.run_complete_analysis(target_address)
        
        # Print executive summary
        analysis.print_executive_summary(report)
        
        # Show top issues
        critical_issues = [i for i in report['all_issues'] if i['severity'] == 'CRITICAL']
        high_issues = [i for i in report['all_issues'] if i['severity'] == 'HIGH']
        
        if critical_issues or high_issues:
            print(f"\n🚨 TOP PRIORITY ISSUES:")
            for issue in (critical_issues + high_issues)[:5]:
                print(f"   [{issue['severity']}] {issue['name']}")
                print(f"      {issue['description']}")
        
        # Show recommendations
        print(f"\n💡 KEY RECOMMENDATIONS:")
        for rec in report['recommendations'][:10]:
            print(f"   {rec}")
        
        # Show next steps  
        print(f"\n📋 NEXT STEPS:")
        for step in report['next_steps']:
            print(f"   {step}")
        
        # Export report
        filepath = analysis.export_comprehensive_report(report)
        print(f"\n📄 Comprehensive report exported to: {filepath}")
        
        # Final assessment
        if report['executive_summary']['address_safe_to_use']:
            print(f"\n✅ ASSESSMENT: Address has acceptable risk level")
        else:
            print(f"\n⚠️ ASSESSMENT: Address has significant security concerns")
            
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())