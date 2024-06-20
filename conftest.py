import pytest
import requests
from datetime import datetime
from pytest_metadata.plugin import metadata_key

passed_count = 0
failed_count = 0
skipped_count = 0
total_count = 0

def pytest_configure(config):
    config.stash[metadata_key]["Test Executed By"] = "Deekshith"


def pytest_html_report_title(report):
    report.title = "Test-Report"


def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend(["<p>Suite Description: API testing of IDOCX API's</p>"])


def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>Description</th>")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global passed_count, failed_count, skipped_count, total_count
    outcome = yield
    report = outcome.get_result()
    report.description = item.function.__doc__

    if call.when == 'call':
        total_count += 1
        if call.excinfo is None:
            passed_count += 1
        elif call.excinfo.errisinstance(pytest.skip.Exception):
            skipped_count += 1
        else:
            failed_count += 1


def pytest_html_results_table_row(report, cells):
    if hasattr(report, "description"):
        cells.insert(2, f"<td>{report.description}</td>")
    else:
        cells.insert(2, "<td>No description available</td>")


@pytest.fixture(scope='session', autouse=True)
def final_cleanup(request):
    yield
    current_date_time = datetime.now().strftime("%m-%d-%Y %I:%M:%S %p")
    message = f'[b]Regression Testing Summary for IDOCX[/b]%0ADate: {current_date_time}%0A%0APassed: {passed_count}%0AFailed: {failed_count}%0ASkipped: {failed_count}%0ATotal Test Cases: {total_count}'
    requests.get(f'https://sirmaglobal.bitrix24.com/rest/118/b2iecuj66krfw9kk/imbot.message.add.json?BOT_ID=214&CLIENT_ID=6gvjn227c5aayn2qo6ur6e16rpbwtn4r&DIALOG_ID=216&MESSAGE={message}')
    print("Bitrix Notification Sent!")


