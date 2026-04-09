"""5G Network Digital Twin — main entry point using pytwinnet.

This module builds the network Digital Twin from the 5G topology models
and exposes a simple CLI interface for running on Linux servers.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from loguru import logger

import pytwinnet
from pytwinnet import DigitalTwin, Network, TransceiverProperties, WirelessNode

from ..core.topology.models import NodeStatus, TopologySnapshot, gNodeB, DU

# ── Logging setup ──────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)


# ── Builders ──────────────────────────────────────────────────────────────────


def _transceiver_from_du(du: DU) -> TransceiverProperties:
    """Convert a DU model to pytwinnet TransceiverProperties."""
    return TransceiverProperties(
        transmit_power_dbm=du.tx_power_dbm,
        antenna_gain_dbi=0.0,
        carrier_frequency_hz=3_500_000_000.0,  # default 3.5 GHz (n78)
        additional={
            "cell_id": du.cell_id,
            "frequency_band": str(du.frequency_band),
            "status": du.status,
        },
    )


def _node_from_gnodeb(gnb: gNodeB) -> WirelessNode:
    """Convert a gNodeB model to a pytwinnet WirelessNode."""
    return WirelessNode(
        node_id=str(gnb.id),
        position=(0.0, 0.0, 30.0),  # default 30 m height; updated from telemetry
        metadata={
            "name": gnb.name,
            "gnb_id": gnb.gnb_id,
            "plmn_id": gnb.plmn_id,
            "vendor": gnb.vendor,
            "status": gnb.status,
        },
    )


def build_digital_twin(snapshot: TopologySnapshot) -> DigitalTwin:
    """Build a pytwinnet DigitalTwin from a 5G topology snapshot.

    Args:
        snapshot: Current topology snapshot containing gNodeBs and DUs.

    Returns:
        Configured DigitalTwin instance.
    """
    network = Network()

    # Add gNodeBs as wireless nodes
    for gnb in snapshot.gnodebs:
        node = _node_from_gnodeb(gnb)
        network.add_node(node)
        logger.info("Added gNodeB '{}' (id={}) to digital twin", gnb.name, gnb.gnb_id)

    # Add DUs as wireless nodes
    for du in snapshot.dus:
        du_node = WirelessNode(
            node_id=str(du.id),
            transceiver_properties=_transceiver_from_du(du),
            metadata={
                "name": du.name,
                "cell_id": du.cell_id,
                "status": du.status,
                "type": "DU",
            },
        )
        network.add_node(du_node)
        logger.info("Added DU '{}' (cell_id={}) to digital twin", du.name, du.cell_id)

    twin = DigitalTwin(network=network)
    logger.info(
        "Digital Twin built: {} nodes in network",
        len(network.list_nodes()),
    )
    return twin


def get_twin_snapshot(twin: DigitalTwin) -> dict:
    """Return a serialisable snapshot of the current Digital Twin state."""
    snap = twin.snapshot()
    return snap if isinstance(snap, dict) else {"snapshot": str(snap)}


# ── CLI entry point ────────────────────────────────────────────────────────────


def main(argv: Optional[list] = None) -> int:
    """CLI entry point for the 5G NDT application on Linux.

    Usage:
        python -m src.api.main            # run with empty topology
        python -m src.api.main --seed     # run with sample topology
    """
    args = argv if argv is not None else sys.argv[1:]
    use_seed = "--seed" in args

    if use_seed:
        snapshot = _build_sample_snapshot()
    else:
        snapshot = TopologySnapshot()

    twin = build_digital_twin(snapshot)

    logger.info("5G Network Digital Twin running — {} nodes", len(twin.network.list_nodes()))
    logger.info("Twin snapshot: {}", get_twin_snapshot(twin))
    return 0


def _build_sample_snapshot() -> TopologySnapshot:
    """Build a minimal sample topology for demonstration."""
    from uuid import uuid4
    from ..core.topology.models import CU, FrequencyBand

    gnb = gNodeB(
        name="gNB-KAI-01",
        gnb_id=1,
        plmn_id="26601",
        frequency_bands=[FrequencyBand.N78],
        status=NodeStatus.ACTIVE,
        vendor="KAI Lab",
    )
    du = DU(
        name="DU-KAI-01",
        cell_id=100,
        tx_power_dbm=23.0,
        status=NodeStatus.ACTIVE,
    )
    cu = CU(name="CU-KAI-01", status=NodeStatus.ACTIVE)
    return TopologySnapshot(gnodebs=[gnb], dus=[du], cus=[cu])


if __name__ == "__main__":
    sys.exit(main())
