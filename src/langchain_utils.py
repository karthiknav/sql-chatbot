import os
from dotenv import load_dotenv
import re
import boto3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('../.env.local')
load_dotenv('../.env')

# Debug all environment variables starting with DB_
logger.info("Environment variables starting with DB_:")
for key, value in os.environ.items():
    if key.startswith('DB_'):
        logger.info(f"  {key} = {value}")

def get_db_credentials():
    """Get database credentials from AWS Secrets Manager, fallback to .env"""
    try:
        # Try to get from Secrets Manager first
        secret_arn = os.getenv("DB_SECRET_ARN")
        logger.info(f"secret_arn = {secret_arn}")
        
        if secret_arn:
            client = boto3.client('secretsmanager', region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = client.get_secret_value(SecretId=secret_arn)
            secret = json.loads(response['SecretString'])
            logger.info(f"Retrieved secret = {secret}")
            
            credentials = {
                'user': secret['username'],
                'password': secret['password'],
                'host': secret['host'],
                'name': secret['dbname']
            }
            logger.info(f"Parsed credentials = {credentials}")
            return credentials
    except Exception as e:
        logger.info(f"Could not retrieve from Secrets Manager: {e}")
        logger.info("Falling back to .env file...")
    
    # Fallback to .env file
    fallback_creds = {
        'user': os.getenv("db_user"),
        'password': os.getenv("db_password"),
        'host': os.getenv("db_host"),
        'name': os.getenv("db_name")
    }
    logger.info(f"Fallback credentials = {fallback_creds}")
    return fallback_creds

# Get database credentials
db_creds = get_db_credentials()
db_user = db_creds['user']
db_password = db_creds['password']
db_host = db_creds['host']
db_name = db_creds['name']

# AWS credentials will be loaded automatically from ~/.aws/credentials
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")



from langchain_aws import ChatBedrock
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_classic.memory import ChatMessageHistory

from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import RunnablePassthrough, RunnableLambda


from table_details import table_chain as select_table, get_tables, get_table_details, get_parser
from prompts import final_prompt, answer_prompt

# Remove streamlit dependency for standalone execution
try:
    import streamlit as st
    @st.cache_resource
    def get_chain():
        return _create_chain()
except ImportError:
    def get_chain():
        return _create_chain()
def clean_sql_query(query_text):
    """Extract only SQL from LLM response"""
    # Remove common prefixes/explanations
    query_text = re.sub(r'^.*?(?=SELECT|INSERT|UPDATE|DELETE|WITH)', '', query_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove trailing explanations after semicolon
    if ';' in query_text:
        query_text = query_text.split(';')[0] + ';'
    
    return query_text.strip()

def _create_chain():
    logger.info("Creating chain")
    db_creds = get_db_credentials()
    db_user = db_creds['user']
    db_password = db_creds['password']
    db_host = db_creds['host']
    db_name = db_creds['name']
    logger.info(f"db_host = {db_host}") 
    db = SQLDatabase.from_uri(f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}")    
    llm = ChatBedrock(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name=AWS_REGION,
        model_kwargs={"temperature": 0}
    ) 
    generate_query = create_sql_query_chain(llm, db,final_prompt) | RunnableLambda(clean_sql_query)
    execute_query = QuerySQLDataBaseTool(db=db)
    rephrase_answer = answer_prompt | llm | StrOutputParser()
    chain = (
    RunnablePassthrough.assign(parsed_tables=select_table)
        | RunnableLambda(lambda x: {
        "table_names_to_use": get_tables(x["parsed_tables"]),
        "question": x["question"],
        "messages": x["messages"]
        })
        | RunnablePassthrough.assign(query=generate_query)
        .assign(result=itemgetter("query") | execute_query)
        | rephrase_answer
)
    return chain

def create_history(messages):
    history = ChatMessageHistory()
    for message in messages:
        if message["role"] == "user":
            history.add_user_message(message["content"])
        else:
            history.add_ai_message(message["content"])
    return history

def invoke_chain(question,messages):
    logger.info("About to call get_db_credentials()")
    db_creds = get_db_credentials()
    logger.info(f"get_db_credentials() returned: {db_creds}")
    chain = get_chain()
    history = create_history(messages)
    response = chain.invoke({
        "question": question,
        "table_details": get_table_details(),
        "format_instructions": get_parser().get_format_instructions(),
        "messages":history.messages
    })
    history.add_user_message(question)
    history.add_ai_message(response)
    return response

def main():
    """Debug method to test components step by step"""
    try:
        logger.info("=== Testing Database Connection ===")
        db = SQLDatabase.from_uri(f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}")
        logger.info("✓ Database connected")
        logger.info(f"Tables: {db.get_usable_table_names()}")
        
        logger.info("=== Testing LLM Connection ===")
        llm = ChatBedrock(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name=AWS_REGION,
            model_kwargs={"temperature": 0}
        )
        test_response = llm.invoke("Hello")
        logger.info(f"✓ LLM connected: {test_response.content[:50]}...")
        
        logger.info("=== Testing Full Chain ===")
        response = invoke_chain("How many customers do we have?", [])
        logger.info(f"✓ Chain executed: {response[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()