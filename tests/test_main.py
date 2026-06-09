import pytest
from unittest.mock import patch, MagicMock


def test_main_runs_all_agents_in_order():
    with patch("main.AgentAgregasi") as MockAgregasi, \
         patch("main.AgentValidasi") as MockValidasi, \
         patch("main.AgentPelaporan") as MockPelaporan, \
         patch("main.MySQLConnector"), \
         patch("main.SheetsConnector"), \
         patch("main.anthropic.Anthropic"):

        mock_agregasi_inst = MagicMock()
        mock_agregasi_inst.run.return_value = {"date": "2026-06-09", "findings": [], "summary": {}}
        MockAgregasi.return_value = mock_agregasi_inst

        mock_validasi_inst = MagicMock()
        mock_validasi_inst.run.return_value = {"date": "2026-06-09", "findings": [], "summary": {}}
        MockValidasi.return_value = mock_validasi_inst

        mock_pelaporan_inst = MagicMock()
        mock_pelaporan_inst.run.return_value = {"markdown": "# Test", "docx_path": "test.docx"}
        MockPelaporan.return_value = mock_pelaporan_inst

        from main import run_pipeline
        result = run_pipeline()

        assert mock_agregasi_inst.run.called
        assert mock_validasi_inst.run.called
        assert mock_pelaporan_inst.run.called
        assert "markdown" in result
