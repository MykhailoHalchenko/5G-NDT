"""Real-time async network synchronization service.

``AsyncNetworkSyncService`` runs a continuous asyncio event loop that
polls every registered gNodeB adapter concurrently, aggregates KPIs, and
writes results to the time-series database — all without blocking the main
application thread.

Design goals
------------
* **High concurrency** — ``asyncio.gather`` fans out telemetry polls to all
  gNodeBs simultaneously so that network size does not increase poll latency.
* **Low latency** — I/O-bound adapter calls are all ``async def``; the event
  loop is never blocked by a single slow device.
* **Real-time synchronization** — the service runs on a configurable interval
  (default 5 s) to keep the Digital Twin state fresh.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..adapters.oRAN.gnb_adapter import AsyncGnbAdapter, GnbAdapterConfig
from .kpi.aggregator import KPIAggregator
from .telemetry.time_series import TimeSeriesDB

logger = logging.getLogger(__name__)


class SyncServiceConfig:
    """Configuration for the async network sync service."""

    def __init__(
        self,
        poll_interval_seconds: float = 5.0,
        max_concurrent_polls: int = 50,
    ) -> None:
        self.poll_interval_seconds = poll_interval_seconds
        self.max_concurrent_polls = max_concurrent_polls


class AsyncNetworkSyncService:
    """Continuously synchronizes the Digital Twin state with the physical network.

    Usage::

        config = SyncServiceConfig(poll_interval_seconds=5.0)
        service = AsyncNetworkSyncService(config=config, db=time_series_db)
        service.register_gnodeb(GnbAdapterConfig(gnb_id=..., host="10.0.0.1"))
        await service.start()   # returns immediately; runs in the background
        ...
        await service.stop()
    """

    def __init__(
        self,
        config: Optional[SyncServiceConfig] = None,
        aggregator: Optional[KPIAggregator] = None,
        db: Optional[TimeSeriesDB] = None,
    ) -> None:
        self._config = config or SyncServiceConfig()
        self._aggregator = aggregator or KPIAggregator()
        self._db = db
        self._adapters: List[AsyncGnbAdapter] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        logger.info(
            "AsyncNetworkSyncService initialised — interval=%.1fs max_concurrent=%d",
            self._config.poll_interval_seconds,
            self._config.max_concurrent_polls,
        )

    def register_gnodeb(self, adapter_config: GnbAdapterConfig) -> None:
        """Register a gNodeB adapter to be polled on each sync cycle.

        Args:
            adapter_config: Connection configuration for the gNodeB.
        """
        adapter = AsyncGnbAdapter(adapter_config)
        self._adapters.append(adapter)
        logger.info(
            "AsyncNetworkSyncService: registered gNodeB gnb_id=%s host=%s",
            adapter_config.gnb_id,
            adapter_config.host,
        )

    async def _poll_gnodeb(self, adapter: AsyncGnbAdapter) -> Optional[Dict[str, Any]]:
        """Poll a single gNodeB for telemetry and return the result dict."""
        try:
            telemetry = await adapter.get_telemetry()
            if telemetry and self._db is not None:
                await self._db.async_write_metric(
                    measurement="gnb_telemetry",
                    fields=telemetry,
                    tags={"gnb_id": str(adapter._config.gnb_id)},
                )
            return telemetry
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "AsyncNetworkSyncService._poll_gnodeb error gnb_id=%s: %s",
                adapter._config.gnb_id,
                exc,
            )
            return None

    async def _sync_cycle(self) -> None:
        """Fan out telemetry polls to all registered gNodeBs concurrently."""
        if not self._adapters:
            return
        semaphore = asyncio.Semaphore(self._config.max_concurrent_polls)

        async def _bounded_poll(adapter: AsyncGnbAdapter) -> Optional[Dict[str, Any]]:
            async with semaphore:
                return await self._poll_gnodeb(adapter)

        results = await asyncio.gather(
            *[_bounded_poll(a) for a in self._adapters],
            return_exceptions=True,
        )
        successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.debug(
            "AsyncNetworkSyncService._sync_cycle: %d/%d polls succeeded",
            successful,
            len(self._adapters),
        )

    async def _run_loop(self) -> None:
        """Main loop: run a sync cycle every ``poll_interval_seconds``."""
        logger.info("AsyncNetworkSyncService._run_loop started")
        while self._running:
            try:
                await self._sync_cycle()
            except Exception as exc:  # noqa: BLE001
                logger.error("AsyncNetworkSyncService._run_loop unhandled error: %s", exc)
            await asyncio.sleep(self._config.poll_interval_seconds)
        logger.info("AsyncNetworkSyncService._run_loop stopped")

    async def start(self) -> None:
        """Start the background sync loop.

        Returns immediately; the sync loop runs as an asyncio background task.
        """
        if self._running:
            logger.warning("AsyncNetworkSyncService.start() called while already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AsyncNetworkSyncService started — %d gNodeBs registered", len(self._adapters))

    async def stop(self) -> None:
        """Stop the background sync loop and await its completion."""
        if not self._running:
            return
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("AsyncNetworkSyncService stopped")

    @property
    def is_running(self) -> bool:
        """Return True if the sync loop is active."""
        return self._running
