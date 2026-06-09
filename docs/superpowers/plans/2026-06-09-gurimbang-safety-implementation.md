# Gurimbang Safety Intelligence System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun sistem AI agents harian yang menarik data safety dari AWS RDS MySQL & Google Sheets, memvalidasi temuan dengan rule-based + Claude LLM, dan menghasilkan laporan intervensi markdown + .docx otomatis setiap pagi.

**Architecture:** Tiga agen Python berjalan berurutan: Agregasi (tarik & gabung data) → Validasi (rule-based lalu LLM fallback) → Pelaporan (markdown + docx). Entry point `main.py` mengorkestrasikan ketiganya, dijadwalkan via CronCreate.

**Tech Stack:** Python 3.11+, pymysql, gspread, anthropic SDK, python-docx, python-dotenv, pytest

---

## File Map

| File | Tanggung Jawab |
|------|----------------|
| `requirements.txt` | Semua dependensi Python |
| `.env.example` | Template environment variables |
| `connectors/mysql_connector.py` | Koneksi AWS RDS, query insiden/inspeksi/lokasi |
| `connectors/sheets_connector.py` | Koneksi Google Sheets, baca PJ area & kategori risiko |
| `agents/agent_agregasi.py` | Gabungkan semua data menjadi satu struktur |
| `agents/agent_validasi.py` | Rule-based + LLM fallback validation |
| `agents/agent_pelaporan.py` | Generate laporan markdown + docx |
| `main.py` | Orkestrator: jalankan semua agents berurutan |
| `tests/test_mysql_connector.py` | Unit test MySQL connector |
| `tests/test_sheets_connector.py` | Unit test Sheets connector |
| `tests/test_agent_agregasi.py` | Unit test agent agregasi |
| `tests/test_agent_validasi.py` | Unit test validasi rule-based & LLM |
| `tests/test_agent_pelaporan.py` | Unit test pelaporan |
| `tests/test_main.py` | Integration test orchestrator |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `connectors/__init__.py`
- Create: `agents/__init__.py`
- Create: `tests/__init__.py`
- Create: `reports/.gitkeep`

- [ ] **Step 1: Buat folder structure**

```bash
cd C:\Users\davi.tantra\Documents\Claude\Gurimbang-Safety
mkdir connectors agents tests reports
```

- [ ] **Step 2: Buat requirements.txt**

```
pymysql==1.1.1
SQLAlchemy==2.0.30
gspread==6.1.2
google-auth==2.29.0
anthropic==0.28.0
python-docx==1.1.2
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
```

- [ ] **Step 3: Buat .env.example**

```
# AWS RDS MySQL
MYSQL_HOST=your-rds-endpoint.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_DATABASE=your_database_name

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
SHEET_ID_PJ_AREA=your_google_sheet_id_for_pj_area
SHEET_ID_KATEGORI_RISIKO=your_google_sheet_id_for_risk_categories

# Claude API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Validation Config
BLINDSPOT_THRESHOLD_DAYS=14
```

- [ ] **Step 4: Buat file `__init__.py` kosong di setiap folder**

```bash
echo. > connectors\__init__.py
echo. > agents\__init__.py
echo. > tests\__init__.py
echo. > reports\.gitkeep
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: semua package terinstall tanpa error.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example connectors/ agents/ tests/ reports/
git commit -m "chore: project setup — struktur folder dan dependencies"
```

---

## Task 2: MySQL Connector

**Files:**
- Create: `connectors/mysql_connector.py`
- Create: `tests/test_mysql_connector.py`

> **PENTING:** Sesuaikan nama tabel dan kolom di bawah dengan schema aktual database Anda sebelum menjalankan ke production.

- [ ] **Step 1: Tulis failing test**

Buat `tests/test_mysql_connector.py`:

```python
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
```

- [ ] **Step 2: Jalankan test — harus FAIL**

```bash
pytest tests/test_mysql_connector.py -v
```

Expected: `ModuleNotFoundError: No module named 'connectors.mysql_connector'`

