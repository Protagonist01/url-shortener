# Test-tool dependency isolation — DEP03 / issue62

## Boundary and selected repair

The [primary PyPA advisory](https://raw.githubusercontent.com/pypa/advisory-database/main/vulns/pytest/PYSEC-2026-1845.yaml) covers UNIX pytest temporary-root handling through9.0.2. [Maintainer PR14343](https://github.com/pytest-dev/pytest/pull/14343) rejects symlink user roots and stops following symlinks for supported stat/chmod operations. The repository installed8.3.4 in both test and production requirements. No current application route into this boundary is established; this is a local test-tool finding.

The narrow complete repair updates pytest to9.1.1 and pytest-asyncio to1.4.0, separates install scopes and covers all of them with fresh advisory resolution. Keeping plugin0.25.2 is incompatible: its primary package metadata requires pytest below9. [Current plugin changes](https://pytest-asyncio.readthedocs.io/en/stable/reference/changelog.html) support pytest9 and change loop handling; preserve auto mode and explicitly choose function-scoped test/fixture loops for the existing async generator HTTP client.

| Manifest | Installed purpose / audit scope |
|---|---|
| requirements.txt | API, worker, beat and startup Alembic / runtime |
| requirements-test.txt | Runtime plus pytest9.1.1, pytest-asyncio1.4.0 and owned-process psutil7.2.2 |
| requirements-ci.txt | Alias including requirements-test.txt / test |
| requirements-ops.txt | Runtime plus optional Flower2.0.1 / operations |
| requirements-audit.txt | Separate pip-audit2.10.1 scanner and cleanup helper |
| requirements-legacy-pytest.txt | Intentionally vulnerable before-fix fixture, separate interpreter only |
| requirements-legacy-jwt.txt | Intentionally historical token-compatibility fixture, separate interpreter only |

Direct pins and exact resolved advisory reports are reproducibility evidence, not a complete hash-locked transitive installation. Full lock/enforcement remains F03 work. The historical fixture pins are excluded from runtime, normal tests, operations and target scans deliberately; they are never deployed. Compose's Flower uses a separate external mher/flower:2.0 image. The new operations manifest does not certify or alter that image's dependencies.

## Reproduce in a clean Python3.12 checkout

Use separate fresh virtual environments, public PyPI and disabled pip configuration; never install into the owner's existing environment or read private dotenv files. Each install should run pip check.

```bash
python -m venv output/test-env
output/test-env/bin/python -m pip install -r requirements-ci.txt
output/test-env/bin/python -m pip check
python -m venv output/legacy-pytest
output/legacy-pytest/bin/python -m pip install -r requirements-legacy-pytest.txt
output/legacy-pytest/bin/python -m scripts.verify_pytest_boundary --expect-vulnerable
output/test-env/bin/python -m scripts.verify_pytest_boundary
output/test-env/bin/python -m scripts.verify_runtime_dependencies
python -m venv output/operations
output/operations/bin/python -m pip install -r requirements-ops.txt
output/operations/bin/python -m pip check
output/operations/bin/python -m celery --broker=redis://127.0.0.1:26379/1 flower --help
```

The security probe requires POSIX and exercises the actual installed TempPathFactory in an owned temporary directory: ordinary0700 root, direct symlink and chained symlink to an owned target with a sentinel. Old pytest accepts both links; the fixed version must reject them without modifying the target's mode/content. This is a same-owner focused substitute, not a cross-user escalation proof or proof that all denial of service is prevented. A Windows refusal is unverified UNIX coverage.

The runtime verifier archives committed HEAD only, refuses tracked private dotenv paths and builds the actual Dockerfile. Do not use it to validate uncommitted requirements: commit the scoped candidate first. It asserts non-root user/default startup command, absent test/monitor/scanner packages, pip check, actual API health via ASGI, task discovery and Alembic/Uvicorn/Celery worker/beat CLI availability. Runtime containers have no network, no real credentials and no mounted checkout. Image cleanup checks its unique owned label. This proves package availability and in-process health; the separate foundation harness proves real PostgreSQL/Redis migrations, worker delivery and HTTP behavior.

Prepare the separate historical JWT fixture, then follow [JWT verification](jwt-dependency-remediation.md) for all18 existing HTTP tests and real token/anchor checks, and [foundation CI](foundation-ci.md) for migrations/worker delivery. Do not run tests/test_api.py directly: its broad Redis cleanup is safe only behind the labeled disposable-service and API-identity guards. Explicit pytest.ini keeps async auto mode in the empty-cwd harness.

In a separate requirements-audit.txt environment:

```bash
python -m scripts.audit_dependencies --scope runtime
python -m scripts.audit_dependencies --scope test
python -m scripts.audit_dependencies --scope operations
python -m scripts.verify_dependency_remediation
```

Audit exit1 preserves known findings;2 is operational/incomplete failure. Each scope has distinct report/log/metadata filenames; runtime retains the original baseline-linux.json convention. Recursive local manifest hashes and current HEAD must match before gates accept evidence. The targeted gate requires no test/monitor/scanner packages in runtime, fixed pytest/plugin pins without findings in tests, and intended operations pin with no test/scanner packages. Framework/parser findings remain visible under issue61; a successful evidence job is not full security approval.

## Compatibility, rollout and rollback

Publish only after actual Linux foundation and all-scope advisory jobs pass and the candidate is reviewed. No schema/query/cache/session change occurs. Rebuild API/worker/beat images from runtime requirements; use a separate test environment for pytest and a separate operational environment for the optional CLI. Existing development Compose commands and external Flower service remain unchanged.

To roll back dependency separation, revert this reviewed commit and rebuild from that revision, then rerun compatibility checks. That restores vulnerable pytest8.3.4 and is not an acceptable security baseline; prefer a reviewed forward correction with compatible fixed pins. There is no data migration to undo. No manual deployment, image-size/startup-time improvement, capacity or production SLO is claimed.

## Verification status

Candidate syntax/import checks and actual Linux jobs are pending until their recorded results are published here. Local Docker daemon is unavailable at this checkpoint; that is not a passing image check. Parent3, issue61 and all milestone/security gates remain open.
