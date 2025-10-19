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
venv\Scripts\activate
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