- [ ] **Step 3: Implementasi `connectors/mysql_connector.py`**

```python
import pymysql
import pymysql.cursors
from typing import Any


class MySQLConnector:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def _get_connection(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )

    def _execute_query(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()

    def get_findings(self) -> list[dict]:
        """
        Ambil semua temuan inspeksi yang masih Open.
        SESUAIKAN nama tabel dan kolom dengan schema aktual Anda.
        """
        sql = """
            SELECT
                f.id,
                f.location_id,
                f.description,
                f.inspection_date,
                f.status,
                f.risk_level,
                f.due_date,
                f.closed_date,
                f.created_at
            FROM findings f
            WHERE f.status = 'Open'
            ORDER BY f.created_at DESC
        """
        return self._execute_query(sql)

    def get_locations(self) -> list[dict]:
        """
        Ambil semua data lokasi.
        SESUAIKAN nama tabel dan kolom dengan schema aktual Anda.
        """
        sql = """
            SELECT id, name, area, site
            FROM locations
            ORDER BY name
        """
        return self._execute_query(sql)

    def get_incidents(self) -> list[dict]:
        """
        Ambil insiden dalam 30 hari terakhir.
        SESUAIKAN nama tabel dan kolom dengan schema aktual Anda.
        """
        sql = """
            SELECT
                id,
                location_id,
                description,
                incident_date,
                status
            FROM incidents
            WHERE incident_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY incident_date DESC
        """
        return self._execute_query(sql)

    def get_last_inspection_per_location(self) -> list[dict]:
        """
        Ambil tanggal inspeksi terakhir per lokasi (untuk deteksi blindspot).
        SESUAIKAN nama tabel dan kolom dengan schema aktual Anda.
        """
        sql = """
            SELECT
                location_id,
                MAX(inspection_date) AS last_inspection_date
            FROM findings
            GROUP BY location_id
        """
        return self._execute_query(sql)
```

- [ ] **Step 4: Jalankan test — harus PASS**

```bash
pytest tests/test_mysql_connector.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add connectors/mysql_connector.py tests/test_mysql_connector.py
git commit -m "feat: mysql connector — query findings, locations, incidents"
```

---

## Task 3: Google Sheets Connector

**Files:**
- Create: `connectors/sheets_connector.py`
- Create: `tests/test_sheets_connector.py`

- [ ] **Step 1: Tulis failing test**

Buat `tests/test_sheets_connector.py`:

```python
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
```

- [ ] **Step 2: Jalankan test — harus FAIL**

```bash
pytest tests/test_sheets_connector.py -v
```

Expected: `ModuleNotFoundError: No module named 'connectors.sheets_connector'`

- [ ] **Step 3: Implementasi `connectors/sheets_connector.py`**

```python
import gspread
from google.oauth2.service_account import Credentials
from typing import Any


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class SheetsConnector:
    def __init__(self, service_account_json: str, pj_sheet_id: str, risk_category_sheet_id: str):
        self.service_account_json = service_account_json
        self.pj_sheet_id = pj_sheet_id
        self.risk_category_sheet_id = risk_category_sheet_id
        self._client = None

    def _get_client(self) -> gspread.Client:
        if self._client is None:
            creds = Credentials.from_service_account_file(
                self.service_account_json, scopes=SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client

    def _read_sheet(self, sheet_id: str, worksheet_index: int = 0) -> list[dict]:
        client = self._get_client()
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(worksheet_index)
        return worksheet.get_all_records()

    def get_pj_area(self) -> list[dict]:
        """
        Baca data penanggung jawab area dari Google Sheets.
        Kolom yang diharapkan: location_id, pj_name, pj_contact, area
        SESUAIKAN nama kolom dengan header aktual di sheet Anda.
        """
        return self._read_sheet(self.pj_sheet_id)

    def get_risk_categories(self) -> list[dict]:
        """
        Baca kategori temuan berisiko tinggi dari Google Sheets.
        Kolom yang diharapkan: category_name, description
        SESUAIKAN nama kolom dengan header aktual di sheet Anda.
        """
        return self._read_sheet(self.risk_category_sheet_id)

    def get_pj_map(self) -> dict[str, dict]:
        """
        Kembalikan dict dengan key = location_id (string),
        value = dict info PJ area.
        Memudahkan lookup cepat saat agregasi.
        """
        records = self.get_pj_area()
        return {str(r["location_id"]): r for r in records}
```

