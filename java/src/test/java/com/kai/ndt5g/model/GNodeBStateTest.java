package com.kai.ndt5g.model;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link GNodeBState}.
 */
class GNodeBStateTest {

    private GNodeBState state;

    @BeforeEach
    void setUp() {
        state = new GNodeBState("gnb-001", "gNodeB-Test", 1001, "26601");
    }

    @Test
    void constructor_sets_id_name_gnbId_plmnId() {
        assertEquals("gnb-001", state.getId());
        assertEquals("gNodeB-Test", state.getName());
        assertEquals(1001, state.getGnbId());
        assertEquals("26601", state.getPlmnId());
    }

    @Test
    void default_status_is_INACTIVE() {
        assertEquals(GNodeBState.NodeStatus.INACTIVE, state.getStatus());
    }

    @Test
    void recordKpi_stores_snapshot_by_metric_name() {
        KpiSnapshot kpi = KpiSnapshot.of("gnb-001", "latency_ms", 15.0, "ms");
        state.recordKpi(kpi);

        Optional<KpiSnapshot> found = state.getKpi("latency_ms");
        assertTrue(found.isPresent());
        assertEquals(15.0, found.get().getValue(), 1e-9);
    }

    @Test
    void recordKpi_replaces_previous_snapshot_for_same_metric() {
        state.recordKpi(KpiSnapshot.of("gnb-001", "latency_ms", 10.0, "ms"));
        state.recordKpi(KpiSnapshot.of("gnb-001", "latency_ms", 25.0, "ms"));

        assertEquals(25.0, state.getKpi("latency_ms").get().getValue(), 1e-9);
    }

    @Test
    void getKpi_returns_empty_for_unknown_metric() {
        assertTrue(state.getKpi("nonexistent").isEmpty());
    }

    @Test
    void getKpis_returns_unmodifiable_view() {
        state.recordKpi(KpiSnapshot.of("gnb-001", "throughput_mbps", 500.0, "Mbps"));
        assertThrows(UnsupportedOperationException.class,
                () -> state.getKpis().put("foo", KpiSnapshot.of("gnb-001", "foo", 1.0, "")));
    }

    @Test
    void recordKpi_null_throws() {
        assertThrows(NullPointerException.class, () -> state.recordKpi(null));
    }

    @Test
    void null_id_in_constructor_throws() {
        assertThrows(NullPointerException.class,
                () -> new GNodeBState(null, "name", 1, "26601"));
    }

    @Test
    void setStatus_updates_updatedAt() throws InterruptedException {
        var before = state.getUpdatedAt();
        Thread.sleep(1);   // ensure clock advances
        state.setStatus(GNodeBState.NodeStatus.ACTIVE);
        assertFalse(state.getUpdatedAt().isBefore(before));
        assertEquals(GNodeBState.NodeStatus.ACTIVE, state.getStatus());
    }
}
