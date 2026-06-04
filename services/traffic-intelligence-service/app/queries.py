"""
queries.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
CQRS Query Side — read operations only.
This class never writes, never commits, never rolls back.
Every method is a pure SELECT that returns data and nothing else.
"""

from app.database import get_connection, release_connection


class TrafficQueryRepository:

    def get_all_traffic_records(self) -> list[dict]:
        """
        Fetch every row in traffic_data ordered by created_at descending.
        Called by the ML pipeline at startup to load all training data.
        Also served directly by GET /traffic-data.
        """
        sql = """
            SELECT id, location_name, latitude, longitude,
                   day_of_week, hour, congestion_level, source, created_at
            FROM   traffic_data
            ORDER  BY created_at DESC;
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                return [self._row_to_dict(cur, row) for row in rows]
        finally:
            release_connection(conn)

    def get_traffic_records_by_location(self, location_name: str) -> list[dict]:
        """
        Fetch all rows for a specific location using a case-insensitive match.
        Useful for per-location analysis and debugging predictions.
        """
        sql = """
            SELECT id, location_name, latitude, longitude,
                   day_of_week, hour, congestion_level, source, created_at
            FROM   traffic_data
            WHERE  LOWER(location_name) = LOWER(%s)
            ORDER  BY day_of_week, hour;
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (location_name,))
                rows = cur.fetchall()
                return [self._row_to_dict(cur, row) for row in rows]
        finally:
            release_connection(conn)

    def get_record_count(self) -> int:
        """
        Return the total number of rows in traffic_data.
        Called by GET /model/status to report training data size.
        """
        sql = "SELECT COUNT(*) FROM traffic_data;"
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchone()[0]
        finally:
            release_connection(conn)

    def get_distinct_locations(self) -> list[str]:
        """
        Return a sorted list of all unique location names in the dataset.
        Served by GET /locations so callers know valid values before hitting /predict.
        """
        sql = """
            SELECT DISTINCT location_name
            FROM   traffic_data
            ORDER  BY location_name;
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return [row[0] for row in cur.fetchall()]
        finally:
            release_connection(conn)

    @staticmethod
    def _row_to_dict(cur, row) -> dict:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))