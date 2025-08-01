"""Tests for edge cases and error conditions."""

import os
import stat
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from main import app, get_files_to_batch, process_batches


class TestFilePermissionErrors:
    """Test handling of file permission issues."""
    
    @pytest.mark.skipif(os.name == "nt", reason="Permission tests don't work the same on Windows")
    def test_readonly_source_file(self, temp_dir):
        """Test handling of read-only source files."""
        # Create a file and make it read-only
        readonly_file = temp_dir / "readonly.txt"
        readonly_file.write_text("content")
        readonly_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # Read-only
        
        # Create a normal file too
        normal_file = temp_dir / "normal.txt"
        normal_file.write_text("content")
        
        files = ["readonly.txt", "normal.txt"]
        
        # Should handle the error gracefully
        process_batches(files, temp_dir, 1, "batch", dry_run=False)
        
        # Normal file should be moved, readonly might fail but shouldn't crash
        assert (temp_dir / "batch1").exists() or (temp_dir / "batch2").exists()
    
    def test_permission_denied_target_directory(self, temp_dir):
        """Test handling when target batch directory can't be created."""
        files = ["file1.txt"]
        (temp_dir / "file1.txt").write_text("content")
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            # Should handle the error gracefully
            with pytest.raises(PermissionError):
                process_batches(files, temp_dir, 1, "batch", dry_run=False)


class TestFilesystemEdgeCases:
    """Test various filesystem edge cases."""
    
    def test_very_long_filename(self, temp_dir):
        """Test handling of very long filenames."""
        # Create a file with a very long name (but within typical limits)
        long_name = "a" * 100 + ".txt"  # Reduced length for Windows compatibility
        long_file = temp_dir / long_name
        
        try:
            long_file.write_text("content")
            files = [long_name]
            
            process_batches(files, temp_dir, 1, "batch", dry_run=False)
            
            # Check if file was moved successfully or if there was an error
            if (temp_dir / "batch1" / long_name).exists():
                assert True  # File moved successfully
            else:
                # On Windows, very long paths might fail - that's expected behavior
                assert (temp_dir / long_name).exists()  # Original file still exists
        except OSError:
            # Skip test if OS doesn't support such long names
            pytest.skip("OS doesn't support long filenames")
    
    def test_files_with_special_characters(self, temp_dir):
        """Test handling files with special characters in names."""
        special_files = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
            "file(with)parentheses.txt",
            "file[with]brackets.txt"
        ]
        
        # Create files (skip any that the OS doesn't support)
        created_files = []
        for filename in special_files:
            try:
                (temp_dir / filename).write_text("content")
                created_files.append(filename)
            except OSError:
                # Skip files with characters not supported by OS
                continue
        
        if created_files:
            process_batches(created_files, temp_dir, 2, "batch", dry_run=False)
            
            # Verify files were moved
            batch1_files = list((temp_dir / "batch1").iterdir())
            assert len(batch1_files) > 0
    
    def test_unicode_filenames(self, temp_dir):
        """Test handling of Unicode filenames."""
        unicode_files = [
            "文件.txt",  # Chinese
            "файл.txt",  # Russian  
            "αρχείο.txt",  # Greek
            "ファイル.txt",  # Japanese
            "🎉emoji🎊.txt"  # Emoji
        ]
        
        # Create files (skip any that the OS doesn't support)
        created_files = []
        for filename in unicode_files:
            try:
                (temp_dir / filename).write_text("content")
                created_files.append(filename)
            except (OSError, UnicodeError):
                # Skip files with characters not supported by OS
                continue
        
        if created_files:
            process_batches(created_files, temp_dir, 1, "batch", dry_run=False)
            
            # Verify at least one file was moved
            batch_dirs = [d for d in temp_dir.iterdir() if d.is_dir() and d.name.startswith("batch")]
            assert len(batch_dirs) > 0


