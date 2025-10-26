#!/usr/bin/env python3
"""
GitHub Secrets Setup Guide for ClinChat HealthAI RAG
Helps configure repository secrets for production deployment
"""

import webbrowser
import time

def main():
    print("🔐 GitHub Secrets Setup for Production Deployment")
    print("=" * 60)
    
    # Repository URL
    repo_url = "https://github.com/reddygautam98/ClinChat-style-RAG-app"
    secrets_url = f"{repo_url}/settings/secrets/actions"
    
    print(f"📍 Repository: {repo_url}")
    print(f"🔗 Secrets Page: {secrets_url}")
    print()
    
    # Required secrets
    secrets = [
        {
            "name": "AWS_ROLE_ARN",
            "value": "arn:aws:iam::607520774335:role/github-actions-role",
            "description": "AWS IAM role for GitHub Actions deployment"
        },
        {
            "name": "GOOGLE_GEMINI_API_KEY", 
            "value": "[YOUR_GEMINI_API_KEY]",
            "description": "Google Gemini AI API key",
            "get_url": "https://makersuite.google.com/app/apikey"
        },
        {
            "name": "GROQ_API_KEY",
            "value": "[YOUR_GROQ_API_KEY]", 
            "description": "Groq AI API key",
            "get_url": "https://console.groq.com/keys"
        }
    ]
    
    print("📋 REQUIRED SECRETS TO ADD:")
    print("-" * 40)
    
    for i, secret in enumerate(secrets, 1):
        print(f"\n{i}. {secret['name']}")
        print(f"   Description: {secret['description']}")
        if secret['value'] != "[YOUR_GEMINI_API_KEY]" and secret['value'] != "[YOUR_GROQ_API_KEY]":
            print(f"   Value: {secret['value']}")
        else:
            print(f"   Value: {secret['value']} (you need to get this)")
            if 'get_url' in secret:
                print(f"   Get it from: {secret['get_url']}")
    
    print("\n" + "=" * 60)
    print("🚀 STEP-BY-STEP INSTRUCTIONS:")
    print("=" * 60)
    
    instructions = [
        "1. Open the GitHub secrets page in your browser",
        "2. For each secret above, click 'New repository secret'",
        "3. Enter the secret name exactly as shown",
        "4. Enter the secret value (get API keys from the URLs above)",
        "5. Click 'Add secret'",
        "6. Repeat for all 3 secrets"
    ]
    
    for instruction in instructions:
        print(f"   {instruction}")
    
    print("\n🔗 Open GitHub secrets page? (y/n): ", end="")
    response = input().lower().strip()
    
    if response == 'y' or response == 'yes':
        print(f"🌐 Opening {secrets_url}")
        webbrowser.open(secrets_url)
        print("✅ Browser opened - add the secrets manually")
    
    print("\n⏳ After adding secrets, return here and press Enter to continue...")
    input()
    
    print("\n🎉 Great! Your secrets should now be configured.")
    print("📋 NEXT: Trigger deployment by pushing a commit or wait for current pipeline to complete.")
    
    print("\n✨ Your production deployment is ready to activate!")

if __name__ == "__main__":
    main()