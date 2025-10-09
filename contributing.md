# Contributing Guide

## Architecture Overview

### Components
- `mail_client_api`: defines the public contracts for interacting with a mail system. 
```
mail_client_api 
→ Client, Message (Abstract Classes)
→ get_client, get_message (Factory Methods)
```
- `gmail_client_impl`: houses the production implementation that satisfies the contracts using the Gmail REST API. 
```
gmail_client_impl
→ GmailClient, GmailMessage (implementation of abstraction using Gmail API)
→ get_client_impl, get_message_impl (concrete factory method)
→ register (for Dependency Injection)
```
- Top-level runtime: run `main.py` in folder root.
```python
main.py 
-> import gmail_client_impl (dependency injection) 
-> import mail_client_api (abstract API)
-> mail_client_api.get_client (returns a GmailClient instance)
```

### Interface Design
#### Interface Overview
**Public Interfaces**
- Mail client contract
  - client(ABC) with operations
  - get_client() factory function
- Message contract
  - Message(ABC) with properties
  - get_message() factory function
- Package surface
**Implementations**
- Gmail client
  - client implementation: `GmailClient(mail_client_api.Client) -> client(ABC)` using the Gmail API.
  - core methods: 
    - `get_message` builds a contract `Message`
    - `delete_message` and `mark_as_read` call Gmail endpoints and return bool
  - Auth modes: are layered with helper methods `_auth_from_env`, `_auth_from_token_file`, `_run_interactive_flow`.
  - DI hook: `get_client_impl(interactive=False)` returns `GmailClient`, and `register()` assigns `mail_client_api.get_client = get_client_impl`
- Gmail message
  - message implementation: `GmailMessage(message.Message) -> Message(ABC)` 
  - Handles multipart, charset decoding, RFC 2047 subjects, and guards against malformed/binary payloads (e.g., _is_binary_garbage) while returning safe defaults
  - DI hook: `get_message_impl(msg_id, raw_data)` and `register()` that assigns into both `mail_client_api.message.get_message` and `mail_client_api.get_message`
- Auto-registration and entrypoint
  - `__init__.py` calls register() at import time so DI is automatic.
  - `main.py` imports `gmail_client_impl` to trigger registration. Then calls `mail_client_api.get_client()` to obtain a Client and exercise methods without depending on Gmail types.
#### Design Choices
- **Hiding implementation** Users of `Client` don't need to know or change details of Gmail API, which allows simply swap different implementations.
- **callable contructors:** It enables single import path (mail_client_api) for app code which wants to construct client or message.
- **Clear, minimal public API:** Centralize exports in `mail_client_api/__init__.py` and set `__all__`. It keeps import paths stable, hides internal module structure, and prevents abstractions leak.

### Implementation Details
#### Python features used to define the interface
- `abc.ABC`:  declare abstract contracts.
- `@property + @abstractmethod`: add interface properties at definition time.
- `collections.abc.Iterator`: to type the get_messages return value.
- Package `__all__` and `__init__`: re-exports to present a clean, stable surface.
- Factory function like `get_client()`: create instances.
#### How to implement
- Concrete classes implement the ABCs: `GmailClient(mail_client_api.Client)`
- Factories wired via registration: `register(): mail_client_api.get_client = get_client_impl`
- Consumer usage: `import gmail_client_impl`
####  Differences between this and Protocol from the Typing module
|            Concept            |                 ABC (Abstract Base Class)                |                               Protocol (Structural Subtyping)                              |
|:-----------------------------:|:--------------------------------------------------------:|:------------------------------------------------------------------------------------------:|
| Type system                   | Nominal typing (based on inheritance)                    | Structural typing (based on method signatures)                                             |
| How you declare compatibility | A class must explicitly inherit from the ABC             | A class is compatible if it has the required methods/attributes — inheritance not required |
| Checked by                    | isinstance() and issubclass() at runtime                 | Checked only by type checkers (e.g. mypy, pyright), not at runtime                         |
| Use case                      | You want to enforce an interface at runtime              | You just want static type checking — duck typing “done right”                              |
| Performance                   | Slightly slower (extra inheritance + metaclass overhead) | Lightweight (no runtime impact)                                                            |

