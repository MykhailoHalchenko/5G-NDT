package com.kai.ndt5g.model;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.io.Serializable;
import java.time.Instant;
import java.util.*;

/**
 * Mutable Digital-Twin state for a 5G gNodeB.
 *
 * <p>This class is used by all three integration layers:
 * <ul>
 *   <li><b>WLDT</b> — carried inside a {@code DigitalTwinStateProperty} and updated by
 *       {@code GNodeBShadowingFunction} whenever physical telemetry arrives.</li>
 *   <li><b>Azure Digital Twins</b> — serialised to a {@code BasicDigitalTwin} and pushed to
 *       Azure ADT whenever the WLDT shadow changes.</li>
 *   <li><b>ScaleOut</b> — the {@code GNodeBDigitalTwinState} wraps this record and persists
 *       it in the ScaleOut in-memory grid.</li>
 * </ul>
 */
public class GNodeBState implements Serializable {

    /** Operational status matching the Python {@code NodeStatus} enum. */
    public enum NodeStatus { ACTIVE, INACTIVE, DEGRADED, MAINTENANCE, FAILED }

    // ── Identity ───────────────────────────────────────────────────────────────

    private String id;
    private String name;
    private int    gnbId;
    private String plmnId;
    private String vendor;
    private String softwareVersion;
    private String ipAddress;

    // ── Status ─────────────────────────────────────────────────────────────────

    private NodeStatus status = NodeStatus.INACTIVE;
    private Instant    updatedAt = Instant.now();

    // ── Real-time telemetry ────────────────────────────────────────────────────

    private Double totalThroughputMbps;
    private Double averageLatencyMs;
    private Integer activeUes;

    // ── Associated KPIs ────────────────────────────────────────────────────────

    /** Latest KPI snapshots keyed by metric name. */
    private final Map<String, KpiSnapshot> kpis = new LinkedHashMap<>();

    // ── Constructors ───────────────────────────────────────────────────────────

    public GNodeBState() { /* for Jackson and frameworks */ }

    @JsonCreator
    public GNodeBState(
            @JsonProperty("id")    String id,
            @JsonProperty("name")  String name,
            @JsonProperty("gnbId") int    gnbId,
            @JsonProperty("plmnId")String plmnId) {
        this.id     = Objects.requireNonNull(id,     "id");
        this.name   = Objects.requireNonNull(name,   "name");
        this.gnbId  = gnbId;
        this.plmnId = Objects.requireNonNull(plmnId, "plmnId");
    }

    // ── KPI helpers ────────────────────────────────────────────────────────────

    /**
     * Record a new KPI measurement.  The snapshot replaces any previous value
     * for the same metric name.
     *
     * @param snapshot non-null KPI snapshot
     */
    public void recordKpi(KpiSnapshot snapshot) {
        Objects.requireNonNull(snapshot, "snapshot");
        kpis.put(snapshot.getMetricName(), snapshot);
        this.updatedAt = Instant.now();
    }

    /**
     * Return the latest snapshot for {@code metricName}, or {@code Optional.empty()}
     * if no measurement has been recorded yet.
     */
    public Optional<KpiSnapshot> getKpi(String metricName) {
        return Optional.ofNullable(kpis.get(metricName));
    }

    /** Return an unmodifiable view of all recorded KPI snapshots. */
    public Map<String, KpiSnapshot> getKpis() {
        return Collections.unmodifiableMap(kpis);
    }

    // ── Getters / setters ──────────────────────────────────────────────────────

    public String     getId()                                      { return id; }
    public void       setId(String id)                             { this.id = id; }

    public String     getName()                                    { return name; }
    public void       setName(String name)                         { this.name = name; }

    public int        getGnbId()                                   { return gnbId; }
    public void       setGnbId(int gnbId)                          { this.gnbId = gnbId; }

    public String     getPlmnId()                                  { return plmnId; }
    public void       setPlmnId(String plmnId)                     { this.plmnId = plmnId; }

    public String     getVendor()                                  { return vendor; }
    public void       setVendor(String vendor)                     { this.vendor = vendor; }

    public String     getSoftwareVersion()                         { return softwareVersion; }
    public void       setSoftwareVersion(String softwareVersion)   { this.softwareVersion = softwareVersion; }

    public String     getIpAddress()                               { return ipAddress; }
    public void       setIpAddress(String ipAddress)               { this.ipAddress = ipAddress; }

    public NodeStatus getStatus()                                  { return status; }
    public void       setStatus(NodeStatus status)                 { this.status = status; this.updatedAt = Instant.now(); }

    public Instant    getUpdatedAt()                               { return updatedAt; }
    public void       setUpdatedAt(Instant updatedAt)              { this.updatedAt = updatedAt; }

    public Double     getTotalThroughputMbps()                     { return totalThroughputMbps; }
    public void       setTotalThroughputMbps(Double v)             { this.totalThroughputMbps = v; }

    public Double     getAverageLatencyMs()                        { return averageLatencyMs; }
    public void       setAverageLatencyMs(Double v)                { this.averageLatencyMs = v; }

    public Integer    getActiveUes()                               { return activeUes; }
    public void       setActiveUes(Integer v)                      { this.activeUes = v; }

    // ──────────────────────────────────────────────────────────────────────────

    @Override
    public String toString() {
        return String.format("GNodeBState{id=%s, name=%s, gnbId=%d, status=%s, latency=%.1f ms, kpis=%d}",
                id, name, gnbId, status,
                averageLatencyMs != null ? averageLatencyMs : 0.0,
                kpis.size());
    }
}