- [ ] **Step 4: Jalankan test — harus PASS**

```bash
pytest tests/test_sheets_connector.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add connectors/sheets_connector.py tests/test_sheets_connector.py
git commit -m "feat: google sheets connector — pj area dan kategori risiko"
```

---

## Task 4: Agent Agregasi

**Files:**
- Create: `agents/agent_agregasi.py`
- Create: `tests/test_agent_agregasi.py`

- [ ] **Step 1: Tulis failing test**

Buat `tests/test_agent_agregasi.py`:

```python
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
```

- [ ] **Step 2: Jalankan test — harus FAIL**

```bash
pytest tests/test_agent_agregasi.py -v
```

Expected: `ModuleNotFoundError: No module named 'agents.agent_agregasi'`

- [ ] **Step 3: Implementasi `agents/agent_agregasi.py`**

```python
from datetime import date
from connectors.mysql_connector import MySQLConnector
from connectors.sheets_connector import SheetsConnector


class AgentAgregasi:
    def __init__(self, mysql_connector: MySQLConnector, sheets_connector: SheetsConnector):
        self.mysql = mysql_connector
        self.sheets = sheets_connector

    def run(self) -> dict:
        """
        Tarik semua data dari MySQL dan Google Sheets,
        gabungkan menjadi satu struktur terpadu.
        """
        findings = self.mysql.get_findings()
        locations = self.mysql.get_locations()
        incidents = self.mysql.get_incidents()
        last_inspections = self.mysql.get_last_inspection_per_location()
        pj_map = self.sheets.get_pj_map()
        risk_categories = self.sheets.get_risk_categories()

        # Index lokasi untuk lookup cepat
        location_map = {str(loc["id"]): loc for loc in locations}

        # Index last inspection per lokasi
        last_inspection_map = {
            str(row["location_id"]): row["last_inspection_date"]
            for row in last_inspections
        }

        # Enrich setiap finding dengan data lokasi dan PJ
        enriched_findings = []
        for finding in findings:
            loc_id = str(finding["location_id"])
            location = location_map.get(loc_id, {})
            pj = pj_map.get(loc_id, {})
            enriched_findings.append({
                **finding,
                "location_name": location.get("name", "Unknown"),
                "area": location.get("area", "Unknown"),
                "site": location.get("site", "Unknown"),
                "pj_name": pj.get("pj_name", "Tidak ada PJ"),
                "pj_contact": pj.get("pj_contact", "-"),
                "last_inspection_date": last_inspection_map.get(loc_id),
                # Fields yang akan diisi oleh AgentValidasi
                "is_blindspot": None,
                "is_overdue": None,
                "is_high_risk": None,
                "validation_source": None,
            })

        return {
            "date": str(date.today()),
            "findings": enriched_findings,
            "incidents": incidents,
            "risk_categories": risk_categories,
            "location_map": location_map,
            "last_inspection_map": last_inspection_map,
        }
```

- [ ] **Step 4: Jalankan test — harus PASS**

```bash
pytest tests/test_agent_agregasi.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add agents/agent_agregasi.py tests/test_agent_agregasi.py
git commit -m "feat: agent agregasi — gabungkan data mysql dan sheets"
```

---

## Task 5: Agent Validasi — Rule-Based

**Files:**
- Create: `agents/agent_validasi.py`
- Create: `tests/test_agent_validasi.py`

- [ ] **Step 1: Tulis failing test untuk rule-based**

Buat `tests/test_agent_validasi.py`:

```python
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
```

- [ ] **Step 2: Jalankan test — harus FAIL**

```bash
pytest tests/test_agent_validasi.py -v
```

Expected: `ModuleNotFoundError: No module named 'agents.agent_validasi'`