### Dependency Injection
This project uses a factory function pattern for dependency injection.
#### Where Injection Occurs
1. A factory function is defined in API `mail_client_api`
```python
# src/mail_client_api/src/mail_client_api/client.py
def get_client(*, interactive: bool = False) -> Client:
    """Return an instance of a Mail Client."""
    raise NotImplementedError
```
2. The implementation of API defines register function to register real factory function`get_client_impl`.
```python
# src/gmail_client_impl/src/gmail_client_impl/gmail_impl.py
def register() -> None:
    """Register the Gmail client implementation with the mail client API."""
    mail_client_api.get_client = get_client_impl
```
3. Dependency injection happens at import time then `register()`
```python
# src/gmail_client_impl/src/gmail_client_impl/__init__.py
register()
```
4. Contributer's application can now use the api which returns the implementation.
```python
# main.py
import gmail_client_impl
import mail_client_api

client = mail_client_api.get_client(interactive=False)
```
Contributers are enable to:

1. Swap implementations without changing consumers.
2. Keep API imports stable.
3. Avoid cycle dependence. 

## Repository Structure

### Project Organization
```
.
|-- docs/                     # MkDocs documentation (architecture, testing, CI guides)
|-- src/
|   |-- mail_client_api/      # Abstract contracts and developer-facing API
|   `-- gmail_client_impl/    # Gmail-backed implementation of the contracts
|-- tests/
|   |-- integration/          # Cross-package tests against the registered Gmail client
|   `-- e2e/                  # Black-box tests that execute main.py
|-- main.py                   # Demo entry point that drives the abstractions
|-- pyproject.toml            # Workspace definition, toolchain configuration
`-- uv.lock                   # Locked dependency graph shared across all components
```

### Configuration Files
1. Root `pyproject.toml`: 
  - Declares `uv` workspace members for both packages (`pyproject.toml: [tool.uv.workspace]`).
  - Centralizes dev extras (ruff, mypy, pytest, coverage, mkdocs) used across the repo (`pyproject.toml: [project.optional-dependencies].dev`).
  
2. Component `pyproject.toml`:
  - Package metadata: Name, version, Python requirement, readme and dependencies (`src/mail_client_api/pyproject.toml: [project]`).
  - Defines how to build the component (`src/mail_client_api/pyproject.toml: [build-system]`).
  - Resolves uv source mapping (`src/gmail_client_impl/pyproject.toml: [tool.uv.sources]`).

### Package Structure
#### `__init__.py`
Locations:
- `src/mail_client_api/src/mail_client_api/__init__.py`
- `src/gmail_client_impl/src/gmail_client_impl/__init__.py:1`

Roles:
- Mark the folder as a python package.
- Initialize the package.
- API package(`mail_client_api`):
  - Re-exports the public surface: `Client`, `Message`, `get_client`, `get_message`, and `message` for applications to import from a single place.
- Implementation package (`gmail_client_impl`):
  - Re-exports the concrete types and factories (`GmailClient`, `GmailMessage`, `get_client_impl`, `get_message_impl`) to provide a clean public surface.
  - Performs dependency injection wiring by calling `register()` at import time so consumers can just import `gmail_client_impl` and then use the abstract factories.

#### keep `__init__.py` slim
meaning: 
- only re-export public symbols in `__init__.py`.
- perform minimal wiring such as single DI `register()`.

benefits for contributers:
- Reduce circuler imports.
- Easier testing and maintenance. 

### Import Guidelines
- Prefer simple imports: 
```python
import mail_client_api
```
- Import from package surfaces (__init__.py re-exports), not deep module paths.
```python
from mail_client_api import Message
```
- The API package must not import implementation packages (e.g., no `gmail_client_impl` in `mail_client_api`).

## Testing Strategy

### Testing Philosophy
1. Prefer the test pyramid: many unit tests, some integration, few end‑to‑end.
2. Make unit tests FIRST: Fast, Isolated, Repeatable, Self‑checking (use assert), Timely.
3. Don’t change tests for refactors or bug fixes; add new tests instead.
4. Keep tests simple: no logic/branches; clear names and failure messages.
### Test Organization
**Unit Tests** (`src/*/tests`): Fast, isolated tests for each component. Use mocks where needed.

**Integration tests**(`tests/integration`): Marked with `@pytest.mark.integration`. Check components working together.

**E2E tests**(`tests/e2e`): Marked with `@pytest.mark.e2e`. Run the app like a user.

**Config**
- Root pyproject.toml sets `testpaths = ["tests", "src/*/tests"]` and `pythonpath = [".", "src"]`, so tests import code with absolute imports.

**init.py in Tests**
- no `__init__.py` in test folders.

- Reason:
  - Avoids import/package quirks and circular imports between tests.
  - Encourages importing the code under test via public, absolute imports.

