import os
import time
from pathlib import Path
from typing import Optional

import typer
from tqdm import tqdm
from typing_extensions import Annotated

app = typer.Typer(help="A high-speed Python utility for organizing files into batches.")


def get_files_to_batch(source_directory: Path) -> list[str]:
    """Get list of files to batch, excluding this script."""
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
    """Validate that the directory exists."""
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
    """Process files into batches."""
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


@app.command()
def batch(
    directory: Annotated[Path, typer.Argument(help="Directory containing files to batch")] = None,
    batch_size: Annotated[int, typer.Option("--batch-size", "-b", help="Number of files per batch")] = None,
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
    
    # Interactive mode or missing arguments
    if interactive or directory is None:
        if directory is None:
            directory_str = typer.prompt("Enter the path to the directory with files").strip().strip('\'"')
            directory = Path(directory_str)
    
    if interactive or batch_size is None:
        if batch_size is None:
            while True:
                try:
                    batch_size = typer.prompt("Enter the number of files per batch", type=int)
                    break
                except typer.BadParameter:
                    typer.echo("Invalid input. Please enter a whole number.")
    
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