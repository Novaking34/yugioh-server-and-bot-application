# 🧪 Automated Test Suite (`development/tests/`)

The `development/tests/` directory contains unit and integration tests powered by **Pytest**, providing automated validation for the FastAPI web server, SQLite CDB compiler, Duelingbook importer, ocgcore Lua effect generator, and binary bitmasks.

---

## 📁 Test Manifest

| Test Module | Coverage Scope | Target Components |
| :--- | :--- | :--- |
| [`test_api_server.py`](file:///home/professorseanex/yugioh-server/development/tests/test_api_server.py) | Web Dashboard, REST API endpoints, FTS search, card manifest | `production/main/web/api_server.py` |
| [`test_cdb_builder.py`](file:///home/professorseanex/yugioh-server/development/tests/test_cdb_builder.py) | CDB bitmask calculation, scale bit-packing, Link arrows, desc format | `development/tools/cdb_builder.py` |
| [`test_constants.py`](file:///home/professorseanex/yugioh-server/development/tests/test_constants.py) | Bitwise orthogonality, enum mappings, dictionary consistency | `development/tools/constants.py` |
| [`test_duelingbook_importer.py`](file:///home/professorseanex/yugioh-server/development/tests/test_duelingbook_importer.py) | JSON parsing, passcode generation, classification logic | `development/tools/duelingbook_importer.py` |
| [`test_lua_generator.py`](file:///home/professorseanex/yugioh-server/development/tests/test_lua_generator.py) | Xyz/Link/Pendulum procedure generation, effect analyzer, syntax | `development/tools/lua_generator.py` |

---

## 🚀 Running the Test Suite

### 1. Via Master CLI Controller (Recommended)

* **Linux / macOS:**

  ```bash
  ./manage.sh test
  ```

* **Windows:**

  ```cmd
  manage.bat test
  ```

### 2. Direct Pytest Execution

```bash
# Run all tests with verbose output
pytest -v development/tests

# Run a specific test module
pytest -v development/tests/test_api_server.py

# Run tests matching an expression
pytest -k "cdb or lua"
```

---

## 🔍 Key Test Categories

### A. Binary Encoding & Bit-Packing

Verifies that:

* Primary card types (`TYPE_MONSTER`, `TYPE_SPELL`, `TYPE_TRAP`) are mathematically orthogonal (`TYPE_MONSTER & TYPE_SPELL == 0`).
* Pendulum Scales and Monster Levels are correctly bit-packed into 32-bit integers without overflow or collision.
* Link Arrow compass directions correctly compute to octal bitmasks in `datas.def`.

### B. Lua Script Generation & Syntax Verification

Verifies that:

* Xyz procedure generators produce valid `Xyz.AddProcedure(c, nil, 8, 2)` syntax.
* Link procedure generators produce valid `Link.AddProcedure(c, nil, 2, 2, s.lcheck)` syntax.
* Generated Lua scripts pass basic compilation checks via `luac` when available.

### C. REST API & Web Catalog Endpoints

Verifies that:

* `/` returns valid HTML dashboard with HTTP 200.
* `/api/cards` returns valid card pools with filtering support.
* `/api/shared/manifest` serves the live expansion manifest with correct SHA-256 hashes.
* `/api/shared/cdb` serves the binary `custom_cards.cdb` with appropriate download headers.
