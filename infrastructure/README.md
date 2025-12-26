# Infrastructure

This directory contains AWS CDK stacks for the SQL Chatbot application infrastructure.

## Stacks

### 1. VPC Stack (`vpc_stack.py`)
- Creates a VPC with public and private subnets across 2 AZs
- Includes NAT Gateway for private subnet internet access
- Exports VPC ID and private subnet IDs for other stacks

### 2. RDS Stack (`rds_stack.py`)
- Creates PostgreSQL 15.4 database in private subnets
- Uses generated secrets for database credentials
- Configured for the DVD rental database schema
- Exports database endpoint and secret ARN

### 3. EKS Stack (`eks_stack.py`)
- Creates EKS cluster in private subnets
- Includes managed node group with t3.medium instances
- Configured for public and private endpoint access
- Exports cluster name, endpoint, and ARN

### 4. Pipeline Stack (`cdk_pipeline_stack.py`)
- Existing CI/CD pipeline for application deployment
- Updated to work with the new EKS cluster name

## Deployment

### Prerequisites
```bash
npm install -g aws-cdk
pip install aws-cdk-lib constructs
```

### Deploy Infrastructure
```bash
# Deploy all stacks in order
deploy-infrastructure.bat

# Or deploy individually
cdk deploy SqlChatbotVpcStack
cdk deploy SqlChatbotRdsStack
cdk deploy SqlChatbotEksStack
```

### Cleanup
```bash
# Destroy all infrastructure
destroy-infrastructure.bat
```

## Outputs

After deployment, the stacks export the following values:
- **VPC**: VPC ID, Private Subnet IDs
- **RDS**: Database endpoint, port, secret ARN
- **EKS**: Cluster name, endpoint, ARN

## Configuration

### Database Connection
Retrieve database credentials:
```bash
aws secretsmanager get-secret-value --secret-id [SecretArn from RDS output]
```

### EKS Access
Configure kubectl:
```bash
aws eks update-kubeconfig --region us-east-1 --name sqlchatbot-cluster
```