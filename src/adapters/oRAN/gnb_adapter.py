"""gNodeB O-RAN adapter (stub).

Provides a protocol adapter for retrieving configuration and telemetry
from gNodeB devices via O-RAN interfaces (NETCONF/YANG, gNMI, REST).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class GnbAdapterConfig:
    """Connection configuration for a single gNodeB."""

    def __init__(
        self,
        gnb_id: UUID,
        host: str,
        port: int = 830,
        username: str = "admin",
        password: str = "",
        protocol: str = "NETCONF",
    ) -> None:
        self.gnb_id = gnb_id
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol


class GnbAdapter:
    """Adapter for communicating with a single gNodeB over O-RAN interfaces.

    Stub implementation — all methods log and return empty/None values.
    Phase 3 will replace these with real NETCONF/gNMI calls.
    """

    def __init__(self, config: GnbAdapterConfig) -> None:
        self._config = config
        self._session = None
        logger.info(
            "GnbAdapter initialised (stub) — gnb_id=%s host=%s protocol=%s",
            config.gnb_id,
            config.host,
            config.protocol,
        )

    def connect(self) -> bool:
        """Open a management session to the gNodeB.

        Returns:
            True on success, False otherwise.
        """
        logger.info("GnbAdapter.connect() — stub, host=%s", self._config.host)
        return False

    def disconnect(self) -> None:
        """Close the management session."""
        logger.info("GnbAdapter.disconnect() — stub")

    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """Retrieve the full running configuration of the gNodeB.

        Returns:
            Configuration dict, or None on failure.
        """
        logger.debug("GnbAdapter.get_configuration() — stub, gnb_id=%s", self._config.gnb_id)
        return None

    def get_telemetry(self) -> Optional[Dict[str, Any]]:
        """Retrieve current telemetry (KPIs) from the gNodeB.

        Returns:
            Telemetry dict with keys such as 'latency_ms', 'throughput_mbps', etc.
        """
        logger.debug("GnbAdapter.get_telemetry() — stub, gnb_id=%s", self._config.gnb_id)
        return None

    def get_cells(self) -> List[Dict[str, Any]]:
        """Return the list of configured cells (DU/cell associations).

        Returns:
            List of cell configuration dicts.
        """
        logger.debug("GnbAdapter.get_cells() — stub, gnb_id=%s", self._config.gnb_id)
        return []

    def apply_configuration(self, config_delta: Dict[str, Any]) -> bool:
        """Push a partial configuration update to the gNodeB.

        Args:
            config_delta: Dict of parameters to apply (YANG-compliant).

        Returns:
            True on success, False otherwise.
        """
        logger.info(
            "GnbAdapter.apply_configuration() — stub, gnb_id=%s delta_keys=%s",
            self._config.gnb_id,
            list(config_delta.keys()),
        )
        return False

    def health_check(self) -> bool:
        """Return True if the gNodeB is reachable and responsive."""
        logger.debug("GnbAdapter.health_check() — stub, gnb_id=%s", self._config.gnb_id)
        return False
