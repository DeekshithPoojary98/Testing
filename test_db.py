import pytest
import mysql.connector
from datetime import datetime

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sirma@123",
        database="testdb"
    )

@pytest.fixture(scope="function", autouse=True)
def insert_test_data(request):
    connection = get_db_connection()
    cursor = connection.cursor()

    def teardown():
        test_case_name = request.node.nodeid
        start_time = datetime.fromtimestamp(request.node.start_time)
        status = "passed" if request.node.rep_setup.passed else "failed"
        fail_reason = request.node.rep_setup.longreprtext if request.node.rep_setup.failed else None

        insert_query = """
            INSERT INTO pytest_results (test_case_name, start_time, status, fail_reason)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (test_case_name, start_time, status, fail_reason))
        connection.commit()
        cursor.close()
        connection.close()

    request.addfinalizer(teardown)

def test_pass():
    assert True

def test_fail():
    assert False
