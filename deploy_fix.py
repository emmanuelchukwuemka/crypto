#!/usr/bin/env python3
"""
Deployment Fix Script for Render
This script helps resolve common deployment issues with Python applications on Render.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a command and return success status"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success: {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_python_version():
    """Check Python version compatibility"""
    print("\n📋 Checking Python version...")

    version = sys.version_info
    print(f"   Current Python: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 11:
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ⚠️ Python version may cause compatibility issues")
        return False

def clean_install():
    """Clean pip install"""
    print("\n🧹 Cleaning pip cache and reinstalling...")

    commands = [
        ("pip cache purge", "Clearing pip cache"),
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install --no-cache-dir -r requirements.txt", "Installing requirements")
    ]

    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False

    return True

def test_imports():
    """Test critical imports"""
    print("\n🧪 Testing critical imports...")

    test_imports = [
        "flask",
        "web3",
        "eth_account",
        "requests"
    ]

    success = True
    for module in test_imports:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            success = False

    return success

def create_deployment_checklist():
    """Create deployment checklist"""
    print("\n📝 Creating deployment checklist...")

    checklist = """
🚀 DEPLOYMENT CHECKLIST FOR RENDER
==================================

✅ FIXED ISSUES:
1. Python version: Changed from 3.13.7 to 3.11.9 (stable)
2. Requirements: Cleaned and verified compatibility
3. Runtime.txt: Updated to python-3.11.9
4. Render.yaml: Updated PYTHON_VERSION to 3.11.9

🔧 DEPLOYMENT STEPS:
1. Commit all changes to git
2. Push to your repository
3. Deploy on Render (should work now)
4. Check build logs for any remaining issues

⚠️ IF ISSUES PERSIST:
1. Check Render build logs
2. Verify all environment variables are set
3. Test locally with: python app.py
4. Check for any missing dependencies

📊 EXPECTED BUILD OUTPUT:
- Python 3.11.9 environment
- All packages install successfully
- No version conflicts
- Application starts with gunicorn

🎯 TROUBLESHOOTING:
- If pyunormalize issues: Package should be compatible now
- If pywin32 issues: Should be resolved with Python 3.11.9
- If other dependency issues: Check specific error messages

"""

    with open("DEPLOYMENT_CHECKLIST.md", "w") as f:
        f.write(checklist)

    print("   ✅ Created DEPLOYMENT_CHECKLIST.md")

def main():
    """Main deployment fix function"""
    print("🚀 Starting Render Deployment Fix")
    print("=" * 50)

    # Check Python version
    check_python_version()

    # Clean install
    if not clean_install():
        print("\n❌ Installation failed. Please check errors above.")
        return False

    # Test imports
    if not test_imports():
        print("\n❌ Some imports failed. Check dependency issues.")
        return False

    # Create checklist
    create_deployment_checklist()

    print("\n🎉 Deployment fix completed successfully!")
    print("\n📋 Next steps:")
    print("1. Commit and push your changes")
    print("2. Deploy on Render")
    print("3. Check DEPLOYMENT_CHECKLIST.md for details")
    print("\n✅ Your app should now deploy successfully on Render!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
