import logging
import os
import json
import pandas as pd
from openai import OpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def read_api_key(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_assistant(client):
    return client.beta.assistants.create(
        name="Data Analyst Assistant",
        instructions="You are an expert data analyst. Extract data from pdfs.",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def upload_file(client, file_path):
    return client.files.create(file=open(file_path, "rb"), purpose="assistants")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_thread(client, message_file_id):
    return client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content":  f"""
             Extract the following fields from the given PDF file and output a python list of a one-dimensional Python dictionary/dictionaries. The value for each key should be a string, if more than one, multiple items can be concatenated and separated by commas, if value is not found, put "unspecified", ensure keys and values are in double quotes.:

            - Asset Name #this is the primary key, a pdf file can have many assets in it
            - Filename #this is the source or the file name of the pdf where the asset is extracted
            - Delivery Date
            - City
            - Country
            - Start of Lease
            - Lease Duration in Years
            - Seller
            - Tenant
            - GLA (Gross Leasable Area)
            - IP-Rent
            - Start of Contract

            If you can recognize a table in the pdf make sure to extract data from each and every row
            """,
                "attachments": [
                    {"file_id": message_file_id, "tools": [{"type": "file_search"}]}
                ],
            }
        ]
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_and_poll_run(client, thread_id, assistant_id):
    return client.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=assistant_id)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def list_messages(client, thread_id, run_id):
    return list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run_id))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def correct_json_with_openai(client, json_text):
    prompt = f"Correct the following JSON data:\n\n{json_text}\n\nEnsure it is valid and properly formatted."
    response = client.Completion.create(
        model="gpt-4",
        prompt=prompt,
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

def validate_json_data(client, json_text):
    try:
        parsed_data = json.loads(json_text)
        return parsed_data
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
        print("correcting json..")
        corrected_json_text = correct_json_with_openai(client, json_text)
        try:
            parsed_data = json.loads(corrected_json_text)
            return parsed_data
        except json.JSONDecodeError as e:
            logging.error(f"Corrected JSON Decode Error: {e}")
            raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_file(client, file_path, assistant_id):
    try:
        message_file = upload_file(client, file_path)
        thread = create_thread(client, message_file.id)
        run = create_and_poll_run(client, thread.id, assistant_id)
        messages = list_messages(client, thread.id, run.id)
        message_content = messages[0].content[0].text

        extracted_json = message_content.value
        start_pos = extracted_json.find('{')
        end_pos = extracted_json.rfind('}') + 1
        json_text = extracted_json[start_pos:end_pos]

        # Log the raw JSON text for inspection
        logging.info(f"Extracted JSON text: {json_text}")
        json_text_list = f"[{json_text}]"

        # Validate parsed data with retry mechanism for JSON decode errors
        parsed_data = validate_json_data(client, json_text_list)
        if isinstance(parsed_data, list) and all(isinstance(item, dict) for item in parsed_data):
            return parsed_data
        else:
            raise ValueError("Parsed data is not a valid list of dictionaries")

    except OpenAIError as e:
        logging.error(f"OpenAI API Error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        raise

def main():
    try:
        api_key = read_api_key('api_key.txt')
        client = OpenAI(api_key=api_key)
        assistant = create_assistant(client)
        
        input_dir = './input'
        output_file = './output/extracted.xlsx'
        
        all_data = []

        for filename in os.listdir(input_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(input_dir, filename)
                try:
                    data = process_file(client, file_path, assistant.id)
                    all_data.extend(data)
                except Exception as e:
                    logging.error(f"Failed to process file {file_path}: {e}")
                    
        if all_data:
            df = pd.DataFrame(all_data)
            with pd.ExcelWriter(output_file, mode='a', if_sheet_exists='overlay') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=writer.sheets['Sheet1'].max_row)
        
        print("Data from all files appended to Excel file successfully.")
    except OpenAIError as e:
        logging.error(f"OpenAI API Error: {e}")
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")

if __name__ == "__main__":
    main()
