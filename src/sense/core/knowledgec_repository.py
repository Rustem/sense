"""Repository for accessing KnowledgeC database."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from sense.models.events import AppUsageEvent


class KnowledgeCRepository:
    """Repository for querying macOS KnowledgeC database."""

    MACOS_EPOCH_OFFSET = 978307200

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"KnowledgeC database not found at {db_path}")

    def _convert_timestamp(self, mac_timestamp: float) -> datetime:
        """Convert macOS timestamp to Python datetime."""
        return datetime.fromtimestamp(mac_timestamp + self.MACOS_EPOCH_OFFSET)

    def get_events(
        self, start_date: datetime, end_date: datetime, app_name: str | None = None
    ) -> list[AppUsageEvent]:
        """Query app usage events from KnowledgeC database.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            app_name: Optional filter for specific app/domain

        Returns:
            List of app usage events sorted by start time
        """
        with sqlite3.connect(self.db_path, timeout=5.0) as conn:
            cursor = conn.cursor()

            query = """
            SELECT
                COALESCE(ZSTRUCTUREDMETADATA.Z_DKDIGITALHEALTHMETADATAKEY__WEBDOMAIN,
                         ZOBJECT.ZVALUESTRING) AS app_name,
                COALESCE(ZSOURCE.ZBUNDLEID, 'web') AS bundle_id,
                ZOBJECT.ZSTARTDATE AS start_time,
                ZOBJECT.ZENDDATE AS end_time,
                (ZOBJECT.ZENDDATE - ZOBJECT.ZSTARTDATE) AS duration
            FROM ZOBJECT
            LEFT JOIN ZSOURCE ON ZOBJECT.ZSOURCE = ZSOURCE.Z_PK
            LEFT JOIN ZSTRUCTUREDMETADATA ON ZOBJECT.ZSTRUCTUREDMETADATA = ZSTRUCTUREDMETADATA.Z_PK
            WHERE
                (ZSTREAMNAME = '/app/usage' OR ZSTREAMNAME = '/app/webUsage')
                AND ZOBJECT.ZSTARTDATE IS NOT NULL
                AND ZOBJECT.ZENDDATE IS NOT NULL
                AND ZOBJECT.ZENDDATE > ZOBJECT.ZSTARTDATE
                AND ZOBJECT.ZSTARTDATE >= ?
                AND ZOBJECT.ZSTARTDATE < ?
            """

            end_date_exclusive = end_date + timedelta(days=1)
            params: list[float | str] = [
                start_date.timestamp() - self.MACOS_EPOCH_OFFSET,
                end_date_exclusive.timestamp() - self.MACOS_EPOCH_OFFSET,
            ]

            if app_name:
                query += " AND COALESCE(ZSTRUCTUREDMETADATA.Z_DKDIGITALHEALTHMETADATAKEY__WEBDOMAIN, ZOBJECT.ZVALUESTRING) = ?"
                params.append(app_name)

            query += " ORDER BY ZOBJECT.ZSTARTDATE ASC"

            cursor.execute(query, params)

            events = []
            for row in cursor.fetchall():
                app, bundle_id, start_ts, end_ts, duration = row

                if app and duration > 0:
                    events.append(
                        AppUsageEvent(
                            app_name=app,
                            bundle_id=bundle_id or "unknown",
                            start_time=self._convert_timestamp(start_ts),
                            end_time=self._convert_timestamp(end_ts),
                            duration_seconds=duration,
                        )
                    )

            return events
