<<<<<<< HEAD
import fitz  # PyMuPDF
import tabula
import pandas as pd
from openai import OpenAI

def read_api_key(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text() + "\n\n"
    return text

def extract_tables_from_pdf(pdf_path):
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
    tables_dict = {}
    for i, table in enumerate(tables):
        page_num = i + 1
        if page_num not in tables_dict:
            tables_dict[page_num] = []
        tables_dict[page_num].append(table)
    return tables_dict

def integrate_text_and_tables(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    tables_dict = extract_tables_from_pdf(pdf_path)
    document = fitz.open(pdf_path)
    output_text = ""
    for page_num in range(len(document)):
        page_text = document.load_page(page_num).get_text()
        output_text += f"Page {page_num + 1}\n"
        output_text += page_text + "\n"
        if page_num + 1 in tables_dict:
            for i, table in enumerate(tables_dict[page_num + 1]):
                output_text += f"Table {i + 1} on Page {page_num + 1}\n"
                output_text += table.to_string(index=False) + "\n\n"
    return output_text

def extract_fields_from_text(text):
    api_key = read_api_key('api_key.txt')
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"system","content":"You are a data analyst that extracts from pdf files"},
                  {"role":"user","content":f"Extract fields from the given text then output python dictionary or list of dictionaries if there are more than one asset:Asset Name, Filename, Delivery Date, City, Country,Start of Lease,Tenant, GLA,IP-Rent, Start of Contract, with Text:{text}"},
                  {"role":"assistant","content":f"""
    The fields are:
    - Asset Name // This is the primary key, a pdf file can have many assets in it
    - Filename // this is the filename of the pdf file from where the asset is extracted
    - Delivery Date // delivery date of the  asset
    - City // city of the asset
    - Country // country of the asset
    - Start of Lease //asset's start of lease
    - Lease Duration in Years //asset's lease duration in years
    - Seller //asset's seller
    - Tenant //asset's tenant
    - GLA (Gross Leasable Area) //asset's GLA
    - IP-Rent //asset's IP-Rent
    - Start of Contract //asset's start of contract
    """}],     
    )
    result = response.choices[0].message.content
    return result

def main(pdf_path):
    output_text = integrate_text_and_tables(pdf_path)
    fields = extract_fields_from_text(output_text)
    return fields

if __name__ == "__main__":
    pdf_path = "./input/Project Reverso - OM.pdf"  # Replace with your PDF file path
    result = main(pdf_path)
    print(result)
=======
import pdfplumber
import pandas as pd

# Open the PDF file
with pdfplumber.open("./input/Project Reverso - OM.pdf") as pdf:
    # Iterate through each page
    for page in pdf.pages:
        # Extract text
        text = page.extract_text()
        print("Text:", text)
        
        # Extract tables
        tables = page.extract_tables()
        for table in tables:
            df = pd.DataFrame(table[1:], columns=table[0])
            print(df)
>>>>>>> ec0b68d699cc588f8815261a476e4dea09a357b1
