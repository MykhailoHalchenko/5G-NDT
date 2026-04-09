# 5G Network Digital Twin (NDT) — KAI Network Lab

A production-grade Python project that creates a **Digital Twin** for 5G/O-RAN networks,
enabling real-time topology awareness, KPI monitoring, and automated service activation.

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/MykhailoHalchenko/5G-NDT.git
cd 5G-NDT
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# edit .env with your settings

# 3. Start local dev stack (Neo4j, InfluxDB, Kafka)
make docker-up

# 4. Run API server
make run

# 5. Open docs
open http://localhost:8000/docs
```

## Architecture

The system operates on three levels:
1. **Structural** — Graph-based topology of gNodeB, CU/DU, slices, core
2. **Dynamic** — Real-time telemetry overlaid on the topology graph
3. **Predictive** — "What-if" simulations for failure/load scenarios

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full C4 diagrams.

## Project Structure

```
src/           — Application source code
tests/         — Unit & integration tests
infra/         — Docker & Kubernetes configs
docs/          — Project documentation
scripts/       — Utility scripts
config/        — Environment configurations
.github/       — CI/CD workflows
```

## Documentation

| Document | Description |
|---|---|
| [ROADMAP.md](docs/ROADMAP.md) | 12-month implementation roadmap |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & C4 diagrams |
| [DATA_MODEL.md](docs/DATA_MODEL.md) | 5G entity definitions |
| [API_SPEC.md](docs/API_SPEC.md) | REST API endpoints |
| [SETUP.md](docs/SETUP.md) | Local development guide |
| [REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional & non-functional requirements |
| [SECURITY.md](docs/SECURITY.md) | Security policies |
| [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) | O-RAN/5G Lab integration |

## Development

```bash
make dev-install    # Install dev dependencies
make test           # Run all tests with coverage
make lint           # Run flake8
make format         # Run black formatter
make type-check     # Run mypy
```

## License

See [LICENSE](LICENSE).
