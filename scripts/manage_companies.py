import boto3
from tabulate import tabulate

# Configure your region
REGION = 'us-east-1'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('job_scraper_companies')

def list_companies():
    """List all companies"""
    response = table.scan()
    companies = response['Items']
    
    if not companies:
        print("No companies found")
        return
    
    headers = ['Company Name', 'URL', 'Check']
    rows = [[c['company_name'], c['url'], c['check']] for c in companies]
    print(tabulate(rows, headers=headers, tablefmt='grid'))

def add_company():
    """Add a new company"""
    name = input("Company name: ")
    url = input("Careers URL: ")
    check = input("Check (Yes/No): ")
    
    table.put_item(Item={
        'company_name': name,
        'url': url,
        'check': check
    })
    print(f"✅ Added {name}")

def update_check(company_name: str, check: str):
    """Update the check status for a company"""
    table.update_item(
        Key={'company_name': company_name},
        UpdateExpression='SET #check = :check',
        ExpressionAttributeNames={'#check': 'check'},
        ExpressionAttributeValues={':check': check}
    )
    print(f"✅ Updated {company_name} check to {check}")

def delete_company(company_name: str):
    """Delete a company"""
    table.delete_item(Key={'company_name': company_name})
    print(f"✅ Deleted {company_name}")

def main():
    while True:
        print("\n" + "="*40)
        print("Company Management")
        print("="*40)
        print("1. List companies")
        print("2. Add company")
        print("3. Enable company (set Check=Yes)")
        print("4. Disable company (set Check=No)")
        print("5. Delete company")
        print("6. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == '1':
            list_companies()
        elif choice == '2':
            add_company()
        elif choice == '3':
            name = input("Company name: ")
            update_check(name, 'Yes')
        elif choice == '4':
            name = input("Company name: ")
            update_check(name, 'No')
        elif choice == '5':
            name = input("Company name: ")
            confirm = input(f"Delete {name}? (yes/no): ")
            if confirm.lower() == 'yes':
                delete_company(name)
        elif choice == '6':
            break

if __name__ == '__main__':
    main()