#!/usr/bin/env python3
"""
Quick test script to verify the Agent Council web app setup.
"""

import sys
import os
from pathlib import Path

def check_file(path, description):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        print(f"✅ Python package: {package_name}")
        return True
    except ImportError:
        print(f"❌ Python package: {package_name} - NOT INSTALLED")
        return False

def main():
    # Change working directory to project root
    os.chdir(Path(__file__).resolve().parent.parent)

    print("🔍 Agent Council Web App - Setup Verification\n")
    print("=" * 60)
    
    all_good = True
    
    # Check core files
    print("\n📁 Checking Core Files:")
    all_good &= check_file("agentcouncil.py", "CLI script")
    all_good &= check_file("requirements.txt", "Core requirements")
    all_good &= check_file(".env", "Environment file with API key")
    
    # Check web backend files
    print("\n🌐 Checking Web Backend:")
    all_good &= check_file("requirements-web.txt", "Web requirements")
    all_good &= check_file("run_api.py", "API startup script")
    all_good &= check_file("src/web/api.py", "FastAPI application")
    all_good &= check_file("src/web/services.py", "Service layer")
    all_good &= check_file("src/web/session_manager.py", "Session manager")
    
    # Check frontend files
    print("\n⚛️  Checking Frontend:")
    all_good &= check_file("web-ui/package.json", "NPM package file")
    all_good &= check_file("web-ui/src/App.jsx", "Main app component")
    all_good &= check_file("web-ui/src/api.js", "API client")
    all_good &= check_file("web-ui/.env", "Frontend environment")
    
    # Check startup scripts
    print("\n🚀 Checking Startup Scripts:")
    all_good &= check_file("start_backend.sh", "Backend startup script")
    all_good &= check_file("start_frontend.sh", "Frontend startup script")
    
    # Check Python packages
    print("\n🐍 Checking Python Dependencies:")
    all_good &= check_python_package("openai")
    all_good &= check_python_package("agents")
    all_good &= check_python_package("fastapi")
    all_good &= check_python_package("uvicorn")
    all_good &= check_python_package("rich")
    
    # Check if .env has API key
    print("\n🔑 Checking API Key:")
    if Path(".env").exists():
        with open(".env", "r") as f:
            content = f.read()
            if "OPENAI_API_KEY" in content and "sk-" in content:
                print("✅ OPENAI_API_KEY found in .env")
            else:
                print("⚠️  .env exists but API key may not be set correctly")
                all_good = False
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("\n✨ Setup looks good! You're ready to start the web app.")
        print("\nTo start:")
        print("  Terminal 1: ./start_backend.sh")
        print("  Terminal 2: ./start_frontend.sh")
        print("\nThen open: http://localhost:5173")
        return 0
    else:
        print("\n⚠️  Some issues found. Please fix them before starting.")
        print("\nFor help, see:")
        print("  - START_WEB_APP.md")
        print("  - README_WEB.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
