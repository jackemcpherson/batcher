"""Unit tests for core batcher functions.

Tests the individual functions that form the core logic of the batcher
application, including file discovery, directory validation, and the
batch processing functionality with various configurations.
"""

import pytest
from unittest.mock import patch

import typer

from main import (
    get_files_to_batch,
    validate_directory,
    process_batches
)


class TestGetFilesToBatch:
    """Test the get_files_to_batch function."""
    
    def test_get_files_success(self, sample_files_dir) -> None:
        """Test successful file discovery."""
        files = get_files_to_batch(sample_files_dir)
        
        # Should exclude main.py (script itself) but include all other files
        expected_files = {
            "file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt",
            "document.pdf", "image.jpg", "data.csv", "script.py", "readme.md"
        }
        
        assert set(files) == expected_files
        assert len(files) == 10
    
    def test_get_files_excludes_script(self, temp_dir) -> None:
        """Test that the script itself is excluded from file list."""
        # Create some files including main.py
        (temp_dir / "file1.txt").write_text("content")
        (temp_dir / "main.py").write_text("# This is the script")
        (temp_dir / "file2.txt").write_text("content")
        
        files = get_files_to_batch(temp_dir)
        
        assert "main.py" not in files
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert len(files) == 2
    
    def test_get_files_ignores_directories(self, dir_with_subdirs) -> None:
        """Test that subdirectories are ignored."""
        files = get_files_to_batch(dir_with_subdirs)
        
        # Should only include files in root, not subdirectories
        assert set(files) == {"file1.txt", "file2.txt"}
        assert len(files) == 2
    
    def test_get_files_empty_directory(self, empty_dir) -> None:
        """Test behavior with empty directory."""
        files = get_files_to_batch(empty_dir)
        
        assert files == []
    
    def test_get_files_nonexistent_directory(self, temp_dir) -> None:
        """Test behavior with non-existent directory."""
        nonexistent = temp_dir / "does_not_exist"
        
        with pytest.raises(typer.Exit):
            get_files_to_batch(nonexistent)
    
    @patch('os.scandir')
    def test_get_files_oserror(self, mock_scandir, temp_dir) -> None:
        """Test handling of OS errors during scanning."""
        mock_scandir.side_effect = OSError("Permission denied")
        
        with pytest.raises(typer.Exit):
            get_files_to_batch(temp_dir)


class TestValidateDirectory:
    """Test the validate_directory function."""
    
    def test_validate_existing_directory(self, temp_dir) -> None:
        """Test validation of existing directory."""
        result = validate_directory(temp_dir)
        assert result == temp_dir
    
    def test_validate_nonexistent_directory(self, temp_dir) -> None:
        """Test validation of non-existent directory."""
        nonexistent = temp_dir / "does_not_exist"
        
        with pytest.raises(typer.Exit):
            validate_directory(nonexistent)
    
    def test_validate_file_not_directory(self, temp_dir) -> None:
        """Test validation when path is a file, not directory."""
        file_path = temp_dir / "not_a_dir.txt"
        file_path.write_text("content")
        
        with pytest.raises(typer.Exit):
            validate_directory(file_path)


