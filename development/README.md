# 🛠️ Development & Tooling Subsystem (`development/`)

The `development/` directory houses the core data compilation pipelines, relational database schemas, automated testing suites, and developer documentation that drive the Yu-Gi-Oh! custom card, story, and duel simulation platform.

---

## 📁 Subsystem Directory Structure

```bash
development/
├── README.md                      # Development subsystem master guide (this file)
├── __init__.py                    # Python package root exports
├── tools/                         # Custom Card compilation & conversion pipelines
│   ├── README.md                  # Comprehensive toolchain operations manual
│   ├── __init__.py                # Toolchain exports
│   ├── cdb_builder.py             # Compiles SQLite custom_cards.cdb for ocgcore
│   ├── constants.py               # Bitmasks, attributes, monster types, and Link arrows
│   ├── duelingbook_importer.py    # Imports custom cards from Duelingbook JSON
│   ├── export_deck.py             # Exports character & player decks to standard .ydk
│   └── lua_generator.py           # Generates syntactically valid ocgcore Lua scripts
├── database/                      # Story database schema & seed scripts
│   ├── README.md                  # Relational schema architecture & migration guide
│   ├── __init__.py                # Database helpers
│   ├── schema.sql                 # SQLite relational DDL definition
│   └── seed_story_data.py         # Bootstraps sample cards, factions, and story arcs
├── tests/                         # Automated unit & integration test suite
│   ├── README.md                  # Pytest architecture & test execution guide
│   ├── __init__.py                # Test package initialization
│   ├── test_api_server.py         # FastAPI endpoint tests (HTML dashboard & JSON API)
│   ├── test_cdb_builder.py        # CDB bitmask & binary encoding tests
│   ├── test_constants.py          # OCGCore bitwise orthogonality tests
│   ├── test_duelingbook_importer.py # Duelingbook JSON parsing & ID generation tests
│   └── test_lua_generator.py      # Procedure generators & Lua syntax tests
└── docs/                          # In-depth technical architecture manuals
    ├── README.md                  # Documentation index & cross-reference
    ├── HOSTING_24_7.md            # Cloud VPS options (Oracle Cloud, Hetzner, DigitalOcean)
    ├── ORACLE_CLOUDFLARE_SETUP.md # Step-by-step Oracle Cloud + Cloudflare Zero Trust guide
    └── PACKAGING_AND_DISTRIBUTION.md # Architecture of client/server release builders
```

---

## 🚀 Quick Start for Developers

### 1. Synchronize All Custom Cards & Lua Scripts

Compile the live story database (`ygo_story.db`) into the simulator's binary CDB and regenerate all Lua scripts:

* **Linux / macOS:**

  ```bash
  ./manage.sh sync
  ```

* **Windows:**

  ```cmd
  manage.bat sync
  ```

### 2. Run the Automated Test Suite

Execute the 26 unit and integration tests with Pytest:

* **Linux / macOS:**

  ```bash
  ./manage.sh test
  ```

* **Windows:**

  ```cmd
  manage.bat test
  ```

### 3. Validate Lua Script Syntax

Verify syntax across all generated Lua card scripts using `luac`:

* **Linux / macOS:**

  ```bash
  ./manage.sh validate-lua
  ```

* **Windows:**

  ```cmd
  manage.bat validate-lua
  ```

### 4. Build Release Distribution Packages

Bundle the player client zip and host server deployment tarball into `dist/`:

* **Linux / macOS:**

  ```bash
  ./manage.sh package
  ```

* **Windows:**

  ```cmd
  manage.bat package
  ```

---

## 🧩 Architectural Modules

| Module | Location | Primary Purpose | Key Technologies |
| :--- | :--- | :--- | :--- |
| **Card Compilers** | [`development/tools/`](file:///home/professorseanex/yugioh-server/development/tools) | Transforms high-level card definitions into simulator binary assets | Python, SQLite, Bitwise Operations |
| **Story Database** | [`development/database/`](file:///home/professorseanex/yugioh-server/development/database) | Relational database schema for lore, characters, factions, and cards | SQLite3, FTS5 Virtual Tables |
| **Test Suite** | [`development/tests/`](file:///home/professorseanex/yugioh-server/development/tests) | Validates API contracts, CDB bitmasks, Lua syntax, and JSON parsers | Pytest, FastAPI TestClient |
| **Documentation** | [`development/docs/`](file:///home/professorseanex/yugioh-server/development/docs) | Operational manuals for cloud infrastructure, tunneling, and packaging | Markdown |
