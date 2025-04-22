#!/usr/bin/env python3
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
    Each version has either a date or a numeric version number.
    Date versions can have an optional letter suffix (e.g., 'a', 'b').
    """
    def __init__(self, version_str: str):
        self.version_str = version_str
        self.is_date_version = version_str.startswith('v')
        self.is_numeric_version = version_str.startswith('_v')
        self.letter = None
        
        if self.is_date_version:
            # Extract letter suffix if present
            letter_match = re.search(r'[a-zA-Z]$', version_str)
            if letter_match:
                self.letter = letter_match.group(0)
                clean_version = version_str[:-1]
            else:
                clean_version = version_str
                
            if len(clean_version) == 9:  # vYYYYMMDD
                self.date = datetime.strptime(clean_version[1:], '%Y%m%d')
            elif len(clean_version) == 13:  # vYYYYMMDDhhmm
                self.date = datetime.strptime(clean_version[1:], '%Y%m%d%H%M')
            else:
                raise ValueError(f"Invalid date version format: {version_str}")
        elif self.is_numeric_version:
            self.version_num = int(version_str[2:])
        else:
            raise ValueError(f"Invalid version format: {version_str}")

    def __lt__(self, other: 'VersionInfo') -> bool:
        """
        Compare two versions to determine which is older.
        Date versions and numeric versions are never compared directly.
        For date versions, first compares dates, then letters if dates are equal.
        Versions without letters are considered older than those with letters.
        """
        if self.is_date_version and other.is_date_version:
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
        elif self.is_numeric_version and other.is_numeric_version:
            return self.version_num < other.version_num
        else:
            raise ValueError("Cannot compare date versions with numeric versions")

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
        base_name, version_str, _ = parse_filename(file_path.name)
        
        if version_str:
            try:
                version_info = VersionInfo(version_str)
                if base_name not in files_by_base:
                    files_by_base[base_name] = []
                files_by_base[base_name].append((file_path, version_info))
            except ValueError as e:
                print(f"Warning: Skipping file {file_path.name} - {str(e)}")
        else:
            unversioned_files.append(file_path)
    
    # Check for mixed version types
    for base_name, files in files_by_base.items():
        has_date_versions = any(v.is_date_version for _, v in files)
        has_numeric_versions = any(v.is_numeric_version for _, v in files)
        
        if has_date_versions and has_numeric_versions:
            print(f"\nError: Mixed version types found for {base_name}:")
            print("This file set contains both date-based versions (vYYYYMMDD) and numeric versions (_vN)")
            print("Please resolve this manually before running the script again")
            print("Files:")
            for file_path, _ in files:
                print(f"  - {file_path.name}")
            raise ValueError(f"Mixed version types found for {base_name}")
    
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
    Scan a directory for files and identify which versions to keep/delete.
    Returns:
    - Total number of files to delete
    - Total size of files to delete in bytes
    - Dictionary of files to delete, grouped by base name
    - List of unversioned files
    """
    files_by_base, unversioned_files = find_latest_versions(directory)
    total_files = 0
    total_bytes = 0
    files_to_delete: Dict[str, List[Tuple[Path, VersionInfo]]] = {}
    
    print(f"\n{Colors.BOLD}Scanning directory: {directory}{Colors.ENDC}")
    print(f"{Colors.CYAN}Will keep the {versions_to_keep} most recent version(s) of each file{Colors.ENDC}")
    if unversioned_files:
        print(f"{Colors.YELLOW}Found {len(unversioned_files)} unversioned files (these will always be kept){Colors.ENDC}")
    print("=" * 80)
    
    for base_name, files in files_by_base.items():
        # Sort files by version (newest first)
        files.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n{Colors.BOLD}Base name: {base_name}{Colors.ENDC}")
        
        # Keep the specified number of versions
        files_to_keep = files[:versions_to_keep]
        files_to_delete[base_name] = files[versions_to_keep:]
        
        print(f"{Colors.GREEN}Will keep:{Colors.ENDC}")
        for file_path, version_info in files_to_keep:
            print(f"  - {file_path.name}")
        
        if files_to_delete[base_name]:
            print(f"\n{Colors.RED}Will delete:{Colors.ENDC}")
            for file_path, version_info in files_to_delete[base_name]:
                file_size = file_path.stat().st_size
                print(f"  - {file_path.name} ({get_human_readable_size(file_size)})")
                total_bytes += file_size
                total_files += 1
        else:
            print(f"\n{Colors.YELLOW}No files to delete for this base name{Colors.ENDC}")
        
        print("-" * 80)
    
    return total_files, total_bytes, files_to_delete, unversioned_files

