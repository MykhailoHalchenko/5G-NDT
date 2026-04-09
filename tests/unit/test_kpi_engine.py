"""Unit tests for the KPI rules engine."""

from __future__ import annotations

import pytest
from uuid import uuid4

from src.core.kpi.rules import KPIRule, KPIRuleEngine, DEFAULT_RULES
from src.core.topology.models import KPI, KPISeverity


def _make_kpi(metric_name: str, value: float, entity_type: str = "gNodeB", **kwargs) -> KPI:
    return KPI(
        entity_id=uuid4(),
        entity_type=entity_type,
        metric_name=metric_name,
        value=value,
        **kwargs,
    )


class TestKPIRule:
    def test_info_below_warning(self):
        rule = KPIRule(metric_name="latency_ms", warning_threshold=10.0, critical_threshold=50.0)
        kpi = _make_kpi("latency_ms", 5.0)
        assert rule.evaluate(kpi) == KPISeverity.INFO

    def test_warning_at_threshold(self):
        rule = KPIRule(metric_name="latency_ms", warning_threshold=10.0, critical_threshold=50.0)
        kpi = _make_kpi("latency_ms", 10.0)
        assert rule.evaluate(kpi) == KPISeverity.WARNING

    def test_critical_at_threshold(self):
        rule = KPIRule(metric_name="latency_ms", warning_threshold=10.0, critical_threshold=50.0)
        kpi = _make_kpi("latency_ms", 50.0)
        assert rule.evaluate(kpi) == KPISeverity.CRITICAL

    def test_no_thresholds_always_info(self):
        rule = KPIRule(metric_name="some_metric")
        kpi = _make_kpi("some_metric", 9999.0)
        assert rule.evaluate(kpi) == KPISeverity.INFO

    def test_only_warning_threshold(self):
        rule = KPIRule(metric_name="cpu", warning_threshold=80.0)
        assert rule.evaluate(_make_kpi("cpu", 79.0)) == KPISeverity.INFO
        assert rule.evaluate(_make_kpi("cpu", 80.0)) == KPISeverity.WARNING
        assert rule.evaluate(_make_kpi("cpu", 99.0)) == KPISeverity.WARNING


class TestKPIRuleEngine:
    def test_default_rules_loaded(self):
        engine = KPIRuleEngine()
        assert len(engine._rules) == len(DEFAULT_RULES)

    def test_evaluate_latency_warning(self):
        engine = KPIRuleEngine()
        kpi = _make_kpi("latency_ms", 15.0, entity_type="gNodeB")
        result = engine.evaluate(kpi)
        assert result == KPISeverity.WARNING

    def test_evaluate_latency_critical(self):
        engine = KPIRuleEngine()
        kpi = _make_kpi("latency_ms", 60.0, entity_type="gNodeB")
        result = engine.evaluate(kpi)
        assert result == KPISeverity.CRITICAL

    def test_evaluate_no_matching_rule_returns_info(self):
        engine = KPIRuleEngine()
        kpi = _make_kpi("unknown_metric_xyz", 999.0, entity_type="SomeEntity")
        result = engine.evaluate(kpi)
        assert result == KPISeverity.INFO

    def test_add_rule(self):
        engine = KPIRuleEngine(rules=[])
        assert len(engine._rules) == 0
        engine.add_rule(KPIRule(metric_name="test_metric", warning_threshold=5.0))
        assert len(engine._rules) == 1

    def test_get_rules_for_entity_and_metric(self):
        engine = KPIRuleEngine()
        rules = engine.get_rules_for("gNodeB", "latency_ms")
        assert len(rules) >= 1
        for rule in rules:
            assert rule.metric_name == "latency_ms"

    def test_evaluate_batch(self):
        engine = KPIRuleEngine()
        kpis = [
            _make_kpi("latency_ms", 5.0, entity_type="gNodeB"),
            _make_kpi("latency_ms", 55.0, entity_type="gNodeB"),
        ]
        results = engine.evaluate_batch(kpis)
        assert len(results) == 2
        severities = list(results.values())
        assert KPISeverity.INFO in severities
        assert KPISeverity.CRITICAL in severities

    def test_cu_cpu_rule(self):
        engine = KPIRuleEngine()
        kpi = _make_kpi("cpu_utilization_percent", 92.0, entity_type="CU")
        assert engine.evaluate(kpi) == KPISeverity.CRITICAL

    def test_slice_utilization_warning(self):
        engine = KPIRuleEngine()
        kpi = _make_kpi("utilization_percent", 75.0, entity_type="NetworkSlice")
        assert engine.evaluate(kpi) == KPISeverity.WARNING
