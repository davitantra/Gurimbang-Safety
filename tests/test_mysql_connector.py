import pytest
from unittest.mock import patch, MagicMock
from connectors.mysql_connector import MySQLConnector


def test_get_findings_returns_list():
    connector = MySQLConnector(
        host="localhost", port=3306,
        user="test", password="test", database="test"
    )
    mock_rows = [
        {
            "id": 1, "location_id": 10, "description": "Kabel terkelupas",
            "inspection_date": "2026-06-08", "status": "Open",
            "risk_level": None, "due_date": None, "closed_date": None
        }
    ]
    with patch.object(connector, "_execute_query", return_value=mock_rows):
        result = connector.get_findings()
    assert isinstance(result, list)
    assert result[0]["id"] == 1
    assert result[0]["status"] == "Open"


def test_get_locations_returns_list():
    connector = MySQLConnector(
        host="localhost", port=3306,
        user="test", password="test", database="test"
    )
    mock_rows = [
        {"id": 10, "name": "Area Tambang A", "area": "Pit 1", "site": "GMO"}
    ]
    with patch.object(connector, "_execute_query", return_value=mock_rows):
        result = connector.get_locations()
    assert isinstance(result, list)
    assert result[0]["name"] == "Area Tambang A"


def test_get_incidents_returns_list():
    connector = MySQLConnector(
        host="localhost", port=3306,
        user="test", password="test", database="test"
    )
    mock_rows = [
        {"id": 5, "location_id": 10, "description": "Kecelakaan ringan",
         "incident_date": "2026-06-07", "status": "Open"}
    ]
    with patch.object(connector, "_execute_query", return_value=mock_rows):
        result = connector.get_incidents()
    assert isinstance(result, list)
    assert result[0]["id"] == 5
