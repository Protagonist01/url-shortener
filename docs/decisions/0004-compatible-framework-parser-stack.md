# ADR0004 — Upgrade framework, parser and metrics together

Status: implemented and actual Linux compatibility verified; final integration
pending in Sprint1/issue61.
Date:2026-10-08. Scope: dependency repair, not deployment/product policy.

## Problem and decision
Remaining actual reports identify thirteen canonical Starlette/multipart IDs.
Current FastAPI0.115.6 and instrumentator7.0.0 both constrain old Starlette.
Pin FastAPI0.141.1, Starlette1.7.0, multipart0.0.32 and instrumentator8.1.0
together. Existing Pydantic/Prometheus pins satisfy their primary metadata.
Choose the latest pre-OpenTelemetry FastAPI release for this narrow repair;
future support/advisories remain F03 responsibilities, with no maintenance promise.

## Alternatives and tradeoffs
Forcing new Starlette with the old consumers breaks declared compatibility.
Upgrading only FastAPI still leaves instrumentator's below1 constraint.
Latest FastAPI0.142.4 adds a telemetry API dependency; accepting that broader
change needs its own behavior/performance review. Removing multipart would
reduce optional surface but silently avoid, rather than repair and verify,
the parser contract requested by61 and future published upload checks.

## Evidence and consequences
[Verification/source map](../verification/framework-dependency-remediation.md)
links exact metadata, maintainer fixes, all thirteen boundaries, fresh scan
requirements and rollout/rollback. [Sprint1](../sprints/01-issue-61.md) governs
completion: actual Linux/Python3.12 resolution and API/image/worker/resource
checks are mandatory. Candidate metadata and local tests alone cannot pass.
Strict JSON headers/newer library defaults require HTTP client regression checks;
HTTPX TestClient fallback deprecation remains visible. No new production route,
schema, migration, telemetry exporter or upload quota is added. Unpublished QR
work is excluded. F01/F05 performance budgets and parent release gates remain.
