import pandas as pd
import streamlit as st
from operator import itemgetter
from langchain.chains.openai_tools import create_extraction_chain_pydantic
from pydantic import BaseModel, Field
from langchain_aws import ChatBedrock
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain_core.prompts import MessagesPlaceholder
import os

llm = ChatBedrock(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    model_kwargs={"temperature": 0}
) 
from typing import List

@st.cache_data
def get_table_details():
    # Read the CSV file into a DataFrame
    # Get the directory of the current file and construct path to CSV
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "dvdrental_table_descriptions.csv")
    table_description = pd.read_csv(csv_path)
    # Iterate over the DataFrame rows to create Document objects
    table_details = ""
    for index, row in table_description.iterrows():
        table_details = table_details + "Table Name:" + row['Table'] + "\n" + "Table Description:" + row['Description'] + "\n\n"

    return table_details

def get_parser():
    return PydanticOutputParser(pydantic_object=ListTable)

class Table(BaseModel):
    """Table in SQL database."""

    name: str = Field(description="Name of table in SQL database.")

class ListTable(BaseModel):
    tables: List[Table] = Field(description="List of tables in the database.")

def get_tables(parsed_tables: ListTable) -> List[str]:
    return [table.name for table in parsed_tables.tables]


# table_names = "\n".join(db.get_usable_table_names())
table_details = get_table_details()
table_details_prompt = """Return the names of all of tables that MIGHT be relevant to the user question.\
The tables are:

{table_details}
Question is: {question}
You must follow the following format instructions:
{format_instructions}
Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed.
"""

parser = get_parser()
system_message_prompt = SystemMessagePromptTemplate.from_template(table_details_prompt)
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(table_details_prompt),
    HumanMessagePromptTemplate.from_template("{question}")
])
table_chain = chat_prompt | llm | parser