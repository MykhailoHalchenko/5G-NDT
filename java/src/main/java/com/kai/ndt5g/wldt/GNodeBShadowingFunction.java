package com.kai.ndt5g.wldt;

import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import it.wldt.adapter.physical.PhysicalAssetDescription;
import it.wldt.adapter.physical.event.PhysicalAssetEventNotification;
import it.wldt.adapter.physical.event.PhysicalAssetPropertyVariation;
import it.wldt.adapter.physical.event.PhysicalAssetRelationshipInstanceCreated;
import it.wldt.adapter.physical.event.PhysicalAssetRelationshipInstanceDeleted;
import it.wldt.core.model.ShadowingModelFunction;
import it.wldt.core.state.DigitalTwinState;
import it.wldt.core.state.DigitalTwinStateProperty;
import it.wldt.exception.EventBusException;
import it.wldt.exception.ModelException;
import it.wldt.exception.WldtRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Objects;
import java.util.function.Consumer;

/**
 * WLDT Shadowing Model Function for a 5G gNodeB.
 *
 * <p>The shadowing function is the <em>brain</em> of the Digital Twin: it
 * receives physical-side property variations published by
 * {@link GNodeBPhysicalAdapter} and translates them into updates to the
 * {@link DigitalTwinState} that the {@link GNodeBDigitalAdapter} then
 * forwards to consumers (Azure ADT, ScaleOut, REST API, etc.).
 *
 * <p>Key design decisions:
 * <ul>
 *   <li>Each incoming physical property update is mapped 1-to-1 to a
 *       {@code DigitalTwinStateProperty} update, keeping the shadow
 *       consistent with the real device.</li>
 *   <li>A {@link GNodeBState} domain object is maintained alongside the raw
 *       WLDT state so that consumers receive typed data rather than raw
 *       {@code Object} values.</li>
 *   <li>An optional {@link Consumer}{@code <GNodeBState>} callback lets
 *       higher-level code (e.g. the Azure connector) react to every state
 *       change without coupling to the WLDT event bus.</li>
 * </ul>
 */
public class GNodeBShadowingFunction extends ShadowingModelFunction {

    private static final Logger log = LoggerFactory.getLogger(GNodeBShadowingFunction.class);

    // ── KPI thresholds (should be externalised to config in production) ────────

    private static final double LATENCY_WARNING_MS  = 20.0;
    private static final double LATENCY_CRITICAL_MS = 50.0;
    private static final double LOSS_WARNING_PCT    =  1.0;
    private static final double LOSS_CRITICAL_PCT   =  5.0;

    // ── Internal state ─────────────────────────────────────────────────────────

    private final GNodeBState          gnbState;
    private final Consumer<GNodeBState> stateChangeCallback;

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * @param functionId          unique WLDT identifier for this function instance
     * @param initialState        pre-populated domain state (id, name, gnbId, etc.)
     * @param stateChangeCallback invoked synchronously after each shadow update;
     *                            may be {@code null} to disable callbacks
     */
    public GNodeBShadowingFunction(String functionId,
                                    GNodeBState initialState,
                                    Consumer<GNodeBState> stateChangeCallback) {
        super(functionId);
        this.gnbState            = Objects.requireNonNull(initialState, "initialState");
        this.stateChangeCallback = stateChangeCallback;
    }

    // ── ShadowingModelFunction lifecycle ──────────────────────────────────────

    /**
     * Called once the WLDT engine has successfully bound this function to all
     * registered physical adapters.  This is the right place to initialise the
     * digital-twin state with the known properties.
     */
    @Override
    public void onDigitalTwinBound(Map<String, PhysicalAssetDescription> adaptersDescriptionMap)
            throws WldtRuntimeException, EventBusException, ModelException {
        log.info("GNodeBShadowingFunction[{}] bound to {} adapter(s)",
                getId(), adaptersDescriptionMap.size());

        // Register state properties that mirror the physical asset description.
        digitalTwinState.create();
        digitalTwinState.startUpdate();
        try {
            digitalTwinState.createProperty(
                    new DigitalTwinStateProperty<>(GNodeBPhysicalAdapter.PROP_THROUGHPUT_MBPS, 0.0));
            digitalTwinState.createProperty(
                    new DigitalTwinStateProperty<>(GNodeBPhysicalAdapter.PROP_LATENCY_MS, 0.0));
            digitalTwinState.createProperty(
                    new DigitalTwinStateProperty<>(GNodeBPhysicalAdapter.PROP_ACTIVE_UES, 0));
            digitalTwinState.createProperty(
                    new DigitalTwinStateProperty<>(GNodeBPhysicalAdapter.PROP_PACKET_LOSS_PCT, 0.0));
            digitalTwinState.createProperty(
                    new DigitalTwinStateProperty<>(GNodeBPhysicalAdapter.PROP_STATUS, "INACTIVE"));
        } finally {
            digitalTwinState.stopUpdate();
        }

        log.info("GNodeBShadowingFunction[{}] digital twin state initialised", getId());
    }

