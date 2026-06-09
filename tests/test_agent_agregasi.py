import pytest
from unittest.mock import MagicMock
from agents.agent_agregasi import AgentAgregasi


@pytest.fixture
def sample_findings():
    return [
        {"id": 1, "location_id": 10, "description": "Kabel terkelupas",
         "inspection_date": "2026-06-08", "status": "Open",
         "risk_level": None, "due_date": None, "closed_date": None,
         "created_at": "2026-06-08 08:00:00"}
    ]

@pytest.fixture
def sample_locations():
    return [{"id": 10, "name": "Area Tambang A", "area": "Pit 1", "site": "GMO"}]

@pytest.fixture
def sample_incidents():
    return [{"id": 5, "location_id": 10, "description": "Kecelakaan ringan",
              "incident_date": "2026-06-07", "status": "Open"}]

@pytest.fixture
def sample_last_inspections():
    return [{"location_id": 10, "last_inspection_date": "2026-06-08"}]

@pytest.fixture
def sample_pj_map():
    return {"10": {"location_id": "10", "pj_name": "Budi Santoso",
                   "pj_contact": "08123456789", "area": "Pit 1"}}

@pytest.fixture
def sample_risk_categories():
    return [{"category_name": "Electrical Hazard", "description": "Bahaya listrik"}]


def test_aggregate_returns_correct_structure(
    sample_findings, sample_locations, sample_incidents,
    sample_last_inspections, sample_pj_map, sample_risk_categories
):
    mysql_mock = MagicMock()
    mysql_mock.get_findings.return_value = sample_findings
    mysql_mock.get_locations.return_value = sample_locations
    mysql_mock.get_incidents.return_value = sample_incidents
    mysql_mock.get_last_inspection_per_location.return_value = sample_last_inspections

    sheets_mock = MagicMock()
    sheets_mock.get_pj_map.return_value = sample_pj_map
    sheets_mock.get_risk_categories.return_value = sample_risk_categories

    agent = AgentAgregasi(mysql_connector=mysql_mock, sheets_connector=sheets_mock)
    result = agent.run()

    assert "date" in result
    assert "findings" in result
    assert "incidents" in result
    assert "risk_categories" in result
    assert isinstance(result["findings"], list)


def test_findings_enriched_with_pj_data(
    sample_findings, sample_locations, sample_incidents,
    sample_last_inspections, sample_pj_map, sample_risk_categories
):
    mysql_mock = MagicMock()
    mysql_mock.get_findings.return_value = sample_findings
    mysql_mock.get_locations.return_value = sample_locations
    mysql_mock.get_incidents.return_value = sample_incidents
    mysql_mock.get_last_inspection_per_location.return_value = sample_last_inspections

    sheets_mock = MagicMock()
    sheets_mock.get_pj_map.return_value = sample_pj_map
    sheets_mock.get_risk_categories.return_value = sample_risk_categories

    agent = AgentAgregasi(mysql_connector=mysql_mock, sheets_connector=sheets_mock)
    result = agent.run()

    finding = result["findings"][0]
    assert finding["pj_name"] == "Budi Santoso"
    assert finding["location_name"] == "Area Tambang A"
