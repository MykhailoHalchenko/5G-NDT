package com.kai.ndt5g.wldt;

import com.kai.ndt5g.model.GNodeBState;
import it.wldt.adapter.digital.DigitalAdapter;
import it.wldt.adapter.digital.event.DigitalActionRequest;
import it.wldt.core.state.DigitalTwinState;
import it.wldt.core.state.DigitalTwinStateChange;
import it.wldt.exception.EventBusException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Objects;
import java.util.function.BiConsumer;

/**
 * WLDT Digital Adapter for a 5G gNodeB.
 *
 * <p>The Digital Adapter is the <em>outbound</em> side of the Digital Twin: it
 * receives state-change notifications from the shadowing layer and forwards them
 * to external consumers — REST API clients, Azure ADT, ScaleOut, dashboards,
 * or any other sink registered via the {@code stateChangeListener} callback.
 *
 * <p>It also handles inbound digital actions (e.g. "apply this configuration")
 * by forwarding them back through the WLDT event bus to the physical adapter.
 */
public class GNodeBDigitalAdapter extends DigitalAdapter {

    private static final Logger log = LoggerFactory.getLogger(GNodeBDigitalAdapter.class);

    /**
     * Callback invoked when the digital state changes.
     *
     * <p>Parameters: {@code (currentState, changeList)}.  The implementation
     * in {@link Ndt5gWldtInstance} wires this to the Azure ADT connector and the
     * ScaleOut twin service.
     */
    private final BiConsumer<DigitalTwinState, List<DigitalTwinStateChange>> stateChangeListener;

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * @param adapterId           unique WLDT identifier for this adapter instance
     * @param stateChangeListener callback for every state-change notification;
     *                            may be {@code null} to disable forwarding
     */
    public GNodeBDigitalAdapter(String adapterId,
                                 BiConsumer<DigitalTwinState, List<DigitalTwinStateChange>> stateChangeListener) {
        super(adapterId);
        this.stateChangeListener = stateChangeListener;
    }

    // ── DigitalAdapter lifecycle ───────────────────────────────────────────────

    @Override
    public void onAdapterStart() {
        log.info("GNodeBDigitalAdapter[{}] started", getId());
    }

    @Override
    public void onAdapterStop() {
        log.info("GNodeBDigitalAdapter[{}] stopped", getId());
    }

    /**
     * Invoked when the shadowing function has produced an initial bound state and
     * the digital adapter can begin receiving updates.
     */
    @Override
    public void onDigitalTwinBound(DigitalTwinState initialState) {
        log.info("GNodeBDigitalAdapter[{}] bound — initial property count: {}",
                getId(), initialState.getPropertyList().map(List::size).orElse(0));
    }

    @Override
    public void onDigitalTwinUnBound(DigitalTwinState finalState, String adapterId) {
        log.warn("GNodeBDigitalAdapter[{}] unbound from adapter {}", getId(), adapterId);
    }

    // ── State change notifications ─────────────────────────────────────────────

    @Override
    public void onStateChangePropertyCreated(DigitalTwinState currentState,
                                              DigitalTwinStateChange stateChange) {
        log.debug("GNodeBDigitalAdapter[{}] property created: {}",
                getId(), stateChange.getResourceId());
        notifyStateChange(currentState, List.of(stateChange));
    }

    @Override
    public void onStateChangePropertyUpdated(DigitalTwinState currentState,
                                              DigitalTwinStateChange stateChange) {
        log.debug("GNodeBDigitalAdapter[{}] property updated: {}",
                getId(), stateChange.getResourceId());
        notifyStateChange(currentState, List.of(stateChange));
    }

    @Override
    public void onStateChangePropertyDeleted(DigitalTwinState currentState,
                                              DigitalTwinStateChange stateChange) {
        log.debug("GNodeBDigitalAdapter[{}] property deleted: {}",
                getId(), stateChange.getResourceId());
        notifyStateChange(currentState, List.of(stateChange));
    }

    // ── Action handling ────────────────────────────────────────────────────────

    /**
     * Handle an inbound digital action request (e.g. push configuration to gNodeB).
     * The action is forwarded to the physical adapter via the WLDT event bus.
     */
    @Override
    public void onDigitalActionRequest(DigitalActionRequest actionRequest) {
        log.info("GNodeBDigitalAdapter[{}] forwarding action to physical: type={} body={}",
                getId(), actionRequest.getActionType(), actionRequest.getActionBody());
        try {
            publishDigitalActionRequest(actionRequest);
        } catch (EventBusException e) {
            log.error("GNodeBDigitalAdapter[{}] failed to forward action: {}",
                    getId(), e.getMessage(), e);
        }
    }

    // ── Internal helpers ──────────────────────────────────────────────────────

    private void notifyStateChange(DigitalTwinState state, List<DigitalTwinStateChange> changes) {
        if (stateChangeListener != null) {
            try {
                stateChangeListener.accept(state, changes);
            } catch (Exception e) {
                log.warn("GNodeBDigitalAdapter[{}] stateChangeListener threw: {}",
                        getId(), e.getMessage(), e);
            }
        }
    }
}
