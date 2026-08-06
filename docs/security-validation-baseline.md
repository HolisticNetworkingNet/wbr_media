# Security and package-validation baseline

This document records the baseline used by `proof_goblin` and the current gap
analysis for `wbr_media`. It is an audit and implementation checklist, not a
formal security assessment.

## Baseline comparison

| Control | Proof Goblin baseline | wbr_media status | Follow-up |
| --- | --- | --- | --- |
| Source linting and formatting | Ruff lint plus format checks in CI and pre-commit | Implemented in pull-request and release CI | Keep the local and CI commands aligned |
| Test quality | Pytest with warnings treated as errors across a supported-version matrix | Implemented for Python 3.12–3.14 | Keep the supported matrix current |
| Dependency consistency | `pip check` after installing all dependency groups | Implemented in dependency-security CI | Review failures before merging |
| Dependency vulnerability audit | Strict `pip-audit` job on pull requests and weekly schedule | Implemented with the local project removed before audit | Review and document exceptions narrowly |
| Dependency update monitoring | Dependabot for Python and GitHub Actions | Implemented with weekly grouped updates | Review Dependabot PRs promptly |
| Package build | Isolated PEP 517 build of wheel and source distribution | Implemented in pull-request and release CI | Keep artifact checks required |
| Package metadata | Strict `twine check` | Implemented in pull-request and release CI | Fix metadata failures before release |
| Package contents | Explicit distribution-content boundary validation | Implemented by `scripts/validate_distribution.py` | Update intentionally when package contents change |
| Clean artifact install | Wheel and sdist installed into clean environments | Implemented by `scripts/validate_installation.py` | Keep smoke test minimal and representative |
| Workflow supply chain | Third-party actions pinned to commit SHA; read-only default permissions | Implemented in CI and release workflows | Keep action pins current through Dependabot |
| Workflow concurrency | Superseded runs are cancelled for checks | Implemented for validation and security workflows | Retain cancellation on new workflows |
| Release provenance | Protected source/version verification, one validated artifact bundle, OIDC publishing | Implemented in the release workflow | Publish only through the workflow |

## Scope decision

The audit established the baseline and identified gaps. Implementation is now
covered by the follow-up issues linked from #23:

- package and artifact validation
- dependency and secret scanning
- CI integration
- release-readiness documentation

The baseline does not require copying Proof Goblin's application-specific
documentation build, CLI checks, or multi-platform matrix. Those controls do
not apply directly to this Django package unless the project later adopts the
same surfaces.

## Implemented order

1. Added development/security optional dependencies and Ruff configuration.
2. Added pull-request checks for linting, tests, package metadata, contents, and
   clean artifact installation.
3. Added dependency auditing, Dependabot, and secret scanning.
4. Hardened release publication around the already-validated artifacts and
   least-privilege permissions.
5. Documented the local and CI release gates in `README.md` and
   `docs/releasing.md`.
