#!/usr/bin/env python3
"""
Deploy Lambda functions to AWS.
Cross-platform Python replacement for deploy_lambdas.sh
"""

import boto3
from botocore.exceptions import ClientError
import subprocess
import os
import shutil
import zipfile
import sys

# Configuration
REGION = 'us-east-1'

# Get AWS account ID
sts = boto3.client('sts', region_name=REGION)
ACCOUNT_ID = sts.get_caller_identity()['Account']
SNS_TOPIC_ARN = f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:job-scraper-notifications"

lambda_client = boto3.client('lambda', region_name=REGION)

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LAMBDAS_DIR = os.path.join(PROJECT_ROOT, 'lambdas')
DIST_DIR = os.path.join(PROJECT_ROOT, 'dist')


def create_zip(source_dir: str, output_path: str, include_scrapers: bool = False):
    """Create a zip file from a directory."""
    package_dir = os.path.join(source_dir, 'package')
    
    # Clean up any existing package directory
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Install dependencies
    requirements_file = os.path.join(source_dir, 'requirements.txt')
    if os.path.exists(requirements_file):
        print(f"  Installing dependencies from {requirements_file}...")
        
        # Install Linux-compatible packages for Lambda
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '-r', requirements_file,
            '-t', package_dir,
            '--platform', 'manylinux2014_x86_64',
            '--implementation', 'cp',
            '--python-version', '3.9',
            '--only-binary=:all:',
            '--upgrade',
            '--quiet'
        ], capture_output=True, text=True)
        
        # If platform-specific install fails, try without binary constraint
        # (for pure Python packages)
        if result.returncode != 0:
            print(f"  Retrying with fallback for pure Python packages...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                '-r', requirements_file,
                '-t', package_dir,
                '--platform', 'manylinux2014_x86_64',
                '--implementation', 'cp',
                '--python-version', '3.9',
                '--quiet'
            ], check=False)
            
            # Final fallback: install without platform constraints
            # (pure Python packages will work cross-platform)
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                '-r', requirements_file,
                '-t', package_dir,
                '--upgrade',
                '--quiet'
            ], check=True)
            
            # Remove Windows-specific files
            print(f"  Cleaning up Windows-specific files...")
            cleanup_windows_files(package_dir)
    
    # Copy lambda function
    lambda_file = os.path.join(source_dir, 'lambda_function.py')
    if os.path.exists(lambda_file):
        shutil.copy(lambda_file, package_dir)
    
    # Copy scrapers directory if needed (for scraper lambda)
    if include_scrapers:
        scrapers_src = os.path.join(source_dir, 'scrapers')
        scrapers_dst = os.path.join(package_dir, 'scrapers')
        if os.path.exists(scrapers_src):
            print(f"  Copying scrapers directory...")
            shutil.copytree(scrapers_src, scrapers_dst)
    
    # Create zip
    print(f"  Creating zip file: {output_path}")
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Clean up
    shutil.rmtree(package_dir)
    
    return output_path


def cleanup_windows_files(directory: str):
    """Remove Windows-specific compiled files."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Remove Windows .pyd files and other platform-specific files
            if file.endswith('.pyd') or 'win' in file.lower() and file.endswith('.whl'):
                file_path = os.path.join(root, file)
                print(f"    Removing: {file}")
                os.remove(file_path)


def function_exists(function_name: str) -> bool:
    """Check if a Lambda function exists."""
    try:
        lambda_client.get_function(FunctionName=function_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        raise


def deploy_lambda(function_name: str, zip_path: str, role_name: str, 
                  handler: str, timeout: int, memory: int, env_vars: dict):
    """Create or update a Lambda function."""
    role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
    
    # Read zip file
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()
    
    if function_exists(function_name):
        print(f"  Function exists, updating code...")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_bytes
        )
        
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=timeout,
            MemorySize=memory,
            Environment={'Variables': env_vars}
        )
        print(f"  ✅ Updated function: {function_name}")
    else:
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Handler=handler,
            Role=role_arn,
            Code={'ZipFile': zip_bytes},
            Timeout=timeout,
            MemorySize=memory,
            Environment={'Variables': env_vars}
        )
        print(f"  ✅ Created function: {function_name}")


def main():
    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Region: {REGION}")
    print(f"SNS Topic ARN: {SNS_TOPIC_ARN}")
    
    # Create dist directory
    os.makedirs(DIST_DIR, exist_ok=True)
    
    # ========================================
    # Deploy Orchestrator Lambda
    # ========================================
    print("\n📦 Packaging orchestrator Lambda...")
    
    orchestrator_dir = os.path.join(LAMBDAS_DIR, 'orchestrator')
    orchestrator_zip = os.path.join(DIST_DIR, 'orchestrator.zip')
    
    create_zip(orchestrator_dir, orchestrator_zip, include_scrapers=False)
    
    print("🚀 Deploying orchestrator Lambda...")
    deploy_lambda(
        function_name='job-scraper-orchestrator',
        zip_path=orchestrator_zip,
        role_name='job-scraper-orchestrator-role',
        handler='lambda_function.lambda_handler',
        timeout=60,
        memory=256,
        env_vars={
            'COMPANIES_TABLE': 'job_scraper_companies',
            'SCRAPER_FUNCTION': 'job-scraper-function'
        }
    )
    
    # ========================================
    # Deploy Scraper Lambda
    # ========================================
    print("\n📦 Packaging scraper Lambda...")
    
    scraper_dir = os.path.join(LAMBDAS_DIR, 'scraper')
    scraper_zip = os.path.join(DIST_DIR, 'scraper.zip')
    
    create_zip(scraper_dir, scraper_zip, include_scrapers=True)
    
    print("🚀 Deploying scraper Lambda...")
    deploy_lambda(
        function_name='job-scraper-function',
        zip_path=scraper_zip,
        role_name='job-scraper-scraper-role',
        handler='lambda_function.lambda_handler',
        timeout=300,
        memory=512,
        env_vars={
            'JOBS_TABLE': 'job_scraper_jobs',
            'SNS_TOPIC_ARN': SNS_TOPIC_ARN
        }
    )
    
    print("\n🎉 All Lambdas deployed successfully!")


if __name__ == '__main__':
    main()