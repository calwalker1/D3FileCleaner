# D3 File Cleaner

A script to delete MOV/PNGs from a directory while retaining the latest version (simmilar to 'manage old media' function in Disguise).

## Features

- Supports both `.mov` and `.png` files
- Identifies files with version dates in the format vYYYYMMDD (plus letter suffix support)
- Keeps a specified number of most recent versions
- Automatically preserves files without version numbers
- Processes multiple directories in sequence
- Automatically skips directories that don't need changes
- Provides detailed summaries of files to be kept and deleted
- Shows total space saved across all directories
- Multiple confirmation steps before deletion

## Usage

```bash
python3 d3_file_cleaner.py <directory> [--versions N]
```

### Arguments

- `directory`: The root directory to scan for files
- `--versions N`: (Optional) Number of versions to keep. If not provided, you'll be prompted to enter this value.

### Process Flow

1. The script scans the specified directory and all its subdirectories
2. For each directory:
   - Scans for `.mov` and `.png` files
   - Groups files by their base name (everything before the version number)
   - Identifies the most recent versions to keep
   - If no files need to be deleted, automatically moves to the next directory
   - If files need to be deleted:
     - Shows a list of files to be kept and deleted
     - Requires confirmation before proceeding
     - After deletion, asks if you want to continue to the next directory
3. Shows a final summary of all deletions across all directories

### Confirmation Steps

When files need to be deleted, the script requires multiple confirmations:

1. Shows a list of files to be kept and deleted
2. Requires typing "delete" to proceed
3. Requires entering the exact number of files to be deleted as a final sanity check

### Example Output

```
Found 3 subdirectories to process
========================================

Processing directory 1 of 3
Processing directory: /path/to/dir1
No files need to be deleted.
Moving to next directory...

Processing directory 2 of 3
Processing directory: /path/to/dir2
[shows files to delete]
[confirmation steps]
[deletion summary]

Press 'Y' to continue to the next directory, or 'N' to stop: Y

Processing directory 3 of 3
Processing directory: /path/to/dir3
No files need to be deleted.

========================================

Final Summary:
Total files deleted across all directories: 15
Total space saved across all directories: 1.5 GB
========================================
```

## Requirements

- Python 3.6 or higher
- No external dependencies required

## Safety Features

- Multiple confirmation steps before deletion
- Shows exactly which files will be kept and deleted
- Requires typing "delete" to proceed
- Final sanity check requiring the exact number of files to be deleted
- Automatically preserves files without version numbers
- Must keep at least 1 version of each file
- Shows total space to be saved before deletion
- Provides a final summary of all actions taken

## Notes

- Files without version numbers (e.g., `clip.mov`) are always preserved
- The script will automatically skip directories that don't need any changes
- You can stop the process at any time by choosing not to continue to the next directory
- If you cancel deletion in any directory, the entire process will stop and show a summary of actions taken up to that point 