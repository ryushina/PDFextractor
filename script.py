import os
import re
import json
import sys
import traceback  # Import json module
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
def analyze_data(table_data):
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
    """}],temperature=0.1)     
    
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

def load_tbl_data(result, pdf_path ,attempt=1, max_attempts=3):
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
                meaningful_tables = get_meaningful_tables(pdf_path)
                combined_tbl_text = "\n\n".join(table.to_string(index=False) for table in meaningful_tables)
                new_result = analyze_data(combined_tbl_text)
                return load_tbl_data(new_result, attempt + 1, max_attempts)
            else:
                print("Max retry attempts reached. Returning empty list.")
                return []
    return []

def load_txt_data(result, pdf_path ,attempt=1, max_attempts=3):
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
                full_text = extract_text_from_pdf(pdf_path)
                new_result = analyze_data(full_text)
                return load_txt_data(new_result, attempt + 1, max_attempts)
            else:
                print("Max retry attempts reached. Returning empty list.")
                return []
    return []

def extract_text_from_pdf(pdf_path, separator="\n" + "="*80 + "\n"):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    # Initialize a list to hold the text from each page
    all_text = []
    # Iterate through each page
    for page_number in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_number)
        # Extract text from the page
        text = page.get_text() 
        # Add the text to the list
        all_text.append(f"Page {page_number + 1}\n{text}")
    # Join the list into a single string with the separator
    full_text = separator.join(all_text)  
    return full_text


def main(pdf_path):
    try:
        print(f"Extracting tables from pdf: {pdf_path}...")
        meaningful_tables = get_meaningful_tables(pdf_path)
        print(f"Extracting text from pdf: {pdf_path}..")
        full_text = extract_text_from_pdf(pdf_path)
        print("Successfully extracted text from pdf...")
        combined_tbl_text = "\n\n".join(table.to_string(index=False) for table in meaningful_tables)
        #Feed to OPENAI
        print("Successfully extracted tables from pdf...")
        print("Feeding tables to OpenAI...")
        result_table = analyze_data(combined_tbl_text)
        print("Feeding texts to OpenAI...")
        result_text = analyze_data(full_text)
        print("Converting tables to dictionary format...")
        final_tbl_res = load_tbl_data(result_table, pdf_path=pdf_path)
        print("Converting texts to dictionary format...")
        final_txt_res = load_txt_data(result_text,pdf_path=pdf_path)
        # Convert the results to DataFrames and print them
        df_tbl = pd.DataFrame(final_tbl_res)
        print("Dataframe from tables:")
        print(df_tbl)
        df_txt = pd.DataFrame(final_txt_res)
        print("Dataframe from texts:")
        print(df_txt)
        # Combine the dataframes
        combined_df = pd.concat([df_tbl, df_txt], ignore_index=True)
        # Calculate the number of non-null entries in each row
        combined_df['completeness'] = combined_df.notnull().sum(axis=1)
        # Sort by 'Asset Name' and 'completeness', then drop duplicates
        merged_df = combined_df.sort_values(['Asset Name', 'completeness'], ascending=[True, False]).drop_duplicates('Asset Name').drop('completeness', axis=1)
        return merged_df    
    except Exception as e:
        traceback.print_exception(e)
        wait_for_it = input('Press enter to close the terminal window')
if __name__ == "__main__":
    try:
    # Determine the base directory where the executable is located
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Set the path to the Tabula JAR file
        jar_path = os.path.join(base_dir, 'tabula', './.venv/Lib/site-packages/tabula/tabula-1.0.5-jar-with-dependencies.jar')

# Set the CLASSPATH for the JAR file
        os.environ['CLASSPATH'] = jar_path

        input_dir = "./input"
        output_dir = "./output"
        output_file = "combined_output.xlsx"

        all_dfs = []

        for filename in os.listdir(input_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(input_dir, filename)
                df = main(pdf_path)
                all_dfs.append(df)

        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            output_path = os.path.join(output_dir, output_file)
            final_df.to_excel(output_path, index=False)
            print(f"Combined DataFrame saved to {output_path}")
        else:
            print("No PDF files found in the input directory.")

        input()
    
    except Exception as e:
        traceback.print_exception(e)
        wait_for_it = input('Press enter to close the terminal window')

   