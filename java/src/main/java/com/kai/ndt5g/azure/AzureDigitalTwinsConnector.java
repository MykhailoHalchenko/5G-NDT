package com.kai.ndt5g.azure;

import com.azure.core.credential.TokenCredential;
import com.azure.digitaltwins.core.DigitalTwinsAsyncClient;
import com.azure.digitaltwins.core.DigitalTwinsClientBuilder;
import com.azure.digitaltwins.core.models.BasicDigitalTwin;
import com.azure.digitaltwins.core.models.BasicDigitalTwinMetadata;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.kai.ndt5g.config.NdtConfig;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.model.KpiSnapshot;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;

/**
 * Asynchronous connector to <a href="https://azure.microsoft.com/products/digital-twins">
 * Azure Digital Twins</a> (ADT).
 *
 * <p>Responsibilities:
 * <ol>
 *   <li>On startup, ensure a twin instance exists in Azure ADT for every gNodeB
 *       managed by the platform (upsert semantics).</li>
 *   <li>Whenever the WLDT shadow state changes, push the updated properties to
 *       the corresponding Azure twin so it stays in sync with the physical
 *       network in real time.</li>
 *   <li>All Azure SDK calls are made through the {@link DigitalTwinsAsyncClient}
 *       (Project Reactor-based), so they never block the calling thread.  The
 *       returned {@link CompletableFuture} allows callers to compose additional
 *       async work or simply ignore the result after logging.</li>
 * </ol>
 *
 * <p>When {@link NdtConfig#azureDryRun} is {@code true}, no actual API calls
 * are made — operations are only logged.  This is the default so that the module
 * compiles and runs correctly without Azure credentials.
 */
public class AzureDigitalTwinsConnector {

    private static final Logger log = LoggerFactory.getLogger(AzureDigitalTwinsConnector.class);

    private final NdtConfig             config;
    private final DigitalTwinsAsyncClient client;   // null in dry-run mode

    // ── Constructor ────────────────────────────────────────────────────────────

    /**
     * Build a connector from the given configuration.
     *
     * <p>If {@link NdtConfig#azureDryRun} is {@code true} or
     * {@link NdtConfig#azureEndpoint} is {@code null}, the connector operates
     * in dry-run mode — no SDK client is instantiated.
     *
     * @param config application configuration
     */
    public AzureDigitalTwinsConnector(NdtConfig config) {
        this.config = Objects.requireNonNull(config, "config");

        if (config.azureDryRun || config.azureEndpoint == null) {
            log.info("AzureDigitalTwinsConnector: dry-run mode — Azure API calls disabled");
            this.client = null;
        } else {
            TokenCredential credential = new DefaultAzureCredentialBuilder().build();
            this.client = new DigitalTwinsClientBuilder()
                    .credential(credential)
                    .endpoint(config.azureEndpoint)
                    .buildAsyncClient();
            log.info("AzureDigitalTwinsConnector: connected to {}", config.azureEndpoint);
        }
    }

    // ── Public API ────────────────────────────────────────────────────────────

    /**
     * Ensure a gNodeB twin exists in Azure ADT, creating it if necessary.
     *
     * <p>Implements upsert semantics: if a twin with the same ID already exists
     * it is returned unchanged; if it does not, a new twin is created from the
     * provided {@link GNodeBState}.
     *
     * @param state the gNodeB domain state
     * @return a future that completes when the operation finishes; the value
     *         is the twin ID on success or {@code null} in dry-run mode
     */
    public CompletableFuture<String> ensureTwinExistsAsync(GNodeBState state) {
        Objects.requireNonNull(state, "state");
        String twinId = toTwinId(state.getId());

        if (client == null) {
            log.info("ADT [dry-run] ensureTwinExists: twinId={}", twinId);
            return CompletableFuture.completedFuture(twinId);
        }

        BasicDigitalTwin twin = buildBasicTwin(twinId, state);

        return client.createOrReplaceDigitalTwin(twinId, twin, BasicDigitalTwin.class)
                .map(BasicDigitalTwin::getId)
                .doOnSuccess(id -> log.info("ADT twin upserted: twinId={}", id))
                .doOnError(e  -> log.error("ADT upsert failed: twinId={} error={}", twinId, e.getMessage()))
                .toFuture();
    }

