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
    pattern = r'\b\w*Error:'
    # assertion_error_pattern = r"AssertionError:.*?Failed conditions:(.*)"
    match = re.findall(pattern, text)

    if len(match) != 0:
        result = match[0].replace(":", "")
        return result, text
    return "Error", text


def get_db_connection():
    return mysql.connector.connect(
        host="host.docker.internal",
        # host="localhost",
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
        error_type = None
        reason = None

        try:
            # Check if the test setup failed
            if request.node.rep_setup.failed:
                results = "error"
                reason = "Test setup failed"
                error_type = "Error"
            else:
                # Check if the test case failed
                if request.node.rep_call.failed:
                    results = "failed"
                    reason = str(request.node.rep_call.longrepr)
                    error_type, reason = extract_error_message(reason)
        except Exception as e:
            results = "error"
            reason = str(e)
            error_type = "Error"

        # Calculate response time
        response_time = (end_time - start_time).total_seconds()

        # Insert test result into the database
        insert_query = """
            INSERT INTO testdb.pytest_results (test_case_name, start_time, response_time, results, error_type, reason)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (test_case_name, start_time, response_time, results, error_type, reason))
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
        browser = play.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://103.171.98.14:9068")
        page.fill("//input[@placeholder='User Identification*']", username)
        page.fill("//input[@placeholder='Password*']", password)
        # page.fill("//input[@placeholder='Enter captcha text']", "a")
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
    This test case verifies that an API successfully creates a directory with a specified name. It checks that
    calling the API results in the creation of a directory at the designated path in the filesystem. If the directory
    creation operation succeeds, the test confirms that the system can create directories as intended.
    """
    global manual_dir_id
    response = api_session.post(url=create_directory_url,
                                json=test_create_manualworkspace_directory_json,
                                headers=header)
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    manual_dir_id = (response.json())['data']['id']
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
def test_create_manualworkspace_directory_with_mismatch_foldername(api_session):
    test_json = test_create_manualworkspace_directory_json.copy()
    test_json["folderName"] = "InvalidFolderName"
    response = api_session.post(url=create_directory_url,
                                json=test_json,
                                headers=header)
    assert (response.json())[
               'message'] == f"{test_json['folderName']} folder Name is not matching with given folder path {test_json['folderPath']}"
    print(json.dumps(response.json(), indent=4))


@pytest.mark.run(order=4)
@pytest.mark.parametrize('field', workspace_field_names)
def test_create_manualworkspace_directory_with_blank_fields(field, api_session):
    global error_message
    test_json = test_create_manualworkspace_directory_json.copy()
    if field == "blank_foldername":
        test_json["folderName"] = ""
        error_message = "Folder Name must not be blank."
    elif field == "blank_filepath":
        test_json["folderPath"] = ""
        error_message = "Folder Path is required"
    elif field == "character_limit":
        invalid_folder_name = "1" * 60
        test_json["filePath"] = f"/IDOC_Filesystem/workspace/manualworkspace/{invalid_folder_name}"
        test_json["folderName"] = invalid_folder_name
        error_message = "Folder Name must be a maximum of 56 characters"
    else:
        test_json = test_create_manualworkspace_directory_json
        error_message = f"Folder already exists with cifId: {cifID}"

    response = api_session.post(url=create_directory_url,
                                json=test_json,
                                headers=header)
    assert (response.json())['message'] == error_message
    print(json.dumps(response.json(), indent=4))


@pytest.mark.run(order=5)
@pytest.mark.parametrize('api_name', list(api_data.keys()))
def test_create_manual_directory_invalid_token(api_name, api_session):
    invalid_token = header.copy()
    invalid_token['Authorization'] = "invalid_token"
    response = api_session.post(url=api_data[api_name]['url'],
                                json=api_data[api_name]['data'],
                                headers=invalid_token)
    assert response.status_code == 500


@pytest.mark.run(order=6)
@pytest.mark.parametrize('workspace', workspaces)
def test_get_all_folder_structure(workspace, api_session):
    """
    This test verifies that an API correctly lists directories within a specified workspace. It checks if a newly
    created directory appears in the list returned by the API after creation.
    """
    response = api_session.get(url=get_all_folder_structure_url.format(workSpaceName=workspace),
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    if workspace == "MANUALWORKSPACE":
        id_validation = api_obj.validate_key_value(response.json(), 'id', manual_dir_id)
    workspace_type_validation = api_obj.validate_key_value(response.json(), 'workSpaceType', workspace)
    print_results(f"Folder {folder_name} exists with id {manual_dir_id}",
                  f"Folder {folder_name} doesnt exists", locals())


@pytest.mark.run(order=7)
# @pytest.mark.skip(reason="skipping for now")
def test_upload(api_session):
    """
    This test validates an API for uploading files to a specific directory. It confirms the API's success message
    upon uploading a file into the designated directory.
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


@pytest.mark.run(order=8)
@pytest.mark.parametrize('field_name', test_cases)
def test_upload_file_with_invalid_field_values(field_name, api_session):
    test_json = test_upload_data.copy()
    test_file = test_upload_file

    if field_name == "blank_files":
        test_file = test_cases[field_name][1]
    else:
        test_json[test_cases[field_name][0]] = test_cases[field_name][1]

    response = api_session.post(url=upload_url,
                                data=test_json,
                                files=test_file,
                                headers=header)
    assert (response.json())['message'] == test_cases[field_name][-1]
    print(json.dumps(response.json(), indent=4))


@pytest.mark.run(order=9)
def test_get_documents(api_session):
    """
    This test validates an API for listing files within a specified directory. It checks if the file uploaded in the
    previous step appears in the list returned by the API when queried with the directory path.
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


@pytest.mark.run(order=10)
def test_get_documents_blank_filepath(api_session):
    test_params = test_get_documents_params.copy()
    test_params['filePath'] = ""
    response = api_session.get(url=documents_url,
                               params=test_params,
                               headers=header)
    assert (response.json())['message'] == "File Path must not be blank."
    print(json.dumps(response.json(), indent=4))


@pytest.mark.run(order=11)
def test_get_download(api_session):
    """
    This test evaluates an API for downloading files using their IDs. It verifies the successful download of the file
    to the local machine by checking its integrity against the original file stored on the server.
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


@pytest.mark.run(order=12)
def test_update_file_name(api_session):
    """
    This test evaluates an API for updating file names using their IDs. It verifies the update's success by providing
    the file ID and checking the API's response.
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


@pytest.mark.run(order=13)
def test_update_file_tags(api_session):
    """
    This test evaluates an API for updating file tags using their IDs. It verifies the update's success by providing
    the file ID and checking the API's response.
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

    print_results(f"Updated file tag to {new_tag}",
                  f"Unable to update file tag to {new_tag}", locals())


@pytest.mark.run(order=14)
def test_update_file_remark(api_session):
    """
    This test evaluates an API for updating file remarks using their IDs. It verifies the update's success by providing
    the file ID and checking the API's response.
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

    print_results(f"Updated file remarks to {new_remarks}",
                  f"Unable to update file remarks to {new_remarks}", locals())


@pytest.mark.run(order=15)
def test_update_file_is_verified(api_session):
    """
    This test evaluates an API for updating file verified status using their IDs. It verifies the update's success by providing
    the file ID and checking the API's response.
    """
    test_update_file_is_verified_json["id"] = pdf_doc_id1
    response = api_session.put(update_file_url,
                               json=test_update_file_is_verified_json,
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
    verified_validation = api_obj.validate_key_value(response.json(), 'verified', True)

    print_results("Updated document verified status",
                  " Unable to update document verified status", locals())


@pytest.mark.run(order=16)
def test_update_file_password(api_session):
    """
    This test evaluates an API for updating file password using their IDs. It verifies the update's success by providing
    the file ID and checking the API's response.
    """
    test_update_file_password_json["id"] = pdf_doc_id1
    response = api_session.put(update_file_url,
                               json=test_update_file_password_json,
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
    verified_validation = api_obj.validate_key_value(response.json(), 'verified', True)
    password_validation = api_obj.validate_key_value(response.json(), 'passwordProtected', True)

    print_results("Updated document password",
                  " Unable to update document password", locals())


@pytest.mark.run(order=17)
def test_update_folder_name(api_session):
    """
    This test case evaluates an API for updating folder names. It verifies the functionality by providing a folder
    ID, updating its name, and checking the API response for successful execution.
    """
    response = api_session.put(update_folder_url.format(id=manual_dir_id),
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


@pytest.mark.run(order=18)
def test_auditing_documents(api_session):
    test_audit_params["id"] = pdf_doc_id1
    response = api_session.get(url=auditing_url,
                               params=test_audit_params,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    resource_id_validation = api_obj.validate_key_value(response.json(), 'resourceId', pdf_doc_id1)
    resource_type_validation = api_obj.validate_key_value(response.json(), 'resourceType', "DOCUMENT")
    operated_by_validation = api_obj.validate_key_value(response.json(), 'operatedBy', username)

    print_results(f"Fetched history of document ID {manual_dir_id}",
                  f" Unable to fetch history of document ID {manual_dir_id}", locals())


@pytest.mark.run(order=19)
def test_auditing_folders(api_session):
    test_audit_params["id"] = manual_dir_id
    response = api_session.get(url=auditing_url,
                               params=test_audit_params,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    resource_id_validation = api_obj.validate_key_value(response.json(), 'resourceId', manual_dir_id)
    resource_type_validation = api_obj.validate_key_value(response.json(), 'resourceType', "FOLDER")
    operated_by_validation = api_obj.validate_key_value(response.json(), 'operatedBy', username)

    print_results(f"Fetched history of folder ID {manual_dir_id}",
                  f" Unable to fetch history of folder ID {manual_dir_id}", locals())


@pytest.mark.run(order=20)
@pytest.mark.parametrize('validation', list(password_validations.keys()))
def test_check_password(validation, api_session):
    test_check_password_json["id"] = pdf_doc_id1
    test_check_password_json["password"] = password_validations[validation][0]

    response = api_session.post(url=check_password_url,
                                json=test_check_password_json,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    data_validation = api_obj.validate_key_value(response.json(), 'data', password_validations[validation][1])

    print_results(f"Fetched history of folder ID {manual_dir_id}",
                  f" Unable to fetch history of folder ID {manual_dir_id}", locals())


@pytest.mark.run(order=21)
def test_get_all_flexcube_documents(api_session):
    response = api_session.get(url=flexcube_documents.format(cifID=cifID))
    print(response.content)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"


# Search
# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=22)
@pytest.mark.parametrize("search_filter", search_filters)
def test_search_file(api_session, search_filter):
    """
    This test evaluates the search functionality of an API for folders and files. It verifies whether uploaded files
    and created directories are correctly listed based on specified search parameters. The test examines the API
    response to confirm accurate retrieval and listing of expected items.
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


# PDF Operations
# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=12)
@pytest.mark.parametrize("file_format", file_formats)
def test_convert_pdf_to_other_formats(api_session, file_format):
    """
    This test case verifies that an API correctly converts PDF files to various formats including JPEG, PNG, DOCX,
    XLSX, TIFF, and TXT. It uploads a sample PDF file, requests conversion to each format, and checks for a success
    status code (e.g., 200). The converted files are saved locally for visual inspection to confirm successful
    conversion.
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
    # create_folder(f"../downloads/pdf-{file_format}") save_decoded_file((response.json())['data'], file_format,
    # f'../downloads/pdf-{file_format}/converted_{file_format}')


# @pytest.mark.skip(reason="skipping for now")
@pytest.mark.run(order=13)
@pytest.mark.parametrize("operation_type, value, page_count", operation_types)
def test_pdf_split(api_session, operation_type, value, page_count):
    """
    This test case verifies that an API correctly splits PDF files by single page, page range, or random pages. It
    checks for a success status code (e.g., 200), saves the split PDFs locally, and ensures they contain the correct
    pages. This confirms the API's functionality in extracting specific pages and generating new PDF files.
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
    '''create_folder(f"../downloads/pdf_split_{operation_type}") save_decoded_file((response.json())['data'], 'pdf', 
    f'../downloads/pdf_split_{operation_type}/split_{operation_type}')
    count_pdf_pages_and_verify(
    f'../downloads/pdf_split_{operation_type}/split_{operation_type}_0.pdf', f"PDF Split - {operation_type}", 
    page_count)'''


@pytest.mark.run(order=14)
def test_pdf_rotate(api_session):
    """This test case verifies that an API correctly rotates PDF pages 90 degrees clockwise. It provides a PDF ID,
    requests rotation, and checks for a success status code (e.g., 200). The rotated PDF is saved locally for visual
    inspection to ensure the pages have been correctly rotated without loss of content or formatting."""
    test_pdf_rotate_params["documentId"] = pdf_doc_id1
    response = api_session.post(url=pdf_rotate_url,
                                params=test_pdf_rotate_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/rotated-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/rotated-pdf/rotated_pdf')
    count_pdf_pages_and_verify('../downloads/rotated-pdf/rotated_pdf.pdf', "PDF rotation", pdf_page_count)
    '''


@pytest.mark.run(order=15)
def test_pdf_compress(api_session):
    """This test case verifies that an API correctly compresses PDF files. It provides a PDF ID,
    requests compression, and checks for a success status code (e.g., 200). The compressed PDF is saved locally for
    visual inspection."""
    test_pdf_compress_params["documentId"] = pdf_doc_id1
    response = api_session.post(url=pdf_compress_url,
                                params=test_pdf_compress_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/compressed-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/compressed-pdf/compressed_pdf')'''


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
    '''create_folder("../downloads/text-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/text-pdf/converted_pdf')'''


@pytest.mark.run(order=17)
def test_convert_tiff_file_to_pdf(api_session):
    """
    This test case verifies that an API correctly converts TIFF files to PDF. It uploads a sample TIFF file,
    requests the conversion, and checks for a success status code (e.g., 200). The converted PDF is saved locally for
    visual inspection.
    """
    test_convert_tiff_file_to_pdf_params["documentId"] = tiff_doc_id
    response = api_session.post(url=tiff_file_to_pdf_url,
                                params=test_convert_tiff_file_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/tiff-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/tiff-pdf/converted_pdf')'''


@pytest.mark.run(order=18)
def test_convert_image_to_pdf(api_session):
    """
    This test case verifies that an API correctly converts images to PDF. It uploads a sample image, requests the
    conversion, and checks for a success status code (e.g., 200). The converted PDF is saved locally for visual
    inspection.
    """
    test_convert_image_to_pdf_params["documentId"] = image_doc_id
    response = api_session.post(url=image_to_pdf_url,
                                params=test_convert_image_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/image-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/image-pdf/converted_pdf')'''


@pytest.mark.run(order=19)
def test_convert_xlsx_file_to_pdf(api_session):
    """
    This test case verifies that an API correctly converts XLSX files to PDF. It uploads a sample XLSX file,
    requests the conversion, and checks for a success status code (e.g., 200). The converted PDF is saved locally for
    visual inspection.
    """
    test_convert_xlsx_file_to_pdf_params["documentId"] = xlsx_doc_id
    response = api_session.post(url=xlsx_file_to_pdf_url,
                                params=test_convert_xlsx_file_to_pdf_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/xlsx-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/xlsx-pdf/converted_pdf')'''


@pytest.mark.run(order=20)
def test_merge_pdfs(api_session):
    """This test case verifies that an API correctly merges multiple PDF documents into a single file. It uploads
    sample PDFs, sends a merge request with their IDs, and checks for a success status code (e.g., 200). The merged
    PDF is saved locally for visual inspection to ensure all input documents are combined accurately, preserving
    content and formatting."""
    test_merge_pdfs_params["documentId"] = pdf_doc_id1, pdf_doc_id2
    response = api_session.post(url=merge_pdf_url,
                                params=test_merge_pdfs_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/merge-pdf")
    save_decoded_file((response.json())['data'], 'pdf', '../downloads/merge-pdf/merged_pdf')'''


# @pytest.mark.skip("Skipping for now")
@pytest.mark.run(order=21)
def test_download_zip(api_session):
    """This test case verifies that an API correctly zips and downloads documents given an array of document IDs. It
    ensures the API responds with a success status code (e.g., 200). The test then saves the downloaded zip file
    locally for visual inspection to confirm all input documents are included and can be extracted without issues."""
    test_download_zip_params["documentIds"] = pdf_doc_id1, pdf_doc_id2
    response = api_session.post(url=download_zip_url,
                                params=test_download_zip_params,
                                headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    '''create_folder("../downloads/download-zip")
    save_decoded_file((response.json())['data'], 'zip', '../downloads/download-zip/zip_file')'''


'''
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
    test_make_folder_fav_arch_trs_json["ids"] = [manual_dir_id]

    response = api_session.put(url=make_fav_arc_trs_url,
                               json=test_make_folder_fav_arch_trs_json,
                               headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    id_validation = api_obj.validate_key_value(response.json(), 'id', manual_dir_id)
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
    id_validation = api_obj.validate_key_value(response.json(), 'id', manual_dir_id)
    folder_name_validation = api_obj.validate_key_value(response.json(), 'folderName', updated_folder_name)
    folder_path_validation = api_obj.validate_key_value(response.json(), 'folderPath',
                                                        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}")

    print_results(f"Successfully fetched folder {updated_folder_name}",
                  f"Unable to fetch folder {updated_folder_name}", locals())



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
    test_delete_folder_fav_arch_trs_json["ids"] = [manual_dir_id]
    response = api_session.delete(url=delete_fav_arc_trs_url,
                                  json=test_delete_folder_fav_arch_trs_json,
                                  headers=header)
    print(json.dumps(response.json(), indent=4))
    response.raise_for_status()
    assert (response.json())['message'] == "success"
    assert len((response.json())['data']) != 0, "Empty Response"
    res = api_obj.validate_key_value(response.json(), 'data', "Successfully deleted the :folder")

    if res:
        print(f"PASSED: Successfully deleted folder {manual_dir_id}")
    else:
        raise Exception(f"FAILED: Unable to delete the  folder {manual_dir_id}")

'''