- [ ] **Step 3: Implementasi `agents/agent_validasi.py` (rule-based dulu, LLM menyusul Task 6)**

```python
import json
from datetime import date, timedelta, datetime
from typing import Any


DUE_DATE_DAYS = {
    "High": 1,
    "Medium": 3,
    "Low": 7,
}


class AgentValidasi:
    def __init__(self, anthropic_client: Any, blindspot_threshold_days: int = 14):
        self.client = anthropic_client
        self.blindspot_threshold_days = blindspot_threshold_days

    def run(self, dataset: dict) -> dict:
        validated_findings = []
        for finding in dataset["findings"]:
            finding = self._apply_rule_based(finding)
            if self._needs_llm(finding):
                finding = self._apply_llm(finding, dataset["risk_categories"])
            validated_findings.append(finding)

        dataset["findings"] = validated_findings
        dataset["summary"] = self._build_summary(validated_findings)
        return dataset

    def _apply_rule_based(self, finding: dict) -> dict:
        finding = dict(finding)
        created_at = finding.get("created_at")
        risk_level = finding.get("risk_level")

        # Hitung due date jika risk_level sudah diketahui
        if risk_level in DUE_DATE_DAYS and not finding.get("due_date"):
            created_date = self._parse_date(created_at)
            if created_date:
                delta = timedelta(days=DUE_DATE_DAYS[risk_level])
                finding["due_date"] = str(created_date + delta)
                finding["validation_source"] = "rule-based"

        # Flag overdue
        if finding.get("due_date") and not finding.get("closed_date"):
            due = self._parse_date(finding["due_date"])
            if due and due < date.today():
                finding["is_overdue"] = True
            else:
                finding["is_overdue"] = False
        else:
            finding["is_overdue"] = False

        # Flag blindspot
        last_insp = finding.get("last_inspection_date")
        if last_insp:
            last_date = self._parse_date(last_insp)
            if last_date:
                days_since = (date.today() - last_date).days
                finding["is_blindspot"] = days_since > self.blindspot_threshold_days
            else:
                finding["is_blindspot"] = True
        else:
            finding["is_blindspot"] = True  # tidak ada inspeksi sama sekali

        return finding

    def _needs_llm(self, finding: dict) -> bool:
        """LLM dipanggil jika risk_level masih None setelah rule-based."""
        return finding.get("risk_level") is None

    def _apply_llm(self, finding: dict, risk_categories: list[dict]) -> dict:
        """Panggil Claude API untuk kasus abu-abu."""
        if self.client is None:
            return finding  # skip jika tidak ada client (test mode)

        categories_text = ", ".join(
            r.get("category_name", "") for r in risk_categories
        )
        prompt = f"""Anda adalah safety expert. Analisis temuan inspeksi berikut:

Deskripsi temuan: {finding.get("description", "")}
Lokasi: {finding.get("location_name", "")} - {finding.get("area", "")}
Kategori risiko tinggi yang diketahui: {categories_text}

Tentukan dalam format JSON:
{{
  "risk_level": "Low|Medium|High",
  "is_high_risk": true|false,
  "is_blindspot": true|false,
  "reasoning": "penjelasan singkat"
}}

Jawab HANYA dengan JSON, tanpa teks lain."""

        message = self.client.messages.create(
            model="claude-opus-4-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            raw = message.content[0].text.strip()
            llm_result = json.loads(raw)
            finding["risk_level"] = llm_result.get("risk_level", "Low")
            finding["is_high_risk"] = llm_result.get("is_high_risk", False)
            finding["validation_source"] = "llm"

            # Hitung due date setelah LLM menentukan risk level
            created_date = self._parse_date(finding.get("created_at"))
            risk = finding["risk_level"]
            if created_date and risk in DUE_DATE_DAYS:
                finding["due_date"] = str(
                    created_date + timedelta(days=DUE_DATE_DAYS[risk])
                )
        except (json.JSONDecodeError, KeyError, IndexError):
            # Fallback jika LLM response tidak valid
            finding["risk_level"] = "Medium"
            finding["is_high_risk"] = False
            finding["validation_source"] = "llm-fallback"

        return finding

    def _build_summary(self, findings: list[dict]) -> dict:
        return {
            "total": len(findings),
            "overdue": sum(1 for f in findings if f.get("is_overdue")),
            "high_risk": sum(1 for f in findings if f.get("risk_level") == "High"),
            "blindspot": sum(1 for f in findings if f.get("is_blindspot")),
            "needs_intervention": sum(
                1 for f in findings
                if f.get("is_overdue") or f.get("risk_level") == "High"
            ),
        }

    @staticmethod
    def _parse_date(value) -> date | None:
        if not value:
            return None
        if isinstance(value, date):
            return value
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        return None
```

