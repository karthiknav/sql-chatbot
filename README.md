# SQL Chatbot

A Natural Language to SQL (NL2SQL) chatbot built with LangChain, AWS Bedrock, and Streamlit. This application allows users to query a PostgreSQL database using natural language questions, which are automatically converted to SQL queries and executed.

## Features

- **Natural Language Processing**: Convert plain English questions into SQL queries
- **AWS Bedrock Integration**: Uses Claude 3.7 Sonnet model for intelligent query generation
- **Interactive Chat Interface**: Streamlit-based web interface with chat history
- **Database Schema Awareness**: Automatically understands table structures and relationships
- **DVD Rental Database**: Pre-configured with sample DVD rental database schema

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- AWS account with Bedrock access
- AWS credentials configured
- **S3 Bucket**: `s3://dvdrental-tar-nav/dvdrental.tar` with DVD rental sample database
- **IAM Roles**:
  - `arn:aws:iam::206409480438:role/EKSKubectlRole` - For EKS cluster access and management. This role is used by CDK to deploy the EKS cluster and by CodeBuild for CI/CD operations. It has `eks:Describe*` permissions and allows the AWS account root to assume it, enabling both infrastructure deployment and kubectl access to manage the cluster.
  - `arn:aws:iam::206409480438:role/EC2toS3FullAccess` - For EC2 bastion host S3 access
- **AWS Secrets Manager**: RDS credentials stored in Secrets Manager
- **EKS Cluster**: Named `eks-cdk-sqlchatbot` in `us-east-1` region

## Installation

### 1. Clone the Repository
```bash
git clone https://gitlab.com/naveena.karthik/sqlchatbot.git
cd sqlchatbot
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
source venv/Scripts/activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install main dependencies
pip install -r requirements.txt

```

### 4. Environment Configuration
```bash
# Copy environment template
copy .env.example .env

# Edit .env file with your credentials
```

Update the `.env` file with your actual values:
```env
# Database Configuration
db_user=your_db_user
db_password=your_db_password
db_host=your_db_host
db_name=your_db_name

# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# LangChain Configuration (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key
```

## Infrastructure Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.8+ and pip installed

### Cloud Deployment

#### Quick Deploy All Stacks
```bash
cdk deploy --all --require-approval never
```
Deploys all infrastructure stacks with proper dependency management and automatically approves all changes.

#### Destroy All Stacks
```bash
cdk destroy --all --force
```
Removes all infrastructure resources in reverse dependency order without confirmation prompts.

**Note**: The `app.py` file automatically handles stack dependencies, ensuring VPC is created first, followed by RDS and EKS (which depend on VPC), and finally the Pipeline stack. This eliminates the need to deploy stacks individually in a specific order.

### Individual Stack Deployment (Optional)

If you prefer to deploy stacks individually:

#### 1. VPC Stack (First)
```bash
cdk deploy VpcStack
```
Creates the network foundation with public and private subnets.

#### 2. RDS Stack (Second)
```bash
cdk deploy RdsStack
```
Creates PostgreSQL database in private subnets. Depends on VPC stack.

#### 3. EKS Stack (Third)
```bash
cdk deploy EksStack
```
Creates EKS cluster and worker nodes in private subnets. Depends on VPC stack.

#### 4. Pipeline Stack (Last)
```bash
cdk deploy SqlChatbotPipelineStack
```
Creates CI/CD pipeline that builds and deploys the application to EKS.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        VPC                                  │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │  Public Subnet  │              │  Public Subnet  │      │
│  │     AZ-1a       │              │     AZ-1b       │      │
│  │                 │              │                 │      │
│  │  - NAT Gateway  │              │  - ALB          │      │
│  │  - Internet GW  │              │                 │      │
│  └─────────────────┘              └─────────────────┘      │
│           │                                │               │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │ Private Subnet  │              │ Private Subnet  │      │
│  │     AZ-1a       │              │     AZ-1b       │      │
│  │                 │              │                 │      │
│  │ - EKS Nodes     │              │ - EKS Nodes     │      │
│  │ - RDS Primary   │              │ - RDS Standby   │      │
│  │                 │              │                 │      │
│  └─────────────────┘              └─────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Traffic Flow
- **Internet** → **ALB** (public subnets) → **EKS Pods** (private subnets) → **RDS** (private subnets)
- **EKS Pods** → **AWS Bedrock** (via NAT Gateway)

## Database Setup

### Manual Database Loading

Since the RDS instance is in private subnets, you'll need to use an EC2 instance (Bastion Host) in the public subnet to load the sample DVD rental database.

#### 1. Launch EC2 Instance
- Launch an EC2 instance (Amazon Linux 2023) in one of the public subnets of the VPC created through VpcStack
- Attach IAM role: `arn:aws:iam::206409480438:role/EC2toS3FullAccess`
- SSH into the instance and install PostgreSQL client tools:

```bash
# Update system packages
sudo dnf update -y

# Install PostgreSQL client tools
sudo dnf install -y postgresql15

# Download the DVD rental sample database from S3
aws s3 cp s3://dvdrental-tar-nav/dvdrental.tar /tmp/dvdrental.tar

# Verify file is downloaded
ls -la /tmp/dvdrental.tar
```

#### 2. Connect to RDS and Load Sample Data

```bash
# Set password as environment variable
export PGPASSWORD='passowrd'

# Connect to PostgreSQL and create dvdrental database
psql -h rdsstack-postgresdatabase0a8a7373-5mk5e7kmnude.ceviyi5z4s3h.us-east-1.rds.amazonaws.com -U postgres -d postgres -c "CREATE DATABASE dvdrental;"

# Restore the sample database from tar file
pg_restore -h \
rdsstack-postgresdatabase0a8a7373-dd4yeb7eu9g2.ceviyi5z4s3h.us-east-1.rds.amazonaws.com -p 5432 \
-U postgres -d dvdrental -v \
/tmp/dvdrental.tar

# Verify the database was loaded successfully
psql -h rdsstack-postgresdatabase0a8a7373-dd4yeb7eu9g2.ceviyi5z4s3h.us-east-1.rds.amazonaws.com -U postgres -d dvdrental -c "\dt"
```

**Note**: Replace the RDS endpoint with your actual RDS endpoint from the CloudFormation outputs.

## EKS Cluster Management

### Configure kubectl for EKS Cluster

After deploying the EKS stack, configure kubectl to connect to your EKS cluster:

```bash
aws eks update-kubeconfig --region us-east-1 --name eks-cdk-sqlchatbot --role-arn arn:aws:iam::206409480438:role/EKSKubectlRole
```

**Note**: The `--role-arn` parameter is required because the EKS cluster was deployed using this specific IAM role. By assuming this role, kubectl gains the necessary permissions to access and manage the cluster resources.

**Why this command is helpful:**
- **Pod Management**: View running pods, their status, and resource usage
- **Log Access**: Stream real-time logs from application pods for debugging
- **Troubleshooting**: Diagnose deployment issues and monitor application health
- **Scaling**: Manually scale deployments up or down as needed

### Common kubectl Commands

### Health Checks and Monitoring

#### Check Application Pod Health
```bash
# Check SQL Chatbot application pods
kubectl get pods -l app=sql-chatbot

# View detailed pod status and events
kubectl describe pods -l app=sql-chatbot

# Check pod logs for troubleshooting
kubectl logs -l app=sql-chatbot -f
```

#### Check ALB Controller Health
```bash
# Verify AWS Load Balancer Controller is running
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check ALB controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# View ALB ingress status
kubectl get ingress -n default
```

#### Get Application Load Balancer URL
```bash
# Get the ALB URL for accessing the SQL Chatbot application
kubectl get ingress sql-chatbot-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**Access the Application**: Once deployed, access the SQL Chatbot at the ALB URL returned by the above command.

### Common kubectl Commands

```bash
# View all pods with their labels
kubectl get pods --show-labels

# View logs from all pods with app=sql-chatbot label
kubectl logs -n default -l app=sql-chatbot

# Tail logs from all pods with app=sql-chatbot label (real-time)
kubectl logs -n default -l app=sql-chatbot -f

# View all pods in the cluster
kubectl get pods -A

# Describe pod details and events
kubectl describe pod <pod-name> -n default

# View services and ingress
kubectl get svc,ingress -n default

# Print environment variables of pod
kubectl exec <podname> -- printenv
```

## Running the Application

### Start the Streamlit App
```bash
streamlit run src/main.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

1. **Start the Application**: Run the Streamlit app using the command above
2. **Ask Questions**: Type natural language questions about your database
3. **Get Results**: The chatbot will convert your question to SQL, execute it, and provide a natural language response

### Example Questions
- "How many customers do we have?"
- "What are the top 5 most rented movies?"
- "Show me all customers from California"
- "What's the total revenue for last month?"

## Project Structure

```
sqlchatbot/
├── src/                             # Application source code
│   ├── main.py                      # Streamlit web interface
│   ├── langchain_utils.py           # Core LangChain logic and database connection
│   ├── prompts.py                   # Custom prompts for SQL generation
│   ├── table_details.py             # Database schema management
│   └── dvdrental_table_descriptions.csv # Database table descriptions
├── infrastructure/                  # CDK infrastructure code
│   ├── app.py                       # CDK app entry point
│   └── cdk_pipeline_stack.py        # CDK pipeline stack
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

## Database Schema

The application is configured to work with a DVD rental database containing tables for:
- Customers, Staff, and Stores
- Movies (Films), Actors, and Categories
- Rentals, Payments, and Inventory
- Geographic data (Countries, Cities, Addresses)

## Troubleshooting

### Common Issues

1. **Database Connection Error**: Verify your database credentials in `.env`
2. **AWS Bedrock Access**: Ensure your AWS credentials have Bedrock permissions
3. **Module Import Error**: Make sure virtual environment is activated and dependencies are installed

### Deactivate Virtual Environment
```bash
deactivate
```


