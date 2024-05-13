import pytest
import mysql.connector
from datetime import datetime

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
        status = "passed"
        fail_reason = None

        try:
            request.node.rep_setup.failed
        except AssertionError as e:
            status = "failed"
            fail_reason = str(e)
        except Exception as e:
            status = "error"
            fail_reason = traceback.format_exc()

        insert_query = """
            INSERT INTO pytest_results (test_case_name, start_time, results, fail_reason)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (test_case_name, start_time, status, fail_reason))
        connection.commit()

        cursor.close()
        connection.close()

    request.addfinalizer(teardown)
    setup()

def test_pass():
    assert True

def test_fail():
    assert False
