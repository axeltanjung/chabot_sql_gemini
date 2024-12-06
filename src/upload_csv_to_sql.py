# Script to upload CSV to MySQL

import pandas as pd
import mysql.connector

# Step 1: Load the CSV file
csv_file = 'data.csv'
df = pd.read_csv(csv_file, encoding='ISO-8859-1')

# Replace NaN values with None
df = df.where(pd.notnull(df), None)

# Step 2 : Connect to MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="mydatabase"
)
cursor = conn.cursor()

# Step 3 : Define function to map Pandas dytpes to MySQL data types
def map_dtype(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        return 'FLOAT'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATE'
    else:
        return "VARCHAR(255)"  # Default to VARCHAR for object/string types
    
# Step 4 : Create table in MySQL database
table_name = 'sales_table'
schema = ', '.join([f'{col} {map_dtype(dtype)}' for col, dtype in zip(df.columns, df.dtypes)])

# Step 5: Create the table
create_table_query = f"CREATE TABLE IF NOT EXIST {table_name} ({schema});"
cursor.execute(create_table_query)
print(f"Table `{table_name}` created successfully!")

# Step 6: Insert data into the table
for _, row in df.iterrows():
    placeholders = ', '.join(['%s'] * len(row))
    insert_query = f"INSERT INTO {table_name} VALUES ({placeholders});"
    cursor.execute(insert_query, tuple(row))

conn.commit()
cursor.close()
conn.close()
print("Data inserted successfully!")

