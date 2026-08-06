"""Install each built artifact into an isolated environment and smoke-test it."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_installation.py DIST_DIR")
    directory = Path(sys.argv[1]).resolve()
    artifacts = sorted(directory.glob("*.whl")) + sorted(directory.glob("*.tar.gz"))
    if len(artifacts) != 2:
        raise SystemExit("expected exactly one wheel and one source distribution")

    with tempfile.TemporaryDirectory(prefix="wbr-media-install-") as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = environment / "bin" / "python"
        if sys.platform == "win32":
            python = environment / "Scripts" / "python.exe"
        for artifact in artifacts:
            subprocess.run(
                [python, "-m", "pip", "install", "--no-deps", str(artifact)],
                check=True,
            )
            subprocess.run(
                [python, "-c", "import wbr_media; print(wbr_media.__name__)"],
                check=True,
            )
            subprocess.run(
                [python, "-m", "pip", "uninstall", "-y", "wbr-media"],
                check=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
