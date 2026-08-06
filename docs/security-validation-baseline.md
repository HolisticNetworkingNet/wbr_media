# Security and package-validation baseline

This document records the baseline used by `proof_goblin` and the current gap
analysis for `wbr_media`. It is an audit and implementation checklist, not a
formal security assessment.

## Baseline comparison

| Control | Proof Goblin baseline | wbr_media status | Follow-up |
| --- | --- | --- | --- |
| Source linting and formatting | Ruff lint plus format checks in CI and pre-commit | Missing | Add to the development tool set and CI |
| Test quality | Pytest with warnings treated as errors across a supported-version matrix | Basic pytest job; warnings are not errors and there is no matrix | Define the supported matrix and run `python -m pytest -q -W error` |
| Dependency consistency | `pip check` after installing all dependency groups | Missing | Add an explicit dependency-consistency check |
| Dependency vulnerability audit | Strict `pip-audit` job on pull requests and weekly schedule | Missing | Add `pip-audit --local --strict` after removing the local project package |
| Dependency update monitoring | Dependabot for Python and GitHub Actions | Missing | Add weekly Dependabot configuration |
| Package build | Isolated PEP 517 build of wheel and source distribution | Build occurs only in the publish workflow | Add build validation to pull-request checks |
| Package metadata | Strict `twine check` | Missing | Validate all built artifacts with `twine check --strict` |
| Package contents | Explicit distribution-content boundary validation | Missing | Define and test the intended package boundary |
| Clean artifact install | Wheel and sdist installed into clean environments | Missing | Add clean-install smoke validation |
| Workflow supply chain | Third-party actions pinned to commit SHA; read-only default permissions | Actions use floating major tags; permissions are not explicitly restricted | Pin actions and set `contents: read` by default |
| Workflow concurrency | Superseded runs are cancelled for checks | Missing | Add concurrency groups to validation workflows |
| Release provenance | Protected source/version verification, one validated artifact bundle, OIDC publishing | Publish workflow builds and publishes directly on release | Address in the release-validation work after this audit |

## Scope decision

The immediate scope for #24 is to establish the baseline and identify gaps.
Implementation is tracked by the follow-up issues linked from #23:

- package and artifact validation
- dependency and secret scanning
- CI integration
- release-readiness documentation

The baseline does not require copying Proof Goblin's application-specific
documentation build, CLI checks, or multi-platform matrix. Those controls do
not apply directly to this Django package unless the project later adopts the
same surfaces.

## Recommended implementation order

1. Add development/security optional dependencies and Ruff configuration.
2. Add pull-request checks for linting, tests, package metadata, contents, and
   clean artifact installation.
3. Add dependency auditing, Dependabot, and secret scanning.
4. Harden release publication around the already-validated artifacts and
   least-privilege permissions.
5. Document the local and CI release gates.
