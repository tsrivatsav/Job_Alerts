#!/usr/bin/env python3
"""
Complete setup script for the Job Scraper system.
Run this once to set up everything.
"""

import subprocess
import sys
import time

def run_script(script_name):
    """Run a Python script"""
    print(f"\n{'='*50}")
    print(f"Running: {script_name}")
    print('='*50)
    result = subprocess.run([sys.executable, script_name], capture_output=False)
    return result.returncode == 0

def run_shell(script_name):
    """Run a shell script"""
    print(f"\n{'='*50}")
    print(f"Running: {script_name}")
    print('='*50)
    result = subprocess.run(['bash', script_name], capture_output=False)
    return result.returncode == 0

def main():
    print("🚀 Starting Job Scraper Setup")
    print("="*50)
    
    # Step 1: Create DynamoDB tables
    if not run_script('create_tables.py'):
        print("❌ Failed to create tables")
        return
    
    # Step 2: Create SNS topic
    if not run_script('create_sns.py'):
        print("❌ Failed to create SNS topic")
        return
    
    print("\n⚠️  IMPORTANT: Check your email and confirm the SNS subscription!")
    input("Press Enter after confirming the subscription...")
    
    # Step 3: Create IAM roles
    if not run_script('create_iam_roles.py'):
        print("❌ Failed to create IAM roles")
        return
    
    # Wait for IAM roles to propagate
    print("\n⏳ Waiting 15 seconds for IAM roles to propagate...")
    time.sleep(15)
    
    # Step 4: Deploy Lambda functions
    if not run_shell('deploy_lambdas.sh'):
        print("❌ Failed to deploy Lambdas")
        return
    
    # Step 5: Create EventBridge schedule
    if not run_script('create_eventbridge.py'):
        print("❌ Failed to create EventBridge schedule")
        return
    
    # Step 6: Seed initial companies
    print("\n" + "="*50)
    print("Do you want to seed initial company data? (y/n)")
    if input().lower() == 'y':
        run_script('seed_companies.py')
    
    print("\n" + "="*50)
    print("🎉 Setup Complete!")
    print("="*50)
    print("""
Next steps:
1. Edit lambdas/scraper/lambda_function.py to add your scraping logic
2. Update scripts/seed_companies.py with your companies
3. Run: python scripts/seed_companies.py
4. Test manually: python scripts/test_manual.py
5. The system will run automatically daily at 9 AM UTC
    """)

if __name__ == '__main__':
    main()