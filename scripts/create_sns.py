import boto3

# Configure your region and email
REGION = 'us-east-1'
YOUR_EMAIL = 'tejas299@gmail.com'  # CHANGE THIS

sns = boto3.client('sns', region_name=REGION)

def create_topic():
    """Create SNS topic and subscribe email"""
    # Create topic
    response = sns.create_topic(Name='job-scraper-notifications')
    topic_arn = response['TopicArn']
    print(f"✅ Created SNS topic: {topic_arn}")
    
    # Subscribe email
    sns.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=YOUR_EMAIL
    )
    print(f"✅ Subscription created for {YOUR_EMAIL}")
    print("⚠️  Check your email and confirm the subscription!")
    
    return topic_arn

if __name__ == '__main__':
    topic_arn = create_topic()
    print(f"\n📝 Save this ARN for later: {topic_arn}")