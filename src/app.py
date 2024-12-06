import os
from dotenv import load_dotenv
import streamlit as st
import mysql.connector
import google.generativeai as genai

# Configure Google Gemini API
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Create Utility Functions
def configure_streamlit():
    """Configure Streamlit app."""
    st.set_page_config(page_title='Chat with database using Gemini', layout='wide')
    st.header('Chat with database using Gemini')

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

    The SQL database "sales_database" has the table "sales_table" and the following columns:
    - ORDERNUMBER: Unique identifier for sales
    - QUANTITYORDERED: Number of products sold
    - SALES: Amount of sales or revenue in USD
    - PRODUCTLINE: Line of products
    - ORDERDATE: Date of order
    - YEAR_ID: Year of the order
    - COUNTRY: Country
    - CUSTOMERNAME: Name of customer

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

# Main Streamlit App
def main():
    show_query = True
    configure_streamlit()
    
    #user input
    question = st.text_input('Input:', key="input")
    if st.button("Ask the question") and question:
        with st.spinner("Processing your query..."):
            sql_query = get_gemini_response(question, PROMPT_QUERY)
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
                    st.subheader('Gemini Response:')
                    st.write(humane_response)
                else:
                    st.error('Error reading SQL query')

        # Sitebar for Database Configuration
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

# Run Streamlit App
if __name__ == "__main__":
    main()
