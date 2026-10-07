# Compatible framework/parser repair — issue61

Status: candidate implementation; actual Linux resolution/HTTP/resource evidence
is pending. Do not close61 or advance Sprint1 from this document alone.

## Compatible pins and scope

FastAPI0.141.1, Starlette1.7.0, python-multipart0.0.32 and
prometheus-fastapi-instrumentator8.1.0 are pinned jointly in requirements.txt.
Their primary PyPI metadata permits Python3.12, existing Pydantic2.10.4 and
Prometheus0.21.1. Instrumentator7.0.0 requires Starlette below1; upgrading the
framework alone or forcing an incompatible override is insufficient.
FastAPI0.141.1 metadata admits Starlette>=0.46, while8.1.0 admits>=1,<2.

The current latest FastAPI0.142.4 has a new base OpenTelemetry API dependency.
Choose the latest pre-OpenTelemetry release for this scoped repair; this is not
a claim of an ongoing upstream maintenance promise. F03 must continue checking
future supported releases and advisories. No exporter, external telemetry or
additional service is enabled. Existing JSON endpoints, metrics and static file
delivery are compatibility requirements. No schemas/indexes/migrations change.

Primary sources checked2026-10-08:
[FastAPI metadata](https://pypi.org/pypi/fastapi/0.141.1/json),
[Starlette metadata](https://pypi.org/pypi/starlette/1.7.0/json),
[multipart metadata](https://pypi.org/pypi/python-multipart/0.0.32/json),
[instrumentator metadata](https://pypi.org/pypi/prometheus-fastapi-instrumentator/8.1.0/json),
[FastAPI releases](https://fastapi.tiangolo.com/release-notes/),
[Starlette releases](https://starlette.dev/release-notes/),
[multipart0.0.32](https://github.com/Kludex/python-multipart/releases/tag/0.0.32),
[instrumentator8.1.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/releases/tag/v8.1.0).
Public wheel bytes were verified against the metadata SHA256 before source review.

## All thirteen recorded advisory boundaries

The preserved baseline/scoped reports retain raw IDs and aliases. The following
table reviews every canonical ID, using its maintainer source; a fixed version
is a source assertion until actual fresh scans and contracts agree.

| Canonical ID | Maintainer fix | Boundary and regression |
|---|---|---|
| PYSEC-2026-161 | [1.0.1](https://github.com/Kludex/starlette/security/advisories/GHSA-86qp-5c8j-p5mr) | Host containing path/authority characters must not change reconstructed path or trusted authority; ordinary Host control |
| PYSEC-2026-1941 | [0.47.2](https://github.com/Kludex/starlette/security/advisories/GHSA-2c2j-9gv5-cj73) | A write crossing spool threshold runs in a worker thread; actual file bytes preserved; fixture2MiB uploads coexist with redirects |
| PYSEC-2026-1942 | [0.49.1](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8) | Large invalid numeric range fails safely; overlapping/suffix ranges and excessive-range fallback; published static/root HTTP controls |
| PYSEC-2026-2280 | [1.1.0](https://github.com/Kludex/starlette/security/advisories/GHSA-x746-7m8f-x49c) | Custom HTTP verb cannot invoke an internal HTTPEndpoint helper; ordinary GET works |
| PYSEC-2026-2281 | [1.1.0](https://github.com/Kludex/starlette/security/advisories/GHSA-wqp7-x3pw-xc5r) | Absolute/UNC input rejected before filesystem resolution, with a spy that prevents any SMB contact; normal static lookup works |
| PYSEC-2026-248 | [1.3.0](https://github.com/Kludex/starlette/security/advisories/GHSA-jp82-jpqv-5vv3) | Non-slash path cannot move authority to an attacker hostname |
| PYSEC-2026-249 | [1.3.1](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq) | Urlencoded field count/size enforced across chunks; legitimate fields accepted |
| PYSEC-2026-1852 | [0.0.22](https://github.com/Kludex/python-multipart/security/advisories/GHSA-wp53-j4wj-2cfg) | Nondefault retained filenames cannot overwrite an owned sentinel outside upload directory; only synthetic temporary paths |
| PYSEC-2026-3036 | [0.0.30](https://github.com/Kludex/python-multipart/security/advisories/GHSA-5rvq-cxj2-64vf) | Separator-heavy form input stops at explicit fixture field bound; mixed HTTP/resource probe |
| PYSEC-2026-3037 | [0.0.30](https://github.com/Kludex/python-multipart/security/advisories/GHSA-6jv3-5f52-599m) | Semicolon remains ordinary value bytes across stream chunk sizes; cannot introduce an overriding role field |
| PYSEC-2026-3038 | [0.0.26](https://github.com/Kludex/python-multipart/security/advisories/GHSA-mj87-hwqh-73pj) | Large preamble/epilogue keeps legitimate payload; bounded synthetic input |
| PYSEC-2026-3039 | [0.0.27](https://github.com/Kludex/python-multipart/security/advisories/GHSA-pp6c-gr5w-3c5g) | Oversized part header/repeated header count rejected; ordinary part accepted |
| PYSEC-2026-3040 | [0.0.31](https://github.com/Kludex/python-multipart/security/advisories/GHSA-v9pg-7xvm-68hf) | Negative Content-Length rejected before any stream read; legitimate chunked convenience-API control |

Published app/main.py serves StaticFiles and FileResponse, so static/Range paths
are actually reachable. There are no published request.form, Form, UploadFile,
HTTPEndpoint subclasses or parse_form consumers. The negative-length record
explicitly distinguishes parse_form from Starlette's streamed parser. Library
probes prepare regressions; they do not establish exposed production upload
routes or exploitability of all thirteen findings. Windows UNC guard is checked
without contacting a host; Linux CI alone does not prove Windows runtime behavior.
Owner's unpublished QR uploads and /q aliases remain IN08 and are not copied here.

## Reproduce and judge evidence

Install requirements-ci.txt in a fresh disposable Linux/Python3.12 environment,
then run pip check. Run `python -m unittest tests.test_framework_boundaries -v`.
Foundation CI also runs the runtime Docker image, token/worker/migration tests
and guarded real API suite. `scripts.verify_authentication` installs parser and
loop-observer routes only in its owned loopback fixture and calls verify_framework.
It confirms root/static exact bytes, range/status/cache/path controls, metrics,
malformed JSON/non-JSON and concurrent printed-anchor redirects.

The mixed experiment uses one owned API, real isolated PostgreSQL/Redis,
synthetic GeoIP and BackgroundTasks tracking. It compares40 redirects in four
lanes with the same redirect workload plus24 static requests,16 bounded invalid
forms and four2MiB synthetic file parses. Eight HTTP connections, finite loops,
10ms CPU/RSS/thread/loop sampling and a30s experiment timeout bound the fixture.
Form limits8 fields/1 file/256-byte part are test values, not product quotas;
max_part_size does not impose a maximum uploaded file size.

Artifacts output/framework-dependency/evidence.json and mixed-workload-raw.json
record source/runtime/pins/profile, p50/p95/p99/max latency/loop lag/RSS/CPU,
actual host CPU/memory, throughput, errors/timeouts and raw samples. Quantiles
use empirical nearest rank; four file samples cannot estimate stable tails.
These are finite closed-loop requests without dedicated warmup;10ms sampling
can miss short resource spikes. A short compatibility experiment is
not saturation, sustained capacity, queue delivery, zero-DB-read or a production
SLO pass. Worker delivery is checked separately. No new DB query/index exists to
EXPLAIN; existing analytics/pools/redirect dispatch require later issue gates.
F01/F05 must approve and verify release budgets; none is silently waived here.

The separate actual advisory job audits runtime/test/operations without ignored
IDs. Its targeted gate requires exact clean framework/parser/instrumentator pins
in all scopes and keeps unrelated findings visible. Scanner-tool and historical
test fixtures remain outside app resolution; no clean full-security claim follows.

## Rollout and rollback

Rebuild the complete pinned image; do not hot-patch only Starlette. Check startup,
Alembic, worker/beat/monitoring, metrics and JSON clients in staging. FastAPI's
newer strict JSON content-type behavior may reject clients omitting the header;
test valid application/json and invalid/missing header contracts. Existing
optional bearer behavior must remain explicit. HTTPX0.28.1 remains supported by
this Starlette TestClient fallback but emits a deprecation; an HTTPX2 migration
is separate compatibility work, not required for these application HTTP clients.
No schema/printed destination change is authorized; retain stable redirect paths
and anchor bytes. Validate any later published upload/QR export separately.

If integration fails before release, keep61 open and correct the candidate.
Rollback an app image only under the established deployment authority; reverting
to the old stack reintroduces known advisories and is not an accepted secure
steady state. No production deployment, historical secret cleanup, owner budget
decision or release approval is performed by this PR.
