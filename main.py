import os
import time
from tqdm import tqdm # You will need to `pip install tqdm` or `uv pip install tqdm`

def create_batches_ultimate(source_directory, files_per_batch):
    """
    Organizes files in a source directory into subfolders using the fastest possible methods.
    This version forces os.rename() to avoid slow copy-delete on network drives.
    """
    # --- 1. Input Validation ---
    if not os.path.isdir(source_directory):
        print(f"Error: Directory '{source_directory}' not found.")
        return

    if files_per_batch <= 0:
        print("Error: Number of files per batch must be greater than 0.")
        return

    # --- 2. Fast File Listing with os.scandir() ---
    print("Scanning directory for files...")
    try:
        with os.scandir(source_directory) as it:
            files_to_move = [entry.name for entry in it if entry.is_file()]
        
        # Exclude the script itself
        try:
            script_name = os.path.basename(__file__)
            if script_name in files_to_move: files_to_move.remove(script_name)
        except NameError: pass
            
    except OSError as e:
        print(f"Error accessing directory: {e}")
        return

    total_files = len(files_to_move)
    if not total_files:
        print("No files to batch in the specified directory.")
        return
        
    print(f"Found {total_files} files.")
    
    # --- 3. High-Speed Move Operation ---
    # Use a tqdm progress bar for great user feedback on large jobs.
    pbar = tqdm(total=total_files, unit="file", desc="Moving files", smoothing=0.1)

    batch_number = 1
    for i in range(0, total_files, files_per_batch):
        current_batch_files = files_to_move[i:i + files_per_batch]
        
        batch_folder_name = f"batch{batch_number}"
        batch_folder_path = os.path.join(source_directory, batch_folder_name)
        os.makedirs(batch_folder_path, exist_ok=True)
        
        pbar.set_description(f"Moving to {batch_folder_name}")
        
        for file_name in current_batch_files:
            source_path = os.path.join(source_directory, file_name)
            destination_path = os.path.join(batch_folder_path, file_name)
            
            try:
                # --- THIS IS THE CRITICAL CHANGE ---
                # Use os.rename() for an instantaneous move on the same filesystem/share.
                os.rename(source_path, destination_path)
            except Exception as e:
                # tqdm.write is a thread-safe way to print without messing up the bar
                tqdm.write(f"ERROR moving {file_name}: {e}")
            
            pbar.update(1) # Increment the progress bar for each file

        batch_number += 1

    pbar.close()
    print("\nBatching complete!")

# --- Main execution block ---
if __name__ == "__main__":
    target_dir = input("Enter the path to the directory with files: ").strip().strip('\'"')
    
    while True:
        try:
            batch_size_str = input("Enter the number of files per batch: ").strip()
            num_files_per_batch = int(batch_size_str)
            break
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    start = time.time()
    create_batches_ultimate(target_dir, num_files_per_batch)
    end = time.time()
    print(f"Total execution time: {end - start:.2f} seconds.")