"""Verify that a published release tag matches the package version."""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    with Path("pyproject.toml").open("rb") as project_file:
        version = tomllib.load(project_file)["project"]["version"]
    tag_version = re.sub(r"^v", "", args.release_tag)
    if tag_version != version:
        raise SystemExit(
            f"release tag {args.release_tag!r} does not match package version {version!r}"
        )

    checked_out_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    if checked_out_commit != args.commit:
        raise SystemExit(
            f"checked-out commit {checked_out_commit} does not match release commit {args.commit}"
        )
    print(f"validated release {args.release_tag} at {args.commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