def confirm_deletion(files_to_delete: Dict[str, List[Tuple[Path, VersionInfo]]], 
                    total_files: int, 
                    total_bytes: int,
                    versions_to_keep: int) -> bool:
    """
    Show files to be deleted and get user confirmation.
    Returns True if user confirms deletion.
    """
    print(f"\n{Colors.BOLD}Files to be kept and deleted:{Colors.ENDC}")
    print("=" * 80)
    
    for base_name, files in files_to_delete.items():
        # Sort files by version (newest first)
        sorted_files = sorted(
            files,
            key=lambda x: x[1],  # VersionInfo objects are already comparable
            reverse=True
        )
        
        print(f"\n{Colors.BOLD}{base_name}:{Colors.ENDC}")
        print(f"{Colors.GREEN}  Keeping:{Colors.ENDC}")
        for file_path, version_info in sorted_files[:versions_to_keep]:
            print(f"    {file_path.name}")
        
        files_to_delete_for_base = sorted_files[versions_to_keep:]
        if files_to_delete_for_base:
            print(f"{Colors.RED}  Deleting:{Colors.ENDC}")
            for file_path, version_info in files_to_delete_for_base:
                print(f"    {file_path.name}")
    
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}Total files to delete: {total_files}{Colors.ENDC}")
    print(f"{Colors.BOLD}Total space to save: {get_human_readable_size(total_bytes)}{Colors.ENDC}")
    print("=" * 80)
    
    while True:
        response = input(f"\n{Colors.YELLOW}Type 'delete' to proceed with deletion, or 'cancel' to abort: {Colors.ENDC}").lower()
        if response == 'cancel':
            return False
        elif response == 'delete':
            # Final sanity check
            try:
                confirm_number = int(input(f"\n{Colors.YELLOW}As a final sanity check, please type the number of files to be deleted ({total_files}): {Colors.ENDC}"))
                if confirm_number == total_files:
                    return True
                print(f"{Colors.RED}Number does not match. Aborting deletion.{Colors.ENDC}")
                return False
            except ValueError:
                print(f"{Colors.RED}Invalid input. Aborting deletion.{Colors.ENDC}")
                return False
        else:
            print(f"{Colors.RED}Please type either 'delete' or 'cancel'{Colors.ENDC}")

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
    If no subdirectories are found, returns a list containing just the current directory.
    """
    dir_path = Path(directory)
    subdirs = [d for d in dir_path.iterdir() if d.is_dir()]
    return subdirs if subdirs else [dir_path]

def process_directory(directory: str, versions_to_keep: int) -> Tuple[int, int, bool, bool]:
    """
    Process a single directory: scan, analyze, and optionally delete files.
    Returns:
    - Number of files deleted
    - Total space saved in bytes
    - Whether to continue processing (False if deletion was cancelled)
    - Whether there were files to delete (True) or not (False)
    """
    print(f"\n{Colors.BOLD}Processing directory: {directory}{Colors.ENDC}")
    print("=" * 80)
    
    total_files, total_bytes, files_to_delete, unversioned_files = delete_old_versions(
        directory,
        versions_to_keep
    )
    
    if total_files == 0:
        print(f"\n{Colors.YELLOW}No files need to be deleted.{Colors.ENDC}")
        if unversioned_files:
            print(f"{Colors.YELLOW}Found {len(unversioned_files)} unversioned files (these will always be kept){Colors.ENDC}")
        return 0, 0, True, False
    
    if confirm_deletion(files_to_delete, total_files, total_bytes, versions_to_keep):
        # Calculate space to be saved before deletion
        space_saved = sum(
            file_path.stat().st_size 
            for files in files_to_delete.values() 
            for file_path, _ in files
        )
        perform_deletion(files_to_delete, versions_to_keep, unversioned_files)
        return total_files, space_saved, True, True
    else:
        print(f"\n{Colors.YELLOW}Deletion cancelled.{Colors.ENDC}")
        return 0, 0, False, True

def main():
    """
    Main function that orchestrates the entire process:
    1. Parse command line arguments
    2. Get number of versions to keep
    3. Scan for subdirectories (or use current directory if none found)
    4. Process each directory with user confirmation between each
    5. Show final summary of all deletions
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up old versions of D3 media files')
    parser.add_argument('directory', help='Directory to scan for files (.mov and .png)')
    parser.add_argument('--versions', type=int, help='Number of versions to keep (if not provided, will prompt)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"{Colors.RED}Error: {args.directory} is not a valid directory{Colors.ENDC}")
        return
    
    versions_to_keep = args.versions if args.versions else get_versions_to_keep()
    if versions_to_keep < 1:
        print(f"{Colors.RED}Error: Must keep at least 1 version of each file{Colors.ENDC}")
        return
    
    # Get all subdirectories (or current directory if none found)
    subdirs = get_subdirectories(args.directory)
    print(f"\n{Colors.BOLD}Found {len(subdirs)} {'subdirectories' if len(subdirs) > 1 else 'directory'} to process{Colors.ENDC}")
    print("=" * 80)
    
    # Track totals across all directories
    total_files_deleted = 0
    total_space_saved = 0
    
    for i, subdir in enumerate(subdirs, 1):
        print(f"\n{Colors.BOLD}Processing directory {i} of {len(subdirs)}{Colors.ENDC}")
        files_deleted, space_saved, should_continue, had_files_to_delete = process_directory(str(subdir), versions_to_keep)
        total_files_deleted += files_deleted
        total_space_saved += space_saved
        
        if not should_continue:
            print(f"\n{Colors.YELLOW}Process stopped at user request.{Colors.ENDC}")
            break
            
        # Only ask to continue if there were files to delete
        if had_files_to_delete and i < len(subdirs):
            while True:
                response = input(f"\n{Colors.YELLOW}Press 'Y' to continue to the next directory, or 'N' to stop: {Colors.ENDC}").upper()
                if response == 'Y':
                    break
                elif response == 'N':
                    print(f"\n{Colors.YELLOW}Stopping at user request.{Colors.ENDC}")
                    break
                else:
                    print(f"{Colors.RED}Please enter 'Y' or 'N'{Colors.ENDC}")
            if response == 'N':
                break
        elif i < len(subdirs):
            print(f"\n{Colors.CYAN}Moving to next directory...{Colors.ENDC}")
    
    print("\n" + "=" * 80)
    print(f"\n{Colors.BOLD}Final Summary:{Colors.ENDC}")
    print(f"{Colors.BOLD}Total files deleted across all directories: {total_files_deleted}{Colors.ENDC}")
    print(f"{Colors.BOLD}Total space saved across all directories: {get_human_readable_size(total_space_saved)}{Colors.ENDC}")
    print("=" * 80)

if __name__ == '__main__':
    main() 