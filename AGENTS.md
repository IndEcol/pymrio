# Repository Guidelines

## Project Overview
- Pymrio is a Python package for Multi-Regional Input-Output (MRIO) analysis, focused on environmentally extended MRIO tables.
- It provides high-level abstractions for global environmentally extended MRIO databases such as EXIOBASE, WIOD, EORA26, and OECD data.

## Project Structure & Module Organization
- Core package lives in `pymrio/` (`core/` for IO system logic, `tools/` for helpers, `mrio_models/` for bundled classifications).
- Tests are in `tests/`, with mock MRIO data under `tests/mock_mrios/`.
- Documentation sources sit in `doc/` (Sphinx) and `doc/source/notebooks/` for tutorials; build artifacts land in `doc/_build/`.
- Packaging metadata: `pyproject.toml`, `setup.py`, `requirements.txt`, `environment.yml`.

## Architecture

### Core Components
- `pymrio/core/mriosystem.py`: main `IOSystem` and `Extension` classes representing MRIO tables.
- `pymrio/core/fileio.py`: file I/O operations for loading and saving MRIO data.
- `pymrio/core/constants.py`: package constants and configuration.
- `pymrio/tools/iomath.py`: mathematical operations for MRIO calculations, such as `calc_A` and `calc_L`.
- `pymrio/tools/ioparser.py`: parsers for MRIO database formats such as EXIOBASE and WIOD.
- `pymrio/tools/iodownloader.py`: automatic download functions for MRIO databases.
- `pymrio/tools/ioutil.py`: utilities for data manipulation and aggregation.
- `pymrio/tools/ioclass.py`: classification data handling.
- `pymrio/tools/iometadata.py`: metadata management.
- `pymrio/mrio_models/`: test data and concordance files for different MRIO models, including the small `test_mrio/` dataset used for development and examples.

### Key Classes
- `IOSystem`: represents a complete MRIO system with matrices such as A, L, and Z.
- `Extension`: represents satellite accounts such as emissions and land use.
- `MRIOMetaData`: handles metadata and calculation history.
- `ClassificationData`: manages region and sector classifications.

### Standard MRIO Matrix Notation
- `Z`: inter-industry flow matrix.
- `A`: technical coefficient matrix.
- `L`: Leontief inverse matrix.
- `Y`: final demand matrix.
- `x`: total output vector.
- `F`: environmental extension matrix (direct impacts).
- `S`: environmental multiplier matrix.

## Build, Test, and Development Commands
- Install dev deps: `uv sync --all-extras`.
- Sync dependencies through the task runner: `poe sync`.
- Fast tests: `poe test` (maps to `pytest -n auto`).
- Full suite + coverage + lint gate: `poe fulltest` (runs coverage and ruff checks).
- Direct test/lint commands: `pytest --ruff --ruff-format`; add coverage with `coverage run -m pytest --ruff --ruff-format`, then inspect it with `coverage report`.
- Format code: `poe format` (ruff format).
- Lint: `poe check` (add `--fix` to auto-fix).
- Direct code-quality commands: `ruff format`, `ruff check`, and `ruff check --fix`.
- Docs: `poe doc` to build Sphinx HTML; `poe jl` opens notebooks via Jupyter Lab.
- Direct documentation commands: `make -C ./doc clean` and `make -C ./doc html`.
- End-to-end CI-equivalent: `poe build` (format → full tests → docs).

## Coding Style & Naming Conventions
- Python 3, ruff for lint/format (double quotes enforced). Respect existing import ordering and keep functions short where feasible (mccabe budget 50).
- Docstrings use NumPy style; include parameters/returns and examples where helpful.
- Tests/fixtures and helper data should live alongside related modules; avoid duplicating mock data.

## Testing Guidelines
- Primary framework: `pytest`; parallelization enabled by default (`-n auto`).
- Add focused unit tests near the touched functionality; use mocks from `tests/mock_mrios/` when possible to avoid large downloads.
- Prefer descriptive test names (`test_<behavior>`) and mark slow/external cases explicitly.
- The suite covers core functionality with the small test MRIO, parser behavior with mock data, mathematical operations, integrations, and output-format validation.
- Ensure coverage stays stable; run `poe fulltest` before opening a PR.

## Commit & Pull Request Guidelines
- Work issue-first: open/claim an issue, then branch from `master`.
- Commits: concise imperative subject (`Add`, `Fix`, `Refactor`…), group related changes, and include context when touching data files.
- PRs: link the issue (use GitHub closing keywords), summarize changes, note testing (`poe test`/`poe fulltest`), and mention doc/notebook updates when relevant. Include screenshots only if UI/plot output changes.

## Documentation & Notebooks
- Sphinx sources in `doc/source/`; prefer reStructuredText for narrative docs and keep code examples runnable.
- Notebooks in `doc/source/notebooks/` should stay lightweight and reproducible; strip large outputs before committing.

## Dependencies & Development Setup
- The scientific stack includes pandas (>= 2.1) for data handling, NumPy (>= 1.20) for numerical operations, matplotlib for visualization, requests for downloads, and xlrd/openpyxl for Excel support.
- Configuration lives primarily in `pyproject.toml`; the project uses uv for dependency management, ruff for linting and formatting, pytest for tests, poethepoet for task running, and Sphinx for documentation.
