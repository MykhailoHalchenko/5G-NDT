package com.kai.ndt5g.model;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.io.Serializable;
import java.time.Instant;
import java.util.Objects;

/**
 * Immutable snapshot of a single KPI measurement for a network entity.
 *
 * <p>Severity is computed from configurable warning/critical thresholds:
 * <ul>
 *   <li>{@link KpiSeverity#CRITICAL} — value &ge; criticalThreshold</li>
 *   <li>{@link KpiSeverity#WARNING}  — value &ge; warningThreshold</li>
 *   <li>{@link KpiSeverity#INFO}     — otherwise</li>
 * </ul>
 */
public final class KpiSnapshot implements Serializable {

    /** Alert severity level for a KPI observation. */
    public enum KpiSeverity { INFO, WARNING, CRITICAL }

    private final String entityId;
    private final String metricName;
    private final double value;
    private final String unit;
    private final Instant timestamp;
    private final Double warningThreshold;
    private final Double criticalThreshold;
    private final KpiSeverity severity;

    @JsonCreator
    public KpiSnapshot(
            @JsonProperty("entityId")         String entityId,
            @JsonProperty("metricName")        String metricName,
            @JsonProperty("value")             double value,
            @JsonProperty("unit")              String unit,
            @JsonProperty("timestamp")         Instant timestamp,
            @JsonProperty("warningThreshold")  Double warningThreshold,
            @JsonProperty("criticalThreshold") Double criticalThreshold) {

        this.entityId          = Objects.requireNonNull(entityId,    "entityId");
        this.metricName        = Objects.requireNonNull(metricName,   "metricName");
        this.value             = value;
        this.unit              = unit != null ? unit : "";
        this.timestamp         = timestamp != null ? timestamp : Instant.now();
        this.warningThreshold  = warningThreshold;
        this.criticalThreshold = criticalThreshold;
        this.severity          = computeSeverity(value, warningThreshold, criticalThreshold);
    }

    // ── Factory helpers ────────────────────────────────────────────────────────

    /** Create a snapshot with no thresholds (severity is always INFO). */
    public static KpiSnapshot of(String entityId, String metricName, double value, String unit) {
        return new KpiSnapshot(entityId, metricName, value, unit, Instant.now(), null, null);
    }

    // ── Accessors ──────────────────────────────────────────────────────────────

    public String     getEntityId()         { return entityId; }
    public String     getMetricName()       { return metricName; }
    public double     getValue()            { return value; }
    public String     getUnit()             { return unit; }
    public Instant    getTimestamp()        { return timestamp; }
    public Double     getWarningThreshold() { return warningThreshold; }
    public Double     getCriticalThreshold(){ return criticalThreshold; }
    public KpiSeverity getSeverity()        { return severity; }

    // ── Internal ───────────────────────────────────────────────────────────────

    private static KpiSeverity computeSeverity(double value, Double warning, Double critical) {
        if (critical != null && value >= critical) return KpiSeverity.CRITICAL;
        if (warning  != null && value >= warning)  return KpiSeverity.WARNING;
        return KpiSeverity.INFO;
    }

    @Override
    public String toString() {
        return String.format("KpiSnapshot{entity=%s, metric=%s, value=%.3f %s, severity=%s}",
                entityId, metricName, value, unit, severity);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof KpiSnapshot)) return false;
        KpiSnapshot other = (KpiSnapshot) o;
        return Double.compare(other.value, value) == 0
                && Objects.equals(entityId, other.entityId)
                && Objects.equals(metricName, other.metricName)
                && Objects.equals(timestamp, other.timestamp);
    }

    @Override
    public int hashCode() {
        return Objects.hash(entityId, metricName, value, timestamp);
    }
}
