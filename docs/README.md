# 🌌 Yu-Gi-Oh! Platform Engineering Documentation

Welcome to the engineering and architectural documentation for the **Yu-Gi-Oh! Custom Card, Story & Simulator Platform**.

This directory houses the foundational blueprints, operational philosophies, execution plans, and living state ledgers that guide the design and evolution of the codebase.

---

## 📚 Document Index

| Document | Purpose | Lifetime & Scope |
| :--- | :--- | :--- |
| [**`ARCHITECTURE_PHILOSOPHY.md`**](file:///home/professorseanex/yugioh-server/docs/ARCHITECTURE_PHILOSOPHY.md) | **The Core Doctrine**: Systems thinking, Data-Oriented Design, autonomous silos, the "Functional Core, Imperative Shell" pattern, and bi-directional engine lifecycles. | **Invariant / Timeless**: Serves as the platform's architectural constitution. |
| [**`DATA_ARCHITECTURE.md`**](file:///home/professorseanex/yugioh-server/docs/DATA_ARCHITECTURE.md) | **Data Subsystem Blueprint**: Six-tier data hierarchy, authoritative SQLite schema, master spreadsheets, compiled expansions, and ingestion pipelines. | **Structural / Invariant**: Governs storage and data flows. |
| [**`CONFIGURATION_SYSTEM.md`**](file:///home/professorseanex/yugioh-server/docs/CONFIGURATION_SYSTEM.md) | **Configuration & Telemetry Blueprint**: Precedence hierarchy, strongly-typed settings dataclasses, structured logging, and debugger-logger pairing. | **Operational / Invariant**: Governs configuration and observability. |
| [**`ACTION_PLAN.md`**](file:///home/professorseanex/yugioh-server/docs/ACTION_PLAN.md) | **The Execution Roadmap**: Concrete, phased action plan detailing condensation, realignment, utility extraction, and bi-directional wiring. | **Strategic / Temporal**: Guides execution across milestones. |
| [**`REPOSITORY_STATE_TRACKER.md`**](file:///home/professorseanex/yugioh-server/docs/REPOSITORY_STATE_TRACKER.md) | **The Living Ledger**: Real-time component audit matrix, phased task checklist, technical debt register, and session log. | **Tactical / Dynamic**: Actively updated as the codebase evolves. |

---

## 🎯 Architectural Knowledge Hierarchy

To maintain absolute clarity across long-term development, engineering knowledge is strictly organized across distinct dimensions:

1. **Foundational Doctrine (Philosophy)** $\rightarrow$ Invariant engineering principles that prevent anti-patterns and spaghetti architecture.
2. **Subsystem Specifications (Data & Config)** $\rightarrow$ Concrete blueprints for storage tiers, ingestion pipelines, configuration precedence, and observability.
3. **Execution Strategy (Plan)** $\rightarrow$ Phased implementation roadmap from current state to desired state.
4. **Current Status (Tracker)** $\rightarrow$ The real-time tactical ledger of completed, in-progress, and pending work.