- [ ] **Step 4: Jalankan test — harus PASS**

```bash
pytest tests/test_agent_validasi.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add agents/agent_validasi.py tests/test_agent_validasi.py
git commit -m "feat: agent validasi rule-based — due date, overdue, blindspot"
```

---

## Task 6: Agent Validasi — LLM Integration Test

**Files:**
- Modify: `tests/test_agent_validasi.py` (tambah test LLM)

- [ ] **Step 1: Tambah test LLM ke file test yang sudah ada**

Append ke `tests/test_agent_validasi.py`:

```python
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
```

- [ ] **Step 2: Jalankan semua test validasi — harus PASS**

```bash
pytest tests/test_agent_validasi.py -v
```

Expected: 9 tests PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/test_agent_validasi.py
git commit -m "test: tambah LLM integration tests untuk agent validasi"
```

---

## Task 7: Agent Pelaporan

**Files:**
- Create: `agents/agent_pelaporan.py`
- Create: `tests/test_agent_pelaporan.py`

- [ ] **Step 1: Tulis failing test**

Buat `tests/test_agent_pelaporan.py`:

```python
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
```

- [ ] **Step 2: Jalankan test — harus FAIL**

```bash
pytest tests/test_agent_pelaporan.py -v
```

Expected: `ModuleNotFoundError: No module named 'agents.agent_pelaporan'`

- [ ] **Step 3: Implementasi `agents/agent_pelaporan.py`**

```python
import os
from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


RISK_EMOJI = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}


