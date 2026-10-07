## Result
Describe the problem and final behavior. Link the issue and milestone.

## Verification
Record commands, commit/profile/fixtures and results. Label unavailable checks as unverified.
Link the active sprint gate record in docs/sprints/; map G0–G5 and each live issue
acceptance criterion to evidence. State the next step and any held gate.

## Performance
Describe database/query, latency, resource/queue and page/bundle impact as applicable.
Link measurements against docs/PERFORMANCE.md, or explain why benchmarks do not apply.

## Rollout and risks
Explain schema/configuration changes, backwards compatibility, printed-link continuity,
failure behavior and rollback. Link relevant ADRs and Build Book entries.

- [ ] Issue acceptance criteria and prerequisites are satisfied.
- [ ] Relevant security/privacy/tenant isolation and accessibility checks pass.
- [ ] Relevant performance budgets and failure/concurrency checks pass.
- [ ] Documentation and migration/recovery instructions are current.
- [ ] Diff contains only this task's authorized work.
- [ ] Active sprint gates are evidenced; issue/parent/milestone completion claims match their full scope.
