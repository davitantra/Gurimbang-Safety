import logging
import os
import anthropic
from dotenv import load_dotenv

from connectors.mysql_connector import MySQLConnector
from connectors.sheets_connector import SheetsConnector
from agents.agent_agregasi import AgentAgregasi
from agents.agent_validasi import AgentValidasi
from agents.agent_pelaporan import AgentPelaporan

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


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

    logger.info("=" * 50)
    logger.info("Gurimbang Safety Pipeline — mulai")

    logger.info("[1/3] Agent Agregasi...")
    agent_agregasi = AgentAgregasi(mysql_connector=mysql, sheets_connector=sheets)
    dataset = agent_agregasi.run()
    logger.info("[1/3] Selesai: %d findings ditemukan", len(dataset["findings"]))

    logger.info("[2/3] Agent Validasi...")
    agent_validasi = AgentValidasi(
        anthropic_client=anthropic_client,
        blindspot_threshold_days=blindspot_days,
    )
    dataset = agent_validasi.run(dataset)
    s = dataset["summary"]
    logger.info("[2/3] Selesai: %d overdue | %d high risk | %d blindspot", s.get("overdue", 0), s.get("high_risk", 0), s.get("blindspot", 0))

    logger.info("[3/3] Agent Pelaporan...")
    agent_pelaporan = AgentPelaporan(reports_dir="reports")
    report = agent_pelaporan.run(dataset)
    logger.info("[3/3] Selesai: laporan disimpan di %s", report["docx_path"])

    logger.info("=" * 50)
    print("\n" + report["markdown"] + "\n")

    return report


if __name__ == "__main__":
    run_pipeline()
