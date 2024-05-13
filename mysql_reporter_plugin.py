import pytest
from mysql_reporter import MySQLReporter

def pytest_configure(config):
    config.pluginmanager.register(MySQLReporter(config), "mysql-reporter")
