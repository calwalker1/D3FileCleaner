# D3 File Cleaner

A Python script to manage video files in a directory that mirrors a media-server folder from Disguise/D3. The script identifies and retains the latest versions of video clips while deleting older versions.

## Features

- Supports `.mov` and `.png` files
- Handles multiple version formats:
  - Date-based: `vYYYYMMDD[hhmm][a-z]` (e.g., `v20240301`, `v202403011230`, `v20240301a`)
  - Numeric: `_vN` (e.g., `_v1`, `_v2`)
- Keeps a specified number of most recent versions
- Preserves files without version numbers
- Processes multiple directories in sequence
- Shows detailed file comparison before deletion
- Multiple confirmation steps for safety

## Usage

```bash
python d3_file_cleaner.py <directory> [--versions N]
```

### Arguments

- `directory`: The root directory to scan for files
- `--versions N`: (Optional) Number of versions to keep. If not provided, you'll be prompted.

## Process

1. Scans the specified directory and all subdirectories
2. For each directory:
   - Groups files by base name
   - Shows which files will be kept and deleted
   - Requires confirmation before deletion
3. Shows a final summary of all deletions

## Safety Features

- Multiple confirmation steps before deletion
- Shows exactly which files will be kept and deleted
- Requires typing "delete" to proceed
- Final sanity check requiring the exact number of files
- Automatically preserves unversioned files
- Must keep at least 1 version of each file

## Notes

- Files without version numbers are always preserved
- Script automatically skips directories that don't need changes
- Process stops if deletion is cancelled in any directory
- Shows total space saved across all directories 