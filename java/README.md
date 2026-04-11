# 5G NDT — Java Module

Java component of the **5G Network Digital Twin (NDT)** platform developed at
the KAI Network Lab.  It integrates three Digital Twin frameworks to provide
real-time, scalable, cloud-connected twin management for 5G gNodeBs.

---

## Framework integrations

| Framework | Role | Key classes |
|-----------|------|-------------|
| [**WLDT** (White Label Digital Twin)](https://github.com/wldt/wldt-core) | Core DT lifecycle — physical adapter polling, shadowing, digital adapter | `GNodeBPhysicalAdapter`, `GNodeBShadowingFunction`, `GNodeBDigitalAdapter`, `Ndt5gWldtInstance` |
| [**Azure Digital Twins SDK for Java**](https://learn.microsoft.com/azure/digital-twins/how-to-use-apis-sdks) | Cloud-side twin synchronisation via the async Reactor-based client | `AzureDigitalTwinsConnector` |
| [**ScaleOut Digital Twin Builder**](https://www.scaleoutsoftware.com/products/digital-twin-builder/) | In-memory real-time state management and message processing | `GNodeBDigitalTwinState`, `GNodeBMessageProcessor`, `ScaleOutTwinService` |

---

## Architecture

```
Physical Network (gNodeB)
        │  O-RAN (NETCONF/gNMI/REST)
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        WLDT Engine                              │
│  GNodeBPhysicalAdapter ──► GNodeBShadowingFunction              │
│          (polls telemetry)    (maps phys → digital state)       │
│                                      │                          │
│                              GNodeBDigitalAdapter               │
└──────────────────────────────────────┼──────────────────────────┘
                                       │ state change callback
                     ┌─────────────────┼──────────────────┐
                     ▼                 ▼                   ▼
           Azure ADT Connector  ScaleOut Service       Logger/API
           (async Reactor call) (in-memory grid)
```

### WLDT lifecycle

1. `GNodeBPhysicalAdapter.onAdapterStart()` — declares the **Physical Asset
   Description** (properties: `total_throughput_mbps`, `average_latency_ms`,
   `active_ues`, `packet_loss_percent`, `status`) and starts the async polling
   scheduler.
2. Every `poll_interval_seconds` the adapter calls `fetchTelemetry()` (O-RAN
   stub) and publishes `PhysicalAssetPropertyVariation` events to the WLDT bus.
3. `GNodeBShadowingFunction.onPhysicalAssetPropertyVariation()` maps each event
   to a `DigitalTwinStateProperty` update and to the typed `GNodeBState` domain
   object.  KPI severity is computed at this layer.
4. `GNodeBDigitalAdapter` forwards state-change notifications to external
   sinks.

### Azure Digital Twins

All Azure SDK calls go through `DigitalTwinsAsyncClient` (Project Reactor).
The `AzureDigitalTwinsConnector.syncGnbStateAsync()` method returns a
`CompletableFuture<Void>` so the WLDT shadowing thread is never blocked.

When `NDT_AZURE_ENDPOINT` is not set (or `NDT_AZURE_DRY_RUN=true`) the
connector operates in **dry-run mode** — all operations are logged but no API
calls are made.

### ScaleOut Digital Twin Builder

`ScaleOutTwinService` registers `GNodeBDigitalTwinState` and
`GNodeBMessageProcessor` with the ScaleOut runtime.
`GNodeBMessageProcessor.processMessages()` applies inbound `TelemetryUpdate`
messages and refreshes KPI alert counters — without blocking the WLDT event
loop.

When `NDT_SCALEOUT_CONNECTION_STRING` is not set, the service uses a local
`ConcurrentHashMap` as fallback.

---

## Prerequisites

| Tool | Minimum version |
|------|-----------------|
| Java | 17              |
| Maven | 3.9            |

---

## Quick start

```bash
# From the repository root:

# Build the fat JAR
make java-build

# Run all unit tests
make java-test

# Start the application (dry-run mode, no external services required)
make java-run
```

Or directly with Maven:

```bash
cd java
mvn package          # compile + test + shade
mvn test             # unit tests only
java -jar target/5g-ndt-java-0.1.0.jar
```

---

## Configuration

All settings are read from environment variables or JVM system properties
(`-Dproperty=value`).

| Environment variable | System property | Default | Description |
|----------------------|-----------------|---------|-------------|
| `NDT_WLDT_POLL_INTERVAL_SECONDS` | `ndt.wldt.poll.interval.seconds` | `5` | gNodeB polling interval (seconds) |
| `NDT_WLDT_MAX_CONCURRENT_POLLS`  | `ndt.wldt.max.concurrent.polls`  | `50` | Max concurrent gNodeB polls |
| `NDT_AZURE_ENDPOINT`             | `ndt.azure.endpoint`             | `null` (dry-run) | Azure ADT FQDN, e.g. `https://my-instance.api.weu.digitaltwins.azure.net` |
| `NDT_AZURE_GNB_MODEL_ID`         | `ndt.azure.gnb.model.id`         | `dtmi:kai:ndt5g:gNodeB;1` | DTDL model ID for gNodeB twins |
| `NDT_AZURE_DRY_RUN`              | `ndt.azure.dry.run`              | `true` | Disable real Azure API calls |
| `NDT_SCALEOUT_CONNECTION_STRING` | `ndt.scaleout.connection.string` | `null` (local) | ScaleOut connection string |
| `NDT_SCALEOUT_APP_NAME`          | `ndt.scaleout.app.name`          | `5g-ndt` | ScaleOut application namespace |

### Azure authentication

When `NDT_AZURE_ENDPOINT` is set, the SDK uses `DefaultAzureCredential`, which
resolves credentials in this order:
1. Environment variables (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`)
2. Workload identity (AKS)
3. Azure CLI (`az login`)
4. Managed Identity

See [Azure Identity documentation](https://learn.microsoft.com/java/api/overview/azure/identity-readme).

---

## Module structure

```
java/
├── pom.xml
└── src/
    ├── main/java/com/kai/ndt5g/
    │   ├── Ndt5gApplication.java          # main() entry point
    │   ├── config/
    │   │   └── NdtConfig.java             # Configuration holder
    │   ├── model/
    │   │   ├── GNodeBState.java           # gNodeB domain model
    │   │   ├── NetworkSliceState.java     # Network slice domain model
    │   │   └── KpiSnapshot.java           # Immutable KPI measurement
    │   ├── wldt/
    │   │   ├── GNodeBPhysicalAdapter.java # O-RAN polling adapter
    │   │   ├── GNodeBShadowingFunction.java # Physical→digital mapping
    │   │   ├── GNodeBDigitalAdapter.java  # State change forwarder
    │   │   └── Ndt5gWldtInstance.java     # WLDT engine assembly
    │   ├── azure/
    │   │   └── AzureDigitalTwinsConnector.java # Async Azure ADT sync
    │   └── scaleout/
    │       ├── GNodeBDigitalTwinState.java     # ScaleOut state model
    │       ├── GNodeBMessageProcessor.java     # ScaleOut message handler
    │       └── ScaleOutTwinService.java        # ScaleOut lifecycle service
    └── test/java/com/kai/ndt5g/
        ├── model/
        │   ├── KpiSnapshotTest.java
        │   └── GNodeBStateTest.java
        ├── wldt/
        │   └── GNodeBShadowingFunctionTest.java
        ├── azure/
        │   └── AzureDigitalTwinsConnectorTest.java
        └── scaleout/
            └── ScaleOutTwinServiceTest.java
```

---

## Connecting to the Python API

The Python NDT API (`python -m src.api.app`) exposes topology data at
`GET /api/v1/topology/gnodebs`.  Replace `buildSampleGnbList()` in
`Ndt5gApplication` with an HTTP call to load real gNodeB records at startup.
The aiohttp API returns standard JSON that maps directly to `GNodeBState`.

---

## Next steps (Phase 3+)

- Replace the stub `fetchTelemetry()` in `GNodeBPhysicalAdapter` with real
  NETCONF/gNMI calls using [ncclient](https://github.com/ncclient/ncclient) via
  JNI or the Java [netconf4j](https://github.com/opendaylight/netconf) library.
- Upload the DTDL model (`dtmi:kai:ndt5g:gNodeB;1`) to Azure ADT using the
  `DigitalTwinsAsyncClient.createOrReplaceModel()` API.
- Register with the ScaleOut cloud service and remove the local-cache fallback.
- Add Kafka consumer integration to feed `TelemetryUpdate` messages from the
  Python telemetry pipeline into the ScaleOut processor.