### Test Abstraction Levels
#### Unit Tests: 
Test the abstract API, implementation with mocks. 

#### Integration level
Tests how pieces work together (dependency injection, factory wiring). May hit real Gmail if creds exist.
#### End‑to‑end level
Runs the app like a user (calls main.py). Slowest; checks full flow.

### Code Coverage
#### Tool
name: pytest-cov

usage:
```powershell
# All tests with coverage
uv run pytest --cov=src --cov-report=term-missing
# Exclude local-cred tests
uv run pytest src/ tests/ -m "not local_credentials" -v
# Show branches too
uv run pytest --cov --cov-branch
# HTML report
uv run pytest --cov --cov-report=html
# Target specific packages
uv run pytest --cov=src/mail_client_api --cov=src/gmail_client_impl
# Component‑Only
# API only
cd src/mail_client_api
uv run pytest
# Gmail impl only
cd src/gmail_client_impl
uv run pytest
```
#### acceptable thresholds
- Minimum code coverage: 85%. 

## Development Tools

### Workspace Management
#### UV Workspace

**Purpose**

Manage multiple packages together with one env and tool config.

**Members**

 at the root so `mail_client_api` and `gmail_client_impl` build as one workspace.

**Setup**

Install deps + create .venv:
```
uv sync --all-packages --extra dev
```
Run app
```
uv run python main.py
```
**Common Tasks**

Tests (with coverage)
```
uv run pytest
```
Lint
```
uv run ruff check .
```
Format
```
uv run ruff format .
```
Type check
```
uv run mypy src tests
```
Docs (live)
```
uv run mkdocs serve
```
**Root pyproject.toml**

- Declares workspace members and dev extras.
- Central tool config: pytest (paths/markers), coverage (threshold), ruff, mypy.
- One place to run tools across all components.

**Component pyproject.toml (per‑package)**

- Package metadata and build system (hatchling).
- Runtime deps (Gmail impl depends on mail-client-api).
- Workspace source mapping so local packages resolve from the workspace

**Why this setup**

- Single command installs everything.
- Shared tooling and rules; consistent checks.
- Each component still builds/tests on its own when needed.

### Static Analysis and Code Formatting
#### Tools

Lint + format: ruff (style, lint rules, and code formatter)

Static typing: mypy (type checks)

#### Run Checks

Lint
```
uv run ruff check .
```
Auto-fix lint issues
```
uv run ruff check . --fix
```
Format
```
uv run ruff format .
```
Check formatting only
```
uv run ruff format --check .
```
Type check
```
uv run mypy src tests
```

#### Run Without uv

Install
```
pip install ruff mypy
```
Lint
```
ruff check .
```
Format
```
ruff format . 
```
Types
```
mypy src tests
```
#### Why it's important
- Catches obvious bugs early (types, obvious mistakes).
- Keeps code consistent and easy to read across components.
- Protects interfaces so implementations don’t drift. Maintain the consistency of each layer.
- Speeds reviews and reduces merge conflicts.

### Documentation Generation
#### Tool/Framework

- MkDocs with the Material theme. 

- API pages via mkdocstrings-python.

#### Setup

Install dev tools
```
uv sync --extra dev
```
#### Local Preview

Start server
```
uv run mkdocs serve
```
Open http://127.0.0.1:8000

#### Build Static Site

Generate site
```
uv run mkdocs build
```
Output: site/
#### How To Write

Add .md files in docs/

Add docstrings in code; mkdocstrings renders them
#### Integration

Runs through uv so everyone uses the same tool versions and config.

### CI
#### Jobs

build: Set up Python 3.11, install uv, create .venv, uv sync, cache workspace.

lint: Run ruff check ..

unit_test: Run fast tests in src/ with coverage (85% min) and mypy; store reports.

circleci_test: Run all tests in src/ and tests/ except those needing local creds; include coverage; store results.

integration_test: Run integration tests that use real Gmail env vars (no local creds). Uses a CircleCI context for secrets.

report_summary: Print brief summaries and note coverage artifacts.

#### Workflows and Triggers

**build_and_test (feature branches):**

Runs on all branches except main, develop, kamen-requierd-fixes, make-real-deletions.

Order: build → lint → unit_test → circleci_test → report_summary.

**full_integration (protected branches):**

Runs only on main, develop, kamen-requierd-fixes, make-real-deletions.

Order: build → lint → unit_test → circleci_test → integration_test → report_summary.