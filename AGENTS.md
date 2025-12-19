# Repository Guidelines

## Project Structure & Module Organization
- Core package lives in `pymrio/` (`core/` for IO system logic, `tools/` for helpers, `mrio_models/` for bundled classifications).
- Tests are in `tests/`, with mock MRIO data under `tests/mock_mrios/`.
- Documentation sources sit in `doc/` (Sphinx) and `doc/source/notebooks/` for tutorials; build artifacts land in `doc/_build/`.
- Packaging metadata: `pyproject.toml`, `setup.py`, `requirements.txt`, `environment.yml`.

## Build, Test, and Development Commands
- Install dev deps: `uv sync --all-extras`.
- Fast tests: `poe test` (maps to `pytest -n auto`).
- Full suite + coverage + lint gate: `poe fulltest` (runs coverage and ruff checks).
- Format code: `poe format` (ruff format).
- Lint: `poe check` (add `--fix` to auto-fix).
- Docs: `poe doc` to build Sphinx HTML; `poe jl` opens notebooks via Jupyter Lab.
- End-to-end CI-equivalent: `poe build` (format → full tests → docs).

## Coding Style & Naming Conventions
- Python 3, ruff for lint/format (double quotes enforced). Respect existing import ordering and keep functions short where feasible (mccabe budget 50).
- Docstrings use NumPy style; include parameters/returns and examples where helpful.
- Tests/fixtures and helper data should live alongside related modules; avoid duplicating mock data.

## Testing Guidelines
- Primary framework: `pytest`; parallelization enabled by default (`-n auto`).
- Add focused unit tests near the touched functionality; use mocks from `tests/mock_mrios/` when possible to avoid large downloads.
- Prefer descriptive test names (`test_<behavior>`) and mark slow/external cases explicitly.
- Ensure coverage stays stable; run `poe fulltest` before opening a PR.

## Commit & Pull Request Guidelines
- Work issue-first: open/claim an issue, then branch from `master`.
- Commits: concise imperative subject (`Add`, `Fix`, `Refactor`…), group related changes, and include context when touching data files.
- PRs: link the issue (use GitHub closing keywords), summarize changes, note testing (`poe test`/`poe fulltest`), and mention doc/notebook updates when relevant. Include screenshots only if UI/plot output changes.

## Documentation & Notebooks
- Sphinx sources in `doc/source/`; prefer reStructuredText for narrative docs and keep code examples runnable.
- Notebooks in `doc/source/notebooks/` should stay lightweight and reproducible; strip large outputs before committing.
