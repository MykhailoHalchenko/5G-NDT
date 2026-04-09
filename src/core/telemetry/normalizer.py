"""Telemetry data normalizer (stub).

Transforms raw vendor-specific telemetry payloads into the canonical
5G NDT data model format before storage.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NormalizedTelemetry:
    """Canonical telemetry record after normalization."""

    def __init__(
        self,
        entity_id: str,
        entity_type: str,
        metric_name: str,
        value: float,
        unit: str = "",
        timestamp: Optional[datetime] = None,
        labels: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.metric_name = metric_name
        self.value = value
        self.unit = unit
        self.timestamp = timestamp or datetime.utcnow()
        self.labels = labels or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


class TelemetryNormalizer:
    """Normalizes raw telemetry payloads from various sources.

    Each source adapter should register a parser for its specific format.
    The normalizer dispatches to the correct parser based on the
    'source_type' field in the raw message.
    """

    SUPPORTED_SOURCES = ("oran", "gnb_vendor_a", "gnb_vendor_b", "simulated")

    def __init__(self) -> None:
        self._parsers: Dict[str, Any] = {}
        logger.info("TelemetryNormalizer initialised (stub)")

    def register_parser(self, source_type: str, parser_fn: Any) -> None:
        """Register a parser function for a given source type.

        Args:
            source_type: Identifier for the telemetry source.
            parser_fn: Callable(raw_payload) -> NormalizedTelemetry.
        """
        self._parsers[source_type] = parser_fn
        logger.debug("Registered parser for source_type=%s", source_type)

    def normalize(self, raw_payload: Dict[str, Any]) -> Optional[NormalizedTelemetry]:
        """Normalize a raw telemetry payload.

        Args:
            raw_payload: Raw message dict containing at minimum a 'source_type' key.

        Returns:
            NormalizedTelemetry instance, or None if parsing failed.
        """
        source_type = raw_payload.get("source_type", "unknown")
        logger.debug("TelemetryNormalizer.normalize(source_type=%s) — stub", source_type)
        return None

    def normalize_batch(self, raw_payloads: List[Dict[str, Any]]) -> List[NormalizedTelemetry]:
        """Normalize a list of raw payloads.

        Returns:
            List of successfully normalized records (failures are skipped).
        """
        results: List[NormalizedTelemetry] = []
        for payload in raw_payloads:
            record = self.normalize(payload)
            if record is not None:
                results.append(record)
        return results
