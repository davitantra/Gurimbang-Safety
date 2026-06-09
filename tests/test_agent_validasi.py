import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from agents.agent_validasi import AgentValidasi


def make_finding(overrides=None):
    base = {
        "id": 1,
        "location_id": 10,
        "description": "Kabel terkelupas di panel listrik",
        "inspection_date": str(date.today()),
        "status": "Open",
        "risk_level": "High",
        "due_date": None,
        "closed_date": None,
        "created_at": str(date.today()),
        "location_name": "Area A",
        "area": "Pit 1",
        "site": "GMO",
        "pj_name": "Budi",
        "pj_contact": "081",
        "last_inspection_date": str(date.today()),
        "is_blindspot": None,
        "is_overdue": None,
        "is_high_risk": None,
        "validation_source": None,
    }
    if overrides:
        base.update(overrides)
    return base


def make_dataset(findings):
    return {
        "date": str(date.today()),
        "findings": findings,
        "incidents": [],
        "risk_categories": [{"category_name": "Electrical Hazard"}],
        "location_map": {},
        "last_inspection_map": {},
    }


def test_high_risk_due_date_is_1_day():
    finding = make_finding({"risk_level": "High", "created_at": str(date.today())})
    dataset = make_dataset([finding])
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]
    expected_due = str(date.today() + timedelta(days=1))
    assert f["due_date"] == expected_due
    assert f["validation_source"] == "rule-based"


def test_medium_risk_due_date_is_3_days():
    finding = make_finding({"risk_level": "Medium", "created_at": str(date.today())})
    dataset = make_dataset([finding])
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]
    expected_due = str(date.today() + timedelta(days=3))
    assert f["due_date"] == expected_due


def test_low_risk_due_date_is_7_days():
    finding = make_finding({"risk_level": "Low", "created_at": str(date.today())})
    dataset = make_dataset([finding])
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]
    expected_due = str(date.today() + timedelta(days=7))
    assert f["due_date"] == expected_due


def test_overdue_flagged_correctly():
    overdue_created = str(date.today() - timedelta(days=5))
    finding = make_finding({"risk_level": "High", "created_at": overdue_created})
    dataset = make_dataset([finding])
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]
    assert f["is_overdue"] is True


def test_blindspot_flagged_when_no_inspection_beyond_threshold():
    old_date = str(date.today() - timedelta(days=20))
    finding = make_finding({"last_inspection_date": old_date})
    dataset = make_dataset([finding])
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]
    assert f["is_blindspot"] is True


def test_not_blindspot_when_recent_inspection():
    recent_date = str(date.today() - timedelta(days=5))
    finding = make_finding({"last_inspection_date": recent_date})
    dataset = make_dataset([finding])
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]
    assert f["is_blindspot"] is False


def test_llm_called_when_risk_level_is_none():
    finding = make_finding({"risk_level": None, "due_date": None})
    dataset = make_dataset([finding])

    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"risk_level": "High", "is_high_risk": true, "is_blindspot": false, "reasoning": "Kabel terkelupas sangat berbahaya"}')]
    mock_client.messages.create.return_value = mock_message

    agent = AgentValidasi(anthropic_client=mock_client, blindspot_threshold_days=14)
    result = agent.run(dataset)
    f = result["findings"][0]

    assert mock_client.messages.create.called
    assert f["risk_level"] == "High"
    assert f["is_high_risk"] is True
    assert f["validation_source"] == "llm"


def test_llm_not_called_when_risk_level_known():
    finding = make_finding({"risk_level": "High"})
    dataset = make_dataset([finding])

    mock_client = MagicMock()
    agent = AgentValidasi(anthropic_client=mock_client, blindspot_threshold_days=14)
    agent.run(dataset)

    assert not mock_client.messages.create.called


def test_summary_counts_are_correct():
    findings = [
        make_finding({"risk_level": "High", "created_at": str(date.today() - timedelta(days=5))}),
        make_finding({"risk_level": "Low", "created_at": str(date.today())}),
        make_finding({"risk_level": "High", "created_at": str(date.today())}),
    ]
    dataset = make_dataset(findings)
    agent = AgentValidasi(anthropic_client=None, blindspot_threshold_days=14)
    result = agent.run(dataset)

    assert result["summary"]["total"] == 3
    assert result["summary"]["high_risk"] == 2
    assert result["summary"]["overdue"] == 1
