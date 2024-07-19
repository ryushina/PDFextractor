import os
import re
import json  # Import json module
import fitz  # PyMuPDF
import tabula
import pandas as pd
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

def read_api_key(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()
    
# Function to call OpenAI API for table data analysis
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def analyze_table_data(table_data):
    api_key = read_api_key('api_key.txt')
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a data analyst that extracts from pdf files"},
                  {"role": "user", "content": f"Extract fields from the given text then output python dictionary or list of dictionaries if there are more than one asset, take note to not omit any valid entry:Asset Name, Filename, Delivery Date, City, Country, Start of Lease, Tenant, GLA, IP-Rent, Start of Contract, with Text:{table_data}"},
                  {"role": "assistant", "content": """
    Extract fields from the given text and output a Python dictionary or a list of dictionaries if there are more than one asset. Ensure no valid entry is omitted. 

The fields are:
- Asset Name (string, required)
- Filename (string, required)
- Delivery Date (string, optional)
- City (string, optional)
- Country (string, optional)
- Start of Lease (string, optional)
- Lease Duration in Years (integer, optional)
- Seller (string, optional)
- Tenant (string, optional)
- GLA (Gross Leasable Area, string, optional)
- IP-Rent (string, optional)
- Start of Contract (string, optional)

The result should be a valid JSON string. 

Here is an example of the expected output format:
```json
[
    {
        "Asset Name": "Asset 1",
        "Filename": "example.pdf",
        "Delivery Date": "2023-01-01",
        "City": "New York",
        "Country": "USA",
        "Start of Lease": "2023-01-01",
        "Lease Duration in Years": 5,
        "Seller": "Company A",
        "Tenant": "Tenant A",
        "GLA": "1000 sqft",
        "IP-Rent": "5000 USD",
        "Start of Contract": "2023-01-01"
    },
    {
        "Asset Name": "Asset 2",
        "Filename": "example.pdf",
        "Delivery Date": "2023-01-01",
        "City": "Los Angeles",
        "Country": "USA",
        "Start of Lease": "2023-01-01",
        "Lease Duration in Years": 3,
        "Seller": "Company B",
        "Tenant": "Tenant B",
        "GLA": "2000 sqft",
        "IP-Rent": "10000 USD",
        "Start of Contract": "2023-01-01"
    }
]
    """}, temperature=0.2])     
    
    result = response.choices[0].message.content
    print(result)
    return result

# Define a function to check for relevant keywords
def has_relevant_keyword(df, keywords):
    if df.empty:
        return False
    # Check column names
    for col in df.columns:
        for keyword in keywords:
            if keyword.lower() in col.lower():
                return True 
    # Check data values

    for keyword in keywords:
        if df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1).any():
            return True
    return False

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_meaningful_tables(pdf_path):
    # Relevant keywords to check
    keywords = ['asset name', 'asset', 'tenant', 'rent']
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
    tables_list = []
    for i, table in enumerate(tables):
        tables_list.append(table)
    filtered_dfs = [df for df in tables_list if has_relevant_keyword(df, keywords)]
    return filtered_dfs


def load_data(result, attempt=1, max_attempts=4):
    match = re.search(r'\[(.*)\]', result, re.DOTALL)
    match = match.group(0) if match else None
    if match and match.strip():
        try:
            assets = json.loads(match)
            filename = os.path.basename(pdf_path)
            for asset in assets:
                asset["Filename"] = filename
            num_list = len(assets)
            print(f"You have extracted {num_list} from {filename}")
            return assets
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error on attempt {attempt}: {e}")
            if attempt < max_attempts:
                print("Retrying...")
                new_result = analyze_table_data(combined_text)
                return load_data(new_result, attempt + 1, max_attempts)
            else:
                print("Max retry attempts reached. Returning empty list.")
                return []
    return []

if __name__ == "__main__":
    pdf_path = "./input/Project Reverso - OM.pdf" 
    text_tables = []
    meaningful_tables = get_meaningful_tables(pdf_path)
    combined_text = "\n\n".join(table.to_string(index=False) for table in meaningful_tables)
    #Feed to OPENAI
    result = analyze_table_data(combined_text)
    final_res = load_data(result)
    print(final_res)
    """
    for tabl in meaningful_tables:
        text_table = tabl.to_string(index=False)
        #feed to OPEN AI
        #converted = analyze_table_data(text_table)
        text_tables.append(text_table)
    breakpoint()
    print(f"Here is the result: {text_tables}")
    """

