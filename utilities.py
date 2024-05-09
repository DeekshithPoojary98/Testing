import base64
import os
from pypdf import PdfReader
import shutil
from pymongo import MongoClient
import json


def get_token_values_from_db(mongo_properties_filepath):
    try:
        with open(mongo_properties_filepath) as f:
            db_config = json.load(f)
        host = db_config['HOST']
        port = int(db_config['PORT'])
        username = db_config.get('USERNAME')
        password = db_config.get('PASSWORD')
        db = db_config.get('DATABASE')
        collection = db_config.get('COLLECTION')

        # MongoDB connection URI
        uri = (f"mongodb://{username}:{password}@{host}:{port}/?authSource={db}&authMechanism=SCRAM-SHA-1"
               f"&directConnection=true")

        # Connect to MongoDB
        client = MongoClient(uri)

        database = client[db]
        collection = database[collection]

        # Query MongoDB for the token field
        result = collection.find_one({'userId': "DEEKSHITH"})
        return result['token']

    except Exception as e:
        raise Exception(f"An error occurred while fetching data from the database: {e}")


def count_pdf_pages_and_verify(pdf_path, operation, expected_page_count):
    pdf_page_validation = True
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        num_pages = len(reader.pages)

    if expected_page_count != num_pages:
        pdf_page_validation = False

    print_results(f"{operation} operation successfully done",
                  f"{operation} operation failed as expected page count {[expected_page_count]} didn't match with "
                  f"actual count {[num_pages]}", locals())


def create_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' already exists. Overwriting...")
    os.makedirs(folder_path)
    print(f"Folder '{folder_path}' created successfully.")


def download_file(content, local_filename):
    with open(local_filename, 'wb') as f:
        f.write(content)


def are_files_identical(file1_path, file2_path):
    with open(file1_path, 'rb') as file1:
        with open(file2_path, 'rb') as file2:
            return file1.read() == file2.read()


def save_decoded_file(encoded_data, file_extension, file_name_prefix):
    if isinstance(encoded_data, list):
        for i, data in enumerate(encoded_data):
            try:
                decoded_data = base64.b64decode(data)
                file_name = f"{file_name_prefix}_{i}.{file_extension}"
                with open(file_name, "wb") as file:
                    file.write(decoded_data)
                print(f"File '{file_name}' saved successfully.")
            except Exception as e:
                print(f"Error saving file: {e}")
    elif isinstance(encoded_data, str):
        try:
            decoded_data = base64.b64decode(encoded_data)
            file_name = f"{file_name_prefix}.{file_extension}"
            with open(file_name, "wb") as file:
                file.write(decoded_data)
            print(f"File '{file_name}' saved successfully.")
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        print("Invalid input: encoded_data must be either a list or a string.")


def empty_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def print_results(pass_message, error_message, local_vars):
    failed_conditions = [name for name, value in local_vars.items() if value is False]
    if failed_conditions:
        failed_condition_names = ', '.join(failed_conditions)
        raise AssertionError(
            f"FAILED: {error_message}. Failed conditions: {failed_condition_names}")
    else:
        print(f"PASSED: {pass_message}")
