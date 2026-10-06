# 🏛️ Architecture Philosophy: Game Systems Engineering & Data Pipeline

## 1. Introduction: Beyond Traditional OOP

In traditional Object-Oriented Programming (OOP), systems are typically designed around stateful object graphs: a `Card` object contains mutable stats and methods like `.activate()`; a `Deck` object manages an array of cards and mutates its own contents; a `Duel` object holds player objects, game state, and network sockets all tangled in mutual references.

In high-performance game development, simulation engines, and distributed server architectures, pure OOP inevitably breaks down:

1. **Hidden State Mutations & Side Effects:** Method calls inadvertently alter nested state, making debugging and race condition resolution painful.
2. **Brittle Inheritance Trees:** Modeling nuanced game entities via class inheritance (`Card` $\rightarrow$ `Monster` $\rightarrow$ `EffectMonster` $\rightarrow$ `PendulumMonster` $\rightarrow$ `PendulumXyzMonster`) leads to the fragile base class problem.
3. **Serialization & Compilation Bottlenecks:** Memory cannot be cleanly dumped into low-level binary stores (`.cdb` SQLite tables, `.ydk` streams) without heavy ORM translation layers.
4. **Tight Coupling:** The presentation layer (e.g. Discord bot commands or Web API endpoints) frequently reaches into engine internals, creating spaghetti dependencies.

To solve this, our platform adopts a **Systems Engineering & Data-Oriented Design (DOD)** paradigm: **"Functional Core, Imperative Shell."**

---

## 2. The Hybrid Paradigm: Functional Core, Imperative Shell

We combine the structural strengths of OOP with the mathematical predictability of Functional Programming:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        IMPERATIVE SHELL (OOP)                          │
│  • Resource Management: WebSockets, Process Daemons, Docker Sockets    │
│  • ACID Transactions: SQLite connection pooling & database commits     │
│  • Event Listeners: Discord interactions, HTTP route dispatchers       │
│                                                                        │
│    ┌──────────────────────────────────────────────────────────────┐    │
│    │                    FUNCTIONAL CORE (PURE)                    │    │
│    │  • Bitmask Arithmetic: encode_type(), parse_attribute()      │    │
│    │  • Rules & Legality: validate_deck(), check_opt_clauses()   │    │
│    │  • Mathematical Transformations: calculate_elo_shift()       │    │
│    │  • Serializers: serialize_ydk(), synthesize_lua_script()     │    │
│    │  • Data in Flight: Immutable DTOs / Frozen DataClasses       │    │
│    └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### The Role of OOP: The Imperative Shell

Object-Oriented Programming is strictly reserved for:

* **Lifecycle & Resource Ownership:** Long-lived stateful handles such as the Discord bot gateway connection, the `ocgcore` Docker container supervisor, and the SQLite connection pool.
* **Structural Contracts (Plain Old Data / DTOs):** Strongly typed, immutable data structures (e.g., `@dataclass(frozen=True) class CardDataStruct`) representing memory layouts matching C/C++ `struct card_data`.

### The Role of Functional Programming: The Pure Core

All business logic, game rules, and data compilation steps are implemented as **pure, stateless functions**:

* **Pure & Deterministic:** Given the exact same inputs, a pure function always returns the exact same outputs.
* **Zero Side Effects:** Pure functions never read from global variables, modify arguments in-place, or execute network/disk I/O.
* **Extreme Testability:** Because they require no mocks, no running Docker containers, and no active Discord tokens, thousands of pure rule calculations can run in milliseconds in the unit test suite.

---

## 3. Autonomous Domain Silos

