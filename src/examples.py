examples = [
     {
         "input": "Show me actor's first name, last name that have Nick, Ed and Jennifer as their firstnames.",
         "query": "SELECT first_name, last_name FROM actor WHERE first_name IN ('Nick','Ed', 'Jennifer');"
     },
     {
         "input": "Show me only last name of actor whose first names are Ed, Nick and Jennifer.",
         "query": "SELECT last_name FROM actor WHERE first_name in ('Ed','Nick','Jennifer');"
     },
	 {
         "input": "I want to see both Maximum and minimun amount in the payment table.",
         "query": "SELECT MAX(amount) AS Max_amt, MIN(amount) AS Min_amt FROM payment;"
     },
	 {
         "input": "show the sum of rental rate of films by month.",
         "query": "SELECT DATE_TRUNC('month', film.last_update),SUM(rental_rate) FROM film GROUP BY DATE_TRUNC('month', film.last_update) ORDER BY DATE_TRUNC('month', film.last_update);"
     },
	 {
         "input": "show all film titles.",
         "query": "SELECT film.title FROM film;"
     }
]

from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
import streamlit as st

@st.cache_resource
def get_example_selector():
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(),
        FAISS,
        k=2,
    )
    return example_selector