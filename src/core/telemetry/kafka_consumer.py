"""Kafka consumer for 5G telemetry events (stub).

Consumes raw telemetry messages from Kafka topics and forwards them to
the normalizer pipeline for processing.
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

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
