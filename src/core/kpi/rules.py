"""KPI calculation rules.

Defines the declarative rule set used to evaluate KPI thresholds and
generate alerts when SLA boundaries are violated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..topology.models import KPI, KPISeverity

logger = logging.getLogger(__name__)


@dataclass
class KPIRule:
    """A single KPI evaluation rule."""

    metric_name: str
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    entity_type: Optional[str] = None
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    def evaluate(self, kpi: KPI) -> KPISeverity:
        """Apply this rule to a KPI value and return the resulting severity."""
        if self.critical_threshold is not None and kpi.value >= self.critical_threshold:
            return KPISeverity.CRITICAL
        if self.warning_threshold is not None and kpi.value >= self.warning_threshold:
            return KPISeverity.WARNING
        return KPISeverity.INFO


# ── Default rule set ──────────────────────────────────────────────────────────

DEFAULT_RULES: List[KPIRule] = [
    KPIRule(
        metric_name="latency_ms",
        warning_threshold=10.0,
        critical_threshold=50.0,
        entity_type="gNodeB",
        description="End-to-end latency alert",
    ),
    KPIRule(
        metric_name="packet_loss_percent",
        warning_threshold=1.0,
        critical_threshold=5.0,
        entity_type="gNodeB",
        description="Packet loss rate alert",
    ),
    KPIRule(
        metric_name="cpu_utilization_percent",
        warning_threshold=75.0,
        critical_threshold=90.0,
        entity_type="CU",
        description="CU CPU utilization alert",
    ),
    KPIRule(
        metric_name="memory_utilization_percent",
        warning_threshold=80.0,
        critical_threshold=95.0,
        entity_type="CU",
        description="CU memory utilization alert",
    ),
    KPIRule(
        metric_name="utilization_percent",
        warning_threshold=70.0,
        critical_threshold=90.0,
        entity_type="NetworkSlice",
        description="Slice capacity utilization alert",
    ),
    KPIRule(
        metric_name="current_load_percent",
        warning_threshold=75.0,
        critical_threshold=95.0,
        entity_type="DU",
        description="DU load alert",
    ),
]


class KPIRuleEngine:
    """Evaluates KPIs against a configurable rule set."""

    def __init__(self, rules: Optional[List[KPIRule]] = None) -> None:
        self._rules: List[KPIRule] = rules if rules is not None else list(DEFAULT_RULES)
        logger.info("KPIRuleEngine initialised with %d rules", len(self._rules))

    def add_rule(self, rule: KPIRule) -> None:
        """Register an additional rule."""
        self._rules.append(rule)

    def get_rules_for(self, entity_type: str, metric_name: str) -> List[KPIRule]:
        """Return all rules that match the given entity type and metric name."""
        return [
            r for r in self._rules
            if r.metric_name == metric_name
            and (r.entity_type is None or r.entity_type == entity_type)
        ]

    def evaluate(self, kpi: KPI) -> KPISeverity:
        """Evaluate a KPI against all matching rules and return the highest severity.

        If no rule matches, returns INFO.
        """
        matching_rules = self.get_rules_for(kpi.entity_type, kpi.metric_name)
        if not matching_rules:
            return KPISeverity.INFO
        severities = [rule.evaluate(kpi) for rule in matching_rules]
        severity_order = {KPISeverity.INFO: 0, KPISeverity.WARNING: 1, KPISeverity.CRITICAL: 2}
        return max(severities, key=lambda s: severity_order[s])

    def evaluate_batch(self, kpis: List[KPI]) -> Dict[str, KPISeverity]:
        """Evaluate a list of KPIs and return a mapping of kpi.id -> severity."""
        return {str(kpi.id): self.evaluate(kpi) for kpi in kpis}
