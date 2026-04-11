package com.kai.ndt5g.azure;

import com.kai.ndt5g.config.NdtConfig;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link AzureDigitalTwinsConnector}.
 *
 * <p>All tests run in dry-run mode (no real Azure endpoint configured), so no
 * network calls are made.
 */
class AzureDigitalTwinsConnectorTest {

    private AzureDigitalTwinsConnector connector;
    private GNodeBState gnbState;

    @BeforeEach
    void setUp() {
        // Build a dry-run config (no endpoint → dry-run mode)
        System.setProperty("ndt.azure.dry.run", "true");
        NdtConfig config = NdtConfig.fromEnvironment();
        connector = new AzureDigitalTwinsConnector(config);

        gnbState = new GNodeBState("gnb-001", "gNodeB-Test", 1001, "26601");
        gnbState.setStatus(GNodeBState.NodeStatus.ACTIVE);
        gnbState.setAverageLatencyMs(12.5);
        gnbState.setTotalThroughputMbps(600.0);
        gnbState.recordKpi(new KpiSnapshot(
                "gnb-001", "latency_ms", 12.5, "ms", null, 20.0, 50.0));
    }

    @Test
    void ensureTwinExistsAsync_returns_twin_id_in_dry_run() throws Exception {
        CompletableFuture<String> future = connector.ensureTwinExistsAsync(gnbState);
        String twinId = future.get();
        assertNotNull(twinId);
        assertTrue(twinId.startsWith("gnb-"), "Twin ID should start with 'gnb-'");
    }

    @Test
    void syncGnbStateAsync_completes_in_dry_run() throws Exception {
        CompletableFuture<Void> future = connector.syncGnbStateAsync(gnbState);
        assertDoesNotThrow(() -> future.get());
    }

    @Test
    void deleteTwinAsync_completes_in_dry_run() throws Exception {
        CompletableFuture<Void> future = connector.deleteTwinAsync("gnb-001");
        assertDoesNotThrow(() -> future.get());
    }

    @Test
    void toTwinId_converts_uuid_correctly() {
        assertEquals("gnb-abc-def", AzureDigitalTwinsConnector.toTwinId("abc-def"));
        assertEquals("gnb-gnb-001", AzureDigitalTwinsConnector.toTwinId("gnb-001"));
    }

    @Test
    void ensureTwinExistsAsync_null_state_throws() {
        assertThrows(NullPointerException.class,
                () -> connector.ensureTwinExistsAsync(null));
    }

    @Test
    void syncGnbStateAsync_null_state_throws() {
        assertThrows(NullPointerException.class,
                () -> connector.syncGnbStateAsync(null));
    }
}
