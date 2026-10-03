# ADR 0002 — Small launch architecture and hosting proposal

Date: 2026-10-03. Status: **proposed; owner approval pending**. Tracks [F01](https://github.com/Protagonist01/url-shortener/issues/1).

## Confirmed input

The owner selected FastAPI, PostgreSQL and Next.js. Hosting, region and monthly budget are undecided; Cloudflare is a candidate. Launch is expected to be relatively small, followed by growth. The numerical test profile below is a proposal, not a forecast or approved guarantee.

## Proposed starting architecture

Use a modular FastAPI application and one PostgreSQL correctness authority. Keep Redis and Celery provisionally, fixing their current failure and registration problems before relying on them. Keep redirects lightweight; execute rendering and enrichment behind bounded job admission. Start with separate API and job processes from the same codebase; separate the redirect deployment only when measured contention warrants it.

Use actual Next.js for the interface. Evaluate its OpenNext Cloudflare adapter with a Linux CI build and preview tests; retain standard Next.js tooling for Windows development. OpenNext documents this development/CI arrangement because Windows support is limited. No frontend has been scaffolded or deployed. [OpenNext documentation](https://opennext.js.org/cloudflare).

Place the CPython backend, PostgreSQL, Redis and workers in one selected region with private service connectivity. Evaluate Cloudflare as the public edge/frontend host. Choose the container/database providers only after the owner sets a spending ceiling and audience/region constraints. Cloudflare Containers is one candidate requiring a compatibility/cold-start/cost trial; a conventional container host is another. Keep database durability in managed PostgreSQL, independent of ephemeral application instances.

Do not cache authenticated management responses at the edge. Initially pass redirect requests to the authoritative backend; introduce edge redirect caching only after the revocation window and invalidation protocol are approved and tested. Public URLs and host routing must survive frontend replacement.

## Cloudflare compatibility evidence

| Component | Verified documentation | Project implication |
|---|---|---|
| FastAPI | Python Workers provide an ASGI entrypoint | Framework support exists; this is not proof that the repository runs unchanged. [FastAPI guide](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/) |
| PostgreSQL driver | Hyperdrive's Python guide recommends asyncpg, with compatibility date 2026-09-08 or later | A future driver-level experiment is possible. The same guide explicitly says async SQLAlchemy ORM is unsupported because greenlet is unavailable; this repository uses AsyncSession. [Python Hyperdrive guide](https://developers.cloudflare.com/hyperdrive/examples/python-workers/) |
| Database service | Hyperdrive accelerates connections to existing external databases | It does not supply this project's managed PostgreSQL database. [Hyperdrive overview](https://developers.cloudflare.com/hyperdrive/) |
| Native QR renderer | Python Workers use Pyodide; threading/multiprocessing are nonfunctional and native packages need compatible builds | Existing subprocess/psutil/OpenCV/zxing execution has not been validated there. Keep the renderer in CPython containers for the proposed launch. This is an inference about this repository, not a blanket claim that image libraries cannot run on Workers. [Standard library](https://developers.cloudflare.com/workers/languages/python/stdlib/), [packages](https://developers.cloudflare.com/workers/languages/python/packages/) |
| Next.js | OpenNext adapts Next.js builds to Workers | Test the exact locked Next.js/adapter versions, SSR, cookies, assets, revalidation and error paths before selection. [OpenNext](https://opennext.js.org/cloudflare) |
| Framework alternative | Cloudflare's current Next.js guide presents vinext, a beta reimplementation | Do not silently replace the owner's chosen Next.js runtime with vinext. Adoption would be a separate owner decision. [Cloudflare guide](https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/) |

## Proposed first measurement profile

These figures make F01 review concrete. They do not assert current performance. F05 will measure them after approval and after critical defects are fixed.

| Dimension | Proposed profile |
|---|---|
| Synthetic data | 1,000 accounts, 10,000 active codes, 1,000,000 events over 30 days; deterministic seed and recorded index/schema versions |
| Traffic | 20 redirects/s for 15 minutes, 100/s burst for 60 seconds; 2 management requests/s and 1 analytics request/s alongside redirects |
| Distribution | Warm run: 80% of requests to 100 hot codes, 19% to remaining active codes, 1% invalid codes; separate 100% miss run |
| Initial reference resources | API 2 vCPU/2 GiB with two processes; worker 1 vCPU/1 GiB with concurrency one; PostgreSQL 1 vCPU/2 GiB; Redis 256 MiB. Record actual provisioned limits; this is a reproducible benchmark specification, not a provider purchase |
| Connection budget | Proposal: API pools 5 + overflow 0 per process, worker pool 2 + overflow 0; reserve 5 operational/migration connections. Reconcile with provider max connections and all replicas before provisioning |
| Redirect targets | Server response p95 ≤100 ms/p99 ≤250 ms warm; p95 ≤250 ms/p99 ≤500 ms cold and /q; <0.1% unexpected errors at the specified load; zero PostgreSQL reads on unrestricted warm hits |
| Management/analytics | Management p95 ≤300 ms; bounded 30-day analytics p95 ≤1 s at the profile data size. Record p50/p95/p99 and plans, not averages alone |
| Mobile page experiment | Proposed midrange Android profile: 1.6 Mbps down/750 Kbps up, 150 ms RTT, cold cache, constrained published page; LCP ≤2.5 s. Specify exact emulated/physical device before approval. “Under one second on weak signal” remains undefined |
| Jobs | Retain current renderer admission and resource bounds until stronger evidence exists; benchmark p95 completion, memory and scan validation separately from redirects |
| Growth exercise | Repeat at 10× rows and sustained traffic; publish the first limiting resource and upgrade plan. Passing 10× is not an initial launch promise |

Track latency at the server and separately from an agreed client region. A 100 RPS burst is not a 100 RPS sustained monthly forecast. No performance run has been performed in this audit.

## Cost and operations decision still required

Build a monthly estimate as frontend/edge requests + API instance hours + worker hours + PostgreSQL storage/compute/backups + Redis memory/persistence + object storage/egress + logs/metrics. Show idle, expected and 10× usage, including sleeping-service latency and operational effort. The spending ceiling is **TBD**; do not provision paid resources from this proposal.

Cloudflare Containers pricing currently starts with the $5/month Workers Paid plan and charges for container resources, network and related services. That is not a complete platform price. Measure running hours and provisioned memory/disk before estimating it. [Container pricing](https://developers.cloudflare.com/containers/platform/pricing/).

F01 also needs explicit approval of: audience/data region, availability target, RPO/RTO, analytics delivery/loss and lag, raw IP retention/GeoIP disclosure, revocation consistency, and the proposed profile. Do not retain raw IPs by default in new design work. Decide the first industry pack from a documented discovery process when its roadmap issue is reached.

## Order of work and growth triggers

1. Review this proposal and the foundation audit. Resolve the missing policy/budget inputs.
2. Address access, authentication and redirect correctness findings; establish F03 CI and F04 migration/constraint work.
3. Run F05's profile, dependency-outage and saturation experiments. Adjust limits from evidence.
4. Scaffold Next.js behind preserved route contracts; implement browser-local static generation in M1.
5. Increase API replicas only with a reconciled DB connection budget. Scale job concurrency separately only after tenant fairness and memory tests. Add partitioning, a separate redirect service or an edge data replica only with query/lag/cost evidence.

F01 remains open. Approval of the architecture direction alone would not approve unresolved numerical budgets, privacy policy or a deployment.
