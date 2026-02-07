"""
Project Cleanup Script
Removes temporary files, logs, benchmarks, and test outputs while preserving important data.

Usage:
    python cleanup.py              # Interactive mode (asks for confirmation)
    python cleanup.py --force      # Force cleanup without confirmation
    python cleanup.py --dry-run    # Show what would be deleted without actually deleting
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Directories and files to clean
CLEANUPS = {
    "logs": {
        "patterns": ["*.log", "logs/"],
        "description": "Log files"
    },
    "benchmarks": {
        "patterns": [
            "data/benchmark_report.json",
            "data/benchmark_report.md",
            "data/eval_*.json",
            "data/evaluation_report.json",
            "data/evaluation_results.json"
        ],
        "description": "Benchmark and evaluation reports"
    },
    "cache": {
        "patterns": [
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
            ".mypy_cache/"
        ],
        "description": "Python cache files"
    },
    "temp": {
        "patterns": [
            "*.tmp",
            "temp/",
            ".DS_Store",
            "Thumbs.db"
        ],
        "description": "Temporary files"
    }
}

# Files/directories to PRESERVE (never delete)
PRESERVE = [
    "data/parsed_documents.json",
    "data/faiss_index/",
    "data/company_info.txt",
    "data/questions.csv",
    "data/raw_pdf_flies/",
    "*.py",
    ".env",
    "requirements.txt",
    "README*.md",
    ".git/",
    "venv/",
    ".venv/"
]


def find_files_to_delete(base_dir: str, patterns: list) -> list:
    """Find all files matching the given patterns."""
    base_path = Path(base_dir)
    files_to_delete = []
    
    for pattern in patterns:
        # Handle directory patterns
        if pattern.endswith('/'):
            for path in base_path.rglob(pattern.rstrip('/')):
                if path.is_dir():
                    files_to_delete.append(path)
        else:
            # Handle file patterns
            for path in base_path.rglob(pattern):
                if path.is_file():
                    files_to_delete.append(path)
    
    return files_to_delete


def is_preserved(path: Path, base_dir: Path) -> bool:
    """Check if a path should be preserved."""
    relative_path = path.relative_to(base_dir)
    
    for preserve_pattern in PRESERVE:
        if preserve_pattern.endswith('/'):
            # Directory pattern
            if str(relative_path).startswith(preserve_pattern.rstrip('/')):
                return True
        else:
            # File pattern
            if relative_path.match(preserve_pattern):
                return True
    
    return False


def get_size(path: Path) -> int:
    """Get size of file or directory in bytes."""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return 0


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def cleanup(base_dir: str = ".", dry_run: bool = False, force: bool = False):
    """Main cleanup function."""
    base_path = Path(base_dir).resolve()
    
    print("=" * 70)
    print("🧹 Project Cleanup Script")
    print("=" * 70)
    print(f"\nBase directory: {base_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'FORCE' if force else 'INTERACTIVE'}")
    print("-" * 70)
    
    all_files_to_delete = []
    total_size = 0
    
    # Collect all files to delete
    for category, config in CLEANUPS.items():
        print(f"\n📂 {config['description']}:")
        files = find_files_to_delete(base_path, config['patterns'])
        
        # Filter out preserved files
        files = [f for f in files if not is_preserved(f, base_path)]
        
        if not files:
            print("   ✓ Nothing to clean")
            continue
        
        category_size = 0
        for file in files:
            size = get_size(file)
            category_size += size
            all_files_to_delete.append(file)
            print(f"   - {file.relative_to(base_path)} ({format_size(size)})")
        
        print(f"   Subtotal: {len(files)} items, {format_size(category_size)}")
        total_size += category_size
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"Total items to delete: {len(all_files_to_delete)}")
    print(f"Total space to free: {format_size(total_size)}")
    
    if not all_files_to_delete:
        print("\n✅ Project is already clean!")
        return
    
    # Confirmation
    if dry_run:
        print("\n🔍 DRY RUN - No files were deleted")
        return
    
    if not force:
        print("\n⚠️  WARNING: This will permanently delete the files listed above!")
        response = input("Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("\n❌ Cleanup cancelled")
            return
    
    # Delete files
    print("\n🗑️  Deleting files...")
    deleted_count = 0
    errors = []
    
    for file in all_files_to_delete:
        try:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
            deleted_count += 1
            print(f"   ✓ Deleted: {file.relative_to(base_path)}")
        except Exception as e:
            errors.append((file, str(e)))
            print(f"   ✗ Error deleting {file.relative_to(base_path)}: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ Cleanup Complete!")
    print("=" * 70)
    print(f"Deleted: {deleted_count}/{len(all_files_to_delete)} items")
    print(f"Freed: {format_size(total_size)}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for file, error in errors:
            print(f"   - {file.relative_to(base_path)}: {error}")
    
    # Create cleanup log
    log_path = base_path / "cleanup_log.txt"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n{'=' * 70}\n")
        f.write(f"Cleanup performed: {datetime.now().isoformat()}\n")
        f.write(f"Items deleted: {deleted_count}\n")
        f.write(f"Space freed: {format_size(total_size)}\n")
        f.write(f"{'=' * 70}\n")
    
    print(f"\n📝 Log saved to: {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up temporary files and logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete without confirmation"
    )
    
    parser.add_argument(
        "--dir",
        default=".",
        help="Base directory to clean (default: current directory)"
    )
    
    args = parser.parse_args()
    
    cleanup(base_dir=args.dir, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