    @Override
    public void onDigitalTwinUnBound(Map<String, PhysicalAssetDescription> adaptersDescriptionMap,
                                      String adapterId)
            throws WldtRuntimeException, EventBusException, ModelException {
        log.warn("GNodeBShadowingFunction[{}] adapter {} unbound", getId(), adapterId);
    }

    /**
     * Called whenever a physical property changes.  Maps the raw value to the
     * domain {@link GNodeBState} and updates the WLDT shadow state.
     */
    @Override
    public void onPhysicalAssetPropertyVariation(PhysicalAssetPropertyVariation variation)
            throws WldtRuntimeException, EventBusException, ModelException {
        String key   = variation.getPropertyKey();
        Object value = variation.getPropertyValue();

        log.debug("GNodeBShadowingFunction[{}] property variation: {}={}", getId(), key, value);

        // Update WLDT digital state
        digitalTwinState.startUpdate();
        try {
            digitalTwinState.updateProperty(new DigitalTwinStateProperty<>(key, value));
        } finally {
            digitalTwinState.stopUpdate();
        }

        // Update typed domain model and compute KPI severity
        applyToGnbState(key, value);

        // Notify registered listener (e.g. Azure connector, ScaleOut service)
        if (stateChangeCallback != null) {
            stateChangeCallback.accept(gnbState);
        }
    }

    @Override
    public void onPhysicalAssetEventNotification(PhysicalAssetEventNotification<?> notification)
            throws WldtRuntimeException, EventBusException, ModelException {
        log.info("GNodeBShadowingFunction[{}] event notification: type={}",
                getId(), notification.getType());
        // Forward physical events as digital events if needed.
        // digitalTwinState.notifyDigitalTwinEvent(...);
    }

    @Override
    public void onPhysicalAssetRelationshipInstanceCreated(
            PhysicalAssetRelationshipInstanceCreated<?> event)
            throws WldtRuntimeException, EventBusException, ModelException {
        log.debug("GNodeBShadowingFunction[{}] relationship created: {}", getId(), event);
    }

    @Override
    public void onPhysicalAssetRelationshipInstanceDeleted(
            PhysicalAssetRelationshipInstanceDeleted<?> event)
            throws WldtRuntimeException, EventBusException, ModelException {
        log.debug("GNodeBShadowingFunction[{}] relationship deleted: {}", getId(), event);
    }

    // ── Domain model helpers ──────────────────────────────────────────────────

    /**
     * Map a raw property key/value pair to the typed {@link GNodeBState} and
     * compute/record KPI severities for numeric telemetry.
     */
    private void applyToGnbState(String key, Object value) {
        switch (key) {
            case GNodeBPhysicalAdapter.PROP_THROUGHPUT_MBPS -> {
                double v = toDouble(value);
                gnbState.setTotalThroughputMbps(v);
                gnbState.recordKpi(KpiSnapshot.of(gnbState.getId(), key, v, "Mbps"));
            }
            case GNodeBPhysicalAdapter.PROP_LATENCY_MS -> {
                double v = toDouble(value);
                gnbState.setAverageLatencyMs(v);
                gnbState.recordKpi(new KpiSnapshot(gnbState.getId(), key, v, "ms", null,
                        LATENCY_WARNING_MS, LATENCY_CRITICAL_MS));
            }
            case GNodeBPhysicalAdapter.PROP_ACTIVE_UES -> {
                int v = value instanceof Number n ? n.intValue() : 0;
                gnbState.setActiveUes(v);
                gnbState.recordKpi(KpiSnapshot.of(gnbState.getId(), key, v, "count"));
            }
            case GNodeBPhysicalAdapter.PROP_PACKET_LOSS_PCT -> {
                double v = toDouble(value);
                gnbState.recordKpi(new KpiSnapshot(gnbState.getId(), key, v, "%", null,
                        LOSS_WARNING_PCT, LOSS_CRITICAL_PCT));
            }
            case GNodeBPhysicalAdapter.PROP_STATUS -> {
                try {
                    gnbState.setStatus(GNodeBState.NodeStatus.valueOf(String.valueOf(value)));
                } catch (IllegalArgumentException e) {
                    log.warn("GNodeBShadowingFunction: unknown status value '{}'", value);
                }
            }
            default -> log.debug("GNodeBShadowingFunction: unhandled property '{}'", key);
        }
    }

    private static double toDouble(Object value) {
        if (value instanceof Number n) return n.doubleValue();
        try { return Double.parseDouble(String.valueOf(value)); }
        catch (NumberFormatException e) { return 0.0; }
    }

    // ── Accessors ─────────────────────────────────────────────────────────────

    /** Return the current domain state (useful for tests and direct inspection). */
    public GNodeBState getCurrentState() {
        return gnbState;
    }
}
