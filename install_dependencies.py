#!/usr/bin/env python3
"""
Robust dependency installer for ClinChat HealthAI RAG application
Handles build tools issues and provides fallbacks for problematic packages
"""

import subprocess
import sys
import os
from typing import List, Tuple

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Run a command and return (success, output)"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_package(package: str) -> bool:
    """Try to install a single package with error handling"""
    print(f"Installing {package}...")
    success, output = run_command([sys.executable, "-m", "pip", "install", package])
    
    if success:
        print(f"✅ {package} installed successfully")
        return True
    else:
        print(f"❌ Failed to install {package}: {output}")
        return False

def install_with_fallbacks():
    """Install dependencies with fallback strategies for problematic packages"""
    
    # Core packages that should install without issues
    core_packages = [
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0", 
        "python-multipart>=0.0.6",
        "pydantic>=2.5.0",
        "redis>=5.0.1",
        "pandas>=2.1.3",
        "python-dotenv>=1.0.0",
        "boto3>=1.34.0",
        "matplotlib>=3.8.2",
        "seaborn>=0.13.0",
        "scikit-learn>=1.3.2",
        "scipy>=1.11.4",
        "plotly>=5.17.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "httpx>=0.25.2",
        "pytest-mock>=3.12.0",
        "psutil>=5.9.6",
        "prometheus-client>=0.19.0",
        "structlog>=23.2.0",
        "nltk>=3.8.1",
        "textblob>=0.17.1",
        "fuzzywuzzy>=0.18.0"
    ]
    
    # Packages that might need compilation - try with --only-binary first
    binary_packages = [
        "spacy>=3.7.2",
        "transformers>=4.36.2", 
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4"
    ]
    
    # Packages with alternative fallbacks
    fallback_packages = {
        "python-levenshtein>=0.23.0": "fuzzywuzzy[speedup]>=0.18.0",
        "rouge-score>=0.1.2": "nltk>=3.8.1",  # NLTK has ROUGE implementations
        "bert-score>=0.3.13": "transformers>=4.36.2"  # Can calculate manually if needed
    }
    
    print("🚀 Installing core dependencies...")
    failed_core = []
    for package in core_packages:
        if not install_package(package):
            failed_core.append(package)
    
    print("\n🔧 Installing binary packages (with pre-compiled wheels)...")
    failed_binary = []
    for package in binary_packages:
        # Try with --only-binary first to avoid compilation
        success, output = run_command([
            sys.executable, "-m", "pip", "install", 
            "--only-binary=all", package
        ])
        
        if success:
            print(f"✅ {package} installed (binary)")
        else:
            # Fallback to regular install
            print(f"⚠️  Binary install failed for {package}, trying regular install...")
            if not install_package(package):
                failed_binary.append(package)
    
    print("\n🔄 Installing packages with fallbacks...")
    failed_fallback = []
    for package, fallback in fallback_packages.items():
        if not install_package(package):
            print(f"🔄 Trying fallback for {package} -> {fallback}")
            if not install_package(fallback):
                failed_fallback.append(package)
    
    # Install remaining requirements
    print("\n📦 Installing remaining requirements...")
    remaining_success, _ = run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--no-deps"
    ])
    
    # Summary
    print("\n" + "="*60)
    print("📊 INSTALLATION SUMMARY")
    print("="*60)
    
    if failed_core:
        print(f"❌ Failed core packages: {failed_core}")
    else:
        print("✅ All core packages installed successfully")
    
    if failed_binary:
        print(f"⚠️  Failed binary packages: {failed_binary}")
        print("   These might need manual compilation or alternative approaches")
    
    if failed_fallback:
        print(f"⚠️  Failed fallback packages: {failed_fallback}")
    
    if not (failed_core or failed_binary or failed_fallback):
        print("🎉 ALL DEPENDENCIES INSTALLED SUCCESSFULLY!")
        return True
    else:
        print("⚠️  Some packages failed - application may still work with reduced functionality")
        return False

if __name__ == "__main__":
    print("🔧 ClinChat HealthAI RAG - Dependency Installer")
    print("=" * 50)
    
    # Upgrade pip first
    print("📦 Upgrading pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    success = install_with_fallbacks()
    
    if success:
        print("\n🚀 Ready to run ClinChat HealthAI RAG application!")
        sys.exit(0)
    else:
        print("\n⚠️  Installation completed with some issues. Check summary above.")
        sys.exit(1)