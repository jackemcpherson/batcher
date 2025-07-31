# Batcher

A high-speed Python utility for organizing a large number of files into subfolders.

## Why Batcher?

Moving thousands of files, especially on a network drive, can be incredibly slow. Standard file move operations often perform a "copy-then-delete" action, which is inefficient for large quantities of files over a network.

Batcher solves this by forcing the use of `os.rename()`, which is an atomic (and thus instantaneous) operation when the source and destination are on the same filesystem or network share. This makes it ideal for quickly organizing massive datasets, logs, or any collection of files into manageable batches.

## Features

- **Extremely Fast:** Uses `os.rename()` for instantaneous file moves on the same filesystem.
- **Optimized Scanning:** Employs `os.scandir()` for efficient directory listing.
- **User-Friendly:** A simple command-line interface guides you through the process.
- **Great Feedback:** A `tqdm` progress bar shows real-time progress, which is essential for large jobs.
- **Robust:** Handles input validation and file system errors gracefully.

## Requirements

- Python 3.7+
- [tqdm](https://pypi.org/project/tqdm/)

Install tqdm with:

```bash
pip install tqdm
```

Or, if using [uv](https://github.com/astral-sh/uv):

```bash
uv pip install tqdm
```

## Usage

1. Save the script as `main.py`.
2. Run it from your terminal:

    ```bash
    python main.py
    ```

3. When prompted, enter the full path to the directory containing the files you want to batch.
4. Enter the desired number of files per batch.

The script will create new subfolders named `batch1`, `batch2`, etc., inside your target directory and move the files into them.

## Example

Suppose you have 1,000 files in `C:\Users\you\Documents\photos` and want 200 files per batch:

```bash
Enter the path to the directory with files: C:\Users\you\Documents\photos
Enter the number of files per batch: 200
```

This will create `batch1`, `batch2`, ..., `batch5` inside the `photos` directory, each containing 200 files.

## Notes

- The script only processes files directly within the specified directory; it ignores any existing subfolders.
- The script will not batch itself if it's located in the target directory.
- If batch folders (`batch1`, etc.) already exist, the script will add new files to them.
- File moves are only instantaneous if the source and destination are on the same filesystem/network share.

## License

MIT License
