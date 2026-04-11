package com.kai.ndt5g.wldt;

import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import it.wldt.adapter.physical.PhysicalAdapter;
import it.wldt.adapter.physical.PhysicalAssetDescription;
import it.wldt.adapter.physical.event.PhysicalAssetEventDefinition;
import it.wldt.adapter.physical.event.PhysicalAssetPropertyDefinition;
import it.wldt.core.model.ShadowingModelFunction;
import it.wldt.exception.EventBusException;
import it.wldt.exception.PhysicalAdapterException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * WLDT Physical Adapter for a 5G gNodeB.
 *
 * <p>Responsibilities:
 * <ol>
 *   <li>Declare the physical asset description (properties and events) that
 *       the shadowing function will observe.</li>
 *   <li>Run a background polling loop at {@code pollIntervalSeconds} to
 *       retrieve telemetry from the gNodeB over O-RAN interfaces
 *       (NETCONF / gNMI / REST — currently stubbed).</li>
 *   <li>Publish {@link it.wldt.adapter.physical.event.PhysicalAssetPropertyVariation}
 *       events to the WLDT event bus whenever a measurement changes.</li>
 * </ol>
 *
 * <p>The adapter is intentionally non-blocking: the polling thread is separate
 * from the WLDT event loop, and all publish calls are fire-and-forget from the
 * adapter's perspective.
 */
public class GNodeBPhysicalAdapter extends PhysicalAdapter {

    private static final Logger log = LoggerFactory.getLogger(GNodeBPhysicalAdapter.class);

    // ── Well-known property / event names ─────────────────────────────────────

    /** Property: total downlink+uplink throughput in Mbps. */
    public static final String PROP_THROUGHPUT_MBPS   = "total_throughput_mbps";
    /** Property: average end-to-end round-trip latency in ms. */
    public static final String PROP_LATENCY_MS        = "average_latency_ms";
    /** Property: number of active UEs served by this gNodeB. */
    public static final String PROP_ACTIVE_UES        = "active_ues";
    /** Property: packet loss percentage. */
    public static final String PROP_PACKET_LOSS_PCT   = "packet_loss_percent";
    /** Property: current operational status string. */
    public static final String PROP_STATUS            = "status";

    /** Event: KPI threshold violation alert. */
    public static final String EVENT_KPI_ALERT        = "kpi_alert";

    // ── Internal state ────────────────────────────────────────────────────────

