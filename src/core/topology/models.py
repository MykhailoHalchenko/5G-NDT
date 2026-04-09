"""Pydantic data models for 5G network entities.

Defines the core domain objects used throughout the Digital Twin:
gNodeB, CU, DU, NetworkSlice, KPI, and Connection.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────────


class NodeStatus(str, Enum):
    """Operational status of a network node."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


class SliceType(str, Enum):
    """IMT-2020 / 3GPP slice service types."""

    EMBB = "eMBB"       # Enhanced Mobile Broadband
    URLLC = "URLLC"     # Ultra-Reliable Low-Latency Communications
    MMTC = "mMTC"       # Massive Machine Type Communications
    CUSTOM = "custom"


class FrequencyBand(str, Enum):
    """Supported 5G NR frequency bands (FR1 / FR2)."""

    N78 = "n78"     # 3.5 GHz (Sub-6 GHz)
    N258 = "n258"   # 26 GHz (mmWave)
    N41 = "n41"     # 2.5 GHz
    N77 = "n77"     # 3.3–4.2 GHz
    OTHER = "other"


class ConnectionType(str, Enum):
    """Types of logical connections between network elements."""

    F1 = "F1"       # CU–DU interface
    E1 = "E1"       # CU-CP – CU-UP interface
    NG = "NG"       # gNodeB – 5GC interface
    XN = "Xn"       # Inter-gNodeB interface
    FRONTHAUL = "fronthaul"
    BACKHAUL = "backhaul"
    MIDHAUL = "midhaul"


# ── Base ──────────────────────────────────────────────────────────────────────


class BaseEntity(BaseModel):
    """Common fields shared by all 5G network entities."""

    id: UUID = Field(default_factory=uuid4, description="Unique entity identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name")
    description: Optional[str] = Field(None, max_length=1024)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = Field(default_factory=dict, description="Arbitrary key-value metadata")

    model_config = {"use_enum_values": True}


# ── Network Nodes ─────────────────────────────────────────────────────────────


class DU(BaseEntity):
    """Distributed Unit — lower-layer RAN processing (L1/L2 lower).

    Resides close to the antenna; handles real-time radio signal processing.
    """

    cell_id: int = Field(..., ge=0, description="Physical cell identifier (PCI)")
    frequency_band: FrequencyBand = FrequencyBand.N78
    tx_power_dbm: float = Field(default=23.0, description="Transmit power in dBm")
    status: NodeStatus = NodeStatus.INACTIVE
    location: Optional[str] = Field(None, description="Physical location label")
    # Runtime telemetry snapshot (populated by the telemetry pipeline)
    current_load_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    active_ues: Optional[int] = Field(None, ge=0, description="Number of active UEs")


class CU(BaseEntity):
    """Centralized Unit — higher-layer RAN processing (PDCP/RRC).

    May be split into CU-CP (control plane) and CU-UP (user plane).
    """

    ip_address: Optional[str] = Field(None, description="Management IP address")
    port: int = Field(default=38472, ge=1, le=65535, description="F1AP port")
    status: NodeStatus = NodeStatus.INACTIVE
    connected_dus: List[UUID] = Field(default_factory=list, description="IDs of attached DUs")
    # Runtime telemetry snapshot
    cpu_utilization_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_utilization_percent: Optional[float] = Field(None, ge=0.0, le=100.0)


class gNodeB(BaseEntity):
    """5G base station (gNodeB / gNB).

    Top-level RAN element that aggregates one or more CU/DU pairs and
    provides the NG interface toward the 5G Core.
    """

    gnb_id: int = Field(..., ge=0, description="Global gNodeB identifier")
    plmn_id: str = Field(..., description="PLMN identity (MCC+MNC, e.g. '26601')")
    frequency_bands: List[FrequencyBand] = Field(default_factory=list)
    status: NodeStatus = NodeStatus.INACTIVE
    ip_address: Optional[str] = Field(None, description="NG-U/NG-C interface IP")
    vendor: Optional[str] = None
    software_version: Optional[str] = None
    # Associations
    cu_ids: List[UUID] = Field(default_factory=list, description="Attached CU entities")
    du_ids: List[UUID] = Field(default_factory=list, description="Attached DU entities")
    slice_ids: List[UUID] = Field(default_factory=list, description="Hosted network slices")
    # Runtime telemetry snapshot
    total_throughput_mbps: Optional[float] = Field(None, ge=0.0)
    average_latency_ms: Optional[float] = Field(None, ge=0.0)


# ── Network Slice ─────────────────────────────────────────────────────────────


class SliceQoSProfile(BaseModel):
    """Quality-of-Service parameters for a network slice."""

    max_downlink_mbps: float = Field(..., gt=0)
    max_uplink_mbps: float = Field(..., gt=0)
    max_latency_ms: float = Field(..., gt=0)
    reliability_percent: float = Field(default=99.9, ge=0.0, le=100.0)
    priority: int = Field(default=5, ge=1, le=10, description="Scheduling priority (1=highest)")


class NetworkSlice(BaseEntity):
    """3GPP Network Slice instance.

    Represents an end-to-end logical network tailored for a specific service.
    """

    s_nssai: str = Field(..., description="Single Network Slice Selection Assistance Info (SST:SD)")
    slice_type: SliceType = SliceType.EMBB
    qos_profile: SliceQoSProfile
    status: NodeStatus = NodeStatus.INACTIVE
    gnb_ids: List[UUID] = Field(default_factory=list, description="Hosting gNodeBs")
    # Runtime
    current_subscribers: Optional[int] = Field(None, ge=0)
    utilization_percent: Optional[float] = Field(None, ge=0.0, le=100.0)


# ── KPI ───────────────────────────────────────────────────────────────────────


class KPISeverity(str, Enum):
    """Alert severity levels for KPI threshold violations."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class KPI(BaseModel):
    """Key Performance Indicator snapshot for a network entity.

    Stores the current measured value along with configurable thresholds.
    """

    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID = Field(..., description="ID of the entity this KPI belongs to")
    entity_type: str = Field(..., description="Entity class name, e.g. 'gNodeB'")
    metric_name: str = Field(..., description="Metric identifier, e.g. 'latency_ms'")
    value: float
    unit: str = Field(default="", description="Unit of measurement, e.g. 'ms', '%'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Thresholds
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    # Computed
    severity: Optional[KPISeverity] = None
    labels: Dict[str, Any] = Field(default_factory=dict)

    def compute_severity(self) -> KPISeverity:
        """Determine severity based on configured thresholds."""
        if self.critical_threshold is not None and self.value >= self.critical_threshold:
            return KPISeverity.CRITICAL
        if self.warning_threshold is not None and self.value >= self.warning_threshold:
            return KPISeverity.WARNING
        return KPISeverity.INFO


# ── Connection ────────────────────────────────────────────────────────────────


class Connection(BaseModel):
    """Logical link between two network entities in the topology graph."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID = Field(..., description="Source entity UUID")
    target_id: UUID = Field(..., description="Target entity UUID")
    connection_type: ConnectionType
    bandwidth_mbps: Optional[float] = Field(None, ge=0.0)
    latency_ms: Optional[float] = Field(None, ge=0.0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Topology snapshot ─────────────────────────────────────────────────────────


class TopologySnapshot(BaseModel):
    """Point-in-time snapshot of the entire network topology."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    gnodebs: List[gNodeB] = Field(default_factory=list)
    cus: List[CU] = Field(default_factory=list)
    dus: List[DU] = Field(default_factory=list)
    slices: List[NetworkSlice] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)
