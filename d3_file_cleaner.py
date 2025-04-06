#!/usr/bin/env python3
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

def get_human_readable_size(size_bytes: int) -> str:
    """
    Convert a size in bytes to a human-readable format (e.g., GB, MB).
    This makes the file sizes easier to read in the output.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

class VersionInfo:
    """
    A class to store and compare version information for files.
    Each version has a date and an optional letter suffix (e.g., 'a', 'b').
    """
    def __init__(self, date: datetime, letter: Optional[str] = None):
        self.date = date
        self.letter = letter

    def __lt__(self, other: 'VersionInfo') -> bool:
        """
        Compare two versions to determine which is older.
        First compares dates, then letters if dates are equal.
        Versions without letters are considered older than those with letters.
        """
        if self.date != other.date:
            return self.date < other.date
        # If dates are equal, compare letters
        if self.letter is None and other.letter is None:
            return False
        if self.letter is None:
            return True
        if other.letter is None:
            return False
        return self.letter < other.letter

def parse_filename(filename: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parse a filename into its components:
    - Base name (everything before the version)
    - Version number (if present)
    - Extension
    
    Supports multiple version formats:
    1. vYYYYMMDD[hhmm] (with optional time)
    2. _vN (where N is a number)
    3. vYYYYMMDD[hhmm] followed by a letter (e.g., v20240301a)
    
    Returns:
    - Base name (without version)
    - Version string (if found)
    - File extension
    """
    # Remove the extension first
    name, ext = os.path.splitext(filename)
    
    # Pattern 1: vYYYYMMDD[hhmm] with optional letter suffix
    date_pattern = r'v(\d{8})(\d{4})?([a-zA-Z])?$'
    date_match = re.search(date_pattern, name)
    if date_match:
        base = name[:date_match.start()]
        version = date_match.group(0)
        return base, version, ext
    
    # Pattern 2: _vN where N is a number
    number_pattern = r'_v(\d+)$'
    number_match = re.search(number_pattern, name)
    if number_match:
        base = name[:number_match.start()]
        version = number_match.group(0)
        return base, version, ext
    
    # No version found
    return name, None, ext

def get_version_date(version: str) -> Optional[datetime]:
    """
    Convert a version string to a datetime object.
    Supports multiple version formats:
    1. vYYYYMMDD[hhmm] (with optional time)
    2. _vN (where N is a number)
    3. vYYYYMMDD[hhmm] followed by a letter (e.g., v20240301a)
    
    Returns:
    - datetime object for date-based versions
    - None for non-date versions
    """
    # Handle _vN format
    if version.startswith('_v'):
        try:
            # Convert to a date far in the future to ensure it's kept
            return datetime(9999, 12, 31)
        except ValueError:
            return None
    
    # Handle vYYYYMMDD[hhmm] format
    try:
        # Remove any letter suffix
        version = re.sub(r'[a-zA-Z]$', '', version)
        
        if len(version) == 9:  # vYYYYMMDD
            return datetime.strptime(version[1:], '%Y%m%d')
        elif len(version) == 13:  # vYYYYMMDDhhmm
            return datetime.strptime(version[1:], '%Y%m%d%H%M')
    except ValueError:
        return None
    
    return None

def find_latest_versions(directory: str) -> Tuple[Dict[str, List[Tuple[Path, VersionInfo]]], List[Path]]:
    """
    Scan a directory for .mov and .png files and organize them by base name.
    Returns:
    - A dictionary mapping base names to lists of (file path, version info) tuples
    - A list of files that don't have version numbers (these will always be kept)
    """
    files_by_base: Dict[str, List[Tuple[Path, VersionInfo]]] = {}
    unversioned_files: List[Path] = []
    
    # Scan all .mov and .png files in the directory
    for file_path in Path(directory).glob('*.[mp][no][vg]'):
        base_name, version_info = parse_version_date(file_path.name)
        if base_name and version_info:
            # File has a version number, add it to the appropriate group
            if base_name not in files_by_base:
                files_by_base[base_name] = []
            files_by_base[base_name].append((file_path, version_info))
        else:
            # File has no version number, add it to the unversioned list
            unversioned_files.append(file_path)
    
    return files_by_base, unversioned_files