    private final String            gnbId;
    private final String            gnbHost;
    private final int               pollIntervalSeconds;
    private final AtomicBoolean     running    = new AtomicBoolean(false);
    private       ScheduledFuture<?> pollTask;
    private final ScheduledExecutorService scheduler;

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * @param adapterId          unique identifier for this adapter instance (WLDT requirement)
     * @param gnbId              the gNodeB UUID string
     * @param gnbHost            hostname / IP of the gNodeB management interface
     * @param pollIntervalSeconds interval between successive telemetry polls
     */
    public GNodeBPhysicalAdapter(String adapterId, String gnbId, String gnbHost,
                                  int pollIntervalSeconds) {
        super(adapterId);
        this.gnbId               = Objects.requireNonNull(gnbId, "gnbId");
        this.gnbHost             = Objects.requireNonNull(gnbHost, "gnbHost");
        this.pollIntervalSeconds = pollIntervalSeconds > 0 ? pollIntervalSeconds : 5;
        // Initialise scheduler here so that gnbId is already set and thread name is safe.
        this.scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "gnb-poll-" + this.gnbId);
            t.setDaemon(true);
            return t;
        });
    }

    // ── PhysicalAdapter lifecycle ─────────────────────────────────────────────

    @Override
    public void onAdapterStart() throws PhysicalAdapterException, EventBusException {
        log.info("GNodeBPhysicalAdapter[{}] starting — host={} poll={}s",
                getId(), gnbHost, pollIntervalSeconds);

        // Declare the physical asset description that the shadowing function will observe.
        PhysicalAssetDescription pad = buildAssetDescription();
        notifyPhysicalAdapterBound(pad);

        // Start the async polling loop.
        running.set(true);
        pollTask = scheduler.scheduleAtFixedRate(
                this::pollAndPublish,
                0,
                pollIntervalSeconds,
                TimeUnit.SECONDS);

        log.info("GNodeBPhysicalAdapter[{}] started", getId());
    }

    @Override
    public void onAdapterStop() throws PhysicalAdapterException, EventBusException {
        log.info("GNodeBPhysicalAdapter[{}] stopping", getId());
        running.set(false);
        if (pollTask != null) {
            pollTask.cancel(false);
        }
        scheduler.shutdown();
        log.info("GNodeBPhysicalAdapter[{}] stopped", getId());
    }

    /**
     * Handle action requests forwarded from the digital side (e.g. config push).
     * Currently logged only; Phase-3 will dispatch to the real NETCONF/gNMI client.
     */
    @Override
    public void onIncomingPhysicalAction(
            it.wldt.adapter.physical.event.PhysicalAssetActionRequest actionRequest)
            throws EventBusException, it.wldt.exception.ModelException {
        log.info("GNodeBPhysicalAdapter[{}] incoming action: type={} body={}",
                getId(), actionRequest.getActionType(), actionRequest.getActionBody());
        // TODO Phase-3: translate to NETCONF edit-config / gNMI Set RPC
    }

    // ── Internal helpers ──────────────────────────────────────────────────────

    /**
     * Build the static description of properties and events exposed by this
     * physical gNodeB.
     */
    private PhysicalAssetDescription buildAssetDescription() {
        List<PhysicalAssetPropertyDefinition<?>> props = new ArrayList<>();
        props.add(new PhysicalAssetPropertyDefinition<>(PROP_THROUGHPUT_MBPS, Double.class));
        props.add(new PhysicalAssetPropertyDefinition<>(PROP_LATENCY_MS,      Double.class));
        props.add(new PhysicalAssetPropertyDefinition<>(PROP_ACTIVE_UES,      Integer.class));
        props.add(new PhysicalAssetPropertyDefinition<>(PROP_PACKET_LOSS_PCT, Double.class));
        props.add(new PhysicalAssetPropertyDefinition<>(PROP_STATUS,          String.class));

        List<PhysicalAssetEventDefinition> events = new ArrayList<>();
        events.add(new PhysicalAssetEventDefinition(EVENT_KPI_ALERT));

        return new PhysicalAssetDescription(props, events);
    }

    /**
     * One polling cycle: retrieve telemetry from the physical gNodeB and
     * publish any changed property values to the WLDT event bus.
     *
     * <p>This method runs on the dedicated scheduler thread and must be
     * non-blocking with respect to the WLDT core event loop.
     */
    private void pollAndPublish() {
        if (!running.get()) return;
        try {
            Map<String, Object> telemetry = fetchTelemetry();
            for (Map.Entry<String, Object> entry : telemetry.entrySet()) {
                publishPhysicalAssetPropertyVariation(
                        new it.wldt.adapter.physical.event.PhysicalAssetPropertyVariation(
                                entry.getKey(), entry.getValue()));
            }
            log.debug("GNodeBPhysicalAdapter[{}] published {} property updates",
                    getId(), telemetry.size());
        } catch (Exception e) {
            log.warn("GNodeBPhysicalAdapter[{}] polling error: {}", getId(), e.getMessage(), e);
        }
    }

    /**
     * Retrieve current telemetry from the physical gNodeB.
     *
     * <p><b>Stub:</b> returns synthetic values.  Replace with a real
     * {@code AsyncGnbAdapter.getTelemetry()} call (async task handed off to a
     * dedicated I/O thread pool) in Phase-3.
     *
     * @return map of property name → current value
     */
    private Map<String, Object> fetchTelemetry() {
        // ── Stub telemetry ────────────────────────────────────────────────────
        // In production: connect via NETCONF/gNMI, deserialise YANG data, return.
        Map<String, Object> data = new LinkedHashMap<>();
        data.put(PROP_THROUGHPUT_MBPS,   500.0 + ThreadLocalRandom.current().nextDouble(-50, 50));
        data.put(PROP_LATENCY_MS,         10.0 + ThreadLocalRandom.current().nextDouble(-2, 5));
        data.put(PROP_ACTIVE_UES,              ThreadLocalRandom.current().nextInt(20, 200));
        data.put(PROP_PACKET_LOSS_PCT,    ThreadLocalRandom.current().nextDouble(0, 0.5));
        data.put(PROP_STATUS,             "ACTIVE");
        return data;
    }
}
