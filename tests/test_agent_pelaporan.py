import pytest
import os
from datetime import date, timedelta
from unittest.mock import patch
from agents.agent_pelaporan import AgentPelaporan


def make_validated_dataset():
    today = str(date.today())
    return {
        "date": today,
        "findings": [
            {
                "id": 1, "location_id": 10, "description": "Kabel terkelupas",
                "inspection_date": today, "status": "Open",
                "risk_level": "High",
                "due_date": str(date.today() + timedelta(days=1)),
                "closed_date": None,
                "location_name": "Area Tambang A", "area": "Pit 1", "site": "GMO",
                "pj_name": "Budi Santoso", "pj_contact": "08123456789",
                "is_blindspot": False, "is_overdue": False,
                "is_high_risk": True, "validation_source": "rule-based",
            }
        ],
        "incidents": [],
        "summary": {"total": 1, "overdue": 0, "high_risk": 1, "blindspot": 0, "needs_intervention": 1},
    }


def test_run_returns_markdown_string():
    agent = AgentPelaporan(reports_dir="reports")
    dataset = make_validated_dataset()
    with patch.object(agent, "_save_docx"):
        result = agent.run(dataset)
    assert isinstance(result["markdown"], str)
    assert "Gurimbang Safety" in result["markdown"]
    assert "Budi Santoso" in result["markdown"]


def test_markdown_contains_summary():
    agent = AgentPelaporan(reports_dir="reports")
    dataset = make_validated_dataset()
    with patch.object(agent, "_save_docx"):
        result = agent.run(dataset)
    assert "Total Temuan" in result["markdown"]
    assert "High Risk" in result["markdown"]


def test_run_returns_docx_path():
    agent = AgentPelaporan(reports_dir="reports")
    dataset = make_validated_dataset()
    with patch.object(agent, "_save_docx", return_value="reports/2026-06-09/laporan.docx"):
        result = agent.run(dataset)
    assert "docx_path" in result
