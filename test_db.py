import mysql.connector
from datetime import datetime
import traceback
import json
import time
import requests
import pytest
from api_data import *
from api_methods import APIFramework
from endpoints import *
from utilities import *
from playwright.sync_api import sync_playwright

api_obj = APIFramework()


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


