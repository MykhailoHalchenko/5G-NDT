"""OSS/BSS provisioning adapter — sync stub and async adapter.

Bridges the Digital Twin with the Operational/Business Support System
for service provisioning, inventory sync, and order management.
Both a synchronous stub (ProvisioningAdapter) and an async adapter
(AsyncProvisioningAdapter) are provided to support concurrent requests
to the OSS/BSS northbound interface without blocking the event loop.
"""

from __future__ import annotations

import asyncio
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


class AsyncProvisioningAdapter:
    """Async adapter for OSS/BSS northbound provisioning interface.

    All I/O-bound operations are ``async def`` so that concurrent provisioning
    requests can be handled without blocking the event loop.

    Stub implementation — all methods log and return empty/None values.
    Phase 5 will replace these with real async HTTP calls via ``httpx.AsyncClient``.
    """

    def __init__(self, config: OSSBSSConfig) -> None:
        self._config = config
        logger.info(
            "AsyncProvisioningAdapter initialised (stub) — base_url=%s",
            config.base_url,
        )

    async def health_check(self) -> bool:
        """Asynchronously return True if the OSS/BSS endpoint is reachable."""
        logger.debug("AsyncProvisioningAdapter.health_check() — stub")
        await asyncio.sleep(0)
        return False

    async def get_inventory(self) -> List[Dict[str, Any]]:
        """Asynchronously fetch network inventory from OSS/BSS."""
        logger.debug("AsyncProvisioningAdapter.get_inventory() — stub")
        await asyncio.sleep(0)
        return []

    async def create_service_order(self, order: Dict[str, Any]) -> Optional[str]:
        """Asynchronously submit a service order to OSS/BSS."""
        logger.info(
            "AsyncProvisioningAdapter.create_service_order() — stub, order_type=%s",
            order.get("orderType", "unknown"),
        )
        await asyncio.sleep(0)
        return None

    async def get_service_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Asynchronously retrieve the status of a service order."""
        logger.debug(
            "AsyncProvisioningAdapter.get_service_order_status(id=%s) — stub", order_id
        )
        await asyncio.sleep(0)
        return None

    async def sync_topology(self, topology_data: Dict[str, Any]) -> bool:
        """Asynchronously push topology updates to OSS/BSS inventory."""
        logger.info("AsyncProvisioningAdapter.sync_topology() — stub")
        await asyncio.sleep(0)
        return False

    async def notify_event(self, event: Dict[str, Any]) -> bool:
        """Asynchronously send a network event notification to OSS/BSS."""
        logger.debug(
            "AsyncProvisioningAdapter.notify_event(type=%s) — stub",
            event.get("eventType", "unknown"),
        )
        await asyncio.sleep(0)
        return False