    /**
     * Push all mutable properties of the given {@link GNodeBState} to the
     * corresponding Azure ADT twin.
     *
     * <p>Called by {@link com.kai.ndt5g.wldt.Ndt5gWldtInstance} on every WLDT
     * shadow-state change.  The call is non-blocking: it schedules a Reactor
     * pipeline and returns immediately.
     *
     * @param state the current gNodeB domain state
     * @return a future that completes when the patch has been accepted by Azure ADT
     */
    public CompletableFuture<Void> syncGnbStateAsync(GNodeBState state) {
        Objects.requireNonNull(state, "state");
        String twinId = toTwinId(state.getId());

        if (client == null) {
            log.debug("ADT [dry-run] syncGnbState: twinId={} status={} latency={}ms",
                    twinId, state.getStatus(),
                    state.getAverageLatencyMs() != null ? state.getAverageLatencyMs() : "n/a");
            return CompletableFuture.completedFuture(null);
        }

        Map<String, Object> patch = buildPatch(state);

        // Build a JSON Merge Patch and apply it via the async client.
        return client.updateDigitalTwin(twinId, buildJsonPatchDocument(patch))
                .doOnSuccess(__ -> log.debug("ADT patch applied: twinId={}", twinId))
                .doOnError(e   -> log.warn("ADT patch failed: twinId={} error={}", twinId, e.getMessage()))
                .then(Mono.<Void>empty())
                .toFuture();
    }

    /**
     * Delete the Azure ADT twin for the given gNodeB ID (e.g. on decommission).
     *
     * @param gnbId the gNodeB UUID string
     * @return a future that completes when the twin has been removed
     */
    public CompletableFuture<Void> deleteTwinAsync(String gnbId) {
        String twinId = toTwinId(gnbId);

        if (client == null) {
            log.info("ADT [dry-run] deleteTwin: twinId={}", twinId);
            return CompletableFuture.completedFuture(null);
        }

        return client.deleteDigitalTwin(twinId)
                .doOnSuccess(__ -> log.info("ADT twin deleted: twinId={}", twinId))
                .doOnError(e   -> log.error("ADT delete failed: twinId={} error={}", twinId, e.getMessage()))
                .then(Mono.<Void>empty())
                .toFuture();
    }

    // ── Internal helpers ──────────────────────────────────────────────────────

    /**
     * Derive the Azure ADT twin ID from the platform's gNodeB UUID.
     * Azure twin IDs must be 1–128 chars, letters/digits/hyphens/underscores only.
     */
    static String toTwinId(String gnbId) {
        return "gnb-" + gnbId.replace(":", "-");
    }

    /** Build a {@link BasicDigitalTwin} from the domain state (used at creation time). */
    private BasicDigitalTwin buildBasicTwin(String twinId, GNodeBState state) {
        BasicDigitalTwin twin = new BasicDigitalTwin(twinId)
                .setMetadata(new BasicDigitalTwinMetadata().setModelId(config.azureGnbModelId));
        Map<String, Object> contents = buildPatch(state);
        contents.forEach(twin::addToContents);
        return twin;
    }

    /** Collect all mutable properties that should be synced to Azure ADT. */
    private static Map<String, Object> buildPatch(GNodeBState state) {
        Map<String, Object> patch = new HashMap<>();
        patch.put("name",                  state.getName());
        patch.put("gnbId",                 state.getGnbId());
        patch.put("plmnId",                state.getPlmnId());
        patch.put("status",                state.getStatus() != null ? state.getStatus().name() : null);
        patch.put("vendor",                state.getVendor());
        patch.put("softwareVersion",       state.getSoftwareVersion());
        patch.put("ipAddress",             state.getIpAddress());
        patch.put("totalThroughputMbps",   state.getTotalThroughputMbps());
        patch.put("averageLatencyMs",      state.getAverageLatencyMs());
        patch.put("activeUes",             state.getActiveUes());
        // Include KPI severities as flat properties
        for (KpiSnapshot kpi : state.getKpis().values()) {
            patch.put("kpi_" + kpi.getMetricName() + "_value",    kpi.getValue());
            patch.put("kpi_" + kpi.getMetricName() + "_severity", kpi.getSeverity().name());
        }
        patch.put("updatedAt", state.getUpdatedAt().toString());
        return patch;
    }

    /**
     * Wrap a property map in an Azure SDK {@code JsonPatchDocument}.
     * Uses the ADT SDK's patch document builder to create a series of "replace" operations.
     */
    private static com.azure.core.models.JsonPatchDocument buildJsonPatchDocument(
            Map<String, Object> patch) {
        com.azure.core.models.JsonPatchDocument doc = new com.azure.core.models.JsonPatchDocument();
        patch.forEach((k, v) -> {
            if (v != null) doc.appendReplace("/" + k, v);
        });
        return doc;
    }
}