def format_version_date(filename: str) -> str:
    """
    Format a filename to make the version date more readable.
    Adds spaces between year, month, and day in the version number.
    Example: v20250304 -> v2025 03 04
    """
    # Pattern to match version date in format vYYYYMMDD
    version_pattern = r'(\d{4})(\d{2})(\d{2})'
    return re.sub(version_pattern, r'\1 \2 \3', filename)

def delete_old_versions(directory: str, versions_to_keep: int) -> Tuple[int, int, Dict[str, List[Tuple[Path, VersionInfo]]], List[Path]]:
    """
    Analyze which files should be kept and which should be deleted.
    Returns:
    - Number of files to delete
    - Total bytes to be freed
    - Dictionary of files to delete by base name
    - List of unversioned files
    """
    files_by_base, unversioned_files = find_latest_versions(directory)
    total_files_to_delete = 0
    total_bytes_to_delete = 0
    files_to_delete_by_base = {}
    
    print(f"\nScanning directory: {directory}")
    print(f"Will keep the {versions_to_keep} most recent version(s) of each file")
    if unversioned_files:
        print(f"Found {len(unversioned_files)} unversioned files (these will always be kept)")
    print("=" * 80)
    
    # Process each group of files with the same base name
    for base_name, files in files_by_base.items():
        # Skip if we don't have enough files to delete
        if len(files) <= versions_to_keep:
            continue
            
        # Sort files by version (newest first)
        files.sort(key=lambda x: x[1], reverse=True)
        files_to_keep = files[:versions_to_keep]
        files_to_delete = files[versions_to_keep:]
        
        print(f"\nBase name: {base_name}")
        print("Keeping:")
        for file_path, version_info in files_to_keep:
            print(f"  - {format_version_date(file_path.name)}")
        
        print("Would delete:")
        files_to_delete_by_base[base_name] = files_to_delete
        for file_path, version_info in files_to_delete:
            file_size = file_path.stat().st_size
            print(f"  - {format_version_date(file_path.name)} ({get_human_readable_size(file_size)})")
            total_bytes_to_delete += file_size
            total_files_to_delete += 1
    
    return total_files_to_delete, total_bytes_to_delete, files_to_delete_by_base, unversioned_files

def confirm_deletion(files_to_delete_by_base: Dict[str, List[Tuple[Path, VersionInfo]]], 
                    total_files: int, total_bytes: int) -> bool:
    """
    Get confirmation from the user before proceeding with deletion.
    Requires two steps:
    1. Type 'delete' to proceed
    2. Enter the exact number of files to be deleted as a sanity check
    """
    print("\n" + "=" * 80)
    print(f"\nSummary of files to delete:")
    print(f"Total files to delete: {total_files}")
    print(f"Total space to free: {get_human_readable_size(total_bytes)}")
    
    while True:
        response = input("\nType 'delete' to proceed with deletion, or 'cancel' to abort: ").lower()
        if response == 'cancel':
            return False
        elif response == 'delete':
            # Final sanity check
            try:
                confirm_number = int(input(f"\nAs a final sanity check, please type the number of files to be deleted ({total_files}): "))
                if confirm_number == total_files:
                    return True
                print("Number does not match. Aborting deletion.")
                return False
            except ValueError:
                print("Invalid input. Aborting deletion.")
                return False
        else:
            print("Please type either 'delete' or 'cancel'")

def perform_deletion(files_to_delete_by_base: Dict[str, List[Tuple[Path, VersionInfo]]], 
                    versions_to_keep: int,
                    unversioned_files: List[Path]) -> None:
    """
    Actually delete the files and show a summary of what was done.
    """
    # Calculate total space to be saved before deletion
    total_space_saved = sum(
        file_path.stat().st_size 
        for files in files_to_delete_by_base.values() 
        for file_path, _ in files
    )
    
    print("\nDeleting files...")
    for base_name, files in files_to_delete_by_base.items():
        print(f"\nBase name: {base_name}")
        for file_path, _ in files:
            print(f"  - Deleting: {format_version_date(file_path.name)}")
            file_path.unlink()
    
    print("\n" + "=" * 80)
    print("\nDeletion completed successfully!")
    print(f"Successfully deleted {sum(len(files) for files in files_to_delete_by_base.values())} files")
    print(f"Keeping {versions_to_keep} version(s) of each video")
    if unversioned_files:
        print(f"Kept {len(unversioned_files)} unversioned files")
    print(f"Total space saved: {get_human_readable_size(total_space_saved)}")

