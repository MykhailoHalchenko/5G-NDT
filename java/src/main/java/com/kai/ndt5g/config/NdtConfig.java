package com.kai.ndt5g.config;

import java.util.Objects;

/**
 * Central configuration holder for the 5G NDT Java module.
 *
 * <p>Values are resolved in priority order:
 * <ol>
 *   <li>System property (e.g. {@code -Dndt.azure.endpoint=...})</li>
 *   <li>Environment variable (e.g. {@code NDT_AZURE_ENDPOINT=...})</li>
 *   <li>Built-in default (may be {@code null} for optional settings)</li>
 * </ol>
 *
 * <p>All Azure-specific properties are optional; when absent the
 * {@link com.kai.ndt5g.azure.AzureDigitalTwinsConnector} runs in dry-run mode
 * and logs the operations it would perform.
 */
public final class NdtConfig {

    // ── WLDT ──────────────────────────────────────────────────────────────────

    /** Polling interval in seconds for the Physical Adapter. */
    public final int wldtPollIntervalSeconds;

    /** Maximum number of gNodeBs to poll concurrently. */
    public final int wldtMaxConcurrentPolls;

    // ── Azure Digital Twins ────────────────────────────────────────────────────

    /** Azure Digital Twins service endpoint (FQDN), e.g.
     *  {@code https://my-instance.api.weu.digitaltwins.azure.net}. */
    public final String azureEndpoint;

    /** Model ID used when creating gNodeB twin instances in Azure ADT. */
    public final String azureGnbModelId;

    /** Whether to operate in dry-run mode (no actual Azure API calls). */
    public final boolean azureDryRun;

    // ── ScaleOut ──────────────────────────────────────────────────────────────

    /** Comma-separated list of ScaleOut connection string endpoints. */
    public final String scaleoutConnectionString;

    /** ScaleOut app name (used as the deployment namespace). */
    public final String scaleoutAppName;

    // ── Constructor (use the static factory) ──────────────────────────────────

    private NdtConfig(
            int    wldtPollIntervalSeconds,
            int    wldtMaxConcurrentPolls,
            String azureEndpoint,
            String azureGnbModelId,
            boolean azureDryRun,
            String scaleoutConnectionString,
            String scaleoutAppName) {
        this.wldtPollIntervalSeconds    = wldtPollIntervalSeconds;
        this.wldtMaxConcurrentPolls     = wldtMaxConcurrentPolls;
        this.azureEndpoint              = azureEndpoint;
        this.azureGnbModelId            = azureGnbModelId != null
                ? azureGnbModelId
                : "dtmi:kai:ndt5g:gNodeB;1";
        this.azureDryRun                = azureDryRun;
        this.scaleoutConnectionString   = scaleoutConnectionString;
        this.scaleoutAppName            = scaleoutAppName != null
                ? scaleoutAppName
                : "5g-ndt";
    }

    // ── Factory ───────────────────────────────────────────────────────────────

    /**
     * Build a configuration by reading system properties / environment variables
     * with fall-back to sensible defaults.
     */
    public static NdtConfig fromEnvironment() {
        return new NdtConfig(
                intProp("ndt.wldt.poll.interval.seconds", "NDT_WLDT_POLL_INTERVAL_SECONDS", 5),
                intProp("ndt.wldt.max.concurrent.polls",  "NDT_WLDT_MAX_CONCURRENT_POLLS",  50),
                prop("ndt.azure.endpoint",                "NDT_AZURE_ENDPOINT",              null),
                prop("ndt.azure.gnb.model.id",            "NDT_AZURE_GNB_MODEL_ID",          null),
                boolProp("ndt.azure.dry.run",             "NDT_AZURE_DRY_RUN",               true),
                prop("ndt.scaleout.connection.string",    "NDT_SCALEOUT_CONNECTION_STRING",  null),
                prop("ndt.scaleout.app.name",             "NDT_SCALEOUT_APP_NAME",           null)
        );
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static String prop(String sysProp, String envVar, String defaultValue) {
        String v = System.getProperty(sysProp);
        if (v != null && !v.isBlank()) return v;
        v = System.getenv(envVar);
        if (v != null && !v.isBlank()) return v;
        return defaultValue;
    }

    private static int intProp(String sysProp, String envVar, int defaultValue) {
        String v = prop(sysProp, envVar, null);
        if (v == null) return defaultValue;
        try { return Integer.parseInt(v.trim()); }
        catch (NumberFormatException e) { return defaultValue; }
    }

    private static boolean boolProp(String sysProp, String envVar, boolean defaultValue) {
        String v = prop(sysProp, envVar, null);
        if (v == null) return defaultValue;
        return Boolean.parseBoolean(v.trim());
    }

    @Override
    public String toString() {
        return String.format(
                "NdtConfig{wldtPollInterval=%ds, azureEndpoint=%s, azureDryRun=%b, scaleoutApp=%s}",
                wldtPollIntervalSeconds,
                azureEndpoint != null ? azureEndpoint : "<not set>",
                azureDryRun,
                scaleoutAppName);
    }
}
