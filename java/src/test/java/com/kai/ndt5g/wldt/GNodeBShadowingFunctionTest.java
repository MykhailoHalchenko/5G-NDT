package com.kai.ndt5g.wldt;

import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import it.wldt.adapter.physical.event.PhysicalAssetPropertyVariation;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link GNodeBShadowingFunction}.
 *
 * <p>The WLDT engine is not started in these tests — we call
 * {@link GNodeBShadowingFunction#onPhysicalAssetPropertyVariation} directly to
 * verify that the domain model is updated correctly without needing a running
 * event bus.
 */
class GNodeBShadowingFunctionTest {

    private GNodeBState           gnbState;
    private GNodeBShadowingFunction shadowingFunction;
    private final List<GNodeBState> callbackCapture = new ArrayList<>();

    @BeforeEach
    void setUp() {
        gnbState = new GNodeBState("gnb-001", "gNodeB-Test", 1001, "26601");
        shadowingFunction = new GNodeBShadowingFunction(
                "shadow-gnb-001",
                gnbState,
                callbackCapture::add);
    }

    @Test
    void throughput_property_updates_gnb_state() throws Exception {
        sendVariation(GNodeBPhysicalAdapter.PROP_THROUGHPUT_MBPS, 750.0);

        assertEquals(750.0, gnbState.getTotalThroughputMbps(), 1e-9);
        Optional<KpiSnapshot> kpi = gnbState.getKpi(GNodeBPhysicalAdapter.PROP_THROUGHPUT_MBPS);
        assertTrue(kpi.isPresent());
        assertEquals(750.0, kpi.get().getValue(), 1e-9);
    }

    @Test
    void latency_property_updates_gnb_state_and_computes_severity() throws Exception {
        // Below warning threshold (20 ms) → INFO
        sendVariation(GNodeBPhysicalAdapter.PROP_LATENCY_MS, 10.0);
        assertEquals(KpiSnapshot.KpiSeverity.INFO,
                gnbState.getKpi(GNodeBPhysicalAdapter.PROP_LATENCY_MS).get().getSeverity());

        // At warning threshold (20 ms) → WARNING
        sendVariation(GNodeBPhysicalAdapter.PROP_LATENCY_MS, 20.0);
        assertEquals(KpiSnapshot.KpiSeverity.WARNING,
                gnbState.getKpi(GNodeBPhysicalAdapter.PROP_LATENCY_MS).get().getSeverity());

        // At critical threshold (50 ms) → CRITICAL
        sendVariation(GNodeBPhysicalAdapter.PROP_LATENCY_MS, 50.0);
        assertEquals(KpiSnapshot.KpiSeverity.CRITICAL,
                gnbState.getKpi(GNodeBPhysicalAdapter.PROP_LATENCY_MS).get().getSeverity());
    }

    @Test
    void active_ues_property_updates_gnb_state() throws Exception {
        sendVariation(GNodeBPhysicalAdapter.PROP_ACTIVE_UES, 120);
        assertEquals(120, gnbState.getActiveUes());
    }

    @Test
    void status_property_updates_gnb_status() throws Exception {
        sendVariation(GNodeBPhysicalAdapter.PROP_STATUS, "ACTIVE");
        assertEquals(GNodeBState.NodeStatus.ACTIVE, gnbState.getStatus());

        sendVariation(GNodeBPhysicalAdapter.PROP_STATUS, "DEGRADED");
        assertEquals(GNodeBState.NodeStatus.DEGRADED, gnbState.getStatus());
    }

    @Test
    void invalid_status_value_is_handled_gracefully() throws Exception {
        // Should not throw; unknown values are logged and ignored
        assertDoesNotThrow(() -> sendVariation(GNodeBPhysicalAdapter.PROP_STATUS, "UNKNOWN_STATE"));
    }

    @Test
    void callback_is_invoked_on_each_variation() throws Exception {
        sendVariation(GNodeBPhysicalAdapter.PROP_LATENCY_MS, 5.0);
        sendVariation(GNodeBPhysicalAdapter.PROP_ACTIVE_UES, 50);
        assertEquals(2, callbackCapture.size());
    }

    @Test
    void no_callback_when_null_listener_provided() throws Exception {
        GNodeBShadowingFunction noCallback =
                new GNodeBShadowingFunction("shadow-nocb",
                        new GNodeBState("x", "x", 1, "001"), null);
        // Should not throw
        assertDoesNotThrow(() ->
                noCallback.onPhysicalAssetPropertyVariation(
                        new PhysicalAssetPropertyVariation(GNodeBPhysicalAdapter.PROP_LATENCY_MS, 10.0)));
    }

    @Test
    void getCurrentState_returns_same_instance() {
        assertSame(gnbState, shadowingFunction.getCurrentState());
    }

    // ── Helper ────────────────────────────────────────────────────────────────

    private void sendVariation(String key, Object value) throws Exception {
        shadowingFunction.onPhysicalAssetPropertyVariation(
                new PhysicalAssetPropertyVariation(key, value));
    }
}
