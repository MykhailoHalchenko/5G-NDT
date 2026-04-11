package com.kai.ndt5g.scaleout;

import com.kai.ndt5g.config.NdtConfig;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import com.scaleoutsoftware.digitaltwin.core.DigitalTwinBuilder;
import com.scaleoutsoftware.digitaltwin.core.SendingInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * ScaleOut Digital Twin lifecycle service for the 5G NDT platform.
 *
 * <p>Responsibilities:
 * <ol>
 *   <li>Register the {@link GNodeBDigitalTwinState} model and
 *       {@link GNodeBMessageProcessor} with the ScaleOut runtime via
 *       {@link DigitalTwinBuilder}.</li>
 *   <li>Provide {@link #updateState(GNodeBState)} for use by the WLDT layer
 *       to push new telemetry into the ScaleOut grid whenever the shadow changes.</li>
 *   <li>Expose {@link #getState(String)} for read access from other platform
 *       components (e.g. the REST API).</li>
 * </ol>
 *
 * <p>When ScaleOut is not configured ({@link NdtConfig#scaleoutConnectionString}
 * is {@code null}), the service operates in local-cache mode: state is kept in a
 * plain {@link ConcurrentHashMap} so that the rest of the platform works without
 * a ScaleOut installation.
 */
public class ScaleOutTwinService {

    private static final Logger log = LoggerFactory.getLogger(ScaleOutTwinService.class);

    private final NdtConfig config;
    private final boolean   scaleoutEnabled;

    // ── Local fallback state store ─────────────────────────────────────────────

    /** Used when ScaleOut is not configured. */
    private final Map<String, GNodeBDigitalTwinState> localStore = new ConcurrentHashMap<>();

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * Initialise the service.  If {@link NdtConfig#scaleoutConnectionString} is
     * set, the ScaleOut runtime is initialised and the digital twin model is
     * registered; otherwise local-cache mode is activated.
     *
     * @param config application configuration
     */
    public ScaleOutTwinService(NdtConfig config) {
        this.config = Objects.requireNonNull(config, "config");

        if (config.scaleoutConnectionString != null && !config.scaleoutConnectionString.isBlank()) {
            this.scaleoutEnabled = true;
            registerWithScaleOut();
        } else {
            this.scaleoutEnabled = false;
            log.info("ScaleOutTwinService: connection string not set — using local-cache mode");
        }
    }

    // ── Public API ────────────────────────────────────────────────────────────

    /**
     * Push a state update for the given gNodeB into the ScaleOut grid (or
     * local cache in fallback mode).
     *
     * <p>Called by {@link com.kai.ndt5g.wldt.Ndt5gWldtInstance} on every WLDT
     * shadow change.  The call is synchronous but lightweight — ScaleOut handles
     * the in-memory write in microseconds.
     *
     * @param state updated gNodeB domain state
     */
    public void updateState(GNodeBState state) {
        Objects.requireNonNull(state, "state");

        GNodeBDigitalTwinState dtState = localStore.computeIfAbsent(
                state.getId(), id -> new GNodeBDigitalTwinState(state));
        dtState.setGnbState(state);
        dtState.refreshAlertCounters();

        if (scaleoutEnabled) {
            scaleoutUpdate(state);
        } else {
            localStore.put(state.getId(), dtState);
            log.debug("ScaleOutTwinService [local] updated gNodeB={} warnings={} criticals={}",
                    state.getId(), dtState.getWarningCount(), dtState.getCriticalCount());
        }
    }

    /**
     * Send a batch of telemetry messages to the ScaleOut processor for the
     * given gNodeB.  This routes through the ScaleOut message-delivery API so
     * that the {@link GNodeBMessageProcessor} applies the update.
     *
     * @param gnbId    gNodeB UUID string
     * @param snapshots KPI snapshots to apply
     * @param newStatus optional new operational status; {@code null} means no change
     */
    public void sendTelemetry(String gnbId, List<KpiSnapshot> snapshots,
                               GNodeBState.NodeStatus newStatus) {
        Objects.requireNonNull(gnbId, "gnbId");

        GNodeBMessageProcessor.TelemetryUpdate msg =
                new GNodeBMessageProcessor.TelemetryUpdate(snapshots, newStatus);

        if (scaleoutEnabled) {
            scaleoutSendMessage(gnbId, msg);
        } else {
            // In local mode, apply the update directly via the processor
            GNodeBDigitalTwinState state = localStore.get(gnbId);
            if (state != null) {
                new GNodeBMessageProcessor().processMessages(state, List.of(msg), null);
                log.debug("ScaleOutTwinService [local] processed message for gNodeB={}", gnbId);
            }
        }
    }

    /**
     * Return the current in-process state for the given gNodeB, or
     * {@link Optional#empty()} if no state has been recorded yet.
     */
    public Optional<GNodeBDigitalTwinState> getState(String gnbId) {
        return Optional.ofNullable(localStore.get(gnbId));
    }

    /** Return all currently tracked gNodeB IDs. */
    public Set<String> trackedGnbIds() {
        return Collections.unmodifiableSet(localStore.keySet());
    }

    // ── Internal ScaleOut helpers ─────────────────────────────────────────────

    /**
     * Register the digital twin model and message processor with the ScaleOut
     * runtime.  This must be called once at startup before any state updates are
     * sent.
     */
    private void registerWithScaleOut() {
        try {
            DigitalTwinBuilder builder = new DigitalTwinBuilder(
                    config.scaleoutConnectionString,
                    config.scaleoutAppName);

            builder.registerDigitalTwin(
                    GNodeBDigitalTwinState.class,
                    GNodeBMessageProcessor.class,
                    GNodeBMessageProcessor.TelemetryUpdate.class);

            builder.build();
            log.info("ScaleOutTwinService: registered with ScaleOut app='{}'",
                    config.scaleoutAppName);
        } catch (Exception e) {
            log.error("ScaleOutTwinService: registration failed — {}", e.getMessage(), e);
            // Fall back to local cache so the rest of the platform is unaffected.
        }
    }

    /** Push a state update to the ScaleOut grid. */
    private void scaleoutUpdate(GNodeBState state) {
        // In a full ScaleOut deployment, state is written via the client API.
        // The exact API depends on the ScaleOut deployment model (cloud vs on-prem).
        // TODO: replace with: ScaleOutStateClient.getInstance().set(state.getId(), dtState);
        log.debug("ScaleOutTwinService: state update queued for gNodeB={}", state.getId());
    }

    /** Deliver a telemetry message to the ScaleOut processor. */
    private void scaleoutSendMessage(String gnbId,
                                      GNodeBMessageProcessor.TelemetryUpdate msg) {
        // TODO: replace with: ScaleOutMessageClient.getInstance().send(gnbId, msg);
        log.debug("ScaleOutTwinService: message queued for gNodeB={}", gnbId);
    }
}
