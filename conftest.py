import pytest
from pytest_metadata.plugin import metadata_key


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
    outcome = yield
    report = outcome.get_result()
    report.description = item.function.__doc__


def pytest_html_results_table_row(report, cells):
    if hasattr(report, "description"):
        cells.insert(2, f"<td>{report.description}</td>")
    else:
        cells.insert(2, "<td>No description available</td>")
