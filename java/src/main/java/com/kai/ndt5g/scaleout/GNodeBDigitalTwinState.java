package com.kai.ndt5g.scaleout;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import com.scaleoutsoftware.digitaltwin.core.DigitalTwinBase;

import java.io.Serializable;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;

/**
 * ScaleOut Digital Twin Builder state model for a 5G gNodeB.
 *
 * <p>This class extends {@link DigitalTwinBase} so that the ScaleOut runtime
 * can persist, replicate, and recover it inside the in-memory data grid.
 * It wraps the canonical {@link GNodeBState} domain object to avoid
 * duplicating field definitions.
 *
 * <p>ScaleOut requires state classes to be {@link Serializable}.
 * Jackson's {@link JsonIgnoreProperties} prevents unknown fields from
 * breaking deserialisation when the schema evolves.
 *
 * @see GNodeBMessageProcessor
 * @see ScaleOutTwinService
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class GNodeBDigitalTwinState extends DigitalTwinBase implements Serializable {

    private static final long serialVersionUID = 1L;

    // ── Core state ─────────────────────────────────────────────────────────────

    private GNodeBState gnbState;

    // ── Alert counters (derived, updated by the message processor) ─────────────

    private int warningCount  = 0;
    private int criticalCount = 0;
    private Instant lastAlertAt;

    // ── Constructors ───────────────────────────────────────────────────────────

    /** Default constructor required by ScaleOut serialisation framework. */
    public GNodeBDigitalTwinState() {}

    /**
     * Initialise from a domain state snapshot.
     *
     * @param gnbState domain state (non-null)
     */
    public GNodeBDigitalTwinState(GNodeBState gnbState) {
        this.gnbState = Objects.requireNonNull(gnbState, "gnbState");
    }

    // ── KPI helpers ────────────────────────────────────────────────────────────

    /**
     * Recompute the warning / critical counter from the KPI snapshots currently
     * stored in {@link GNodeBState}.  Called by the message processor after each
     * telemetry update.
     */
    public void refreshAlertCounters() {
        if (gnbState == null) return;
        int warns = 0;
        int crits = 0;
        for (KpiSnapshot kpi : gnbState.getKpis().values()) {
            switch (kpi.getSeverity()) {
                case WARNING  -> warns++;
                case CRITICAL -> crits++;
                default       -> { /* INFO — no counter */ }
            }
        }
        this.warningCount  = warns;
        this.criticalCount = crits;
        if (warns > 0 || crits > 0) {
            this.lastAlertAt = Instant.now();
        }
    }

    // ── Getters / setters ──────────────────────────────────────────────────────

    public GNodeBState getGnbState()     { return gnbState; }
    public void        setGnbState(GNodeBState s) { this.gnbState = s; }

    public int         getWarningCount() { return warningCount; }
    public int         getCriticalCount(){ return criticalCount; }
    public Instant     getLastAlertAt()  { return lastAlertAt; }

    @Override
    public String toString() {
        return String.format(
                "GNodeBDigitalTwinState{id=%s, warnings=%d, criticals=%d}",
                gnbState != null ? gnbState.getId() : "?",
                warningCount, criticalCount);
    }
}
