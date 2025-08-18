"""Pytest configuration and test fixtures for batcher application.

Provides reusable fixtures for creating temporary directories with various
file configurations for comprehensive testing scenarios.
"""

import tempfile
from pathlib import Path
from typing import Generator
import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_files_dir(temp_dir: Path) -> Path:
    """Create a directory with sample files for testing."""
    # Create various test files
    test_files = [
        "file1.txt",
        "file2.txt", 
        "file3.txt",
        "file4.txt",
        "file5.txt",
        "document.pdf",
        "image.jpg",
        "data.csv",
        "script.py",
        "readme.md"
    ]
    
    for filename in test_files:
        (temp_dir / filename).write_text(f"Content of {filename}")
    
    return temp_dir


@pytest.fixture
def large_files_dir(temp_dir: Path) -> Path:
    """Create a directory with many files for testing large batches."""
    # Create 25 test files
    for i in range(1, 26):
        (temp_dir / f"file_{i:03d}.txt").write_text(f"Content of file {i}")
    
    return temp_dir


@pytest.fixture
def empty_dir(temp_dir: Path) -> Path:
    """Create an empty directory for testing."""
    empty_path = temp_dir / "empty"
    empty_path.mkdir()
    return empty_path


@pytest.fixture
def dir_with_subdirs(temp_dir: Path) -> Path:
    """Create a directory with files and subdirectories."""
    # Create files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    # Create subdirectories with files
    subdir1 = temp_dir / "subdir1"
    subdir1.mkdir()
    (subdir1 / "nested_file.txt").write_text("nested content")
    
    subdir2 = temp_dir / "subdir2"
    subdir2.mkdir()
    
    return temp_dir