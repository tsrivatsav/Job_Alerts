import boto3

# Configure your region
REGION = 'us-east-1'

events = boto3.client('events', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
sts = boto3.client('sts')

ACCOUNT_ID = sts.get_caller_identity()['Account']

def create_schedule():
    """Create EventBridge rule to trigger orchestrator at specified UTC hours"""
    
    rule_name = 'job-scraper-daily-trigger'
    lambda_arn = f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:job-scraper-orchestrator'
    
    # Updated cron expression: 1, 13, 16, 19, 22 represent the hours in UTC
    schedule_expression = 'cron(0 1,13,16,19,22 * * ? *)'
    
    # Create rule
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression=schedule_expression,
        State='ENABLED',
        Description='Triggers job scraper at 1AM, 1PM, 4PM, 7PM, and 10PM UTC'
    )
    
    rule_arn = response['RuleArn']
    print(f"✅ Created EventBridge rule: {rule_name}")
    print(f"   Schedule: {schedule_expression}")
    
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
    print("Updating EventBridge schedule...")
    create_schedule()
    print("\n🎉 Schedule updated! The scraper will run at 1AM, 1PM, 4PM, 7PM, and 10PM UTC")