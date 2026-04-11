package com.kai.ndt5g.model;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.io.Serializable;
import java.time.Instant;
import java.util.*;

/**
 * Mutable Digital-Twin state for a 3GPP Network Slice instance.
 *
 * <p>Mirrors the Python {@code NetworkSlice} Pydantic model and provides the
 * same {@link #recordKpi}/{@link #getKpi} helpers as {@link GNodeBState}.
 */
public class NetworkSliceState implements Serializable {

    /** IMT-2020 / 3GPP slice service types. */
    public enum SliceType { EMBB, URLLC, MMTC, CUSTOM }

    /** Operational status. */
    public enum NodeStatus { ACTIVE, INACTIVE, DEGRADED, MAINTENANCE, FAILED }

    // ── Identity ───────────────────────────────────────────────────────────────

    private String    id;
    private String    name;
    private String    sNssai;   // e.g. "1:000001"
    private SliceType sliceType = SliceType.EMBB;

    // ── QoS profile ────────────────────────────────────────────────────────────

    private double maxDownlinkMbps;
    private double maxUplinkMbps;
    private double maxLatencyMs;
    private double reliabilityPercent = 99.9;
    private int    priority           = 5;

    // ── Status / telemetry ─────────────────────────────────────────────────────

    private NodeStatus status          = NodeStatus.INACTIVE;
    private Integer    currentSubscribers;
    private Double     utilizationPercent;
    private Instant    updatedAt       = Instant.now();

    /** Latest KPI snapshots keyed by metric name. */
    private final Map<String, KpiSnapshot> kpis = new LinkedHashMap<>();

    // ── Constructors ───────────────────────────────────────────────────────────

    public NetworkSliceState() {}

    @JsonCreator
    public NetworkSliceState(
            @JsonProperty("id")        String    id,
            @JsonProperty("name")      String    name,
            @JsonProperty("sNssai")    String    sNssai,
            @JsonProperty("sliceType") SliceType sliceType) {
        this.id        = Objects.requireNonNull(id,     "id");
        this.name      = Objects.requireNonNull(name,   "name");
        this.sNssai    = Objects.requireNonNull(sNssai, "sNssai");
        this.sliceType = sliceType != null ? sliceType : SliceType.EMBB;
    }

    // ── KPI helpers ────────────────────────────────────────────────────────────

    public void recordKpi(KpiSnapshot snapshot) {
        Objects.requireNonNull(snapshot, "snapshot");
        kpis.put(snapshot.getMetricName(), snapshot);
        this.updatedAt = Instant.now();
    }

    public Optional<KpiSnapshot> getKpi(String metricName) {
        return Optional.ofNullable(kpis.get(metricName));
    }

    public Map<String, KpiSnapshot> getKpis() {
        return Collections.unmodifiableMap(kpis);
    }

    // ── Getters / setters ──────────────────────────────────────────────────────

    public String    getId()                                    { return id; }
    public void      setId(String id)                           { this.id = id; }

    public String    getName()                                  { return name; }
    public void      setName(String name)                       { this.name = name; }

    public String    getSNssai()                                { return sNssai; }
    public void      setSNssai(String sNssai)                   { this.sNssai = sNssai; }

    public SliceType getSliceType()                             { return sliceType; }
    public void      setSliceType(SliceType sliceType)          { this.sliceType = sliceType; }

    public double    getMaxDownlinkMbps()                       { return maxDownlinkMbps; }
    public void      setMaxDownlinkMbps(double v)               { this.maxDownlinkMbps = v; }

    public double    getMaxUplinkMbps()                         { return maxUplinkMbps; }
    public void      setMaxUplinkMbps(double v)                 { this.maxUplinkMbps = v; }

    public double    getMaxLatencyMs()                          { return maxLatencyMs; }
    public void      setMaxLatencyMs(double v)                  { this.maxLatencyMs = v; }

    public double    getReliabilityPercent()                    { return reliabilityPercent; }
    public void      setReliabilityPercent(double v)            { this.reliabilityPercent = v; }

    public int       getPriority()                              { return priority; }
    public void      setPriority(int priority)                  { this.priority = priority; }

    public NodeStatus getStatus()                               { return status; }
    public void       setStatus(NodeStatus status)              { this.status = status; this.updatedAt = Instant.now(); }

    public Integer   getCurrentSubscribers()                    { return currentSubscribers; }
    public void      setCurrentSubscribers(Integer v)           { this.currentSubscribers = v; }

    public Double    getUtilizationPercent()                    { return utilizationPercent; }
    public void      setUtilizationPercent(Double v)            { this.utilizationPercent = v; }

    public Instant   getUpdatedAt()                             { return updatedAt; }
    public void      setUpdatedAt(Instant updatedAt)            { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return String.format("NetworkSliceState{id=%s, name=%s, type=%s, status=%s, util=%.1f%%}",
                id, name, sliceType, status,
                utilizationPercent != null ? utilizationPercent : 0.0);
    }
}
