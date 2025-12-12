#!/usr/bin/env python3
"""
Quick test script to verify the Agent Council web app setup.
"""

import os
import sys
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
    all_good &= check_file("agentcouncil.py", "CLI orchestrator")
    all_good &= check_file("requirements.txt", "Core requirements")
    
    # Check for .env or .env.example
    if Path(".env").exists():
        print("✅ .env file found")
    elif Path(".env.example").exists():
        print("⚠️  .env not found, but .env.example exists (copy it to .env to start)")
        # Don't fail the check just because .env is missing in a fresh clone, 
        # but warn the user.
    else:
        print("❌ .env AND .env.example - NOT FOUND")
        all_good = False
    
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
    
    if Path("web-ui/.env").exists():
        print("✅ Frontend .env found")
    elif Path("web-ui/.env.example").exists():
        print("⚠️  web-ui/.env not found, but .env.example exists")
    else:
        print("❌ web-ui/.env AND .env.example - NOT FOUND")
        # Optional for now, as Vite has defaults
    
    # Check documentation
    print("\n📚 Checking Documentation:")
    all_good &= check_file("docs/RUNBOOK.md", "Runbook")
    all_good &= check_file("docs/ARCHITECTURE.md", "Architecture doc")
    
    # Check Python packages
    print("\n🐍 Checking Python Dependencies:")
    all_good &= check_python_package("openai")
    all_good &= check_python_package("agents")
    all_good &= check_python_package("fastapi")
    all_good &= check_python_package("uvicorn")
    all_good &= check_python_package("rich")
    
    # Check if .env has API key (if it exists)
    print("\n🔑 Checking API Key:")
    if Path(".env").exists():
        with open(".env") as f:
            content = f.read()
            if "OPENAI_API_KEY" in content and "sk-" in content:
                print("✅ OPENAI_API_KEY found in .env")
            else:
                print("⚠️  .env exists but API key may not be set correctly")
                # Warning only
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("\n✨ Setup looks good! You're ready to start the web app.")
        print("\nTo start:")
        print("  python agentcouncil.py start")
        print("\nThen open: http://localhost:5173")
        return 0
    else:
        print("\n⚠️  Some issues found. Please fix them before starting.")
        print("\nFor help, see:")
        print("  - docs/RUNBOOK.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
