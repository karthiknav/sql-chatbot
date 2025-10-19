import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    'bedrock',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

response = client.list_foundation_models()
for model in response['modelSummaries']:
    print(f"Model ID: {model['modelId']}")
    print(f"Model Name: {model['modelName']}")
    print(f"Provider: {model['providerName']}")
    print("---")