import json
import logging
from datetime import date, timedelta, datetime
from typing import Any

logger = logging.getLogger(__name__)

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
        logger.info("Agent Validasi: memproses %d findings...", len(dataset.get("findings", [])))
        validated_findings = []
        for finding in dataset["findings"]:
            finding = self._apply_rule_based(finding)
            if self._needs_llm(finding):
                finding = self._apply_llm(finding, dataset["risk_categories"])
            validated_findings.append(finding)

        dataset["findings"] = validated_findings
        dataset["summary"] = self._build_summary(validated_findings)
        logger.info("Agent Validasi: selesai. Summary: %s", dataset["summary"])
        return dataset

    def _apply_rule_based(self, finding: dict) -> dict:
        finding = dict(finding)
        created_at = finding.get("created_at")
        risk_level = finding.get("risk_level")

        if risk_level in DUE_DATE_DAYS and not finding.get("due_date"):
            created_date = self._parse_date(created_at)
            if created_date:
                finding["due_date"] = str(created_date + timedelta(days=DUE_DATE_DAYS[risk_level]))
                finding["validation_source"] = "rule-based"

        if finding.get("due_date") and not finding.get("closed_date"):
            due = self._parse_date(finding["due_date"])
            finding["is_overdue"] = bool(due and due < date.today())
        else:
            finding["is_overdue"] = False

        last_insp = finding.get("last_inspection_date")
        if last_insp:
            last_date = self._parse_date(last_insp)
            if last_date:
                finding["is_blindspot"] = (date.today() - last_date).days > self.blindspot_threshold_days
            else:
                finding["is_blindspot"] = True
        else:
            finding["is_blindspot"] = True

        return finding

    def _needs_llm(self, finding: dict) -> bool:
        return finding.get("risk_level") is None

    def _apply_llm(self, finding: dict, risk_categories: list[dict]) -> dict:
        if self.client is None:
            return finding

        categories_text = ", ".join(r.get("category_name", "") for r in risk_categories)
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

        try:
            message = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            llm_result = json.loads(raw)
            finding["risk_level"] = llm_result.get("risk_level", "Low")
            finding["is_high_risk"] = llm_result.get("is_high_risk", False)
            finding["validation_source"] = "llm"

            created_date = self._parse_date(finding.get("created_at"))
            risk = finding["risk_level"]
            if created_date and risk in DUE_DATE_DAYS:
                finding["due_date"] = str(created_date + timedelta(days=DUE_DATE_DAYS[risk]))

            logger.info("LLM memutuskan risk_level=%s untuk finding id=%s", finding["risk_level"], finding.get("id"))
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning("LLM response tidak valid untuk finding id=%s: %s", finding.get("id"), e)
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
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        return None
