import pytest
import time
from influxdb import InfluxDBClient

@pytest.fixture(scope='session', autouse=True)
def influxdb_client():
    client = InfluxDBClient(host='172.17.0.4', port=8086, database='pytest_data')
    yield client
    client.close()

@pytest.fixture(scope='function', autouse=True)
def test_start_time():
    start_time = time.time()
    yield start_time

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == 'call':
        if rep.failed:
            error_message = rep.longreprtext
        else:
            error_message = ""
        end_time = time.time()
        json_body = [
            {
                "measurement": "test_results",
                "tags": {
                    "test_name": item.name,
                    "test_result": "fail" if rep.failed else "pass",
                    "error_message": error_message
                },
                "fields": {
                    "start_time": start_time,
                    "end_time": end_time
                }
            }
        ]
        influxdb_client.write_points(json_body)
      
  def test_example():
    assert 1 == 1  # This test will pass

def test_another_example():
    assert 1 == 2  # This test will fail
