import boto3

# Configure your region
REGION = 'us-east-1'

dynamodb = boto3.client('dynamodb', region_name=REGION)

def create_companies_table():
    """Create the companies table"""
    try:
        dynamodb.create_table(
            TableName='job_scraper_companies',
            KeySchema=[
                {
                    'AttributeName': 'company_name',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'company_name',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✅ Companies table created successfully")
    except dynamodb.exceptions.ResourceInUseException:
        print("ℹ️ Companies table already exists")

def create_jobs_table():
    """Create the jobs table"""
    try:
        dynamodb.create_table(
            TableName='job_scraper_jobs',
            KeySchema=[
                {
                    'AttributeName': 'job_url',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_url',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'company_name',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'company_name_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'company_name',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✅ Jobs table created successfully")
    except dynamodb.exceptions.ResourceInUseException:
        print("ℹ️ Jobs table already exists")

if __name__ == '__main__':
    print("Creating DynamoDB tables...")
    create_companies_table()
    create_jobs_table()
    print("Done!")