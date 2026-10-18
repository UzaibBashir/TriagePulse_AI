# Architecture

![TriagePulse AI solution architecture](triagepulse-architecture.svg)

Browser (vanilla HTML/CSS/JS) polls the Flask API. Observation POSTs are validated, persisted in SQLite in one transaction, assessed with versioned demonstration rules, and optionally create a deduplicated alert. Acknowledgement appends an audit record and leaves the source observation intact. API latency counters use a bounded in-memory sample; persistent records use SQLite. There is no external cloud dependency.

```mermaid
flowchart LR
 S[Scenario simulator] --> I[Flask ingestion API]
 I --> V[Validation]
 V --> D[(SQLite)]
 D --> R[Versioned demo rules]
 R --> A[Assessment and alert]
 A --> D
 D --> P[Dashboard polling API]
 P --> U[Vanilla JS dashboard]
```

The system is educational and not clinically validated. Rule thresholds are demonstration settings, not authoritative clinical thresholds.
