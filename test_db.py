import pytest
import mysql.connector
from datetime import datetime
import traceback

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
    
        # Insert test result into the database
        insert_query = """
            INSERT INTO pytest_results (test_case_name, start_time, end_time, results, fail_reason)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (test_case_name, start_time, end_time, results, fail_reason))
        connection.commit()
    
        cursor.close()
        connection.close()
        
    request.addfinalizer(teardown)
    setup()

def test_pass():
    assert True

def test_fail():
    assert False
