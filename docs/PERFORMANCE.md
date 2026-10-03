# Performance requirements

Performance is a design and release gate for this platform, not a final cleanup task. FastAPI, PostgreSQL and Next.js are confirmed; hosting, regions, capacity and numerical budgets are **not yet agreed**. F01 approves them; F05 measures the baseline. No figures below are claims about the current software.

## Budget register to complete in F01
| Workload | Required agreement | Evidence |
|---|---|---|
| Basic redirect, warm cache | p95/p99 server latency, peak/sustained RPS, errors, availability | End-to-end HTTP run plus zero PostgreSQL reads on unrestricted hits |
| Cold/cache-miss and /q redirects | p95/p99, DB/Redis waits, burst capacity | Real PostgreSQL/Redis fixtures and query plans |
| Protected/routed/limited redirects | p95/p99, consistency and failure policy | Concurrent rule/redemption tests under load |
| Management API | p95/p99 by endpoint, max request/page size | Mixed read/write and growing-cursor workloads |
| Analytics | p95/p99 queries, maximum date range, ingest/rollup lag and allowed loss | Target-size fixtures, replay tests and query plans |
| Hosted pages | TTFB, LCP, transfer/JS/image size, network/device profile | Cold/warm mobile runs including image and font requests |
| Browser static generation | interaction/generation time, memory and supported device | Offline mobile profiling with realistic maximum payload/logo |
| Render/bulk/AI jobs | p95 completion, memory/CPU/concurrency and per-job cost | Saturation, timeout, cancellation and tenant fairness tests |
| Recovery | RPO/RTO, dependency outage behavior and cache freshness | Isolated restore/failover/revocation drills |
| Cost | Infrastructure ceiling and cost per workload/unit | Resource measurements tied to approved hosting prices |

The product scope's “under one second on weak signal” is an aspiration, not a test definition. F01 must define whether it means TTFB, content visibility or LCP, and specify bandwidth, latency, packet loss, device, cache state and page content before enforcing a number. Do not promise a universal network-independent load time.

## Structural gates effective now
- Unrestricted cache-hit redirects make zero PostgreSQL reads; identify any security/limit exceptions.
- No remote enrichment, rendering, AI, provider calls or unbounded retries on redirects.
- Bound cache/broker/DB connect waits and dispatch; prove Redis/worker outages preserve the approved behavior.
- Authoritative disable, password, expiry and redemption controls are not inferred from delayed analytics.
- Growing lists/ranges, body/upload sizes, event buffers, worker concurrency and memory are bounded.
- New queries have tenant scoping and workload-appropriate plans; no avoidable N+1 reads.
- CPU work is isolated from the API event loop; render saturation cannot starve scans.
- Published pages use versioned safe artifacts/cache behavior and exclude the editor runtime.
- Offline static payloads/logos never leave the device; third-party telemetry does not override that rule.
- Pool budgets include all API replicas, jobs, migrations and operational access.

## Reproducible measurements
Every report records commit, tool/version, OS/runtime, CPU/memory, replica/worker counts, region/network, schema/indexes, fixture seed/size/skew, cache state, offered load, actual throughput, warmup/duration, p50/p95/p99, error/timeout rates and raw artifact location. Separate server latency from browser/network latency. Do not follow the destination URL when timing a redirect; measure the redirect response itself.

Use anonymized synthetic fixtures representing popular and cold codes, many tenants, old/new revisions and large event histories. Exercise hit/miss, invalid-code floods, write/read races, protected code limits, queue/Redis failure, slow DB, mixed jobs and a soak long enough to reveal memory/queue growth. Set the duration and thresholds in F01. Report maximum and tail resource use rather than only average CPU.

For database changes collect EXPLAIN (ANALYZE, BUFFERS) on isolated representative PostgreSQL fixtures. ANALYZE executes the query: never run unknown writes or expensive analyses in production. Compare reads, rows, sort/spill, lock/pool waits and write/index costs; a sequential scan can be appropriate for small tables or broad queries.

## Regression and release handling
F05 records baseline values; relevant later issues compare against that exact profile. F03 adds deterministic cheap checks to normal CI; heavier load/soak tests run in a controlled environment as milestone gates. F01 chooses an allowed regression threshold only after baseline variance is understood. Review any exception with evidence, owner, expiry and a linked follow-up; never trade ownership/security or printed-link correctness for speed.

Split cache, event storage, workers, read models or databases only when measurements show a bottleneck and the additional operational costs are justified. Tune query/data access and pool/admission limits before speculative infrastructure expansion.

## Sources
- [PostgreSQL: Using EXPLAIN](https://www.postgresql.org/docs/16/using-explain.html) for plan interpretation; use the deployed server major version.
- [OWASP API Security risks](https://api-security.owasp.org/editions/2023/en/0x11-t10/) for authorization, resource bounds, SSRF and provider trust risks.
