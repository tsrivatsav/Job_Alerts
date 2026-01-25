import boto3

# Configure your region
REGION = 'us-east-1'

events = boto3.client('events', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
sts = boto3.client('sts')

ACCOUNT_ID = sts.get_caller_identity()['Account']

def create_schedule():
    """Create EventBridge rule to trigger orchestrator daily"""
    
    rule_name = 'job-scraper-daily-trigger'
    lambda_arn = f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:job-scraper-orchestrator'
    
    # Create rule (runs at 9 AM UTC daily)
    # Modify the cron expression as needed
    response = events.put_rule(
    Name=rule_name,
    ScheduleExpression='cron(0 13,18,23 * * ? *)',  # 1PM, 6PM, 11PM UTC daily
    State='ENABLED',
    Description='Triggers job scraper orchestrator daily at 13:00, 18:00, 23:00 UTC'
)
    
    rule_arn = response['RuleArn']
    print(f"✅ Created EventBridge rule: {rule_name}")
    print(f"   Schedule: 9 AM UTC daily")
    
    # Add Lambda as target
    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': 'orchestrator-lambda-target',
                'Arn': lambda_arn
            }
        ]
    )
    print(f"✅ Added Lambda target")
    
    # Add permission for EventBridge to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName='job-scraper-orchestrator',
            StatementId='eventbridge-invoke',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn
        )
        print(f"✅ Added Lambda invoke permission")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"ℹ️ Lambda permission already exists")
    
    return rule_arn


if __name__ == '__main__':
    print("Creating EventBridge schedule...")
    create_schedule()
    print("\n🎉 Schedule created! The scraper will run daily at 1PM, 6PM, and 11PM UTC")
    print("   To change the schedule, modify the cron expression in this script")