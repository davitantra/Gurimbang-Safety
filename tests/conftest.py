import os
import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set dummy env vars needed by main.py build_connectors and agents."""
    env = {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "test",
        "MYSQL_PASSWORD": "test",
        "MYSQL_DATABASE": "test",
        "GOOGLE_SERVICE_ACCOUNT_JSON": "{}",
        "SHEET_ID_PJ_AREA": "dummy_sheet_id",
        "SHEET_ID_KATEGORI_RISIKO": "dummy_sheet_id",
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "BLINDSPOT_THRESHOLD_DAYS": "14",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
