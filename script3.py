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
    Result should just be just valid json string
    The fields are:
    - Asset Name // This is the primary key, a pdf file can have many assets in it
    - Filename // this is the filename of the pdf file from where the asset is extracted
    - Delivery Date // delivery date of the asset
    - City // city of the asset
    - Country // country of the asset
    - Start of Lease // asset's start of lease
    - Lease Duration in Years // asset's lease duration in years
    - Seller // asset's seller
    - Tenant // asset's tenant
    - GLA (Gross Leasable Area) // asset's GLA
    - IP-Rent // asset's IP-Rent
    - Start of Contract // asset's start of contract
    """}],temperature=0.2)     
    
    result = response.choices[0].message.content

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


def load_data(result, attempt=1, max_attempts=3):
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

