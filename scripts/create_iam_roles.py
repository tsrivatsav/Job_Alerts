import boto3
import json

# Configure your region
REGION = 'us-east-1'

iam = boto3.client('iam', region_name=REGION)

# Trust policy for Lambda
LAMBDA_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

def create_orchestrator_role():
    """Create IAM role for orchestrator Lambda"""
    role_name = 'job-scraper-orchestrator-role'
    
    try:
        # Create role
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(LAMBDA_TRUST_POLICY),
            Description='Role for job scraper orchestrator Lambda'
        )
        print(f"✅ Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"ℹ️ Role {role_name} already exists")
    
    # Policy for orchestrator
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:Scan"
                ],
                "Resource": f"arn:aws:dynamodb:{REGION}:*:table/job_scraper_companies"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": f"arn:aws:lambda:{REGION}:*:function:job-scraper-function"
            }
        ]
    }
    
    policy_name = 'job-scraper-orchestrator-policy'
    
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy)
        )
        print(f"✅ Attached policy: {policy_name}")
    except Exception as e:
        print(f"Error attaching policy: {e}")
    
    return role_name


def create_scraper_role():
    """Create IAM role for scraper Lambda"""
    role_name = 'job-scraper-scraper-role'
    
    try:
        # Create role
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(LAMBDA_TRUST_POLICY),
            Description='Role for job scraper scraper Lambda'
        )
        print(f"✅ Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"ℹ️ Role {role_name} already exists")
    
    # Policy for scraper
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query"
                ],
                "Resource": [
                    f"arn:aws:dynamodb:{REGION}:*:table/job_scraper_jobs",
                    f"arn:aws:dynamodb:{REGION}:*:table/job_scraper_jobs/index/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sns:Publish"
                ],
                "Resource": f"arn:aws:sns:{REGION}:*:job-scraper-notifications"
            }
        ]
    }
    
    policy_name = 'job-scraper-scraper-policy'
    
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy)
        )
        print(f"✅ Attached policy: {policy_name}")
    except Exception as e:
        print(f"Error attaching policy: {e}")
    
    return role_name


if __name__ == '__main__':
    print("Creating IAM roles...")
    create_orchestrator_role()
    create_scraper_role()
    print("\n⏳ Wait 10 seconds for roles to propagate before creating Lambdas")