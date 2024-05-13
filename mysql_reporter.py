import pytest
import mysql.connector
from datetime import datetime

def pytest_addoption(parser):
    parser.addoption("--mysql-reporter", action="store_true", help="Enable MySQL test reporter")

class MySQLReporter(pytest.TerminalReporter):
    def __init__(self, config):
        super().__init__(config)
        if config.getoption("--mysql-reporter"):
            self.db_connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Sirma@123",
                database="testdb"
            )
            self.cursor = self.db_connection.cursor()
        else:
            self.db_connection = None

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            test_case_name = report.nodeid
            start_time = report.started
            status = "passed" if report.passed else "failed"
            fail_reason = report.longrepr.reprcrash.message if report.failed else None

            insert_query = """
                INSERT INTO test_results (test_case_name, start_time, status, fail_reason)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(insert_query, (test_case_name, start_time, status, fail_reason))
            self.db_connection.commit()

    def pytest_sessionfinish(self, session):
        self.db_connection.close()
