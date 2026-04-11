"""Kafka consumer for 5G telemetry events — sync stub and async consumer.

Consumes raw telemetry messages from Kafka topics and forwards them to
the normalizer pipeline for processing.  The async consumer drives the
event loop so that many concurrent telemetry events can be dispatched
without thread-per-message overhead.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, List, Optional, Union

logger = logging.getLogger(__name__)


class KafkaConsumerConfig:
    """Configuration for the Kafka consumer."""

    def __init__(
        self,
        bootstrap_servers: List[str] = None,
        group_id: str = "ndt-telemetry-consumer",
        topics: Optional[List[str]] = None,
        auto_offset_reset: str = "latest",
    ) -> None:
        self.bootstrap_servers = bootstrap_servers or ["localhost:9092"]
        self.group_id = group_id
        self.topics = topics or ["ndt.telemetry.raw"]
        self.auto_offset_reset = auto_offset_reset


class TelemetryKafkaConsumer:
    """Consumes telemetry events from Apache Kafka topics.

    In production this wraps a `kafka-python` KafkaConsumer.  The stub
    implementation logs method calls without connecting to a real broker.
    """

    def __init__(self, config: KafkaConsumerConfig) -> None:
        self._config = config
        self._consumer = None
        self._running = False
        logger.info("TelemetryKafkaConsumer initialised (stub) — topics=%s", config.topics)

    def connect(self) -> None:
        """Establish connection to Kafka brokers."""
        logger.info(
            "TelemetryKafkaConsumer.connect() — stub, servers=%s",
            self._config.bootstrap_servers,
        )
        # TODO: from kafka import KafkaConsumer
        # self._consumer = KafkaConsumer(
        #     *self._config.topics,
        #     bootstrap_servers=self._config.bootstrap_servers,
        #     group_id=self._config.group_id,
        #     auto_offset_reset=self._config.auto_offset_reset,
        #     value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        # )

    def disconnect(self) -> None:
        """Close the Kafka consumer connection."""
        logger.info("TelemetryKafkaConsumer.disconnect() — stub")
        if self._consumer:
            self._consumer.close()
            self._consumer = None

    def start_consuming(self, handler: Callable[[dict], None]) -> None:
        """Start consuming messages and call handler for each message.

        Args:
            handler: Callable that receives a deserialized message dict.
        """
        self._running = True
        logger.info("TelemetryKafkaConsumer.start_consuming() — stub, handler=%r", handler)

    def stop_consuming(self) -> None:
        """Signal the consumer loop to stop."""
        self._running = False
        logger.info("TelemetryKafkaConsumer.stop_consuming() — stub")

    def health_check(self) -> bool:
        """Return True if the consumer is connected and running."""
        return False


# Async handler type: either a plain callable or a coroutine function
AsyncHandler = Callable[[dict], Union[None, Awaitable[None]]]


class AsyncTelemetryConsumer:
    """Async Kafka consumer for 5G telemetry events.

    Drives an asyncio event loop so that large volumes of concurrent telemetry
    events can be dispatched to handler coroutines without blocking, reducing
    end-to-end latency and enabling real-time synchronization with the physical
    network.

    Stub implementation — the consume loop simulates message delivery.
    Phase 3 will replace the inner loop with an ``aiokafka`` AsyncConsumer.
    """

    def __init__(self, config: KafkaConsumerConfig) -> None:
        self._config = config
        self._running = False
        self._task: Optional[asyncio.Task] = None
        logger.info(
            "AsyncTelemetryConsumer initialised (stub) — topics=%s", config.topics
        )

    async def connect(self) -> None:
        """Asynchronously establish connection to Kafka brokers.

        TODO: Replace with ``aiokafka.AIOKafkaConsumer`` in Phase 3.
        """
        logger.info(
            "AsyncTelemetryConsumer.connect() — stub, servers=%s",
            self._config.bootstrap_servers,
        )
        await asyncio.sleep(0)

    async def disconnect(self) -> None:
        """Asynchronously close the Kafka consumer connection."""
        logger.info("AsyncTelemetryConsumer.disconnect() — stub")
        await self.stop_consuming()
        await asyncio.sleep(0)

    async def _consume_loop(self, handler: AsyncHandler) -> None:
        """Inner consumption loop — yields to the event loop between batches."""
        logger.info(
            "AsyncTelemetryConsumer._consume_loop() started — topics=%s", self._config.topics
        )
        while self._running:
            # In production: fetch a batch from aiokafka and dispatch concurrently.
            # Stub: just yield to the event loop to simulate non-blocking behaviour.
            await asyncio.sleep(1)

    async def start_consuming(self, handler: AsyncHandler) -> None:
        """Start the async consumption loop in the background.

        The handler is called for every deserialized message dict.  It may be
        a plain callable or an ``async def`` coroutine function; both are
        supported transparently.

        Args:
            handler: Callable (sync or async) that processes each message.
        """
        if self._running:
            logger.warning("AsyncTelemetryConsumer.start_consuming() — already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._consume_loop(handler))
        logger.info(
            "AsyncTelemetryConsumer.start_consuming() — stub, handler=%r", handler
        )

    async def stop_consuming(self) -> None:
        """Signal the consumer loop to stop and await its completion."""
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
        logger.info("AsyncTelemetryConsumer.stop_consuming() — stub")

    async def health_check(self) -> bool:
        """Asynchronously return True if the consumer is running."""
        await asyncio.sleep(0)
        return self._running
