# Copyright (c) 2025 We Build Reactions.
# Proprietary and confidential. See LICENSE for details.

#!/usr/bin/env python3
"""
Check/apply We Build Reactions copyright headers.

Usage:
  # Check only (non-zero exit if missing)
  python scripts/copyright_headers.py --check

  # Show what would change
  python scripts/copyright_headers.py --check --verbose

  # Apply headers in-place
  python scripts/copyright_headers.py --apply

  # Apply only to specific extensions
  python scripts/copyright_headers.py --apply --ext .py --ext .html
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# ---- Configuration ----

WBR_HEADER_PY = (
    "# Copyright (c) 2025 We Build Reactions.\n"
    "# Proprietary and confidential. See LICENSE for details.\n"
)

WBR_HEADER_HTML = (
    "{# Copyright (c) 2025 We Build Reactions. #}\n"
    "{# Proprietary and confidential. See LICENSE for details. #}\n"
)

DEFAULT_EXTS = {".py", ".html", ".txt", ".md"}  # adjust as desired

# Directories to skip
DEFAULT_EXCLUDES = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".idea",
    "migrations",  # optional: include if you want
    "docs",
    "seed",
    "static",
    "staticfiles",
    "media",
    "mediafiles",
    "tmp",
}

DENYLIST_FILENAMES = {
    "requirements.txt",
    "requirements-dev.txt",
    "constraints.txt",
    "pip-requirements.txt",
    "document-tree.txt",
}

# Only enforce headers on "base-ish" HTML templates (to avoid component/footer leaks)
HTML_HEADER_REQUIRED_FILENAMES = {
    "base.html",
    # Add more if you want:
    # "base_menu.html",
    # "layout.html",
    # "root.html",
}

# Sentinel substring to detect "already has header"
SENTINEL = "Copyright (c) 2025 We Build Reactions."


@dataclass(frozen=True)
class HeaderSpec:
    header_text: str
    comment_style: str  # for reporting only


def header_for_extension(ext: str) -> HeaderSpec | None:
    if ext == ".py":
        return HeaderSpec(WBR_HEADER_PY, "python")
    if ext == ".html":
        # Django templates are HTML-ish; use Django comment blocks
        return HeaderSpec(WBR_HEADER_HTML, "django-template")
    if ext in {".md", ".txt"}:
        # Markdown/txt: use plain text header
        return HeaderSpec(
            "Copyright (c) 2025 We Build Reactions.\n"
            "Proprietary and confidential. See LICENSE for details.\n",
            "plain",
        )
    return None


def iter_files(root: Path, exts: set[str], excludes: set[str]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue

        # Skip excluded dirs anywhere in path
        if any(part in excludes for part in p.parts):
            continue

        # Skip denylisted filenames
        if p.name in DENYLIST_FILENAMES:
            continue

        ext = p.suffix.lower()
        if ext not in exts:
            continue

        # Tighten HTML scans ONLY: require headers only on base-ish templates
        if ext == ".html" and p.name not in HTML_HEADER_REQUIRED_FILENAMES:
            continue

        yield p


def has_header(text: str) -> bool:
    # Only search near the top for speed and to avoid false positives deep in files
    top = "\n".join(text.splitlines()[:10])
    return SENTINEL in top


def _python_insertion_index(lines: list[str]) -> int:
    """
    Insert after shebang and encoding cookie if present.
    """
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx = 1
    # encoding cookie typically line 1 or 2 (PEP 263)
    for i in range(idx, min(idx + 2, len(lines))):
        if "coding" in lines[i] and lines[i].lstrip().startswith("#"):
            idx = i + 1
    # skip blank lines after those
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    return idx


def _generic_insertion_index(lines: list[str]) -> int:
    """
    Insert at top, skipping leading blank lines.
    """
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    return idx


def apply_header(path: Path, spec: HeaderSpec) -> bool:
    """
    Returns True if file was modified.
    """
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fall back but avoid crashing the hook
        original = path.read_text(errors="ignore")

    if has_header(original):
        return False

    lines = original.splitlines(keepends=True)

    if path.suffix.lower() == ".py":
        idx = _python_insertion_index(lines)
        header = spec.header_text
        # Ensure a blank line after header for readability
        if not header.endswith("\n\n"):
            header = header.rstrip("\n") + "\n\n"
        new_lines = lines[:idx] + [header] + lines[idx:]
    else:
        idx = _generic_insertion_index(lines)
        header = spec.header_text
        if not header.endswith("\n\n"):
            header = header.rstrip("\n") + "\n\n"
        new_lines = lines[:idx] + [header] + lines[idx:]

    new_text = "".join(new_lines)

    # Write only if changed
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root to scan")
    ap.add_argument(
        "--check", action="store_true", help="Check only; exit non-zero if missing"
    )
    ap.add_argument("--apply", action="store_true", help="Apply headers in-place")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    ap.add_argument(
        "--ext",
        action="append",
        default=[],
        help="Extensions to include, e.g. --ext .py --ext .html",
    )
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Directory names to exclude, e.g. --exclude migrations",
    )
    args = ap.parse_args()

    if not args.check and not args.apply:
        ap.error("Choose one: --check or --apply")

    root = Path(args.root).resolve()
    exts = set(args.ext) if args.ext else set(DEFAULT_EXTS)
    excludes = set(DEFAULT_EXCLUDES) | set(args.exclude)

    missing: list[Path] = []
    changed: list[Path] = []

    for f in iter_files(root, exts, excludes):
        spec = header_for_extension(f.suffix.lower())
        if not spec:
            continue

        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = f.read_text(errors="ignore")

        if has_header(text):
            continue

        missing.append(f)

        if args.apply:
            did = apply_header(f, spec)
            if did:
                changed.append(f)

    if args.apply:
        print(f"Applied headers to {len(changed)} file(s).")
        if args.verbose and changed:
            for p in changed:
                print(f"  + {p.relative_to(root)}")
        # After applying, consider it a success
        return 0

    # --check mode
    if missing:
        print(f"Missing copyright header in {len(missing)} file(s):")
        for p in missing[:200]:
            print(f"  - {p.relative_to(root)}")
        if len(missing) > 200:
            print(f"  ... and {len(missing) - 200} more")
        return 1

    if args.verbose:
        print("All checked files contain the header.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
