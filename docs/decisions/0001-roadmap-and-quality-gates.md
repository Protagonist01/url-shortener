# ADR 0001: Evidence-gated QR delivery roadmap

Date: 2026-10-03
Status: Accepted for planning; runtime deployment/capacity decisions remain open in F01.

## Context
The supplied scope extends an existing shortener into offline QR tools, dynamic codes, hosted pages, brand features and a developer platform. The owner selected FastAPI, PostgreSQL and Next.js, made performance a top priority and requested agent instructions plus GitHub milestones/issues. Existing local QR work is uncommitted and cannot be treated as a clean production foundation.

## Decision
Use eight dependency-driven milestones with explicit launch and quality gates. Establish the baseline/audit before expansion, then deliver offline QR, dynamic code and constrained hosted-page capabilities as the MVP. Preserve the wider product catalog in scoped later issues and discovery gates rather than promising all features for launch.

Keep architecture and operational decisions tied to approved workloads. Enforce structural performance rules immediately (bounded work, cheap scan resolution, off-request heavy processing and workload-based indexes); set numerical budgets after agreement on deployment/traffic profiles.

## Alternatives considered
- Preserve only the five broad source phases: fewer milestones, but hosted pages and release readiness would share a large mixed stage.
- Create one issue per catalog bullet: finer granularity, but many unresolved integrations/expansion decisions would look implementation-ready.
- Chosen: forty outcome-based issues across eight milestones, with explicit prerequisites and child-issue splitting where actual implementation needs finer scope.

## Consequences
Agents can tell what is ready, what requires an owner decision and what counts as verified completion. The roadmap is larger than the MVP and makes that boundary explicit. The initial plan is a snapshot; live GitHub status and later justified child issues must be checked before work. This decision does not select hosting, pricing, privacy retention, a first industry pack or a microservice architecture.

## Evidence and follow-up
Eight milestones and forty issues were created in the confirmed repository. Remote verification checked unique identities, milestone assignments and prerequisite links. F01/F02 are the starting issues; F03–F05 establish repeatable quality/security, data and measurement foundations.
