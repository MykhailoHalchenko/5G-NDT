"""KPI aggregation logic — sync stub with async counterparts.

Aggregates raw time-series metrics from the telemetry pipeline into
computed KPI snapshots for each network entity.  Async methods allow
the API layer to aggregate KPIs for many entities concurrently via
``asyncio.gather`` without blocking the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from ..topology.models import KPI
from .rules import KPIRuleEngine

logger = logging.getLogger(__name__)


class AggregationWindow:
    """Specifies the time window for KPI aggregation."""

    def __init__(self, duration_seconds: int = 60) -> None:
        self.duration_seconds = duration_seconds

    @property
    def start(self) -> datetime:
        return datetime.utcnow() - timedelta(seconds=self.duration_seconds)

    @property
    def end(self) -> datetime:
        return datetime.utcnow()


class KPIAggregator:
    """Computes KPI snapshots from raw telemetry data.

    The stub implementation returns empty results.  In Phase 3/4 this
    will query InfluxDB, apply window functions, and feed results through
    the KPIRuleEngine.

    Both synchronous and asynchronous methods are provided:
    * Sync methods are used by integration tests and legacy callers.
    * Async methods allow the API layer to aggregate many entities in
      parallel without blocking the event loop.
    """

    def __init__(self, rule_engine: Optional[KPIRuleEngine] = None) -> None:
        self._rule_engine = rule_engine or KPIRuleEngine()
        logger.info("KPIAggregator initialised (stub)")

    # ── Synchronous methods ────────────────────────────────────────────────────

    def aggregate_entity(
        self,
        entity_id: UUID,
        entity_type: str,
        window: Optional[AggregationWindow] = None,
    ) -> List[KPI]:
        """Compute all KPIs for a single network entity over the given window.

        Args:
            entity_id: UUID of the network entity.
            entity_type: Class name of the entity (e.g. 'gNodeB').
            window: Aggregation time window; defaults to last 60 seconds.

        Returns:
            List of KPI snapshots with computed severity.
        """
        if window is None:
            window = AggregationWindow()
        logger.debug(
            "KPIAggregator.aggregate_entity(id=%s, type=%s) — stub",
            entity_id,
            entity_type,
        )
        return []

    def aggregate_all(
        self,
        window: Optional[AggregationWindow] = None,
    ) -> Dict[str, List[KPI]]:
        """Compute KPIs for every entity in the topology.

        Returns:
            Mapping of entity_id (str) -> list of KPI snapshots.
        """
        logger.debug("KPIAggregator.aggregate_all() — stub")
        return {}

    def get_kpi_summary(
        self,
        entity_id: UUID,
    ) -> Optional[Dict[str, float]]:
        """Return a flat dict of the latest metric values for an entity.

        Returns:
            Dict of metric_name -> value, or None if entity not found.
        """
        logger.debug("KPIAggregator.get_kpi_summary(id=%s) — stub", entity_id)
        return None

    # ── Asynchronous methods ───────────────────────────────────────────────────

    async def async_aggregate_entity(
        self,
        entity_id: UUID,
        entity_type: str,
        window: Optional[AggregationWindow] = None,
    ) -> List[KPI]:
        """Asynchronously compute all KPIs for a single network entity.

        Yields to the event loop so that many entities can be aggregated
        concurrently via ``asyncio.gather``.

        Returns:
            List of KPI snapshots with computed severity.
        """
        await asyncio.sleep(0)
        return self.aggregate_entity(entity_id, entity_type, window)

    async def async_aggregate_all(
        self,
        window: Optional[AggregationWindow] = None,
    ) -> Dict[str, List[KPI]]:
        """Asynchronously compute KPIs for every entity in the topology.

        Returns:
            Mapping of entity_id (str) -> list of KPI snapshots.
        """
        await asyncio.sleep(0)
        return self.aggregate_all(window)

    async def async_get_kpi_summary(
        self,
        entity_id: UUID,
    ) -> Optional[Dict[str, float]]:
        """Asynchronously return the latest metric values for an entity."""
        await asyncio.sleep(0)
        return self.get_kpi_summary(entity_id)
