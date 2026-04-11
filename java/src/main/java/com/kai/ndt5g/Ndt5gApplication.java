package com.kai.ndt5g;

import com.kai.ndt5g.azure.AzureDigitalTwinsConnector;
import com.kai.ndt5g.config.NdtConfig;
import com.kai.ndt5g.model.GNodeBState;
import com.kai.ndt5g.scaleout.ScaleOutTwinService;
import com.kai.ndt5g.wldt.Ndt5gWldtInstance;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

/**
 * Entry point for the 5G NDT Java module.
 *
 * <p>Startup sequence:
 * <ol>
 *   <li>Load {@link NdtConfig} from environment / system properties.</li>
 *   <li>Instantiate the {@link AzureDigitalTwinsConnector} and
 *       {@link ScaleOutTwinService} (both are no-ops when not configured).</li>
 *   <li>For each configured gNodeB, build and start a {@link Ndt5gWldtInstance}
 *       which wires the WLDT physical adapter → shadowing function → digital
 *       adapter → Azure ADT / ScaleOut pipeline.</li>
 *   <li>Block until a SIGINT/SIGTERM is received, then shut down gracefully.</li>
 * </ol>
 *
 * <p>To add real gNodeBs, replace the sample entries in {@link #buildSampleGnbList()}
 * with data loaded from the Python API ({@code GET /api/v1/topology/gnodebs})
 * or from a local configuration file.
 */
public class Ndt5gApplication {

    private static final Logger log = LoggerFactory.getLogger(Ndt5gApplication.class);

    public static void main(String[] args) throws Exception {
        log.info("══════════════════════════════════════════");
        log.info("  5G Network Digital Twin — Java Module   ");
        log.info("══════════════════════════════════════════");

        NdtConfig config = NdtConfig.fromEnvironment();
        log.info("Configuration loaded: {}", config);

        // ── Shared services ────────────────────────────────────────────────────
        AzureDigitalTwinsConnector azureConnector = new AzureDigitalTwinsConnector(config);
        ScaleOutTwinService        scaleOut       = new ScaleOutTwinService(config);

        // ── Spin up a WLDT instance per gNodeB ────────────────────────────────
        List<GNodeBState>      gnbs      = buildSampleGnbList();
        List<Ndt5gWldtInstance> instances = new ArrayList<>();

        for (GNodeBState gnb : gnbs) {
            // Ensure a twin record exists in Azure ADT before starting telemetry
            azureConnector.ensureTwinExistsAsync(gnb).get(30, java.util.concurrent.TimeUnit.SECONDS);

            Ndt5gWldtInstance wldt = new Ndt5gWldtInstance(
                    config, gnb, gnb.getIpAddress() != null ? gnb.getIpAddress() : "localhost",
                    azureConnector, scaleOut);
            wldt.start();
            instances.add(wldt);

            log.info("Started Digital Twin for gNodeB: id={} name={}", gnb.getId(), gnb.getName());
        }

        log.info("All {} Digital Twin instance(s) running. Press Ctrl-C to stop.", instances.size());

        // ── Graceful shutdown ──────────────────────────────────────────────────
        CountDownLatch shutdownLatch = new CountDownLatch(1);
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            log.info("Shutdown signal received — stopping Digital Twins …");
            for (Ndt5gWldtInstance wldt : instances) {
                wldt.stop();
            }
            shutdownLatch.countDown();
        }, "shutdown-hook"));

        shutdownLatch.await();
        log.info("5G NDT Java Module stopped.");
    }

    // ── Sample data (replace with real topology load in production) ───────────

    /**
     * Build a minimal list of gNodeB domain objects for demonstration purposes.
     *
     * <p>In production, load gNodeBs from:
     * <ul>
     *   <li>The Python API: {@code GET /api/v1/topology/gnodebs}</li>
     *   <li>A YAML/properties configuration file</li>
     *   <li>A database query</li>
     * </ul>
     */
    private static List<GNodeBState> buildSampleGnbList() {
        GNodeBState gnb1 = new GNodeBState("gnb-001", "gNodeB-KAI-01", 1001, "26601");
        gnb1.setVendor("Ericsson");
        gnb1.setSoftwareVersion("22.Q4");
        gnb1.setIpAddress("10.0.1.1");
        gnb1.setStatus(GNodeBState.NodeStatus.ACTIVE);

        GNodeBState gnb2 = new GNodeBState("gnb-002", "gNodeB-KAI-02", 1002, "26601");
        gnb2.setVendor("Nokia");
        gnb2.setSoftwareVersion("21.6");
        gnb2.setIpAddress("10.0.1.2");
        gnb2.setStatus(GNodeBState.NodeStatus.ACTIVE);

        return List.of(gnb1, gnb2);
    }
}
