# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pymrio is a Python package for Multi-Regional Input-Output (MRIO) analysis focused on environmentally extended MRIO tables. It provides high-level abstractions for global EE MRIO databases like EXIOBASE, WIOD, EORA26, and OECD data.

## Development Commands

### Testing
- `pytest -n auto` - Fast parallel testing
- `pytest --ruff --ruff-format` - Full test suite with linting
- `coverage run -m pytest --ruff --ruff-format` - Test with coverage
- `coverage report` - Show coverage report

### Code Quality
- `ruff format` - Format all files
- `ruff check` - Lint check (use `--fix` to auto-fix)
- `ruff check --fix` - Lint and auto-fix issues

### Documentation
- `make -C ./doc clean` - Clean documentation build
- `make -C ./doc html` - Build HTML documentation

### Development Workflow
- `poe sync` - Sync all dependencies with uv
- `poe format` - Format code
- `poe check` - Run linting checks
- `poe test` - Fast testing
- `poe fulltest` - Full test suite with coverage
- `poe doc` - Build documentation
- `poe build` - Complete build process (format, test, docs)

## Architecture

### Core Components

**`pymrio/core/`**
- `mriosystem.py` - Main `IOSystem` and `Extension` classes that represent MRIO tables
- `fileio.py` - File I/O operations for loading/saving MRIO data
- `constants.py` - Package constants and configuration

**`pymrio/tools/`**
- `iomath.py` - Mathematical operations for MRIO calculations (calc_A, calc_L, etc.)
- `ioparser.py` - Parsers for different MRIO database formats (EXIOBASE, WIOD, etc.)
- `iodownloader.py` - Automatic download functions for MRIO databases
- `ioutil.py` - Utility functions for data manipulation and aggregation
- `ioclass.py` - Classification data handling
- `iometadata.py` - Metadata management

**`pymrio/mrio_models/`**
- Contains test data and concordance files for different MRIO models
- `test_mrio/` - Small test dataset for development and examples

### Key Classes

- `IOSystem` - Main class representing a complete MRIO system with matrices (A, L, Z, etc.)
- `Extension` - Represents satellite accounts (emissions, land use, etc.)
- `MRIOMetaData` - Handles metadata and calculation history
- `ClassificationData` - Manages region/sector classifications

### Standard MRIO Matrix Notation

The package follows standard MRIO notation:
- `Z` - Inter-industry flow matrix
- `A` - Technical coefficient matrix
- `L` - Leontief inverse matrix
- `Y` - Final demand matrix
- `x` - Total output vector
- `F` - Environmental extension matrix (direct impacts)
- `S` - Environmental multiplier matrix

## Testing

Tests are located in `tests/` directory with mock data in `tests/mock_mrios/`. The test suite covers:
- Core functionality with small test MRIO
- Parser tests with mock data files
- Mathematical operations
- Integration tests
- Output format validation

## Dependencies

Uses modern Python scientific stack:
- pandas >= 2.1 for data handling
- numpy >= 1.20 for numerical operations
- matplotlib for visualization
- requests for downloading data
- xlrd/openpyxl for Excel file support

## Development Setup

Project uses:
- `pyproject.toml` for configuration
- `uv` for dependency management
- `ruff` for linting and formatting
- `pytest` for testing
- `poethepoet` for task running
- Sphinx for documentation