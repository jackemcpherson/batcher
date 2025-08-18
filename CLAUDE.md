# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Batcher is a high-speed Python CLI utility for organizing large numbers of files into subfolders using atomic `os.rename()` operations. Built with Typer framework for modern CLI experience.

## Development Commands

### Dependencies and Environment
- **Install dependencies**: `uv sync`
- **Install development dependencies**: `uv sync --group test`

### Testing
- **Run all tests**: `uv run pytest`
- **Run tests with coverage**: `uv run pytest --cov`
- **Run specific test file**: `uv run pytest tests/test_core_functions.py`
- **Run specific test**: `uv run pytest tests/test_core_functions.py::TestGetFilesToBatch::test_get_files_success`

### Running the Application
- **Run main CLI**: `uv run python main.py`
- **Interactive mode**: `uv run python main.py --interactive`
- **Dry run mode**: `uv run python main.py /path/to/dir --batch-size 100 --dry-run`
- **Get directory info**: `uv run python main.py info /path/to/dir`

## Architecture

### Core Components
- **main.py**: Single-file CLI application built with Typer
- **CLI Commands**:
  - `batch`: Main command for batching files with options for batch size, prefix, dry-run, and interactive mode
  - `info`: Analysis command to show file information without processing

### Key Functions
- **get_files_to_batch()**: Scans directory using `os.scandir()` for performance, excludes script itself and subdirectories
- **validate_directory()**: Input validation for directory paths
- **process_batches()**: Core batching logic using `os.rename()` for atomic file moves with tqdm progress bar

### Testing Structure
- **tests/conftest.py**: Pytest fixtures for temporary directories and test file setups
- **tests/test_core_functions.py**: Unit tests for core functions
- **tests/test_cli_commands.py**: CLI integration tests using Typer's testing utilities
- **tests/test_edge_cases.py**: Edge case and error handling tests

## Key Design Patterns

- Uses `os.scandir()` instead of `os.listdir()` for better performance
- Atomic file operations via `os.rename()` for speed and reliability
- Progress tracking with `tqdm` for user feedback on large operations
- Typer-based CLI with type hints and automatic help generation
- Comprehensive test coverage with pytest fixtures for different scenarios

## Performance Considerations

- Optimized for network drives where `os.rename()` is instantaneous vs copy-then-delete
- Only processes files in the target directory (ignores subdirectories)
- Uses Path objects for cross-platform compatibility