class AgentPelaporan:
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir

    def run(self, dataset: dict) -> dict:
        """
        Generate laporan markdown dan simpan file .docx.
        Returns dict berisi 'markdown' dan 'docx_path'.
        """
        report_date = dataset.get("date", str(date.today()))
        findings = dataset.get("findings", [])
        summary = dataset.get("summary", {})

        markdown = self._build_markdown(report_date, findings, summary)
        docx_path = self._save_docx(report_date, findings, summary)

        return {"markdown": markdown, "docx_path": docx_path, "date": report_date}

    def _build_markdown(self, report_date: str, findings: list, summary: dict) -> str:
        lines = [
            f"# 📋 Laporan Harian Gurimbang Safety",
            f"**Tanggal:** {report_date}",
            "",
            "---",
            "",
            "## Ringkasan Eksekutif",
            "",
            f"| Indikator | Jumlah |",
            f"|-----------|--------|",
            f"| Total Temuan Open | {summary.get('total', 0)} |",
            f"| Overdue | {summary.get('overdue', 0)} |",
            f"| High Risk | {summary.get('high_risk', 0)} |",
            f"| Blindspot | {summary.get('blindspot', 0)} |",
            f"| Perlu Intervensi | {summary.get('needs_intervention', 0)} |",
            "",
            "---",
            "",
            "## Daftar Intervensi",
            "",
            "| # | Lokasi | Temuan | Risiko | Due Date | Status | PJ Area | Kontak |",
            "|---|--------|--------|--------|----------|--------|---------|--------|",
        ]

        for i, f in enumerate(findings, 1):
            risk = f.get("risk_level", "-")
            emoji = RISK_EMOJI.get(risk, "⚪")
            overdue_flag = " ⚠️ OVERDUE" if f.get("is_overdue") else ""
            blindspot_flag = " 🔍 BLINDSPOT" if f.get("is_blindspot") else ""
            lines.append(
                f"| {i} | {f.get('location_name','-')} ({f.get('site','-')}) "
                f"| {f.get('description','-')[:60]} "
                f"| {emoji} {risk} "
                f"| {f.get('due_date','-')}{overdue_flag} "
                f"| {f.get('status','-')}{blindspot_flag} "
                f"| {f.get('pj_name','-')} "
                f"| {f.get('pj_contact','-')} |"
            )

        lines += ["", "---", "", f"*Laporan dibuat otomatis oleh Gurimbang Safety Intelligence System*"]
        return "\n".join(lines)

    def _save_docx(self, report_date: str, findings: list, summary: dict) -> str:
        out_dir = os.path.join(self.reports_dir, report_date)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"laporan-safety-{report_date}.docx")

        doc = Document()
        doc.add_heading(f"Laporan Harian Gurimbang Safety", 0)
        doc.add_paragraph(f"Tanggal: {report_date}")
        doc.add_heading("Ringkasan Eksekutif", level=1)

        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        hdr = table.rows[0].cells
        hdr[0].text = "Indikator"
        hdr[1].text = "Jumlah"
        for label, key in [
            ("Total Temuan Open", "total"),
            ("Overdue", "overdue"),
            ("High Risk", "high_risk"),
            ("Blindspot", "blindspot"),
            ("Perlu Intervensi", "needs_intervention"),
        ]:
            row = table.add_row().cells
            row[0].text = label
            row[1].text = str(summary.get(key, 0))

        doc.add_heading("Daftar Intervensi", level=1)
        if findings:
            cols = ["No", "Lokasi", "Temuan", "Risiko", "Due Date", "Status", "PJ Area", "Kontak"]
            tbl = doc.add_table(rows=1, cols=len(cols))
            tbl.style = "Table Grid"
            for i, col in enumerate(cols):
                tbl.rows[0].cells[i].text = col
            for idx, f in enumerate(findings, 1):
                cells = tbl.add_row().cells
                cells[0].text = str(idx)
                cells[1].text = f"{f.get('location_name','-')} ({f.get('site','-')})"
                cells[2].text = f.get("description", "-")[:80]
                cells[3].text = f.get("risk_level", "-")
                due = f.get("due_date", "-")
                cells[4].text = f"{due} ⚠️" if f.get("is_overdue") else due
                cells[5].text = f.get("status", "-")
                cells[6].text = f.get("pj_name", "-")
                cells[7].text = f.get("pj_contact", "-")

        doc.save(out_path)
        return out_path
```

- [ ] **Step 4: Jalankan test — harus PASS**

```bash
pytest tests/test_agent_pelaporan.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add agents/agent_pelaporan.py tests/test_agent_pelaporan.py
git commit -m "feat: agent pelaporan — markdown dan docx report generator"
```

---

## Task 8: Main Orchestrator

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Tulis failing test**

Buat `tests/test_main.py`:

```python
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
```

- [ ] **Step 2: Jalankan test — harus FAIL**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError: cannot import name 'run_pipeline' from 'main'`

- [ ] **Step 3: Implementasi `main.py`**

