import mysql.connector
from datetime import datetime
import traceback
import json
import time
import requests
import pytest
import re
from api_data import *
from api_methods import APIFramework
from endpoints import *
from utilities import *
from playwright.sync_api import sync_playwright

api_obj = APIFramework()

def extract_error_message(text):
    pattern = r'(AssertionError:.*?)\n\S+\.py:\d+: AssertionError'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        result = match.group(1).strip()
        return result
    return text

def get_db_connection():
    return mysql.connector.connect(
        host="host.docker.internal",
        user="root",
        password="Sirma@123",
        database="testdb"
    )

@pytest.fixture(scope="function", autouse=True)
def insert_test_data(request):
    connection = get_db_connection()
    cursor = connection.cursor()
    start_time = None

    def setup():
        nonlocal start_time
        start_time = datetime.now()

    def teardown():
        test_case_name = request.node.nodeid
        test_case_name = test_case_name.split('::')[-1]
        end_time = datetime.now()
        results = "passed"
        fail_reason = None
    
        try:
            # Check if the test setup failed
            if request.node.rep_setup.failed:
                results = "error"
                fail_reason = "Test setup failed"
            else:
                # Check if the test case failed
                if request.node.rep_call.failed:
                    results = "failed"
                    fail_reason = str(request.node.rep_call.longrepr)
                    fail_resaon = extract_error_message(fail_reason)
        except Exception as e:
            results = "error"
            fail_reason = str(e)
    
        # Calculate response time
        response_time = (end_time - start_time).total_seconds()
    
        # Insert test result into the database
        insert_query = """
            INSERT INTO testdb.pytest_results (test_case_name, start_time, response_time, results, fail_reason)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (test_case_name, start_time, response_time, results, fail_reason))
        connection.commit()
    
        cursor.close()
        connection.close()

        
    request.addfinalizer(teardown)
    setup()


@pytest.fixture
def api_session():
    return requests.Session()


@pytest.mark.run(order=1)
def test_get_login_token():
    global header
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page()
        page.goto("http://103.171.98.14:9068/login")
        page.fill("//input[@placeholder='User Identification*']", username)
        page.fill("//input[@placeholder='Password*']", password)
        page.fill("//input[@placeholder='Enter captcha text']", "a")
        page.click("//span[@class='mat-mdc-button-touch-target']")
        browser.close()
        time.sleep(2)
        token = get_token_values_from_db('cred.json')
        print(token)

        header = {
            'Authorization': token
        }


# ManualWorkspace
@pytest.mark.run(order=2)
def test_create_manualworkspace_directory(api_session):
    """
    This test case validates the functionality of an API designed to create a directory. It ensures that a new
    directory is successfully created with the specified name. The test verifies that upon calling the API,
    a directory is created at the designated path within the filesystem. If the directory creation operation is
    successful, the test passes, indicating that the system can effectively create directories as intended
    """
    global dir_id

    response = api_session.post(url=create_directory_url,
                                json=test_create_manualworkspace_directory_json,
                                headers=header)
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    dir_id = (response.json())['data']['id']
    print(json.dumps(response.json(), indent=4))
    folder_name_validation = api_obj.validate_key_value(response.json(), 'folderName', folder_name)
    folder_path_validation = api_obj.validate_key_value(response.json(), 'folderPath',
                                                        f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}")
    workspace_type_validation = api_obj.validate_key_value(response.json(), 'workSpaceType', "MANUALWORKSPACE")
    archive_validation = api_obj.validate_key_value(response.json(), 'archive', False)
    favourite_validation = api_obj.validate_key_value(response.json(), 'favourite', False)
    trash_validation = api_obj.validate_key_value(response.json(), 'trash', False)
    cif_id_validation = api_obj.validate_key_value(response.json(), 'cifId', str(cifID))
    created_by_validation = api_obj.validate_key_value(response.json(), 'createdBy', username)

    print_results(f" Folder {folder_name} created successfully",
                  f"Folder {folder_name} creation was unsuccessful", locals())


@pytest.mark.run(order=3)
def test_get_workspace(api_session):
    """
    This test verifies the accuracy of an API responsible for listing all directories within a specified workspace.
    After creating a directory using a separate API call, this test ensures that the newly created directory is
    included in the list of directories returned by the API. By confirming the presence of the directory in the list,
    the test confirms that the system accurately retrieves and displays existing directories within the designated
    workspace
    """
    response = api_session.get(url=get_all_folder_structure_url.format(workSpaceName="manualworkspace"),
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    id_validation = api_obj.validate_key_value(response.json(), 'id', dir_id)
    print_results(f"Folder {folder_name} exists with id {dir_id}",
                  f"Folder {folder_name} doesnt exists", locals())


@pytest.mark.run(order=4)
# @pytest.mark.skip(reason="skipping for now")
def test_upload(api_session):
    """
    This test validates the functionality of an API designed for uploading files into a specific directory. The test
    uploads a file into the previously created directory. The test verifies the success of the file upload operation
    by checking if the API returns a success message confirming the successful upload of the file into the designated
    directory
    """

    response = api_session.post(url=upload_url,
                                data=test_upload_data,
                                files=test_upload_file,
                                headers=header)
    print(test_upload_data)
    print(test_upload_file)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', pdf_file_name)
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f'/IDOC_Filesystem/workspace/manualworkspace/{folder_name}/{pdf_file_name}')
    array_length_validation = api_obj.validate_array_length(response.json(), 'data', 6)
    print_results("File uploaded successfully", "File upload unsuccessful", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=5)
def test_get_documents(api_session):
    """
    This test validates the functionality of an API responsible for listing all the files present within a specified
    directory. The test verifies whether the file uploaded in the previous step is correctly listed by the API. By
    querying the API with the directory path, the test ensures that the uploaded file is included in the list of
    files returned by the API.
    """
    global pdf_doc_id1, txt_doc_id, tiff_doc_id, xlsx_doc_id, image_doc_id, pdf_doc_id2
    response = api_session.get(url=documents_url,
                               params=test_get_documents_params,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    pdf_doc_id1 = (response.json())['data'][0]['id']
    txt_doc_id = (response.json())['data'][1]['id']
    tiff_doc_id = (response.json())['data'][2]['id']
    xlsx_doc_id = (response.json())['data'][3]['id']
    image_doc_id = (response.json())['data'][4]['id']
    pdf_doc_id2 = (response.json())['data'][5]['id']
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', pdf_file_name)
    file_path_validation = api_obj.validate_key_value(response.json(), 'filePath',
                                                      f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}")
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f'/IDOC_Filesystem/workspace/manualworkspace/{folder_name}/{pdf_file_name}')
    array_length_validation = api_obj.validate_array_length(response.json(), 'data', 6)

    print_results(f" Uploaded file exists under folder {folder_name}",
                  f"Uploaded file doesnt exists "
                  f"under folder {folder_name}",
                  locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=6)
def test_get_download(api_session):
    """
    This test evaluates the functionality of an API designed to download a file using its ID. By providing the
    file ID as a parameter, the test initiates the download process and verifies that the file is successfully
    downloaded to the local machine. After downloading, the test confirms the integrity of the downloaded file to
    ensure that it matches the original file stored on the server.
    """

    response = api_session.get(download_url.format(id=pdf_doc_id1), headers=header)
    response.raise_for_status()
    file_content = response.content
    download_file(file_content, fr"../downloads/{pdf_file_name}")
    if os.path.exists(fr"../downloads/{pdf_file_name}"):
        is_identical = are_files_identical(fr"../downloads/{pdf_file_name}", pdf_file_name)
        if not is_identical:
            raise Exception("Uploaded and Downloaded files do not match")
    else:
        raise Exception(f"File '{pdf_file_name}' did not download")


# Search
# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=7)
@pytest.mark.parametrize("search_filter", search_filters)
def test_search_file(api_session, search_filter):
    """
    This test evaluates the search functionality of an API, which allows users to search for either a folder or a
    file by providing various search parameters. The test focuses on verifying whether the uploaded file and the
    created directory are correctly listed by the API based on the specified search criteria. By examining the API
    response, the test confirms whether the expected items are accurately retrieved and listed.
    """
    test_search_file_params["filter"] = search_filter
    response = api_session.get(
        search_url,
        params=test_search_file_params,
        headers=header
    )
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', pdf_file_name)
    if search_filter != "notContains":
        print_results(f"Fetched all {pdf_file_name} files",
                      f"Unable to fetch all {pdf_file_name} files", locals())
    else:
        if file_name_validation:
            raise AssertionError(f"{pdf_file_name} is found in search")


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=8)
def test_update_file_name(api_session):
    """
    This test case assesses the functionality of an API designed to update file names. The API accepts the file ID as
    input and modifies the filename accordingly. The test verifies the correct execution of this operation by
    supplying the file ID of a previously uploaded file and updating its name. Upon completion, the test confirms
    whether the filename has been successfully updated by examining the response from the API.
    """

    test_update_file_name_json["id"] = pdf_doc_id1
    response = api_session.put(url=update_file_url,
                               json=test_update_file_name_json,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', updated_file_name)
    file_path_validation = api_obj.validate_key_value(response.json(), 'filePath',
                                                      f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}")
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}/{updated_file_name}")

    print_results(f"Updated file name from {pdf_file_name} to {updated_file_name}",
                  f"Unable to update file name to {updated_file_name}", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=9)
def test_update_file_tags(api_session):
    """
    This test case assesses the functionality of an API designed to update file tags. The API accepts the file ID as
    input and updates the file tag accordingly. The test verifies the correct execution of this operation by
    supplying the file ID of a previously uploaded file and updating its tag. Upon completion, the test confirms
    whether the file tag name has been successfully updated by examining the response from the API.
    """
    test_update_file_tags_json["id"] = pdf_doc_id1
    response = api_session.put(url=update_file_url,
                               json=test_update_file_tags_json,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', updated_file_name)
    file_path_validation = api_obj.validate_key_value(response.json(), 'filePath',
                                                      f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}")
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}/{updated_file_name}")
    workspace_type_validation = api_obj.validate_key_value(response.json(), 'workSpaceType', "MANUALWORKSPACE")
    archive_validation = api_obj.validate_key_value(response.json(), 'archive', False)
    favourite_validation = api_obj.validate_key_value(response.json(), 'favourite', False)
    trash_validation = api_obj.validate_key_value(response.json(), 'trash', False)
    tags_validation = api_obj.validate_key_value(response.json(), 'tags', [new_tag])
    created_by_validation = api_obj.validate_key_value(response.json(), 'createdBy', username)

    print_results(f"Updated file tag from to {new_tag}",
                  f"Unable to update file tag to {new_tag}", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=10)
def test_update_file_remark(api_session):
    """
    This test case assesses the functionality of an API designed to update file remarks. The API accepts the file ID as
    input and updates the file remarks accordingly. The test verifies the correct execution of this operation by
    supplying the file ID of a previously uploaded file and updating its remarks. Upon completion, the test confirms
    whether the file remarks name has been successfully updated by examining the response from the API.
    """
    test_update_file_remark_json["id"] = pdf_doc_id1
    response = api_session.put(url=update_file_url,
                               json=test_update_file_remark_json,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', updated_file_name)
    file_path_validation = api_obj.validate_key_value(response.json(), 'filePath',
                                                      f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}")
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}/{updated_file_name}")
    workspace_type_validation = api_obj.validate_key_value(response.json(), 'workSpaceType', "MANUALWORKSPACE")
    archive_validation = api_obj.validate_key_value(response.json(), 'archive', False)
    favourite_validation = api_obj.validate_key_value(response.json(), 'favourite', False)
    trash_validation = api_obj.validate_key_value(response.json(), 'trash', False)
    tags_validation = api_obj.validate_key_value(response.json(), 'tags', [new_tag])
    remarks_validation = api_obj.validate_key_value(response.json(), 'remarks', new_remarks)
    created_by_validation = api_obj.validate_key_value(response.json(), 'createdBy', username)

    print_results(f"Updated file remarks from to {new_remarks}",
                  f"Unable to update file remarks to {new_remarks}", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=11)
def test_update_folder_name(api_session):
    """
    This test case assesses the functionality of an API designed to update folder names. The API accepts the folder
    ID as input and modifies the filename accordingly. The test verifies the correct execution of this operation by
    supplying the folder ID of a previously created folder and updating its name. Upon completion, the test confirms
    whether the folder name has been successfully updated by examining the response from the API.
    """
    response = api_session.put(update_folder_url.format(id=dir_id),
                               params=test_update_folder_name_params,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    folder_name_validation = api_obj.validate_key_value(response.json(), 'folderName', updated_folder_name)
    folder_path_validation = api_obj.validate_key_value(response.json(), 'folderPath',
                                                        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}")
    workspace_type_validation = api_obj.validate_key_value(response.json(), 'workSpaceType', "MANUALWORKSPACE")
    archive_validation = api_obj.validate_key_value(response.json(), 'archive', False)
    favourite_validation = api_obj.validate_key_value(response.json(), 'favourite', False)
    trash_validation = api_obj.validate_key_value(response.json(), 'trash', False)
    cif_id_validation = api_obj.validate_key_value(response.json(), 'cifId', str(cifID))
    created_by_validation = api_obj.validate_key_value(response.json(), 'createdBy', username)

    print_results(f"Updated folder name from {folder_name} to {updated_folder_name}",
                  f" Unable to update folder name to {updated_folder_name}", locals())


# PSD Operations
# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=12)
@pytest.mark.parametrize("file_format", file_formats)
def test_convert_pdf_to_other_formats(api_session, file_format):
    """
    This test case verifies the functionality of an API designed to convert PDF files to various formats. It ensures
    that the API can successfully convert a provided PDF file to different formats, including JPEG, PNG, ZIP, DOCX,
    XLSX, TIFF, and TXT. The test uploads a sample PDF file to the API and requests conversion to each supported
    format. It then validates that the API responds with the expected success status code (e.g., 200) for each
    conversion request. Upon receiving the converted file, the test saves it locally for visual inspection.
    """
    test_convert_pdf_to_other_format_params["documentId"] = pdf_doc_id1
    test_convert_pdf_to_other_format_params["format"] = file_format
    response = api_session.post(url=pdf_to_other_format_url,
                                params=test_convert_pdf_to_other_format_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder(f"../downloads/pdf-{file_format}")
    save_decoded_file((response.json())['data'], file_format,
                      f'../downloads/pdf-{file_format}/converted_{file_format}')


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=13)
@pytest.mark.parametrize("operation_type, value, page_count", operation_types)
def test_pdf_split(api_session, operation_type, value, page_count):
    """
    This test case evaluates an API designed to split PDF files into smaller PDFs based on specified criteria: single
    page, page range, or random pages. For each split type,
    the test verifies that the API responds with the expected success status code (e.g., 200) and generates the new
    PDF file containing the selected pages. Upon receiving the split PDF files, the test saves them locally and
    performs validation to ensure that each file contains the correct pages as specified in the request. By executing
    this test, we confirm that the PDF splitting API effectively fulfills its purpose of allowing users to extract
    specific pages from PDF documents and generate new files tailored to their requirements.
    """

    test_pdf_split_params["documentId"] = pdf_doc_id1
    test_pdf_split_params["type"] = operation_type
    test_pdf_split_params["range"] = value

    response = api_session.post(url=pdf_split_url,
                                params=test_pdf_split_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder(f"../downloads/pdf_split_{operation_type}")
    save_decoded_file((response.json())['data'], 'pdf',
                      f'../downloads/pdf_split_{operation_type}/split_{operation_type}')
    count_pdf_pages_and_verify(f'../downloads/pdf_split_{operation_type}/split_{operation_type}_0.pdf',
                               f"PDF Split - {operation_type}", page_count)


@pytest.mark.run(order=14)
def test_pdf_rotate(api_session):
    """This test case verifies the functionality of an API designed to rotate PDF pages 90 degrees clockwise. The API
    accepts a PDF ID as a parameter and rotates the pages of the corresponding PDF document. The test validates
    that the API responds with the expected success status code (e.g., 200) for the rotation request. Upon successful
    rotation, the test saves the rotated PDF file locally on the test machine for visual inspection. The rotated file
    is then visually inspected to ensure that the pages have been rotated correctly without loss of content or
    formatting."""
    test_pdf_rotate_params["documentId"] = pdf_doc_id1
    response = api_session.post(url=pdf_rotate_url,
                                params=test_pdf_rotate_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/rotated-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/rotated-pdf/rotated_pdf')
    count_pdf_pages_and_verify('../downloads/rotated-pdf/rotated_pdf.pdf',
                               "PDF rotation", pdf_page_count)


@pytest.mark.run(order=15)
def test_pdf_compress(api_session):
    """This test case verifies the functionality of an API designed to compress PDF files. The API accepts a PDF ID
    as a parameter and compresses the corresponding PDF document. The test validates that the API responds with the
    expected success status code (e.g., 200) for the compression request. Upon successful compression, the test saves
    the compressed PDF file locally on the test machine for visual inspection."""
    test_pdf_compress_params["documentId"] = pdf_doc_id1
    response = api_session.post(url=pdf_compress_url,
                                params=test_pdf_compress_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/compressed-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/compressed-pdf/compressed_pdf')


@pytest.mark.run(order=16)
def test_convert_text_file_to_pdf(api_session):
    """
    This test case verifies the functionality of an API designed to convert txt files to PDF. It ensures that the API
    can successfully convert a provided Text file to PDF formats. The test uploads a sample PDF file to the API and
    requests conversion PDF format. It then validates that the API responds with the expected success
    status code (e.g., 200) for each conversion request. Upon receiving the converted file, the test saves it locally
    for visual inspection.
    """
    test_convert_text_file_to_pdf_params["documentId"] = txt_doc_id
    response = api_session.post(url=text_file_to_pdf_url,
                                params=test_convert_text_file_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/text-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/text-pdf/converted_pdf')


@pytest.mark.run(order=17)
def test_convert_tiff_file_to_pdf(api_session):
    """
    This test case verifies the functionality of an API designed to convert tiff files to PDF. It ensures that the API
    can successfully convert a provided tiff file to PDF formats. The test uploads a sample PDF file to the API and
    requests conversion PDF format. It then validates that the API responds with the expected success
    status code (e.g., 200) for each conversion request. Upon receiving the converted file, the test saves it locally
    for visual inspection.
    """
    test_convert_tiff_file_to_pdf_params["documentId"] = tiff_doc_id
    response = api_session.post(url=tiff_file_to_pdf_url,
                                params=test_convert_tiff_file_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/tiff-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/tiff-pdf/converted_pdf')


@pytest.mark.run(order=18)
def test_convert_image_to_pdf(api_session):
    """
    This test case verifies the functionality of an API designed to convert image to PDF. It ensures that the API
    can successfully convert a provided image to PDF format. The test uploads a sample PDF file to the API and
    requests conversion PDF format. It then validates that the API responds with the expected success
    status code (e.g., 200) for each conversion request. Upon receiving the converted file, the test saves it locally
    for visual inspection.
    """
    test_convert_image_to_pdf_params["documentId"] = image_doc_id
    response = api_session.post(url=image_to_pdf_url,
                                params=test_convert_image_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/image-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/image-pdf/converted_pdf')


@pytest.mark.run(order=19)
def test_convert_xlsx_file_to_pdf(api_session):
    """
    This test case verifies the functionality of an API designed to convert XLSX files to PDF. It ensures that the API
    can successfully convert a provided XLSX file to PDF format. The test uploads a sample PDF file to the API and
    requests conversion PDF format. It then validates that the API responds with the expected success
    status code (e.g., 200) for each conversion request. Upon receiving the converted file, the test saves it locally
    for visual inspection.
    """
    test_convert_xlsx_file_to_pdf_params["documentId"] = xlsx_doc_id
    response = api_session.post(url=xlsx_file_to_pdf_url,
                                params=test_convert_xlsx_file_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/xlsx-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/xlsx-pdf/converted_pdf')


@pytest.mark.run(order=20)
def test_merge_pdfs(api_session):
    """This test case verifies the functionality of an API designed to merge multiple PDF documents into a single
    file. The API accepts an array of document IDs as parameters, representing the PDFs to be merged. During testing,
    sample PDF files are uploaded to the API, and a merge request is made with their respective IDs. The test
    validates that the API responds with the expected success status code (e.g., 200) for the merge request. Upon
    successful merging, the test saves the merged PDF file locally on the test machine for visual inspection. The
    merged file is then visually inspected to ensure that all input documents have been combined accurately and that
    the content and formatting are preserved."""
    test_merge_pdfs_params["documentId"] = pdf_doc_id1, pdf_doc_id2
    response = api_session.post(url=merge_pdf_url,
                                params=test_merge_pdfs_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/merge-pdf")
    save_decoded_file((response.json())['data'], 'pdf',
                      '../downloads/merge-pdf/merged_pdf')


@pytest.mark.run(order=21)
def test_download_zip(api_session):
    """This test case verifies the functionality of an API designed to zip and download documents. The API accepts an
    array of document IDs as parameters, representing the documents to be zipped. The test validates that the API
    responds with the expected success status code (e.g., 200) for the download request. Upon successful download,
    the test saves the zipped file locally on the test machine for visual inspection. The zipped file is then
    visually inspected to ensure that all input documents have been included in the zip archive and can be extracted
    without any issues."""
    test_download_zip_params["documentIds"] = pdf_doc_id1, pdf_doc_id2
    response = api_session.post(url=download_zip_url,
                                params=test_download_zip_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    create_folder("../downloads/download-zip")
    save_decoded_file((response.json())['data'], 'zip',
                      '../downloads/download-zip/zip_file')


# Fav / Arc / Trash
# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.parametrize("action", actions)
@pytest.mark.run(order=22)
def test_make_file_fav_arch_trs(api_session, action):
    """
    This test focuses on setting a previously uploaded file as a favorite/archive/trash using the API under
    consideration. It verifies whether the designated file is successfully marked as a favorite by examining the
    response returned by the API. The test ensures that the file is correctly identified and that the appropriate
    action (setting as a favorite) is performed as expected.
    """
    test_make_file_fav_arch_trs_json["action"] = action
    test_make_file_fav_arch_trs_json["ids"] = [pdf_doc_id1]

    response = api_session.put(url=make_fav_arc_trs_url,
                               json=test_make_file_fav_arch_trs_json,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    assert (response.json())['message'] == "success"
    response.raise_for_status()
    assert len((response.json())['data']) != 0, "Empty Response"
    id_validation = api_obj.validate_key_value(response.json(), 'id', pdf_doc_id1)
    action_validation = api_obj.validate_key_value(response.json(), action, True)
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', updated_file_name)
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/{updated_file_name}")

    print_results(f"Successfully added {(response.json())['data'][0]['fileName']} to {action}",
                  f"Unable to add {(response.json())['data'][0]['fileName']} to {action}", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.parametrize("action", actions)
@pytest.mark.run(order=23)
def test_make_folder_fav_arch_trs(api_session, action):
    """
    This test focuses on setting a previously created folder as a favorite/archive/trash using the API under
    consideration. It verifies whether the designated file is successfully marked as a favorite by examining the
    response returned by the API. The test ensures that the file is correctly identified and that the appropriate
    action (setting as a favorite) is performed as expected.
    """
    test_make_folder_fav_arch_trs_json["action"] = action
    test_make_folder_fav_arch_trs_json["ids"] = [dir_id]

    response = api_session.put(url=make_fav_arc_trs_url,
                               json=test_make_folder_fav_arch_trs_json,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    id_validation = api_obj.validate_key_value(response.json(), 'id', dir_id)
    action_validation = api_obj.validate_key_value(response.json(), action, True)
    folder_name_validation = api_obj.validate_key_value(response.json(), 'folderName', updated_folder_name)
    folder_path_validation = api_obj.validate_key_value(response.json(), 'folderPath',
                                                        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}")

    print_results(f"Successfully added {(response.json())['data'][0]['folderName']} to {action}",
                  f"Unable to add {(response.json())['data'][0]['folderName']} to {action}", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=24)
@pytest.mark.parametrize("action", actions)
def test_get_all_fav_arch_trs_file(api_session, action):
    """
    This test focuses on an API endpoint responsible for retrieving documents marked as favorites,
    archived, or trashed, depending on the provided parameters. By specifying the action (e.g., trash, favorite,
    archive) and the resource type (document or folder), the test submits a request to the API to fetch the relevant
    items. The purpose of this test is to verify the accuracy of the API's response in returning the expected
    documents or folders based on their marked status
    """
    test_get_all_fav_arch_trs_file_params["action"] = action

    response = api_session.get(url=get_all_fav_arc_trs_url,
                               params=test_get_all_fav_arch_trs_file_params,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    id_validation = api_obj.validate_key_value(response.json(), 'id', pdf_doc_id1)
    file_name_validation = api_obj.validate_key_value(response.json(), 'fileName', updated_file_name)
    directory_name_validation = api_obj.validate_key_value(response.json(), 'directoryName',
                                                           f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/{updated_file_name}")

    print_results(f"Successfully fetched document {updated_file_name}",
                  f"Unable to fetch document {updated_file_name}", locals())


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=25)
@pytest.mark.parametrize("action", actions)
def test_get_all_fav_arch_trs_folder(api_session, action):
    """
    This test focuses on an API endpoint responsible for retrieving folders marked as favorites,
    archived, or trashed, depending on the provided parameters. By specifying the action (e.g., trash, favorite,
    archive) and the resource type (document or folder), the test submits a request to the API to fetch the relevant
    items. The purpose of this test is to verify the accuracy of the API's response in returning the expected
    documents or folders based on their marked status
    """
    test_get_all_fav_arch_trs_folder_params["action"] = action

    response = api_session.get(url=get_all_fav_arc_trs_url,
                               params=test_get_all_fav_arch_trs_folder_params,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    id_validation = api_obj.validate_key_value(response.json(), 'id', dir_id)
    folder_name_validation = api_obj.validate_key_value(response.json(), 'folderName', updated_folder_name)
    folder_path_validation = api_obj.validate_key_value(response.json(), 'folderPath',
                                                        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}")

    print_results(f"Successfully fetched folder {updated_folder_name}",
                  f"Unable to fetch folder {updated_folder_name}", locals())


'''
# Permanent Delete
@pytest.mark.skip(reason="skipping as permanent delete will not be part of IDOCX")
@pytest.mark.run(order=25)
def test_delete_file_fav_arch_trs(api_session):
    """
    This test focuses on an API endpoint responsible for deleting documents or folders marked as favorites, archived,
    or trashed. It submits a request to the API with specific parameters, including the IDs of the items to be
    deleted and their type (document or folder). The purpose of this test is to verify that the API successfully
    processes the deletion request and removes the specified items from the system.
    """
    test_delete_file_fav_arch_trs_json["ids"] = [pdf_doc_id1]
    response = api_session.delete(url=delete_fav_arc_trs_url,
                                  json=test_delete_file_fav_arch_trs_json,
                                  headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    res = api_obj.validate_key_value(response.json(), 'data', "Successfully deleted the :document")

    if res:
        print(f"PASSED: Successfully deleted file {pdf_doc_id1}")
    else:
        raise Exception(f"FAILED: Unable to delete the  file {pdf_doc_id1}")


@pytest.mark.skip(reason="skipping as permanent delete will not be part of IDOCX")
@pytest.mark.run(order=26)
def test_delete_folder_fav_arch_trs(api_session):
    """
    This test focuses on an API endpoint responsible for deleting documents or folders marked as favorites, archived,
    or trashed. It submits a request to the API with specific parameters, including the IDs of the items to be
    deleted and their type (document or folder). The purpose of this test is to verify that the API successfully
    processes the deletion request and removes the specified items from the system.
    """
    test_delete_folder_fav_arch_trs_json["ids"] = [dir_id]
    response = api_session.delete(url=delete_fav_arc_trs_url,
                                  json=test_delete_folder_fav_arch_trs_json,
                                  headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    res = api_obj.validate_key_value(response.json(), 'data', "Successfully deleted the :folder")

    if res:
        print(f"PASSED: Successfully deleted folder {dir_id}")
    else:
        raise Exception(f"FAILED: Unable to delete the  folder {dir_id}")

'''