class TestProcessBatches:
    """Test the process_batches function."""
    
    def test_process_batches_dry_run(self, temp_dir, capsys) -> None:
        """Test dry run mode doesn't move files."""
        files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"]
        
        # Create the actual files
        for filename in files:
            (temp_dir / filename).write_text("content")
        
        process_batches(files, temp_dir, 2, "batch", dry_run=True)
        
        # Check output
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "Would process 5 files into batches of 2" in captured.out
        assert "Would create batch1 with 2 files" in captured.out
        assert "Would create batch2 with 2 files" in captured.out
        assert "Would create batch3 with 1 files" in captured.out
        
        # Verify no actual batch directories were created
        assert not (temp_dir / "batch1").exists()
        assert not (temp_dir / "batch2").exists()
        assert not (temp_dir / "batch3").exists()
        
        # Verify original files still exist
        for filename in files:
            assert (temp_dir / filename).exists()
    
    def test_process_batches_actual_move(self, temp_dir) -> None:
        """Test actual file moving."""
        files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
        
        # Create the actual files
        for filename in files:
            (temp_dir / filename).write_text(f"content of {filename}")
        
        process_batches(files, temp_dir, 2, "batch", dry_run=False)
        
        # Check batch directories were created
        assert (temp_dir / "batch1").exists()
        assert (temp_dir / "batch2").exists()
        
        # Check files were moved correctly
        assert (temp_dir / "batch1" / "file1.txt").exists()
        assert (temp_dir / "batch1" / "file2.txt").exists()
        assert (temp_dir / "batch2" / "file3.txt").exists()
        assert (temp_dir / "batch2" / "file4.txt").exists()
        
        # Check original files no longer exist in root
        assert not (temp_dir / "file1.txt").exists()
        assert not (temp_dir / "file2.txt").exists()
        assert not (temp_dir / "file3.txt").exists()
        assert not (temp_dir / "file4.txt").exists()
        
        # Verify file contents preserved
        assert (temp_dir / "batch1" / "file1.txt").read_text() == "content of file1.txt"
        assert (temp_dir / "batch2" / "file4.txt").read_text() == "content of file4.txt"
    
    def test_process_batches_custom_prefix(self, temp_dir) -> None:
        """Test using custom batch prefix."""
        files = ["file1.txt", "file2.txt", "file3.txt"]
        
        # Create the actual files
        for filename in files:
            (temp_dir / filename).write_text("content")
        
        process_batches(files, temp_dir, 2, "group", dry_run=False)
        
        # Check custom prefix was used
        assert (temp_dir / "group1").exists()
        assert (temp_dir / "group2").exists()
        assert not (temp_dir / "batch1").exists()
        
        # Check files were moved
        assert (temp_dir / "group1" / "file1.txt").exists()
        assert (temp_dir / "group1" / "file2.txt").exists()
        assert (temp_dir / "group2" / "file3.txt").exists()
    
    def test_process_batches_large_batch(self, large_files_dir) -> None:
        """Test processing many files."""
        files = [f"file_{i:03d}.txt" for i in range(1, 26)]  # 25 files
        
        process_batches(files, large_files_dir, 10, "batch", dry_run=False)
        
        # Should create 3 batches: 10, 10, 5 files
        assert (large_files_dir / "batch1").exists()
        assert (large_files_dir / "batch2").exists()
        assert (large_files_dir / "batch3").exists()
        
        # Check file counts in each batch
        batch1_files = list((large_files_dir / "batch1").iterdir())
        batch2_files = list((large_files_dir / "batch2").iterdir())
        batch3_files = list((large_files_dir / "batch3").iterdir())
        
        assert len(batch1_files) == 10
        assert len(batch2_files) == 10
        assert len(batch3_files) == 5
    
    def test_process_batches_single_file(self, temp_dir) -> None:
        """Test processing single file."""
        files = ["single_file.txt"]
        (temp_dir / "single_file.txt").write_text("content")
        
        process_batches(files, temp_dir, 10, "batch", dry_run=False)
        
        assert (temp_dir / "batch1").exists()
        assert (temp_dir / "batch1" / "single_file.txt").exists()
        assert not (temp_dir / "single_file.txt").exists()
    
    @patch('os.rename')
    def test_process_batches_move_error(self, mock_rename, temp_dir, capsys) -> None:
        """Test handling of file move errors."""
        files = ["file1.txt", "file2.txt"]
        
        # Create the files
        for filename in files:
            (temp_dir / filename).write_text("content")
        
        # Mock os.rename to raise an error for first file
        mock_rename.side_effect = [OSError("Permission denied"), None]
        
        process_batches(files, temp_dir, 2, "batch", dry_run=False)
        
        # Should continue processing despite error
        captured = capsys.readouterr()
        assert "ERROR moving file1.txt: Permission denied" in captured.out
    
    def test_process_batches_existing_batch_dirs(self, temp_dir) -> None:
        """Test behavior when batch directories already exist."""
        files = ["file1.txt", "file2.txt"]
        
        # Create files and pre-existing batch directory
        for filename in files:
            (temp_dir / filename).write_text("content")
        
        existing_batch = temp_dir / "batch1"
        existing_batch.mkdir()
        (existing_batch / "existing_file.txt").write_text("existing content")
        
        process_batches(files, temp_dir, 1, "batch", dry_run=False)
        
        # Should add new files to existing batch directories
        assert (temp_dir / "batch1" / "existing_file.txt").exists()
        assert (temp_dir / "batch1" / "file1.txt").exists()
        assert (temp_dir / "batch2" / "file2.txt").exists()