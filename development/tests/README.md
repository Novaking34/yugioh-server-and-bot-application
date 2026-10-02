# 🧪 Automated Diagnostic Test Suite & Debugging Framework (`development/tests/`)

The `development/tests/` directory provides an automated diagnostic testing and debugging suite powered by **Pytest**.

Unlike conventional tests designed merely to pass with shallow assertions, this suite is deliberately engineered as an **actionable debugging and failpoint isolation system**. Tests assert boundary limits, bitwise orthogonality, schema integrity, and security vulnerabilities—surfacing clear diagnostic messages when failpoints occur.

---

## 🎯 Diagnostic Testing Philosophy

1. **Designed to Assert Failpoints, Not Just Pass**:
   Tests do not perform trivial assertions. They rigorously test boundary states (scale `0` vs `13`, scale overflow `15`, octal Link arrow compass geometry omitting the center position `0o020`, SQLite NOT NULL constraints, and FTS5 shadow table synchronization).
2. **Diagnostic Error Messages**:
   Failures output detailed context—including hex/octal representations, expected bitmasks, and SQL query context—so the test suite itself operates as a primary debugging tool.
3. **Cross-Platform Parity**:
   Every test runs identically across Linux, Windows, and macOS without path delimiter or platform assumptions.
4. **Isolated Test Fixtures (`conftest.py`)**:
   Provides in-memory SQLite schema fixtures, diagnostic assertion helpers (`diag`), and standard card test data without disk side-effects.

---

## 📁 Test Manifest

| Test Module | Coverage & Diagnostic Focus | Target Component |
| :--- | :--- | :--- |
| [`conftest.py`](file:///home/professorseanex/yugioh-server/development/tests/conftest.py) | Shared diagnostic fixtures (`diag`, `mock_db`, `sample_cards`) | Pytest harness |
| [`test_api_server.py`](file:///home/professorseanex/yugioh-server/development/tests/test_api_server.py) | Web Dashboard, REST endpoints, FTS search, SQL injection defense (`' OR 1=1 --`), 404 handlers | `production/main/web/api_server.py` |
| [`test_cdb_builder.py`](file:///home/professorseanex/yugioh-server/development/tests/test_cdb_builder.py) | CDB bitmask calculation, scale bit-packing, Link arrows in DEF, desc format, SQLite compilation roundtrip | `development/tools/cdb_builder.py` |
| [`test_constants.py`](file:///home/professorseanex/yugioh-server/development/tools/constants.py) | Bitwise orthogonality, power-of-2 attributes, all 26 race masks, 8-arrow compass octal `0o757` | `development/tools/constants.py` |
| [`test_diagnostics.py`](file:///home/professorseanex/yugioh-server/development/tests/test_diagnostics.py) | Asserts that `debug_diagnostics.py` accurately catches DB corruption, scale limits, and bad YDK decks | `development/tools/debug_diagnostics.py` |
| [`test_duelingbook_importer.py`](file:///home/professorseanex/yugioh-server/development/tests/test_duelingbook_importer.py) | Passcode range (`50,000,000` - `59,999,999`), collision retries, path traversal sanitization, FTS5 sync | `development/tools/duelingbook_importer.py` |
| [`test_lua_generator.py`](file:///home/professorseanex/yugioh-server/development/tests/test_lua_generator.py) | Xyz/Link/Pendulum/Synchro procedures, HOPT limits, targeting/battle protection, luac syntax validation | `development/tools/lua_generator.py` |

---

## 🚀 Running Tests & Diagnostics

### 1. Master CLI Controller (Recommended)

* **Linux / macOS:**

  ```bash
  # Run all 56 diagnostic unit tests:
  ./manage.sh test

  # Run full system diagnostics and failpoint auditor:
  ./manage.sh diagnose
  ```

* **Windows:**

  ```cmd
  :: Run all 56 diagnostic unit tests:
  manage.bat test

  :: Run full system diagnostics and failpoint auditor:
  manage.bat diagnose
  ```

### 2. Direct Pytest Execution

```bash
# Run all tests with verbose output
pytest -v development/tests

# Run a specific diagnostic module
pytest -v development/tests/test_diagnostics.py

# Run tests matching an expression
pytest -k "cdb or lua or bitmask"
```

---

## 🔍 Key Diagnostic Assertions & Failpoints

### A. Binary Encoding & Bitwise Orthogonality

* **Primary Types**: Asserts that `TYPE_MONSTER`, `TYPE_SPELL`, and `TYPE_TRAP` share 0 overlapping bits.
* **Link Compass Geometry**: Asserts that the 8 compass arrows sum to octal `0o757` (`495` dec). In ocgcore's 3x3 keypad layout, center position `5` (octal `0o020` / `16` dec) is omitted because a card cannot point to itself.
* **Pendulum Scales**: Asserts that Left and Right Scales (`0` - `13`) pack into bits 24-31 and 16-23 without colliding with the Level bits (0-15).

### B. Security & Input Sanitization

* **SQL Injection**: Asserts that `/api/cards/search` safely handles SQL injection attempts (`' OR 1=1 --`) without syntax errors or data exfiltration.
* **Path Traversal**: Asserts that `sanitize_filename()` strips `../` and dangerous filesystem characters (`<>:"/\\|?*`).

### C. ocgcore Lua Effect Generation & Syntax

* **Summoning Procedures**: Asserts generation of `Xyz.AddProcedure`, `Link.AddProcedure`, `Synchro.AddProcedure`, and `Pendulum.AddProcedure`.
* **Protection Effects**: Asserts continuous targeting immunity (`EFFECT_CANNOT_BE_EFFECT_TARGET`) and battle destruction protection (`EFFECT_INDESTRUCTABLE_BATTLE`).
* **Bytecode Compilation**: Validates generated Lua scripts with `luac -p` to guarantee syntax correctness before deployment.
