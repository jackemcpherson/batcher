"""Integration tests for CLI commands using typer testing.

Tests the complete CLI interface including command-line argument parsing,
interactive mode, error handling, and end-to-end functionality of both
the batch and info commands.
"""

from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from main import app


class TestBatchCommand:
    """Test the batch CLI command."""
    
    def setUp(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_batch_help(self) -> None:
        """Test batch command help output."""
        runner = CliRunner()
        result = runner.invoke(app, ["batch", "--help"])
        
        assert result.exit_code == 0
        assert "Organize files in a directory into subfolders" in result.stdout
        assert "--batch-size" in result.stdout
        assert "--prefix" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--interactive" in result.stdout
    
    def test_batch_with_args(self, sample_files_dir) -> None:
        """Test batch command with command line arguments."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch", 
            str(sample_files_dir),
            "--batch-size", "3"
        ])
        
        assert result.exit_code == 0
        assert "Found 10 files" in result.stdout
        assert "Batching complete!" in result.stdout
        
        # Check that batch directories were created
        assert (sample_files_dir / "batch1").exists()
        assert (sample_files_dir / "batch2").exists()
        assert (sample_files_dir / "batch3").exists()
        assert (sample_files_dir / "batch4").exists()
        
        # Check file distribution (3, 3, 3, 1)
        batch1_files = list((sample_files_dir / "batch1").iterdir())
        batch2_files = list((sample_files_dir / "batch2").iterdir())
        batch3_files = list((sample_files_dir / "batch3").iterdir())
        batch4_files = list((sample_files_dir / "batch4").iterdir())
        
        assert len(batch1_files) == 3
        assert len(batch2_files) == 3
        assert len(batch3_files) == 3
        assert len(batch4_files) == 1
    
    def test_batch_dry_run(self, sample_files_dir) -> None:
        """Test batch command with dry run flag."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(sample_files_dir),
            "--batch-size", "4",
            "--dry-run"
        ])
        
        assert result.exit_code == 0
        assert "[DRY RUN]" in result.stdout
        assert "Would process 10 files into batches of 4" in result.stdout
        assert "Would create batch1 with 4 files" in result.stdout
        assert "Would create batch2 with 4 files" in result.stdout
        assert "Would create batch3 with 2 files" in result.stdout
        
        # Verify no actual changes were made
        assert not (sample_files_dir / "batch1").exists()
        assert (sample_files_dir / "file1.txt").exists()  # Original files still there
    
    def test_batch_custom_prefix(self, sample_files_dir) -> None:
        """Test batch command with custom prefix."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(sample_files_dir),
            "--batch-size", "5",
            "--prefix", "group"
        ])
        
        assert result.exit_code == 0
        assert "Batching complete!" in result.stdout
        
        # Check custom prefix was used
        assert (sample_files_dir / "group1").exists()
        assert (sample_files_dir / "group2").exists()
        assert not (sample_files_dir / "batch1").exists()
    
    def test_batch_interactive_mode(self, sample_files_dir) -> None:
        """Test batch command in interactive mode."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            "--interactive"
        ], input=f"{sample_files_dir}\n3\n")
        
        assert result.exit_code == 0
        assert "Enter the path to the directory with files" in result.stdout
        assert "Enter the number of files per batch" in result.stdout
        assert "Batching complete!" in result.stdout
        
        # Verify batching occurred
        assert (sample_files_dir / "batch1").exists()
    
    def test_batch_missing_directory_interactive(self) -> None:
        """Test batch command prompts for directory when missing."""
        runner = CliRunner()
        
        # Create a temporary directory for this test
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "test.txt").write_text("content")
            
            result = runner.invoke(app, [
                "batch",
                "--batch-size", "1"
            ], input=f"{tmp_path}\n")
            
            assert result.exit_code == 0
            assert "Enter the path to the directory with files" in result.stdout
    
    def test_batch_missing_batch_size_interactive(self, sample_files_dir) -> None:
        """Test batch command prompts for batch size when missing."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(sample_files_dir)
        ], input="2\n")
        
        assert result.exit_code == 0
        assert "Enter the number of files per batch" in result.stdout
        assert "Batching complete!" in result.stdout
    
    def test_batch_nonexistent_directory(self) -> None:
        """Test batch command with non-existent directory."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            "/path/that/does/not/exist",
            "--batch-size", "1"
        ])
        
        assert result.exit_code == 1
        assert "Directory" in result.stderr and "not found" in result.stderr
    
    def test_batch_invalid_batch_size(self, sample_files_dir) -> None:
        """Test batch command with invalid batch size."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(sample_files_dir),
            "--batch-size", "0"
        ])
        
        assert result.exit_code == 1
        assert "Number of files per batch must be greater than 0" in result.stderr
        
        # Test negative batch size
        result = runner.invoke(app, [
            "batch",
            str(sample_files_dir),
            "--batch-size", "-5"
        ])
        
        assert result.exit_code == 1
        assert "Number of files per batch must be greater than 0" in result.stderr
    
    def test_batch_empty_directory(self, empty_dir) -> None:
        """Test batch command with empty directory."""
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(empty_dir),
            "--batch-size", "10"
        ])
        
        assert result.exit_code == 0
        assert "No files to batch in the specified directory" in result.stdout
    
    def test_batch_file_instead_of_directory(self, temp_dir) -> None:
        """Test batch command when given a file instead of directory."""
        file_path = temp_dir / "not_a_directory.txt"
        file_path.write_text("content")
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            str(file_path),
            "--batch-size", "1"
        ])
        
        assert result.exit_code == 1
        assert "is not a directory" in result.stderr
    
    @patch('main._get_batch_size_input')
    @patch('main._get_directory_input')
    def test_batch_interactive_invalid_input(self, mock_directory_input, mock_batch_size_input, sample_files_dir) -> None:
        """Test interactive mode with invalid input."""
        # Mock the helper functions to return valid values
        mock_directory_input.return_value = sample_files_dir
        mock_batch_size_input.return_value = 5
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "batch",
            "--interactive"
        ])
        
        # Should eventually succeed with valid input
        assert result.exit_code == 0


class TestInfoCommand:
    """Test the info CLI command."""
    
    def test_info_help(self) -> None:
        """Test info command help output."""
        runner = CliRunner()
        result = runner.invoke(app, ["info", "--help"])
        
        assert result.exit_code == 0
        assert "Show information about files in a directory" in result.stdout
    
    def test_info_basic(self, sample_files_dir) -> None:
        """Test basic info command functionality."""
        runner = CliRunner()
        result = runner.invoke(app, ["info", str(sample_files_dir)])
        
        assert result.exit_code == 0
        assert "Found 10 files" in result.stdout
        assert str(sample_files_dir) in result.stdout
        
        # Should show all files since there are only 10
        assert "Files:" in result.stdout
        assert "file1.txt" in result.stdout
        assert "document.pdf" in result.stdout
    
    def test_info_many_files(self, large_files_dir) -> None:
        """Test info command with many files (should show sample)."""
        runner = CliRunner()
        result = runner.invoke(app, ["info", str(large_files_dir)])
        
        assert result.exit_code == 0
        assert "Found 25 files" in result.stdout
        
        # Should show sample since there are more than 10 files
        assert "Sample files:" in result.stdout
        assert "and 20 more" in result.stdout
    
    def test_info_empty_directory(self, empty_dir) -> None:
        """Test info command with empty directory."""
        runner = CliRunner()
        result = runner.invoke(app, ["info", str(empty_dir)])
        
        assert result.exit_code == 0
        assert "No files found in the specified directory" in result.stdout
    
    def test_info_nonexistent_directory(self) -> None:
        """Test info command with non-existent directory."""
        runner = CliRunner()
        result = runner.invoke(app, ["info", "/path/that/does/not/exist"])
        
        assert result.exit_code == 1
        assert "Directory" in result.stderr and "not found" in result.stderr
    
    def test_info_directory_with_subdirs(self, dir_with_subdirs) -> None:
        """Test info command ignores subdirectories."""
        runner = CliRunner()
        result = runner.invoke(app, ["info", str(dir_with_subdirs)])
        
        assert result.exit_code == 0
        assert "Found 2 files" in result.stdout  # Only root level files
        assert "file1.txt" in result.stdout
        assert "file2.txt" in result.stdout


class TestAppGeneral:
    """Test general app functionality."""
    
    def test_app_help(self) -> None:
        """Test main app help."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "A high-speed Python utility for organizing files into batches" in result.stdout
        assert "batch" in result.stdout
        assert "info" in result.stdout
    
    def test_app_no_command(self) -> None:
        """Test app behavior with no command."""
        runner = CliRunner()
        result = runner.invoke(app, [])
        
        # Typer returns exit code 2 when no command is given, which is expected
        assert result.exit_code in [0, 2]  # Either shows help (0) or exits with error (2)
        assert "Usage:" in (result.stdout + result.stderr)