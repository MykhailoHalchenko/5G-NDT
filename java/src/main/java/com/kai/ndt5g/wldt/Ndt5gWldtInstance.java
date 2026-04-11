package com.kai.ndt5g.wldt;

import com.kai.ndt5g.azure.AzureDigitalTwinsConnector;
import com.kai.ndt5g.config.NdtConfig;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.scaleout.ScaleOutTwinService;
import it.wldt.core.engine.WldtEngine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Objects;

/**
 * Assembles and manages the WLDT Digital Twin instance for a single gNodeB.
 *
 * <p>Wiring:
 * <pre>
 *   GNodeBPhysicalAdapter ──► GNodeBShadowingFunction ──► GNodeBDigitalAdapter
 *                                       │
 *                            ┌──────────┼───────────┐
 *                            ▼          ▼           ▼
 *                   Azure ADT Connector  ScaleOut   logger
 * </pre>
 *
 * <p>The WLDT {@link WldtEngine} runs entirely on its own internal threads.
 * Start / stop are synchronous with respect to the calling thread.
 */
public class Ndt5gWldtInstance {

    private static final Logger log = LoggerFactory.getLogger(Ndt5gWldtInstance.class);

    private final WldtEngine              engine;
    private final GNodeBShadowingFunction shadowingFunction;
    private final GNodeBPhysicalAdapter   physicalAdapter;
    private final GNodeBDigitalAdapter    digitalAdapter;

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * Build a WLDT instance for the given gNodeB.
     *
     * @param config         application configuration
     * @param gnbState       pre-populated identity state (id, name, gnbId, plmnId)
     * @param gnbHost        management interface hostname / IP
     * @param azureConnector optional Azure ADT connector; pass {@code null} to skip Azure sync
     * @param scaleOut       optional ScaleOut service; pass {@code null} to skip ScaleOut sync
     */
    public Ndt5gWldtInstance(NdtConfig config,
                              GNodeBState gnbState,
                              String gnbHost,
                              AzureDigitalTwinsConnector azureConnector,
                              ScaleOutTwinService scaleOut) throws Exception {

        Objects.requireNonNull(config,   "config");
        Objects.requireNonNull(gnbState, "gnbState");
        Objects.requireNonNull(gnbHost,  "gnbHost");

        String gnbId = gnbState.getId();

        // ── Physical adapter ───────────────────────────────────────────────────
        physicalAdapter = new GNodeBPhysicalAdapter(
                "phys-" + gnbId,
                gnbId,
                gnbHost,
                config.wldtPollIntervalSeconds);

        // ── Shadowing function ─────────────────────────────────────────────────
        // The shadowing-function callback wires domain state changes to downstream sinks.
        shadowingFunction = new GNodeBShadowingFunction(
                "shadow-" + gnbId,
                gnbState,
                state -> onShadowStateChanged(state, azureConnector, scaleOut));

        // ── Digital adapter ────────────────────────────────────────────────────
        digitalAdapter = new GNodeBDigitalAdapter(
                "digital-" + gnbId,
                (dtState, changes) -> log.debug(
                        "Ndt5gWldtInstance[{}] digital state changed: {} change(s)",
                        gnbId, changes.size()));

        // ── Assemble the WLDT engine ───────────────────────────────────────────
        engine = new WldtEngine(shadowingFunction, gnbId);
        engine.addPhysicalAdapter(physicalAdapter);
        engine.addDigitalAdapter(digitalAdapter);

        log.info("Ndt5gWldtInstance assembled for gNodeB id={} host={}", gnbId, gnbHost);
    }

    // ── Public lifecycle ──────────────────────────────────────────────────────

    /**
     * Start the WLDT engine (non-blocking — engine runs on its own threads).
     */
    public void start() throws Exception {
        log.info("Ndt5gWldtInstance starting WldtEngine …");
        engine.startLifeCycle();
        log.info("Ndt5gWldtInstance WldtEngine started");
    }

    /**
     * Stop the WLDT engine gracefully.
     */
    public void stop() {
        log.info("Ndt5gWldtInstance stopping WldtEngine …");
        try {
            engine.stopLifeCycle();
        } catch (Exception e) {
            log.warn("Ndt5gWldtInstance: error during engine stop: {}", e.getMessage(), e);
        }
        log.info("Ndt5gWldtInstance WldtEngine stopped");
    }

    // ── Internal callback ─────────────────────────────────────────────────────

    /**
     * Invoked (on the WLDT shadowing thread) whenever the gNodeB shadow state
     * changes.  Propagates the new state to Azure ADT and ScaleOut asynchronously
     * so as not to block the WLDT event loop.
     */
    private void onShadowStateChanged(GNodeBState state,
                                       AzureDigitalTwinsConnector azureConnector,
                                       ScaleOutTwinService scaleOut) {
        if (azureConnector != null) {
            azureConnector.syncGnbStateAsync(state)
                    .exceptionally(ex -> {
                        log.warn("Azure ADT sync failed for gNodeB {}: {}",
                                state.getId(), ex.getMessage());
                        return null;
                    });
        }
        if (scaleOut != null) {
            scaleOut.updateState(state);
        }
    }

    // ── Accessors ─────────────────────────────────────────────────────────────

    public GNodeBState getCurrentState() {
        return shadowingFunction.getCurrentState();
    }
}
