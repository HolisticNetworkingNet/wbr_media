# Release readiness and PyPI publishing

This project publishes only distributions that pass the same quality and
security gates used for pull requests. The publish workflow uses PyPI Trusted
Publishing with OIDC; no long-lived PyPI token is stored in the repository.

## Before creating a release

From a clean checkout, install the validation tools and run the full local
gate:

```bash
python -m pip install -e ".[dev,test]"
python -m ruff check .
python -m ruff format --check .
python -m pytest -q -W error
rm -rf dist
python -m build --outdir dist
python -m twine check --strict dist/*
python scripts/validate_distribution.py dist
python scripts/validate_installation.py dist
```

Run the dependency and secret checks as well:

```bash
python -m pip install -e ".[security]"
python -m pip check
python -m pip uninstall --yes wbr-media
python -m pip_audit --local --strict --progress-spinner off

docker run --rm \
  --volume "$PWD:/repo" \
  zricethezav/gitleaks:v8.24.2 \
  detect --source=/repo --no-banner --redact --exit-code 1
```

Do not publish if any check reports a failure, warning that is treated as an
error, vulnerable dependency, unexpected package file, or possible secret.

## Version and release source

1. Update `project.version` in `pyproject.toml`.
2. Run the local gates above and merge the change to `main`.
3. Create a GitHub Release whose tag is `v<version>`, for example `v0.2.0`.
4. Publish the release only after the release commit contains the matching
   version and the intended source changes.

The release workflow checks that the tag version matches `pyproject.toml` and
that the checked-out commit is the release commit. Prereleases are not
published to PyPI.

## What the publish workflow does

The workflow checks out the release commit, then:

1. Verifies the tag, package version, and commit identity.
2. Runs Ruff and the warnings-as-errors test suite.
3. Builds one wheel and one source distribution.
4. Runs strict Twine metadata validation.
5. Validates required package contents.
6. Installs each artifact into a clean environment and imports the package.
7. Publishes those exact validated files to PyPI using OIDC.

The artifacts are not rebuilt after validation. If publishing fails, inspect
the workflow run before retrying; do not manually upload a different local
build.

## Handling findings

- Ruff or test failures: fix the code and rerun the complete gate.
- Packaging failures: inspect `dist/` and update package metadata or the
  distribution validation scripts; do not broaden the package boundary just
  to make a build pass.
- Dependency vulnerabilities: upgrade the affected dependency, or document a
  narrowly scoped temporary exception with an owner and review date.
- Secret findings: stop, revoke or rotate the exposed credential, then remove
  the secret from the current files and assess whether it exists in history.
- Unexpected release-source or version failures: stop the release and correct
  the tag or release commit before retrying.
