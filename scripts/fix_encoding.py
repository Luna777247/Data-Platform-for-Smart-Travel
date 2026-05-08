#!/usr/bin/env python3
"""
Fix UTF-16 encoded files to UTF-8.

Usage: python scripts/fix_encoding.py
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

EXCLUDE_DIRS = {
    ".git",
    "storage",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    ".egg-info",
    "dist",
    "build",
}

TARGET_EXTENSIONS = {
    ".py",
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".txt",
    ".sh",
    ".env",
}


def should_process(file_path: Path) -> bool:
    """Check if file should be processed."""
    # Skip excluded directories
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False

    # Check extension
    if file_path.suffix.lower() not in TARGET_EXTENSIONS:
        return False

    return True


def detect_encoding(file_path: Path) -> str:
    """Detect file encoding."""
    try:
        with open(file_path, "rb") as f:
            raw = f.read(4)

        # UTF-16 LE BOM
        if raw.startswith(b"\xff\xfe"):
            return "utf-16-le"
        # UTF-16 BE BOM
        if raw.startswith(b"\xfe\xff"):
            return "utf-16-be"
        # UTF-32 LE BOM
        if raw.startswith(b"\xff\xfe\x00\x00"):
            return "utf-32-le"
        # UTF-32 BE BOM
        if raw.startswith(b"\x00\x00\xfe\xff"):
            return "utf-32-be"

        # Try to read as UTF-8
        with open(file_path, "r", encoding="utf-8") as f:
            f.read(1)
        return "utf-8"

    except (UnicodeDecodeError, Exception):
        # Try other encodings
        for enc in ["utf-16", "utf-32", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(1)
                return enc
            except (UnicodeDecodeError, Exception):
                continue

    return "unknown"


def fix_file_encoding(file_path: Path) -> Tuple[bool, str]:
    """Convert file to UTF-8 if needed."""
    encoding = detect_encoding(file_path)

    if encoding == "utf-8":
        return False, "Already UTF-8"

    if encoding == "unknown":
        return False, "Unknown encoding"

    try:
        # Read with detected encoding
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()

        # Write as UTF-8 with LF line endings
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        return True, f"Converted from {encoding} to UTF-8"

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    print(f"🔍 Scanning {root} for encoding issues...")
    print()

    fixed_files: List[Path] = []
    issue_files: List[Tuple[Path, str]] = []

    # Find all files
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        if not should_process(file_path):
            continue

        # Check encoding
        encoding = detect_encoding(file_path)
        if encoding != "utf-8":
            # Try to fix
            success, msg = fix_file_encoding(file_path)
            if success:
                fixed_files.append(file_path)
                print(f"✅ {file_path.relative_to(root)}")
                print(f"   {msg}")
            else:
                issue_files.append((file_path, msg))
                print(f"⚠️  {file_path.relative_to(root)}")
                print(f"   {msg}")

    print()
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"  ✅ Fixed: {len(fixed_files)} files")
    print(f"  ⚠️  Issues: {len(issue_files)} files")
    print()

    if issue_files:
        print("⚠️  Files with issues:")
        for file_path, msg in issue_files:
            print(f"   - {file_path.relative_to(root)}: {msg}")

    return 0 if len(issue_files) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
