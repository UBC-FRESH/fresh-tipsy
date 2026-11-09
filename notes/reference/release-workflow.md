# Release workflow (P6.2 release operations)

Date: 2026-11-09
Status: configured; publishing requires the `testpypi` and `pypi` environments
Scope: build, TestPyPI, and PyPI publication
Related: [`release-assets.md`](release-assets.md), [`package-build.md`](package-build.md), [`../../.github/workflows/release.yml`](../../.github/workflows/release.yml)

## Triggers

- Publishing a GitHub release runs the full workflow:
  - build wheel and sdist;
  - verify the release tag matches `v<package version>`;
  - publish to TestPyPI;
  - publish to PyPI.
- Manual `workflow_dispatch` builds by default and publishes only when
  `publish_testpypi` or `publish_pypi` is selected.

## Trusted publishing

Both publish jobs use GitHub OIDC and short-lived credentials:

- environment `testpypi`: `pypa/gh-action-pypi-publish`, TestPyPI endpoint;
- environment `pypi`: `pypa/gh-action-pypi-publish`, PyPI endpoint.

No PyPI API token is stored in the repository or workflow. The PyPI and
TestPyPI projects must have trusted publishers configured for this repository
and workflow.

The v0.1.0 GitHub release predates this workflow. To publish 0.1.0 to TestPyPI
or PyPI, run the workflow manually against the `v0.1.0` tag after the
environments and trusted publishers are confirmed.

## Manual commands

Build only:

```bash
gh workflow run release.yml --repo UBC-FRESH/fresh-tipsy \
  --ref v0.1.0 \
  -f publish_testpypi=false -f publish_pypi=false
```

TestPyPI only:

```bash
gh workflow run release.yml --repo UBC-FRESH/fresh-tipsy \
  --ref v0.1.0 \
  -f publish_testpypi=true -f publish_pypi=false
```

PyPI:

```bash
gh workflow run release.yml --repo UBC-FRESH/fresh-tipsy \
  --ref v0.1.0 \
  -f publish_testpypi=false -f publish_pypi=true
```

## Verification

- Build job checks the wheel and sdist are present and readable.
- Release events require the tag to equal `v` plus `pyproject.toml` version.
- Publication logs show the uploaded filenames and digests.
- The source release remains GitHub release `v0.1.0`; raw TIPSY data is not
  part of any package.

## Rollback

PyPI releases are immutable. If a bad artifact is published:

1. yank the release on PyPI;
2. bump the version, rebuild, and publish a new patch release;
3. record the incident and the replacement version in the changelog.
