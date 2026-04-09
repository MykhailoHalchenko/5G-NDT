"""Time-series database integration (stub).

Handles writing and querying KPI/telemetry data in InfluxDB (v2).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class InfluxDBConfig:
    """Configuration for the InfluxDB v2 client."""

    def __init__(
        self,
        url: str = "http://localhost:8086",
        token: str = "",
        org: str = "kai-ndt",
        bucket: str = "5g-telemetry",
    ) -> None:
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket


class TimeSeriesDB:
    """Client for writing and querying time-series telemetry data in InfluxDB.

    The stub logs all method calls without connecting to a real database.
    Replace with actual influxdb-client calls in Phase 3.
    """

    def __init__(self, config: InfluxDBConfig) -> None:
        self._config = config
        self._client = None
        logger.info("TimeSeriesDB initialised (stub) — url=%s", config.url)

    def connect(self) -> None:
        """Open a connection to InfluxDB."""
        logger.info("TimeSeriesDB.connect() — stub")
        # TODO: from influxdb_client import InfluxDBClient
        # self._client = InfluxDBClient(
        #     url=self._config.url,
        #     token=self._config.token,
        #     org=self._config.org,
        # )

    def disconnect(self) -> None:
        """Close the InfluxDB connection."""
        logger.info("TimeSeriesDB.disconnect() — stub")
        if self._client:
            self._client.close()
            self._client = None

    def health_check(self) -> bool:
        """Return True if InfluxDB is reachable."""
        logger.debug("TimeSeriesDB.health_check() — stub, returning False")
        return False

    def write_metric(
        self,
        measurement: str,
        fields: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Write a single metric data point.

        Args:
            measurement: InfluxDB measurement name (e.g. 'gnb_kpis').
            fields: Numeric field values (e.g. {'latency_ms': 4.2}).
            tags: Optional string tag set for filtering.
            timestamp: Optional explicit timestamp; defaults to now.

        Returns:
            True on success, False otherwise.
        """
        logger.debug(
            "TimeSeriesDB.write_metric(measurement=%s, fields=%s) — stub",
            measurement,
            fields,
        )
        return False

    def write_batch(self, records: List[Dict[str, Any]]) -> int:
        """Write multiple metric records in a single batch request.

        Args:
            records: List of dicts each matching the write_metric signature.

        Returns:
            Number of records successfully written.
        """
        logger.debug("TimeSeriesDB.write_batch(%d records) — stub", len(records))
        return 0

    def query(
        self,
        flux_query: str,
    ) -> List[Dict[str, Any]]:
        """Execute a Flux query and return result rows.

        Args:
            flux_query: Flux query string.

        Returns:
            List of result row dictionaries.
        """
        logger.debug("TimeSeriesDB.query() — stub, query=%r", flux_query[:120])
        return []

    def get_latest_metric(
        self,
        entity_id: str,
        metric_name: str,
        bucket: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return the most recent value for a given entity+metric combination."""
        logger.debug(
            "TimeSeriesDB.get_latest_metric(entity=%s, metric=%s) — stub",
            entity_id,
            metric_name,
        )
        return None
