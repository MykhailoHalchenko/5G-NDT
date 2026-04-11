package com.kai.ndt5g.scaleout;

import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import com.scaleoutsoftware.digitaltwin.core.MessageProcessor;
import com.scaleoutsoftware.digitaltwin.core.ProcessingResult;
import com.scaleoutsoftware.digitaltwin.core.SendingInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

/**
 * ScaleOut Digital Twin Builder message processor for a 5G gNodeB.
 *
 * <p>The ScaleOut runtime invokes {@link #processMessages} every time new
 * messages (telemetry updates) arrive for a particular twin instance.
 * The processor updates the {@link GNodeBDigitalTwinState} in-place, refreshes
 * KPI alert counters, and optionally sends derived messages to other twins.
 *
 * <p>Message type convention used here:
 * <ul>
 *   <li>{@link TelemetryUpdate} — a batch of KPI measurements from the physical network.</li>
 * </ul>
 *
 * <p>The processor is stateless (ScaleOut instantiates a new one per
 * invocation), so all mutable state lives inside {@link GNodeBDigitalTwinState}.
 */
public class GNodeBMessageProcessor extends MessageProcessor<GNodeBDigitalTwinState, GNodeBMessageProcessor.TelemetryUpdate> {

    private static final Logger log = LoggerFactory.getLogger(GNodeBMessageProcessor.class);

    // ── Message type ──────────────────────────────────────────────────────────

    /**
     * Inbound message carrying a batch of KPI snapshots for a single gNodeB.
     */
    public static final class TelemetryUpdate implements java.io.Serializable {
        private static final long serialVersionUID = 1L;

        private final List<KpiSnapshot> snapshots;
        private final GNodeBState.NodeStatus newStatus;

        public TelemetryUpdate(List<KpiSnapshot> snapshots, GNodeBState.NodeStatus newStatus) {
            this.snapshots  = snapshots != null ? List.copyOf(snapshots) : List.of();
            this.newStatus  = newStatus;
        }

        public List<KpiSnapshot>       getSnapshots() { return snapshots; }
        public GNodeBState.NodeStatus  getNewStatus() { return newStatus; }
    }

    // ── MessageProcessor entry point ──────────────────────────────────────────

    /**
     * Process a batch of {@link TelemetryUpdate} messages for one twin instance.
     *
     * <p>ScaleOut guarantees single-threaded access to {@code state} per twin ID,
     * so no synchronisation is required here.
     *
     * @param state    the mutable ScaleOut state for the gNodeB twin
     * @param messages the incoming telemetry batch
     * @param sender   interface for sending messages to other twins (unused here)
     * @return {@link ProcessingResult#doUpdateDigitalTwinState()} when the state
     *         was modified, {@link ProcessingResult#noUpdate()} otherwise
     */
    @Override
    public ProcessingResult processMessages(GNodeBDigitalTwinState state,
                                             List<TelemetryUpdate> messages,
                                             SendingInterface sender) {
        if (state.getGnbState() == null || messages == null || messages.isEmpty()) {
            return ProcessingResult.noUpdate();
        }

        boolean changed = false;

        for (TelemetryUpdate msg : messages) {
            // Apply KPI snapshots
            for (KpiSnapshot kpi : msg.getSnapshots()) {
                state.getGnbState().recordKpi(kpi);
                changed = true;
            }
            // Apply status change if present
            if (msg.getNewStatus() != null
                    && msg.getNewStatus() != state.getGnbState().getStatus()) {
                log.info("GNodeBMessageProcessor: status change gNodeB={} {} → {}",
                        state.getGnbState().getId(),
                        state.getGnbState().getStatus(),
                        msg.getNewStatus());
                state.getGnbState().setStatus(msg.getNewStatus());
                changed = true;
            }
        }

        if (changed) {
            state.refreshAlertCounters();
            log.debug("GNodeBMessageProcessor: updated gNodeB={} warnings={} criticals={}",
                    state.getGnbState().getId(),
                    state.getWarningCount(),
                    state.getCriticalCount());
            return ProcessingResult.doUpdateDigitalTwinState();
        }

        return ProcessingResult.noUpdate();
    }
}