class TestConcurrencyAndRaceConditions:
    """Test potential concurrency issues."""
    
    def test_simultaneous_batch_creation(self, temp_dir):
        """Test behavior when batch directories are created simultaneously."""
        files = ["file1.txt", "file2.txt"]
        for filename in files:
            (temp_dir / filename).write_text("content")
        
        # Mock mkdir to simulate race condition
        original_mkdir = Path.mkdir
        call_count = 0
        
        def mock_mkdir(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call succeeds
                return original_mkdir(self, *args, **kwargs) 
            else:
                # Simulate directory already exists
                if kwargs.get('exist_ok', False):
                    return
                raise FileExistsError("Directory already exists")
        
        with patch.object(Path, 'mkdir', mock_mkdir):
            process_batches(files, temp_dir, 1, "batch", dry_run=False)
        
        # Should handle the race condition gracefully
        assert (temp_dir / "batch1").exists()


class TestMemoryAndPerformance:
    """Test memory usage and performance edge cases."""
    
    def test_very_large_file_list(self, temp_dir):
        """Test handling of very large number of files."""
        # Create many files (but not so many as to be slow in tests)
        num_files = 1000
        files = []
        
        for i in range(num_files):
            filename = f"file_{i:04d}.txt"
            (temp_dir / filename).write_text(f"content {i}")
            files.append(filename)
        
        # Process in dry run mode to avoid actually moving 1000 files
        process_batches(files, temp_dir, 100, "batch", dry_run=True)
        
        # Should complete without memory issues
        assert len(files) == num_files
    
    def test_batch_size_equals_file_count(self, sample_files_dir):
        """Test when batch size equals total file count."""
        files = get_files_to_batch(sample_files_dir)
        total_files = len(files)
        
        process_batches(files, sample_files_dir, total_files, "batch", dry_run=False)
        
        # Should create exactly one batch with all files
        assert (sample_files_dir / "batch1").exists()
        assert not (sample_files_dir / "batch2").exists()
        
        batch1_files = list((sample_files_dir / "batch1").iterdir())
        assert len(batch1_files) == total_files
    
    def test_batch_size_larger_than_file_count(self, sample_files_dir):
        """Test when batch size is larger than total file count."""
        files = get_files_to_batch(sample_files_dir)
        total_files = len(files)
        
        process_batches(files, sample_files_dir, total_files + 10, "batch", dry_run=False)
        
        # Should create exactly one batch with all files
        assert (sample_files_dir / "batch1").exists()
        assert not (sample_files_dir / "batch2").exists()
        
        batch1_files = list((sample_files_dir / "batch1").iterdir())
        assert len(batch1_files) == total_files


class TestSymlinksAndSpecialFiles:
    """Test handling of symlinks and special files."""
    
    @pytest.mark.skipif(os.name == "nt", reason="Symlinks require special permissions on Windows")
    def test_symlink_handling(self, temp_dir):
        """Test that symlinks are treated as files."""
        # Create a regular file
        regular_file = temp_dir / "regular.txt"
        regular_file.write_text("content")
        
        # Create a symlink to it
        symlink_file = temp_dir / "symlink.txt"
        symlink_file.symlink_to(regular_file)
        
        files = get_files_to_batch(temp_dir)
        
        # Both regular file and symlink should be included
        assert "regular.txt" in files
        assert "symlink.txt" in files
    
    def test_empty_files(self, temp_dir):
        """Test handling of empty files."""
        empty_files = ["empty1.txt", "empty2.txt", "empty3.txt"]
        
        for filename in empty_files:
            (temp_dir / filename).touch()  # Create empty file
        
        process_batches(empty_files, temp_dir, 2, "batch", dry_run=False)
        
        # Empty files should be moved like any other files
        assert (temp_dir / "batch1").exists()
        assert (temp_dir / "batch2").exists()
        
        batch1_files = list((temp_dir / "batch1").iterdir())
        batch2_files = list((temp_dir / "batch2").iterdir())
        
        assert len(batch1_files) == 2
        assert len(batch2_files) == 1


class TestCliEdgeCases:
    """Test CLI edge cases and error conditions."""
    
    def test_batch_with_quotes_in_path(self, temp_dir):
        """Test handling paths with quotes."""
        # Create a subdirectory with quotes in the name
        quoted_dir = temp_dir / "dir'with'quotes"
        quoted_dir.mkdir()
        (quoted_dir / "file.txt").write_text("content")
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(quoted_dir),
            "--batch-size", "1"
        ])
        
        assert result.exit_code == 0
        assert "Batching complete!" in result.stdout
    
    def test_batch_very_large_batch_size(self, sample_files_dir):
        """Test batch command with extremely large batch size."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(sample_files_dir),
            "--batch-size", "999999"
        ])
        
        assert result.exit_code == 0
        assert "Batching complete!" in result.stdout
        
        # Should create one batch with all files
        assert (sample_files_dir / "batch1").exists()
        assert not (sample_files_dir / "batch2").exists()
    
    def test_interactive_mode_keyboard_interrupt(self, sample_files_dir):
        """Test handling of KeyboardInterrupt in interactive mode."""
        runner = CliRunner()
        
        # Simulate user hitting Ctrl+C during input
        with patch('typer.prompt', side_effect=KeyboardInterrupt):
            result = runner.invoke(app, [
                "batch",
                "--interactive"
            ])
            
            # Should exit gracefully (typer handles KeyboardInterrupt)
            assert result.exit_code != 0 or "Aborted" in result.stdout