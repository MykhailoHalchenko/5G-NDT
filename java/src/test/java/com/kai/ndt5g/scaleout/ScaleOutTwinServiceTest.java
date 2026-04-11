package com.kai.ndt5g.scaleout;

import com.kai.ndt5g.config.NdtConfig;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link ScaleOutTwinService} and {@link GNodeBMessageProcessor}.
 *
 * <p>All tests run in local-cache mode (no ScaleOut connection string configured).
 */
class ScaleOutTwinServiceTest {

    private ScaleOutTwinService service;
    private GNodeBState gnbState;

    @BeforeEach
    void setUp() {
        // Ensure no ScaleOut endpoint is configured
        System.clearProperty("ndt.scaleout.connection.string");
        NdtConfig config = NdtConfig.fromEnvironment();
        service = new ScaleOutTwinService(config);

        gnbState = new GNodeBState("gnb-001", "gNodeB-Test", 1001, "26601");
        gnbState.setStatus(GNodeBState.NodeStatus.ACTIVE);
    }

    @Test
    void updateState_stores_state_in_local_cache() {
        service.updateState(gnbState);
        Optional<GNodeBDigitalTwinState> result = service.getState("gnb-001");
        assertTrue(result.isPresent());
        assertEquals("gnb-001", result.get().getGnbState().getId());
    }

    @Test
    void updateState_tracks_gnb_id() {
        service.updateState(gnbState);
        assertTrue(service.trackedGnbIds().contains("gnb-001"));
    }

    @Test
    void updateState_null_throws() {
        assertThrows(NullPointerException.class, () -> service.updateState(null));
    }

    @Test
    void getState_returns_empty_for_unknown_id() {
        assertTrue(service.getState("unknown").isEmpty());
    }

    @Test
    void sendTelemetry_updates_kpi_in_local_mode() {
        service.updateState(gnbState);

        KpiSnapshot latencyKpi = new KpiSnapshot(
                "gnb-001", "latency_ms", 30.0, "ms", Instant.now(), 20.0, 50.0);
        service.sendTelemetry("gnb-001", List.of(latencyKpi), null);

        Optional<GNodeBDigitalTwinState> result = service.getState("gnb-001");
        assertTrue(result.isPresent());
        Optional<KpiSnapshot> stored = result.get().getGnbState().getKpi("latency_ms");
        assertTrue(stored.isPresent());
        assertEquals(30.0, stored.get().getValue(), 1e-9);
    }

    @Test
    void sendTelemetry_updates_status_in_local_mode() {
        service.updateState(gnbState);

        service.sendTelemetry("gnb-001", List.of(), GNodeBState.NodeStatus.DEGRADED);

        Optional<GNodeBDigitalTwinState> result = service.getState("gnb-001");
        assertTrue(result.isPresent());
        assertEquals(GNodeBState.NodeStatus.DEGRADED, result.get().getGnbState().getStatus());
    }

    // ── GNodeBMessageProcessor ────────────────────────────────────────────────

    @Test
    void processor_returns_doUpdateDigitalTwinState_when_kpis_applied() {
        GNodeBDigitalTwinState dtState = new GNodeBDigitalTwinState(gnbState);
        KpiSnapshot kpi = KpiSnapshot.of("gnb-001", "throughput_mbps", 900.0, "Mbps");
        GNodeBMessageProcessor.TelemetryUpdate msg =
                new GNodeBMessageProcessor.TelemetryUpdate(List.of(kpi), null);

        var result = new GNodeBMessageProcessor().processMessages(dtState, List.of(msg), null);
        assertNotNull(result);
    }

    @Test
    void processor_returns_noUpdate_when_no_messages() {
        GNodeBDigitalTwinState dtState = new GNodeBDigitalTwinState(gnbState);
        var result = new GNodeBMessageProcessor().processMessages(dtState, List.of(), null);
        assertNotNull(result);
    }

    @Test
    void processor_refreshes_alert_counters() {
        GNodeBDigitalTwinState dtState = new GNodeBDigitalTwinState(gnbState);

        // CRITICAL latency
        KpiSnapshot criticalKpi = new KpiSnapshot(
                "gnb-001", "latency_ms", 99.0, "ms", Instant.now(), 20.0, 50.0);
        GNodeBMessageProcessor.TelemetryUpdate msg =
                new GNodeBMessageProcessor.TelemetryUpdate(List.of(criticalKpi), null);

        new GNodeBMessageProcessor().processMessages(dtState, List.of(msg), null);

        assertEquals(1, dtState.getCriticalCount());
        assertEquals(0, dtState.getWarningCount());
    }
}
