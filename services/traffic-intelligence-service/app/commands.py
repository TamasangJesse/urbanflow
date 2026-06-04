"""
commands.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
CQRS Command Side — write operations only.
This class is the only place in the entire service that writes to traffic_data.
No SELECT query belongs here. No endpoint writes SQL directly.
"""

from app.database import get_connection, release_connection


class TrafficCommandRepository:

    def insert_traffic_record(
        self,
        location_name: str,
        latitude: float,
        longitude: float,
        day_of_week: str,
        hour: int,
        congestion_level: str,
        source: str = "api",
    ) -> dict:
        """
        Insert a single new traffic record into traffic_data.
        Called by POST /traffic-data when a real-world reading is submitted.
        Returns the full newly created row as a dict.
        Rolls back cleanly on any error — no partial writes ever committed.
        """
        sql = """
            INSERT INTO traffic_data
                (location_name, latitude, longitude, day_of_week, hour, congestion_level, source)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, location_name, latitude, longitude,
                      day_of_week, hour, congestion_level, source, created_at;
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    location_name,
                    latitude,
                    longitude,
                    day_of_week,
                    hour,
                    congestion_level,
                    source,
                ))
                row = cur.fetchone()
                conn.commit()
                return self._row_to_dict(cur, row)
        except Exception:
            conn.rollback()
            raise
        finally:
            release_connection(conn)

    @staticmethod
    def _row_to_dict(cur, row) -> dict:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))