import os
from dotenv import load_dotenv
import streamlit as st
import mysql.connector
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS

# Configure Google Gemini API
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Create database schema and descriptions
schema_descriptions = [
    "Table: sales_table, Column: ORDERNUMBER, Description: Unique identifier for sales order",
    "Table: sales_table, Column: QUANTITYORDERED, Description: Number of  quantity of products sold in units",
    "Table: sales_table, Column: SALES, Description: Amount of sales or revenue in USD",
    "Table: sales_table, Column: PRODUCTLINE, Description: Line of products",
    "Table: sales_table, Column: ORDERDATE, Description: Date of the order",
    "Table: sales_table, Column: YEAR_ID, Description: Year of the order",
    "Table: sales_table, Column: COUNTRY, Description: Country where the order was placed",
    "Table: sales_table, Column: CUSTOMERNAME, Description: Name of the customer who placed the order",
]

def generate_vector_index(text_segments):
    """
    Create a vector store of text chuncks and saves it to a FAISS index.
    
    Args:
        text_segments (list): List of text segments to create vector store
    
    Returns:
        None: The FAISS index is saved locally as 'faiss_index_store'
    """
    embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_texts(text_segments, embedding=embed_model)
    vector_db.save("faiss_index_store")
    return vector_db

vector_db = generate_vector_index(schema_descriptions)

# Utility functions
def configure_streamlit():
    """Configure Streamlit app."""
    st.set_page_config(page_title='Chat with database using Gemini and RAG', layout='wide')
    st.header('Chat with database using Gemini and RAG')

def get_gemini_response(question, prompt):
    """Get Gemini response."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([prompt, question])
        return response.text
    except Exception as e:
        st.error(f'Error with Google Gemini API: {e}')
        return None
    
def connect_to_database():
    """Connect to MySQL database from Streamlit Session State."""
    try:
        connection = mysql.connector.connect(
            host = st.session_state['host'],
            user = st.session_state['user'],
            password = st.session_state['password'],
            database = st.session_state['database']
        )
        st.success(f"Connected to {st.session_state['database']} successfully!")
        return connection
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None

def read_sql_query(query):
    """Read SQL query from MySQL database."""
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except mysql.connector.Error as e:
            st.error(f"Error reading SQL query: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None

# Prompt Definitions
PROMPT_QUERY = """
    You are an expert in converting English questions to MySQL query!
    Example SQL command: SELECT COUNT(*) FROM sales;

    The output should not include ``` or the word "sql".
"""

PROMPT_HUMANE_RESPONSE_TEMPLATE = """
    You are a customer service agent.

    Previously, you were asked: "{question}"
    The query result from the database is: "{result}".

    Please respond to the customer in a humane and friendly and detailed manner.
    For example, if the question is "What is the biggest sales of product A?", 
    you should answer "The biggest sales of product A is 1000 USD".
"""

# Define functions
def retrieve_schema(user_query):
    """Retrieve schema information from database."""
    return vector_db.similarity_search(user_query, k=5)

def generate_sql_query(question, retrieved_schema):
    """Generate SQL query based on user question and retrieved schema."""
    prompt = f"""

    You are an expert in converting English questions to MySQL query!
    Example SQL command: SELECT COUNT(*) FROM sales;

    The output should not include ``` or the word "sql".
    
    Based on the following database schema:
    {retrieved_schema}
    
    """
    return get_gemini_response(question, prompt)

# Main Application Logic
def main():
    show_query = True
    configure_streamlit()
    # User input

    question = st.text_input('Input:', key="input")

    if st.button("Ask the question") and question:
        with st.spinner("Processing your query..."):
            schema_docs = retrieve_schema(question)
            retrieve_schema = "\n".join([doc.page_content for doc in schema_docs])

            st.subheader('Schema Information:')
            st.write(retrieve_schema)

            # Get SQL Query from gemini
            sql_query = generate_sql_query(question, retrieve_schema)

            if sql_query:
                if show_query:
                    st.subheader('Generate SQL Query:')
                    st.write(sql_query)
                
                # Execute SQL query
                result = read_sql_query(sql_query)
                if result:
                    if show_query:
                        st.subheader('SQL Query Result:')
                        for row in result:
                            st.write(row)

                    # Generate humane response
                    humane_response = get_gemini_response(
                        question,
                        PROMPT_HUMANE_RESPONSE_TEMPLATE.format(
                            question=question,
                            result=result
                        )
                    )
                    st.subheader('Humane Response:')
                    st.write(humane_response)
                else:
                    st.error('No results found for the query.')
    # Sidebar for Database Connection
    with st.sidebar:
        st.subheader('Database Configuration')
        st.text_input('Host', value='localhost', key='host')
        st.text_input('Port', value='3306', key='port')
        st.text_input('User', value='root', key='user')
        st.text_input('Password', value='', type='password', key='password')
        st.text_input('Database', value='sales_database', key='database')
        if st.button('Connect to Database'):
            with st.spinner('Connecting to database...'):
                if connect_to_database():
                    st.success('Connected to database successfully!')

    # Footer
    st.markdown(
        """
        ---
        Developed by Axel
        """
    )

# Run the app
if __name__ == '__main__':
    main()