"""OSS/BSS provisioning adapter (stub).

Bridges the Digital Twin with the Operational/Business Support System
for service provisioning, inventory sync, and order management.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OSSBSSConfig:
    """Connection configuration for the OSS/BSS northbound interface."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: str = "",
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds


class ProvisioningAdapter:
    """Adapter for OSS/BSS northbound provisioning interface.

    Stub implementation — all methods log and return empty/None values.
    Phase 5 will replace these with real REST/SOAP/TM Forum API calls.
    """

    def __init__(self, config: OSSBSSConfig) -> None:
        self._config = config
        logger.info(
            "ProvisioningAdapter initialised (stub) — base_url=%s",
            config.base_url,
        )

    def health_check(self) -> bool:
        """Return True if the OSS/BSS endpoint is reachable."""
        logger.debug("ProvisioningAdapter.health_check() — stub")
        return False

    def get_inventory(self) -> List[Dict[str, Any]]:
        """Fetch network inventory from OSS/BSS.

        Returns:
            List of inventory item dicts.
        """
        logger.debug("ProvisioningAdapter.get_inventory() — stub")
        return []

    def create_service_order(self, order: Dict[str, Any]) -> Optional[str]:
        """Submit a service order to OSS/BSS.

        Args:
            order: TM Forum-compliant service order dict.

        Returns:
            Order ID string on success, None on failure.
        """
        logger.info(
            "ProvisioningAdapter.create_service_order() — stub, order_type=%s",
            order.get("orderType", "unknown"),
        )
        return None

    def get_service_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the status of a previously submitted service order.

        Returns:
            Status dict or None if not found.
        """
        logger.debug("ProvisioningAdapter.get_service_order_status(id=%s) — stub", order_id)
        return None

    def sync_topology(self, topology_data: Dict[str, Any]) -> bool:
        """Push topology updates to OSS/BSS inventory.

        Args:
            topology_data: Serialised topology snapshot.

        Returns:
            True on success, False otherwise.
        """
        logger.info("ProvisioningAdapter.sync_topology() — stub")
        return False

    def notify_event(self, event: Dict[str, Any]) -> bool:
        """Send a network event notification to OSS/BSS.

        Args:
            event: Event payload dict.

        Returns:
            True on success, False otherwise.
        """
        logger.debug(
            "ProvisioningAdapter.notify_event(type=%s) — stub",
            event.get("eventType", "unknown"),
        )
        return False
