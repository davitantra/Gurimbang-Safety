import pymysql
import pymysql.cursors


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