```python
import os
import anthropic
from dotenv import load_dotenv

from connectors.mysql_connector import MySQLConnector
from connectors.sheets_connector import SheetsConnector
from agents.agent_agregasi import AgentAgregasi
from agents.agent_validasi import AgentValidasi
from agents.agent_pelaporan import AgentPelaporan

load_dotenv()


def build_connectors():
    mysql = MySQLConnector(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ.get("MYSQL_PORT", 3306)),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )
    sheets = SheetsConnector(
        service_account_json=os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"],
        pj_sheet_id=os.environ["SHEET_ID_PJ_AREA"],
        risk_category_sheet_id=os.environ["SHEET_ID_KATEGORI_RISIKO"],
    )
    return mysql, sheets


def run_pipeline() -> dict:
    """
    Jalankan semua agents berurutan dan kembalikan hasil laporan.
    Dapat dipanggil manual maupun dari scheduler.
    """
    mysql, sheets = build_connectors()
    anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    blindspot_days = int(os.environ.get("BLINDSPOT_THRESHOLD_DAYS", 14))

    print("🔄 [1/3] Menjalankan Agent Agregasi...")
    agent_agregasi = AgentAgregasi(mysql_connector=mysql, sheets_connector=sheets)
    dataset = agent_agregasi.run()
    print(f"   ✅ {len(dataset['findings'])} temuan ditemukan")

    print("🔄 [2/3] Menjalankan Agent Validasi...")
    agent_validasi = AgentValidasi(
        anthropic_client=anthropic_client,
        blindspot_threshold_days=blindspot_days,
    )
    dataset = agent_validasi.run(dataset)
    s = dataset["summary"]
    print(f"   ✅ {s['overdue']} overdue | {s['high_risk']} high risk | {s['blindspot']} blindspot")

    print("🔄 [3/3] Menjalankan Agent Pelaporan...")
    agent_pelaporan = AgentPelaporan(reports_dir="reports")
    report = agent_pelaporan.run(dataset)
    print(f"   ✅ Laporan disimpan: {report['docx_path']}")

    print("\n" + "="*60)
    print(report["markdown"])
    print("="*60)

    return report


if __name__ == "__main__":
    run_pipeline()
```

- [ ] **Step 4: Jalankan test — harus PASS**

```bash
pytest tests/test_main.py -v
```

Expected: 1 test PASSED

- [ ] **Step 5: Jalankan semua test sekaligus**

```bash
pytest tests/ -v
```

Expected: semua test PASSED (minimal 17 tests)

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main orchestrator — wire semua agents end-to-end"
```

---

## Task 9: Scheduler Harian (CronCreate)

**Files:**
- Create: `run_daily.py` — wrapper script untuk scheduler
- Create: `.env` — dari .env.example (TIDAK di-commit, sudah di .gitignore)

- [ ] **Step 1: Buat .gitignore**

```
.env
reports/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
```

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```

- [ ] **Step 2: Salin .env.example ke .env dan isi kredensial**

```bash
copy .env.example .env
```

Buka `.env` dan isi:
- `MYSQL_HOST` — endpoint AWS RDS Anda
- `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- `GOOGLE_SERVICE_ACCOUNT_JSON` — path ke file JSON service account Google
- `SHEET_ID_PJ_AREA` — ID Google Sheet PJ area (dari URL sheet)
- `SHEET_ID_KATEGORI_RISIKO` — ID Google Sheet kategori risiko
- `ANTHROPIC_API_KEY` — API key dari console.anthropic.com

- [ ] **Step 3: Test koneksi manual**

```bash
python main.py
```

Expected: laporan muncul di terminal, file .docx tersimpan di `reports/YYYY-MM-DD/`

- [ ] **Step 4: Setup CronCreate scheduler via Claude Code**

Jalankan skill `schedule` di Claude Code dengan prompt:

```
Jadwalkan main.py berjalan setiap hari pukul 05.00 WIB (UTC+8 = 21.00 UTC sehari sebelumnya).
Command: python C:\Users\davi.tantra\Documents\Claude\Gurimbang-Safety\main.py
```

- [ ] **Step 5: Push ke GitHub**

```bash
git push origin main
```

---

## Catatan Penting Sebelum Menjalankan

1. **Schema MySQL** — Query di `mysql_connector.py` menggunakan nama tabel `findings`, `locations`, `incidents`. Sesuaikan dengan nama tabel aktual di database Anda.

2. **Google Service Account** — Buat service account di Google Cloud Console, download file JSON, share Google Sheet ke email service account tersebut.

3. **Kolom Google Sheets** — Header kolom di sheet PJ area harus: `location_id`, `pj_name`, `pj_contact`, `area`. Sesuaikan jika berbeda.

4. **Anthropic API Key** — Daftar di console.anthropic.com untuk mendapatkan API key.
