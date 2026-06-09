import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

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
        """Lazy-init gspread client. Raise ConnectionError jika auth gagal."""
        if self._client is None:
            try:
                creds = Credentials.from_service_account_file(
                    self.service_account_json, scopes=SCOPES
                )
                self._client = gspread.authorize(creds)
                logger.info("Google Sheets client berhasil diinisialisasi")
            except Exception as e:
                logger.error("Gagal autentikasi Google Sheets: %s", e)
                raise ConnectionError(f"Gagal autentikasi Google Sheets: {e}") from e
        return self._client

    def _read_sheet(self, sheet_id: str, worksheet_index: int = 0) -> list[dict]:
        """Baca sheet dan kembalikan list of dict. Raise RuntimeError jika gagal."""
        try:
            client = self._get_client()
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.get_worksheet(worksheet_index)
            rows = worksheet.get_all_records()
            logger.debug("Sheet %s mengembalikan %d baris", sheet_id[:8], len(rows))
            return rows
        except ConnectionError:
            raise
        except Exception as e:
            logger.error("Gagal membaca sheet %s: %s", sheet_id[:8], e)
            raise RuntimeError(f"Gagal membaca Google Sheet: {e}") from e

    def get_pj_area(self) -> list[dict]:
        """
        Baca data penanggung jawab area dari Google Sheets.
        Kolom yang diharapkan: location_id, pj_name, pj_contact, area
        SESUAIKAN nama kolom dengan header aktual di sheet Anda.
        """
        logger.info("Mengambil data PJ area dari Google Sheets...")
        return self._read_sheet(self.pj_sheet_id)

    def get_risk_categories(self) -> list[dict]:
        """
        Baca kategori temuan berisiko tinggi dari Google Sheets.
        Kolom yang diharapkan: category_name, description
        SESUAIKAN nama kolom dengan header aktual di sheet Anda.
        """
        logger.info("Mengambil data kategori risiko dari Google Sheets...")
        return self._read_sheet(self.risk_category_sheet_id)

    def get_pj_map(self) -> dict[str, dict]:
        """
        Kembalikan dict dengan key = location_id (string),
        value = dict info PJ area.
        Memudahkan lookup cepat saat agregasi.
        """
        records = self.get_pj_area()
        return {str(r["location_id"]): r for r in records}
