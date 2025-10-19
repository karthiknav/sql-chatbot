import os
from dotenv import load_dotenv
import re

# Load .env.local first (higher priority), then .env as fallback
load_dotenv('.env.local')
load_dotenv('.env')

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")

# AWS credentials will be loaded automatically from ~/.aws/credentials
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_aws import ChatBedrock
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.memory import ChatMessageHistory

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
    print("Creating chain")
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
        print("=== Testing Database Connection ===")
        db = SQLDatabase.from_uri(f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}")
        print(f"✓ Database connected")
        print(f"Tables: {db.get_usable_table_names()}")
        
        print("\n=== Testing LLM Connection ===")
        llm = ChatBedrock(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name=AWS_REGION,
            model_kwargs={"temperature": 0}
        )
        test_response = llm.invoke("Hello")
        print(f"✓ LLM connected: {test_response.content[:50]}...")
        
        print("\n=== Testing Full Chain ===")
        response = invoke_chain("How many customers do we have?", [])
        print(f"✓ Chain executed: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()