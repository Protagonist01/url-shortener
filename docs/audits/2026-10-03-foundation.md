# Foundation audit — 2026-10-03

Tracks [F02](https://github.com/Protagonist01/url-shortener/issues/2). Result: **prototype functionality exists; launch gates fail**. This deliverable records evidence and follow-up work; it does not repair application behavior or establish production readiness.

## Scope and source identity

Audited the owner's existing dirty Windows checkout of main at `26eee06929f6e3cfd6522de3657ea19996d3c212`, not just committed main. Tracked modifications and untracked QR modules, migration 0003, assets and tests are part of the observed prototype. The local snapshot records SHA256 for 76 existing app/test/migration/config/README files. None changed during the audit. BUILD_BOOK.md is appended as a journal; its earlier changes are preserved and excluded from the publication commit.

Only audit helpers, this report, sanitized evidence and a proposed ADR are published by this task. The earlier roadmap is in [draft PR #41](https://github.com/Protagonist01/url-shortener/pull/41). Until existing prototype files are separately reviewed and committed, a clean clone cannot reproduce this working-tree result. The evidence file records each source hash so a future agent can identify drift.

No .env values were opened, copied or published by the audit. Git lists `.env` as tracked; active credential exposure was not determined. Test processes override all credential-bearing application settings with synthetic local values before import.

## Inventory

| Area | Observed implementation | Missing proof or work |
|---|---|---|
| API | FastAPI routes, SQLAlchemy AsyncSession, JWT/bcrypt, URL creation/list/delete, redirects and analytics | Ownership, safe failure behavior and approved latency/capacity budgets |
| Database | Alembic 0001 initial, 0002 country data, uncommitted 0003 QR destinations; users/short_urls/click_events/daily_stats/qr_destinations | Tenant migration design, query plans at scale, rollout/restore/recovery |
| Cache/jobs | Redis URL cache/rate limiter, Celery click task and separate beat rollup module; in-process tracking alternative | Bounded dispatch, registration, idempotency, retention and measured connection budget |
| QR | Server classic/image renderer and style previews, native decoder validation, /q mappings; image renderer identifies itself as 5.0 | Free offline catalog is not implemented; current QR studio sends payload/image to server |
| UI | Existing HTML/JS dashboard and QR studio; JWT in localStorage | Next.js migration, session/CSRF design and browser/accessibility evidence |
| Operations | Docker/Compose, Render blueprint, Prometheus instrumentation, process health endpoint, keepalive workflow | Reproducible CI, readiness, one release migration job, durable jobs/backup drills |

## Verification results

Runtime: Python 3.12.13, FastAPI 0.115.6, SQLAlchemy 2.0.36, Redis client 5.2.1, Celery 5.4.0, bcrypt 4.2.1, Pillow 12.3.0, numpy 2.5.3, OpenCV 5.0.0.93, zxing-cpp 3.1.1, pytest 8.3.4. Docker server 29.7.2; disposable PostgreSQL 16 and Redis 7 containers. This is a local Windows compatibility run, not a pinned clean-install or advisory audit.

| Check | Result | Evidence and limits |
|---|---|---|
| Focused existing QR, aliases and URL-service suite | **81 passed, 1 failed** / 82; 154.27 s | `focused.xml`; off-white split-logo image rejected by final scan gate. Preserve the gate; investigate fixture/renderer/dependency sensitivity |
| Existing API suite against real isolated services | **18 passed**; 11.30 s | Final sequential `api.xml`, after adding audit-server identity guard; GeoIP replaced with synthetic ZZ. Covers behavior expected by existing tests, not missing authorization guarantees |
| Real PostgreSQL migrations | **Passed** | Empty isolated DB upgraded 0001→0002→0003; `alembic_version=0003_qr_destinations`. Does not prove downgrade, old/new app compatibility or restore |
| Alias/fragment contract checks | **Passed within focused suite** | Custom `-`/`_` aliases, reserved current routes, auto/custom collision fallback, /q fragment precedence. Concurrent uniqueness and all future Next routes remain unverified |
| Owned /q redirect live | **302**, original fragment retained | Synthetic owner/link/QR mapping, real PostgreSQL/Redis; direct source deactivation gives /q **404** |
| Ownership and failure probes | **Failed gates** | Results below, captured in offline/live JSON; offline cases use controlled mocks rather than latency/outage load measurements |
| Source preservation | **Passed** | 76 hashes compared, zero existing source files changed |
| Load, recovery, physical QR scans, external providers, browsers and accessibility | **Unverified** | No production guarantee, external availability claim or camera/print reliability claim |

The first API test run began before the audit server was ready (17 passes/1 startup failure). A later overlapping API/live run allowed the test fixture's cache cleanup to affect the live probe. Both attempts are retained in ignored raw artifacts, excluded from final claims. Added a health wait, recreated only the disposable test database, then ran the API suite and live probes sequentially (18 passes/29.24 s). Finally added an audit-only HTTP identity marker, restarted/reset the owned services and repeated sequentially (18 passes/11.30 s); the final artifact records that run. Timing differences are not a throughput benchmark. Existing API fixtures clear Redis keys but do not clean database rows; run them on a fresh isolated DB.

## Findings and required follow-ups

| ID | Gate / evidence | Required outcome and roadmap mapping |
|---|---|---|
| AUD01 | **Access fail:** anonymous GET of an owned link's analytics returns **200**; user dependency is unused (`app/api/analytics.py`). Anonymous-created URL deletion returns **204** (`app/api/urls.py`) | Owner-scoped analytics and management; explicit policy for anonymous legacy links, cross-owner negative tests. Maps F03/D01/D04 |
| AUD02 | **Auth/secrets fail:** tracked .env; bcrypt 4.2.1 accepts distinct passwords after identical first 72 bytes in the controlled probe. Hash/verify execute synchronously in async handlers (`app/core/security.py`, `app/services/auth_service.py`) | Assess actual secret exposure without publishing values; remove secret configuration from tracking in a dedicated change. Choose migration-safe password policy and bounded off-event-loop crypto. Review localStorage/CORS/session/CSRF. Maps F03 |
| AUD03 | **Redirect fail:** Redis get error propagates with **zero DB fallback calls**; Celery enqueue exception propagates before302. A bearer-authenticated cached request performs **one user lookup** (`app/api/deps.py`); no bearer means no such lookup | Bounded cache/dispatch failure policy, lightweight unrestricted redirect path, measured outage behavior. Cache write follows durable creation commit; delete invalidates before DB commit, permitting a refill race (`app/services/url_service.py`). Direct DB deactivation gives cached short302 but /q404: this demonstrates an invalidation policy gap, not API-delete behavior. Maps F04/F05/D01/D03 |
| AUD04 | **Job fail/risk:** clean worker-module import lacks scheduled `aggregate_daily_stats`; task defined only in separate module. Engine created/disposed per click; no event dedupe ID. Seven-day repeated rollup plus per URL/day country query and upsert (`app/worker/celery_app.py`, `beat_tasks.py`) | Register scheduled task, test worker/beat/retries with real services, pool per process, idempotency and incremental/batched rollup. Render blueprint has no worker/beat and uses crash-lossy BackgroundTasks. Maps F03/F04/D03 |
| AUD05 | **Privacy/proxy fail:** arbitrary X-Forwarded-For192.0.2.123 accepted over peer127.0.0.1. Raw IP stored, external plain-HTTP GeoIP call, incomplete string private-range filtering (`redirect.py`, `rate_limit.py`, `geoip_service.py`) | Configure trusted proxies, normalize IPs, approve retention/disclosure and provider policy; prevent untrusted headers bypassing identity/rate controls. GeoIP availability not tested. Maps F01/F03/D03/D04 |
| AUD06 | **Bounds/performance fail:** days=1,000,000,000 returns **500**. List limit/offset lack safe range; created_at ordering has no deterministic tie. Analytics still counts/groups raw history; rollups only cover timeseries (`analytics_service.py`, `url_service.py`) | Bound ranges/page sizes; deterministic cursor design and matching constraints/indexes; EXPLAIN and resource/connection timeout budgets. Existing Redis rate limiter pipeline is transactional; do not report it as non-atomic. Maps F04/F05/D04 |
| AUD07 | **QR regression fail:** `test_split_logo_cleanup_passes_final_scan_gate_and_reports_ink_reduction` raises ValueError at art.py522 on off-white fixture | Diagnose actual dependencies/renderer and preserve final-byte two-decoder/18-transformation acceptance. Retain upload5 MiB/12 MP, child25 s/256 MiB, global render admission one/60 s. Synthetic success is not camera/print proof. Maps F03/Q05/B03 |
| OPS | **Unverified/failing structure:** /health does not check dependencies; start.sh migrates per API startup; keepalive workflow is not CI; Render free-plan comments are not validated current hosting guarantees | F03 adds isolated CI/advisories; F04 one release migration job; F05 capacity/recovery; P05 production release evidence. No shared/production services were tested |

Follow-up issue identities are in [foundation-followups.json](foundation-followups.json); they are remediation work, not mandatory child deliverables of this evidence-only audit. F02 completion does not mean those defects are fixed. Critical findings block release and dependent readiness claims.

## Printed-link and client compatibility matrix

| Contract | Existing behavior/evidence | Migration requirement |
|---|---|---|
| GET /{short_code} | 302; aliases1–16 ASCII letters/digits/_/-; invalid aliases404; known route collisions rejected | Preserve lookup/aliases/Location/fragment rules on original hostname; route public paths before Next catch-all. Inventory existing collisions before expanding reserved paths |
| GET /q/{code} | Persisted QR mapping; owned-source/lifecycle lookup; destination fragment retained; decorative art fragment replaced | Preserve mapping rows and old public hostname across backfill, changes and rollback; test original/destination/empty-fragment cases |
| /api/auth, /api/urls, /api/analytics | Existing HTML client and test suite depend on these routes and shapes | Keep API contracts during UI transition; introduce explicit versioning/deprecation only through reviewed change |
| /api/qr/render and exports | Server upload/render and manifest, experimental image modes | Keep old printed destinations working; introduce offline static generation separately. Never relabel the uploaded workflow as private/offline |
| External is.gd links | Generation endpoint plus30-day Redis cache; mocked success/rejection/cooldown tests passed | Preserve stored external payloads; platform cannot edit or restore provider-owned printed links. Record provider dependency in UI; no live provider longevity test performed |
| /static, /, /health, /metrics, docs | Current mounts/paths precede short-code router | Next routing must reserve all new route roots, preserve necessary assets, and keep monitoring routes deliberate |

The public XOR ID salt is reversible and present in source. It is not authorization or secrecy. The API, database unique constraints and ownership policy must handle collisions and access independently.

## Next.js transition plan

1. Review and publish existing prototype changes separately, so clean CI can reproduce them. Resolve F01 deployment/session/privacy decisions.
2. In F03 establish backend and fresh PostgreSQL/Redis CI; scaffold locked Next.js in a dedicated frontend directory. Document lint/type/build/browser commands and Linux adapter compatibility checks.
3. Keep FastAPI owning existing /api, /q and short-link paths. Verify reverse-proxy routing before replacing /. Do not add a catch-all that swallows printed codes.
4. Build M1 static generation as browser code, including downloaded assets/offline behavior and network assertions that payloads/logos never leave the device. Separate existing experimental upload modes.
5. Replace dashboard/editor flows incrementally behind preserved contracts; choose cookie/token/CSRF handling explicitly. Test keyboard/mobile/error paths and unauthenticated/cross-owner access.
6. Release to preview first. Replay a fixture inventory of old printed links and client contracts, test rollback routing, then obtain launch approval through P05.

## Reproduce safely

Use the same source snapshot and an existing environment with the recorded versions. `scripts/audit_foundation.py` always supplies synthetic local settings. Service modes check container labels and loopback port bindings before importing the application. Snapshot excludes secret configuration values; focused/offline modes use controlled doubles.

From the repository root in PowerShell, verify ports15432,16379,18000 and the two named containers are unused before creation. If a container already exists, inspect its identity; never remove or reuse an unrelated service. No volumes are supplied. These synthetic credentials are for this disposable audit only:

```powershell
docker run --detach --name qr-foundation-audit-20261003-db --label qr.foundation.audit=20261003 --publish 127.0.0.1:15432:5432 --env POSTGRES_USER=audit --env POSTGRES_PASSWORD=audit --env POSTGRES_DB=qr_audit postgres:16-alpine
docker run --detach --name qr-foundation-audit-20261003-redis --label qr.foundation.audit=20261003 --publish 127.0.0.1:16379:6379 redis:7-alpine
.venv/Scripts/python.exe -m scripts.audit_foundation snapshot
.venv/Scripts/python.exe -m scripts.audit_foundation offline
.venv/Scripts/python.exe -m scripts.audit_foundation focused
# Wait until pg_isready succeeds in the owned DB container, then:
.venv/Scripts/python.exe -m scripts.audit_foundation migrate
.venv/Scripts/python.exe -m scripts.audit_foundation serve
```

In another repository-root terminal, run `api-tests`, then `live`, then `compare` using the same module command. Do not run live probes concurrently with existing API tests because their cache fixture clears keys. API runner waits for health before testing; freshness of DB fixtures remains required. Expected focused suite exit is1 until AUD07 is fixed.

Stop only the audit server you started, verify the audit label again, and remove only the two explicitly named audit containers. Existing Supabase/Langfuse containers were untouched. Raw JUnit/probe/server artifacts stay in ignored `output/foundation-audit`; sanitized results/hashes are in [foundation-evidence.json](foundation-evidence.json). Source comparison and service-identity guard compile/import checks supplement application tests; no production load benchmark applies to documentation changes.
