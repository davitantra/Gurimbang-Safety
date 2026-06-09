import logging
from datetime import date

logger = logging.getLogger(__name__)


class AgentAgregasi:
    def __init__(self, mysql_connector, sheets_connector):
        self.mysql = mysql_connector
        self.sheets = sheets_connector

    def run(self) -> dict:
        """
        Tarik semua data dari MySQL dan Google Sheets,
        gabungkan menjadi satu struktur terpadu.
        """
        logger.info("Agent Agregasi: mulai menarik data...")

        findings = self.mysql.get_findings()
        locations = self.mysql.get_locations()
        incidents = self.mysql.get_incidents()
        last_inspections = self.mysql.get_last_inspection_per_location()
        pj_map = self.sheets.get_pj_map()
        risk_categories = self.sheets.get_risk_categories()

        logger.info(
            "Data ditarik: %d findings, %d locations, %d incidents",
            len(findings), len(locations), len(incidents)
        )

        location_map = {str(loc["id"]): loc for loc in locations}
        last_inspection_map = {
            str(row["location_id"]): row["last_inspection_date"]
            for row in last_inspections
        }

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
                "is_blindspot": None,
                "is_overdue": None,
                "is_high_risk": None,
                "validation_source": None,
            })

        logger.info("Agent Agregasi: selesai, %d findings dienrich", len(enriched_findings))

        return {
            "date": str(date.today()),
            "findings": enriched_findings,
            "incidents": incidents,
            "risk_categories": risk_categories,
            "location_map": location_map,
            "last_inspection_map": last_inspection_map,
        }
