import logging
import pymysql
import pymysql.cursors

logger = logging.getLogger(__name__)


class MySQLConnector:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.database = database

    def _get_connection(self) -> pymysql.connections.Connection:
        """Buka koneksi ke MySQL. Raise ConnectionError jika gagal."""
        try:
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
            )
        except pymysql.Error as e:
            logger.error("Gagal koneksi ke MySQL %s:%s/%s — %s", self.host, self.port, self.database, e)
            raise ConnectionError(f"Tidak bisa terhubung ke MySQL: {e}") from e

    def _execute_query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Eksekusi SQL query dan kembalikan list of dict. Raise RuntimeError jika query gagal."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    logger.debug("Query mengembalikan %d baris", len(rows))
                    return list(rows)
        except ConnectionError:
            raise
        except pymysql.Error as e:
            logger.error("Query gagal: %s — %s", sql[:80], e)
            raise RuntimeError(f"Query gagal: {e}") from e

    def get_findings(self) -> list[dict]:
        """
        Ambil semua temuan inspeksi yang masih Open.
        SESUAIKAN nama tabel dan kolom dengan schema aktual Anda.
        """
        logger.info("Mengambil data findings...")
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
        logger.info("Mengambil data locations...")
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
        logger.info("Mengambil data incidents...")
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
        logger.info("Mengambil last inspection per location...")
        sql = """
            SELECT
                location_id,
                MAX(inspection_date) AS last_inspection_date
            FROM findings
            GROUP BY location_id
        """
        return self._execute_query(sql)
