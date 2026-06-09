import pytest
from unittest.mock import patch, MagicMock
from connectors.sheets_connector import SheetsConnector


def test_get_pj_area_returns_list():
    connector = SheetsConnector(
        service_account_json="fake.json",
        pj_sheet_id="sheet_id_1",
        risk_category_sheet_id="sheet_id_2"
    )
    mock_records = [
        {"location_id": "10", "pj_name": "Budi Santoso", "pj_contact": "08123456789", "area": "Pit 1"}
    ]
    with patch.object(connector, "_read_sheet", return_value=mock_records):
        result = connector.get_pj_area()
    assert isinstance(result, list)
    assert result[0]["pj_name"] == "Budi Santoso"


def test_get_risk_categories_returns_list():
    connector = SheetsConnector(
        service_account_json="fake.json",
        pj_sheet_id="sheet_id_1",
        risk_category_sheet_id="sheet_id_2"
    )
    mock_records = [
        {"category_name": "Electrical Hazard", "description": "Bahaya listrik"}
    ]
    with patch.object(connector, "_read_sheet", return_value=mock_records):
        result = connector.get_risk_categories()
    assert isinstance(result, list)
    assert result[0]["category_name"] == "Electrical Hazard"


def test_get_pj_map_returns_dict_keyed_by_location_id():
    connector = SheetsConnector(
        service_account_json="fake.json",
        pj_sheet_id="sheet_id_1",
        risk_category_sheet_id="sheet_id_2"
    )
    mock_records = [
        {"location_id": "10", "pj_name": "Budi", "pj_contact": "081", "area": "Pit 1"},
        {"location_id": "11", "pj_name": "Sari", "pj_contact": "082", "area": "Pit 2"},
    ]
    with patch.object(connector, "_read_sheet", return_value=mock_records):
        result = connector.get_pj_map()
    assert result["10"]["pj_name"] == "Budi"
    assert result["11"]["pj_name"] == "Sari"