The platform is partitioned into autonomous **silos**. A silo is an independent subsystem that owns its data representation and domain logic. Silos never inspect or mutate the internal private state of another silo; they communicate strictly through explicit data packets and API calls.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                               AUTONOMOUS SILOS                               │
├──────────────────────┬──────────────────────┬────────────────────────────────┤
│ SILO 1: CARD & RULE  │ SILO 2: COMPILATION  │ SILO 3: MATCH & TELEMETRY      │
│ ENGINE               │ & ARTIFACT PIPELINE  │ ENGINE                         │
│ • Bitmask arithmetic │ • Binary CDB builder │ • ELO state machine            │
│ • Passcode allocator │ • Lua code generator │ • Win/loss & usage tracking    │
│ • Text AST tokenizer │ • .ydk stream writer │ • Replay (.yrp) analyzer       │
├──────────────────────┴──────────────────────┴────────────────────────────────┤
│ SILO 4: APPLICATION & PRESENTATION SHELLS                                    │
│ • Modular Discord Bot (Slash commands, buttons, interactive duels)           │
│ • FastAPI Web Dashboard (REST endpoints, Jinja2/HTML catalog)                │
│ • Live Duel Simulator (ocgcore TCP 7911 socket & HTTP 7922 room manager)    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Bi-Directional Closed-Loop Lifecycle

A common misconception in early platform architecture is viewing the system as a one-way street: `Seed Data ➔ Application`.

In reality, **the seed data is only the bootstrap ROM** to cold-start the platform. Once the platform is running, the Application Layer is an **active data producer**.

### Downstream Projection (Read Path)

Authoritative data moves from the central database through compilers into runtime memory:
$$\text{Authoritative DB (ygo\_story.db)} \xrightarrow{\text{compile}} \text{CDB / Lua / YDK} \xrightarrow{\text{mount}} \text{Simulator / Bot / Web}$$

### Upstream Mutation (Write Path)

Interactions at the Application Layer flow through validation and commit back into the authoritative store:
$$\text{User Action in Discord/Web} \xrightarrow{\text{validate}} \text{Transaction Guard} \xrightarrow{\text{commit}} \text{Authoritative DB}$$

### The Reactive Re-Synchronization Loop

When a state mutation occurs upstream, the pipeline programmatically triggers downstream re-compilation:

1. **New Card Created (Web API `POST /api/cards`):**
   * Upstream: Validates rules $\rightarrow$ Allocates passcode $\rightarrow$ Writes to `content.db`.
   * Feedback: Automatically compiles delta into `custom_cards.cdb` $\rightarrow$ Synthesizes `c<id>.lua` $\rightarrow$ Updates search index $\rightarrow$ Immediately available for dueling.
2. **New Deck Assembled (Discord `/deck_add` or `/mydeck save`):**
   * Upstream: Validates legality against banlists and deck size constraints $\rightarrow$ Saves to `player_saved_decks`.
   * Feedback: Serializes to `.ydk` stream $\rightarrow$ Staged for EDOPro/YGOPro client synchronization.
3. **Duel Completed (Discord `/duel` or Live Simulator Match):**
   * Upstream: Replay emitted $\rightarrow$ Winner/turns recorded $\rightarrow$ ELO updated $\rightarrow$ Card telemetry incremented.
   * Feedback: Web leaderboards, player tier titles, and card usage statistics dynamically reflect the outcome.

---

## 5. Architectural Invariants (The Non-Negotiables)

1. **Unidirectional Dependency Hierarchy:**
   * Applications depend on Services.
   * Services depend on the Functional Core & Repositories.
   * Repositories depend on the Authoritative Database.
   * *Data never flows backward silently:* An application UI never directly writes raw SQL or directly edits binary `.cdb` files.
2. **Single Source of Truth:**
   * The SQLite databases (`content.db` for static content, `telemetry.db` for player state) and versioned trackers are the sole authoritative master records. All binary databases (`custom_cards.cdb`), Lua scripts (`c<id>.lua`), and deck streams (`.ydk`) are reproducible compiled derivatives.
3. **Immutability of Data in Flight:**
   * Data moving between silos must travel as immutable structs (e.g. frozen dataclasses or read-only dictionaries). No function may alter an incoming payload in-place.
4. **Zero Cross-Contamination Across Shells:**
   * The Discord bot never imports Web API modules; the Web API never imports Discord cogs; the Live Simulator container remains completely agnostic of the bot and web frameworks.