def get_versions_to_keep() -> int:
    """
    Prompt the user for how many versions of each file to keep.
    Must be at least 1 version.
    """
    while True:
        print("\nHow many versions would you like to keep?")
        print("1 = Only the latest version")
        print("2 = The latest version + 1 previous version")
        print("3 = The latest version + 2 previous versions")
        print("And so on...")
        print("Note: Files without version numbers will always be kept")
        
        try:
            versions = int(input("Enter number of versions to keep: "))
            if versions >= 1:  # Must keep at least 1 version
                return versions
            print("Please enter a positive number (at least 1)")
        except ValueError:
            print("Please enter a valid number")

def get_subdirectories(directory: str) -> List[Path]:
    """
    Get all subdirectories in the given directory.
    Returns a list of Path objects for each subdirectory.
    """
    return [d for d in Path(directory).iterdir() if d.is_dir()]

def process_directory(directory: str, versions_to_keep: int) -> Tuple[int, int, bool, bool]:
    """
    Process a single directory: scan, analyze, and optionally delete files.
    Returns:
    - Number of files deleted
    - Total space saved in bytes
    - Whether to continue processing (False if deletion was cancelled)
    - Whether there were files to delete (True) or not (False)
    """
    print(f"\nProcessing directory: {directory}")
    print("=" * 80)
    
    total_files, total_bytes, files_to_delete, unversioned_files = delete_old_versions(
        directory,
        versions_to_keep
    )
    
    if total_files == 0:
        print("\nNo files need to be deleted.")
        if unversioned_files:
            print(f"Found {len(unversioned_files)} unversioned files (these will always be kept)")
        return 0, 0, True, False
    
    if confirm_deletion(files_to_delete, total_files, total_bytes):
        # Calculate space to be saved before deletion
        space_saved = sum(
            file_path.stat().st_size 
            for files in files_to_delete.values() 
            for file_path, _ in files
        )
        perform_deletion(files_to_delete, versions_to_keep, unversioned_files)
        return total_files, space_saved, True, True
    else:
        print("\nDeletion cancelled.")
        return 0, 0, False, True

def main():
    """
    Main function that orchestrates the entire process:
    1. Parse command line arguments
    2. Get number of versions to keep
    3. Scan for subdirectories
    4. Process each directory with user confirmation between each
    5. Show final summary of all deletions
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up old versions of D3 media files')
    parser.add_argument('directory', help='Directory to scan for files (.mov and .png)')
    parser.add_argument('--versions', type=int, help='Number of versions to keep (if not provided, will prompt)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    versions_to_keep = args.versions if args.versions else get_versions_to_keep()
    if versions_to_keep < 1:
        print("Error: Must keep at least 1 version of each file")
        return
    
    # Get all subdirectories
    subdirs = get_subdirectories(args.directory)
    if not subdirs:
        print(f"No subdirectories found in {args.directory}")
        return
    
    print(f"\nFound {len(subdirs)} subdirectories to process")
    print("=" * 80)
    
    # Track totals across all directories
    total_files_deleted = 0
    total_space_saved = 0
    
    for i, subdir in enumerate(subdirs, 1):
        print(f"\nProcessing directory {i} of {len(subdirs)}")
        files_deleted, space_saved, should_continue, had_files_to_delete = process_directory(str(subdir), versions_to_keep)
        total_files_deleted += files_deleted
        total_space_saved += space_saved
        
        if not should_continue:
            print("\nProcess stopped at user request.")
            break
            
        # Only ask to continue if there were files to delete
        if had_files_to_delete and i < len(subdirs):
            while True:
                response = input("\nPress 'Y' to continue to the next directory, or 'N' to stop: ").upper()
                if response == 'Y':
                    break
                elif response == 'N':
                    print("\nStopping at user request.")
                    break
                else:
                    print("Please enter 'Y' or 'N'")
            if response == 'N':
                break
        elif i < len(subdirs):
            print("\nMoving to next directory...")
    
    print("\n" + "=" * 80)
    print("\nFinal Summary:")
    print(f"Total files deleted across all directories: {total_files_deleted}")
    print(f"Total space saved across all directories: {get_human_readable_size(total_space_saved)}")
    print("=" * 80)

if __name__ == '__main__':
    main() 