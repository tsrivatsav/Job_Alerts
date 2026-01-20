import boto3
import json

# Configure your region
REGION = 'us-east-1'

lambda_client = boto3.client('lambda', region_name=REGION)

def test_orchestrator():
    """Manually trigger the orchestrator"""
    print("🧪 Testing orchestrator Lambda...")
    
    response = lambda_client.invoke(
        FunctionName='job-scraper-orchestrator',
        InvocationType='RequestResponse',
        Payload=json.dumps({})
    )
    
    result = json.loads(response['Payload'].read())
    print(f"Response: {json.dumps(result, indent=2)}")
    return result

def test_scraper_directly(company_name: str, url: str):
    """Manually trigger scraper for a specific company"""
    print(f"🧪 Testing scraper for {company_name}...")
    
    response = lambda_client.invoke(
        FunctionName='job-scraper-function',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'company_name': company_name,
            'url': url
        })
    )
    
    result = json.loads(response['Payload'].read())
    print(f"Response: {json.dumps(result, indent=2)}")
    return result

if __name__ == '__main__':
    print("="*50)
    print("Job Scraper Manual Test")
    print("="*50)
    
    print("\nOptions:")
    print("1. Test orchestrator (triggers all companies)")
    print("2. Test single company scraper")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == '1':
        test_orchestrator()
    elif choice == '2':
        company = input("Enter company name: ")
        url = input("Enter URL: ")
        test_scraper_directly(company, url)
    else:
        print("Invalid choice")