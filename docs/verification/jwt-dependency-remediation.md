# JWT dependency remediation — DEP01

[Issue60](https://github.com/Protagonist01/url-shortener/issues/60), [ADR0003](../decisions/0003-hs256-jwt-dependency.md). Replace python-jose[cryptography]3.3.0 with pinned PyJWT2.15.1 without crypto extras. HS256 keys/issued sub+exp/TTL/bearer response remain wire-compatible. Do not reuse an environment containing leftover removed packages as proof of clean resolution.

## Reproduce safely

From a clean checkout, create a Python3.12 app environment and install requirements-ci.txt. Separately create an environment from requirements-legacy-jwt.txt and set LEGACY_JWT_PYTHON to its absolute interpreter path. This intentionally historical fixture has known advisories and is never deployed or included in app/scanner installation. It exchanges only synthetic key/claims over captured stdin/stdout. No real key/token or dotenv file is required.

```powershell
python -m unittest tests.test_security_tokens -v
python -m scripts.verify_configuration --docker
python -m pytest tests/test_worker_registration.py -q
python -m scripts.verify_worker_registration up
try {
    python -m scripts.verify_worker_registration verify
    python -m scripts.verify_authentication run
} finally {
    python -m scripts.verify_worker_registration down
}
```

The API harness verifies owned container labels/loopback ports, refuses a busy API port, starts its own server and checks a fresh fixture identity before the legacy suite's broad Redis cleanup. Settings first load in an empty cwd; only afterward does the server enter the repo for legacy relative static assets. Existing18 API tests plus real historical/current bearer management, malformed claims, owned-delete authorization and cold/warm destination anchor checks run on actual PostgreSQL/Redis. GeoIP is synthetic ZZ and the API uses the background_tasks profile; the legacy suite's in-process setting mutation does not prove a remote server switches backend. Actual Celery task delivery is checked separately through the existing worker harness. No external GeoIP/provider reliability is claimed.

In a separate pinned requirements-audit.txt environment run `python -m scripts.audit_dependencies`, retaining code1 known findings, then `python -m scripts.verify_dependency_remediation`. Operational failures or missing/stale/skipped coverage fail. The targeted gate requires the same requirements hash, absence of python-jose/ecdsa and PyJWT2.15.1 without recorded findings. Other findings remain visible and tracked in61/62; no suppression or global security-pass claim.

## Evidence in progress

Local synthetic JWT contracts:8 unittest tests passed using Python3.12.13/PyJWT2.15.1 and the actual historical python-jose interpreter. Tested both directions, wrong keys/algorithms, expired/malformed expiry, non-string/missing subjects and malformed/non-string input. No real token/key was used. Fresh clean install, service and Linux CI/scan results remain pending.

The first disposable service startup failed on a5s PostgreSQL readiness subprocess timeout and cleaned its own two containers. This was a failed check; a sequential retry is required. No shared containers or Redis state were touched. Existing app interpreter lacks pip, so local PyJWT testing initially used an isolated ignored target installed with the audit tool's pip; that pass alone is not clean-environment evidence.

The next startup succeeded, but the worker verification failed to become ready within its30s limit and terminated its own process. The separately created local application virtualenv install exceeded its300s limit while resolving/download metadata; it is incomplete. Actual clean Linux CI/advisory checks remain required. Record these limitations instead of raising production budgets or counting partially started services as a pass.

## Limits and performance

Record source/requirements hashes, runtime, raw synthetic decode durations and p50/p95/p99/errors/serial throughput under ignored output/authentication-verification. This serial experiment measures ordinary synthetic HS256 tokens, not HTTP throughput, large/adversarial headers, CPU saturation, approved capacity or F01/F05 SLOs. No SQL/cache query changes occur. Parent43 retains optional-exp/session/key/CSRF/bcrypt/header bounds; valid-issued-token compatibility does not resolve those policies. Unpublished /q QR prototype and its checks await IN08 and are excluded from clean-main evidence. No manual deployment or security approval is implied.

## Actual Linux evidence — 2026-10-06

PR63 head eae7f8f4bfd17acffe22ecda2fffbd3ff8f5efcf passed [foundation run37536532072/job112518840890](https://github.com/Protagonist01/url-shortener/actions/runs/37536532072/job/112518840890) and [advisory run37536532081/job112518840637](https://github.com/Protagonist01/url-shortener/actions/runs/37536532081/job/112518840637). Queried the exact-head run/job APIs: every contract/configuration/worker/API/cleanup/upload step succeeded. Downloaded allowed artifact files and checked hashes before publishing sanitized reports. Their source_head1b75eaea is the PR merge checkout, distinct from the branch head.

[Synthetic service evidence](jwt-linux-evidence.json): Python3.12.14/Linux, PyJWT2.15.1,18 existing HTTP API tests passed (6.145s, zero failures/errors/skips), actual old/current bearer management and malformed-claim behavior passed, cold/warm destination anchors retained. Existing actual Celery scheduler/worker delivery also passed; this is solo correctness, not supervision/load proof. The new contract suite passed8 tests; all owned fixture cleanup steps passed in Linux.

[Fresh exact resolved dependencies](../security/dependency-after-jwt-linux.json) and [scan metadata](../security/dependency-after-jwt-linux-metadata.json):55 packages, no skips, no python-jose/ecdsa and no known PyJWT findings. Known findings remain in3 packages,28 raw records/14 unique package-advisory IDs, mapped to61/62. These counts preserve duplicates and are not distinct exploitable-bug counts. The targeted gate passed; the full security/release gate is open.

For2,000 serial decodes after200 warmups, p50/p95/p99 were45.505/57.257/71.323 microseconds with zero errors, approximately21,073 serial operations/s on that runner. These are token-helper measurements, not HTTP RPS or a before/after speed improvement. No DB/cache queries are performed by this helper; aggregate API/worker/database effects under load remain F05. Raw durations/logs stay in the ignored/downloadable artifact, with sanitized summary preserved here. The repeated Windows clean-install timeout and Windows worker failure remain limitations; Linux success does not rewrite them as passes.
