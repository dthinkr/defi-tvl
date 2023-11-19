import os
from google.cloud import bigquery
import sys
sys.path.append('')
from config.config import TABLES
from src.query import BigQueryClient


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

bq_client = BigQueryClient()

# Function to format field information
def format_field(field):
    return f"{field.name} {field.field_type}"

# Define the filename to store the schema
filename = 'data/tvl/db/db_schema.txt'

# Open the file in write mode
with open(filename, 'w') as file:
    for key, table_name in TABLES.items():
        # Write table name to the file
        file.write(f"{table_name}\n-\n")
        
        # Fetch the table schema
        schema = bq_client.get_table_schema(table_name)
        
        # Write each field's information to the file
        for field in schema:
            file.write(format_field(field) + '\n')
        
        # Add a couple of newlines for separation between tables
        file.write('\n\n')
