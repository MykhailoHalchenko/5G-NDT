"""Auto-discovery engine (stub).

Responsible for automatically discovering network elements (gNodeB, CU, DU,
slices) via SNMP, NETCONF/YANG, gNMI, or REST probes and populating the
topology graph.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from .graph_db import GraphDBConnector
from .models import TopologySnapshot

logger = logging.getLogger(__name__)


class DiscoveryConfig:
    """Configuration for the discovery engine."""

    def __init__(
        self,
        poll_interval_seconds: int = 60,
        timeout_seconds: int = 10,
        protocols: Optional[List[str]] = None,
    ) -> None:
        self.poll_interval_seconds = poll_interval_seconds
        self.timeout_seconds = timeout_seconds
        self.protocols = protocols or ["NETCONF", "gNMI", "REST"]


class DiscoveryEngine:
    """Discovers and synchronises network elements into the topology graph.

    The engine periodically probes the network using configured protocols
    and upserts discovered nodes/relationships into the GraphDB.
    """

    def __init__(self, config: DiscoveryConfig, graph_db: GraphDBConnector) -> None:
        self._config = config
        self._graph_db = graph_db
        logger.info("DiscoveryEngine initialised (stub)")

    def discover_all(self) -> TopologySnapshot:
        """Run a full discovery cycle and return the current topology snapshot.

        Returns:
            A TopologySnapshot with all discovered entities.
        """
        logger.info("DiscoveryEngine.discover_all() — stub, returning empty snapshot")
        return TopologySnapshot()

    def discover_node(self, node_id: UUID) -> bool:
        """Refresh discovery data for a single node.

        Args:
            node_id: UUID of the node to re-discover.

        Returns:
            True if the node was found and updated, False otherwise.
        """
        logger.debug("DiscoveryEngine.discover_node(id=%s) — stub", node_id)
        return False

    def start(self) -> None:
        """Start the background polling loop (stub)."""
        logger.info(
            "DiscoveryEngine.start() — stub, poll interval=%ds",
            self._config.poll_interval_seconds,
        )

    def stop(self) -> None:
        """Stop the background polling loop (stub)."""
        logger.info("DiscoveryEngine.stop() — stub")
