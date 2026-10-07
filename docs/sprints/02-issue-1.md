# Sprint2 — issue1: architecture and performance decision gate

Status: **active — held at G0, input_required**.
Issue: https://github.com/Protagonist01/url-shortener/issues/1
Live body inspected2026-10-08. Predecessor61 has all scoped G0–G5 passed,
merged PR67 and verified fetched main/closed issue. No next-stage implementation
starts from this record. There is no calendar duration commitment.

## Gates

| Gate | State | Evidence / remaining work |
|---|---|---|
| G0 | input_required | Owner approvals IN01–IN06 are pending; no hosting/region/budget/privacy/recovery targets are inferred |
| G1 | pending | Owner-approved ADRs and full budget/profile/cost model; explicit dependencies held; evidence mapped to live acceptance |
| G2 | pending | Discovery/source verification and applicable compatibility/printed-link/privacy constraints; review only after choices are concrete |
| G3 | input_required | Agreed measurement boundaries/hardware/data/cache/network, cost ceiling and performance/recovery/delivery budgets required |
| G4 | pending | Reviewed final approved decisions/docs and relevant current-head checks; no provider provisioning or deployment authorized |
| G5 | pending | Reviewed authorized decision PR merged, fetched state and GitHub completion verified; issue1 remains open |

## Required owner inputs

Enter explicit answers in [INPUT_REQUIRED.md](../../INPUT_REQUIRED.md).
The [existing ADR0002 proposal](../decisions/0002-small-launch-hosting-proposal.md)
provides a reviewable starting direction and synthetic workload. It remains a
proposal; Sprint1 measurements do not approve its targets.

| Input | Decision required | Current evidence |
|---|---|---|
| IN01 | Adopt or revise the proposed modular FastAPI/CPython containers/managed PostgreSQL plus Cloudflare frontend/edge direction? | FastAPI/PostgreSQL/Next.js confirmed; Cloudflare only a candidate; exact adapter/provider deployment still unverified |
| IN02 | Monthly infrastructure ceiling and primary audience/data region? | Both undecided; owner's timezone is not an audience/region selection |
| IN03 | Adopt or revise ADR0002's dataset/traffic/resource/latency/network benchmark profile? | Proposed10k codes/1M events,20 RPS sustained/100 burst; warm p95≤100ms/p99≤250ms; not an approved forecast or result |
| IN04 | Required availability and acceptable backup data loss/recovery time (RPO/RTO)? | No numeric guarantee approved |
| IN05 | Acceptable analytics lag/loss and raw IP/GeoIP retention/provider disclosure? | Existing data/network behavior needs explicit minimization policy; no retention period approved |
| IN06 | Maximum edit/revocation cache freshness window and protected/disabled-code outage policy? | Correctness required; no stale-serving exception approved |

IN07–IN18 remain required where their own issue depends on them; these six
answers do not implicitly approve pricing, ownerless management, secret rotation,
prototype publication, names/domains or later providers/expansion.

## Acceptance and continuation

Live1 requires owner-approved architecture/budgets with measurement boundaries,
hardware/dataset/cache/network/cost model, explicit holds for unresolved choices,
verified prerequisite outcomes and linked implementation/evidence. Performance
verification also requires reviewed policy and reproducible profile/results;
discovery documents where benchmarking does not apply. No acceptance box is
marked complete just because this input register exists.

Do not advance to42 while G0/G3 are held. Continue only independent discovery
inside1 without choosing unknown policy or spending money. Any approved answer
must be reconciled with ADRs/PERFORMANCE.md/live issues before implementation.
MilestoneM0 still has11 open/eight completed issues; all8 milestones are open.
