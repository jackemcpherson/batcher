import os
import time
from pathlib import Path

import typer
from tqdm import tqdm
from typing_extensions import Annotated

app = typer.Typer(help="A high-speed Python utility for organizing files into batches.")


def get_files_to_batch(source_directory: Path) -> list[str]:
    """Get list of files to batch from source directory.
    
    Scans the specified directory for files, excluding the script itself
    and any subdirectories. Only processes files at the root level.
    
    Args:
        source_directory: Directory path to scan for files.
        
    Returns:
        List of filenames found in the directory, excluding script itself.
        
    Raises:
        typer.Exit: If directory cannot be accessed due to OS errors.
    """
    try:
        with os.scandir(source_directory) as it:
            files_to_move = [entry.name for entry in it if entry.is_file()]
        
        # Exclude the script itself
        script_name = Path(__file__).name
        files_to_move = [f for f in files_to_move if f != script_name]
        
        return files_to_move
            
    except OSError as e:
        typer.echo(f"Error accessing directory: {e}", err=True)
        raise typer.Exit(1)


def validate_directory(directory: Path) -> Path:
    """Validate that the provided path is an existing directory.
    
    Checks if the path exists and is a directory, not a file.
    
    Args:
        directory: Path to validate as an existing directory.
        
    Returns:
        The validated directory path if checks pass.
        
    Raises:
        typer.Exit: If directory doesn't exist or is not a directory.
    """
    if not directory.exists():
        typer.echo(f"Error: Directory '{directory}' not found.", err=True)
        raise typer.Exit(1)
    
    if not directory.is_dir():
        typer.echo(f"Error: '{directory}' is not a directory.", err=True)
        raise typer.Exit(1)
    
    return directory


def process_batches(
    files: list[str], 
    source_directory: Path, 
    files_per_batch: int,
    batch_prefix: str = "batch",
    dry_run: bool = False
) -> None:
    """Process files into organized batch subdirectories.
    
    Moves files from the source directory into numbered batch subdirectories,
    with each batch containing up to the specified number of files. Uses
    high-speed os.rename() for same-filesystem moves.
    
    Args:
        files: List of filenames to process into batches.
        source_directory: Source directory containing the files.
        files_per_batch: Maximum number of files per batch directory.
        batch_prefix: Prefix for batch directory names (default: "batch").
        dry_run: If True, show what would be done without moving files.
        
    Returns:
        None
        
    Raises:
        None - Handles individual file move errors gracefully.
    """
    total_files = len(files)
    
    if dry_run:
        typer.echo(f"[DRY RUN] Would process {total_files} files into batches of {files_per_batch}")
        num_batches = (total_files + files_per_batch - 1) // files_per_batch
        for i in range(num_batches):
            batch_start = i * files_per_batch
            batch_end = min(batch_start + files_per_batch, total_files)
            batch_size = batch_end - batch_start
            typer.echo(f"[DRY RUN] Would create {batch_prefix}{i+1} with {batch_size} files")
        return
    
    pbar = tqdm(total=total_files, unit="file", desc="Moving files", smoothing=0.1)

    batch_number = 1
    for i in range(0, total_files, files_per_batch):
        current_batch_files = files[i:i + files_per_batch]
        
        batch_folder_name = f"{batch_prefix}{batch_number}"
        batch_folder_path = source_directory / batch_folder_name
        batch_folder_path.mkdir(exist_ok=True)
        
        pbar.set_description(f"Moving to {batch_folder_name}")
        
        for file_name in current_batch_files:
            source_path = source_directory / file_name
            destination_path = batch_folder_path / file_name
            
            try:
                os.rename(source_path, destination_path)
            except OSError as e:
                tqdm.write(f"ERROR moving {file_name}: {e}")
            
            pbar.update(1)

        batch_number += 1

    pbar.close()
    typer.echo("\nBatching complete!")


def _get_directory_input(directory: Path | None, interactive: bool) -> Path:
    """Get directory from user input when missing or in interactive mode.
    
    Args:
        directory: Current directory value or None.
        interactive: Whether running in interactive mode.
        
    Returns:
        Valid directory path from user input.
    """
    if interactive or directory is None:
        directory_str = typer.prompt("Enter the path to the directory with files").strip().strip('\'"')
        directory = Path(directory_str)
    return directory


def _get_batch_size_input(batch_size: int | None, interactive: bool) -> int:
    """Get batch size from user input when missing or in interactive mode.
    
    Args:
        batch_size: Current batch size value or None.
        interactive: Whether running in interactive mode.
        
    Returns:
        Valid batch size from user input.
    """
    if interactive or batch_size is None:
        while True:
            try:
                return typer.prompt("Enter the number of files per batch", type=int)
            except typer.BadParameter:
                typer.echo("Invalid input. Please enter a whole number.")
    return batch_size


@app.command()
def batch(
    directory: Annotated[Path | None, typer.Argument(help="Directory containing files to batch")] = None,
    batch_size: Annotated[int | None, typer.Option("--batch-size", "-b", help="Number of files per batch")] = None,
    batch_prefix: Annotated[str, typer.Option("--prefix", "-p", help="Prefix for batch folder names")] = "batch",
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Show what would be done without actually moving files")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Use interactive mode for input")] = False,
) -> None:
    """
    Organize files in a directory into subfolders using high-speed operations.
    
    This tool uses os.rename() for instantaneous file moves on the same filesystem,
    making it ideal for organizing large numbers of files quickly.
    """
    start_time = time.time()
    
    # Get inputs from user if needed
    directory = _get_directory_input(directory, interactive)
    batch_size = _get_batch_size_input(batch_size, interactive)
    
    # Validate inputs
    directory = validate_directory(directory)
    
    if batch_size <= 0:
        typer.echo("Error: Number of files per batch must be greater than 0.", err=True)
        raise typer.Exit(1)
    
    # Get files to process
    typer.echo("Scanning directory for files...")
    files_to_move = get_files_to_batch(directory)
    
    total_files = len(files_to_move)
    if not total_files:
        typer.echo("No files to batch in the specified directory.")
        return
        
    typer.echo(f"Found {total_files} files.")
    
    # Process batches
    process_batches(files_to_move, directory, batch_size, batch_prefix, dry_run)
    
    # Show timing
    end_time = time.time()
    typer.echo(f"Total execution time: {end_time - start_time:.2f} seconds.")


@app.command()
def info(
    directory: Annotated[Path, typer.Argument(help="Directory to analyze")]
) -> None:
    """Show information about files in a directory without processing them."""
    directory = validate_directory(directory)
    
    typer.echo("Scanning directory for files...")
    files = get_files_to_batch(directory)
    
    total_files = len(files)
    if not total_files:
        typer.echo("No files found in the specified directory.")
        return
    
    typer.echo(f"Found {total_files} files in '{directory}'")
    
    # Show some sample files
    if total_files <= 10:
        typer.echo("Files:")
        for file in files:
            typer.echo(f"  - {file}")
    else:
        typer.echo("Sample files:")
        for file in files[:5]:
            typer.echo(f"  - {file}")
        typer.echo(f"  ... and {total_files - 5} more")


if __name__ == "__main__":
    app()