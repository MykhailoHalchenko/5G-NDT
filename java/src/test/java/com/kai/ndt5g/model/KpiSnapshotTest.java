package com.kai.ndt5g.model;

import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link KpiSnapshot}.
 */
class KpiSnapshotTest {

    @Test
    void severity_is_INFO_when_no_thresholds_set() {
        KpiSnapshot kpi = KpiSnapshot.of("e1", "latency_ms", 100.0, "ms");
        assertEquals(KpiSnapshot.KpiSeverity.INFO, kpi.getSeverity());
    }

    @Test
    void severity_is_INFO_below_warning_threshold() {
        KpiSnapshot kpi = new KpiSnapshot("e1", "latency_ms", 10.0, "ms", Instant.now(), 20.0, 50.0);
        assertEquals(KpiSnapshot.KpiSeverity.INFO, kpi.getSeverity());
    }

    @Test
    void severity_is_WARNING_at_warning_threshold() {
        KpiSnapshot kpi = new KpiSnapshot("e1", "latency_ms", 20.0, "ms", Instant.now(), 20.0, 50.0);
        assertEquals(KpiSnapshot.KpiSeverity.WARNING, kpi.getSeverity());
    }

    @Test
    void severity_is_CRITICAL_at_critical_threshold() {
        KpiSnapshot kpi = new KpiSnapshot("e1", "latency_ms", 50.0, "ms", Instant.now(), 20.0, 50.0);
        assertEquals(KpiSnapshot.KpiSeverity.CRITICAL, kpi.getSeverity());
    }

    @Test
    void severity_is_CRITICAL_above_critical_threshold() {
        KpiSnapshot kpi = new KpiSnapshot("e1", "latency_ms", 99.9, "ms", Instant.now(), 20.0, 50.0);
        assertEquals(KpiSnapshot.KpiSeverity.CRITICAL, kpi.getSeverity());
    }

    @Test
    void factory_of_sets_current_timestamp() {
        Instant before = Instant.now();
        KpiSnapshot kpi = KpiSnapshot.of("e1", "metric", 42.0, "unit");
        assertFalse(kpi.getTimestamp().isBefore(before));
    }

    @Test
    void null_entity_id_throws() {
        assertThrows(NullPointerException.class,
                () -> KpiSnapshot.of(null, "metric", 1.0, "unit"));
    }

    @Test
    void null_metric_name_throws() {
        assertThrows(NullPointerException.class,
                () -> KpiSnapshot.of("e1", null, 1.0, "unit"));
    }

    @Test
    void unit_defaults_to_empty_string_when_null() {
        KpiSnapshot kpi = KpiSnapshot.of("e1", "metric", 1.0, null);
        assertEquals("", kpi.getUnit());
    }
}
