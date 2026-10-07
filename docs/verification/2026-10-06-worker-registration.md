# Worker registration verification — AUD04a / issue #51

## Problem and change

Beat already publishes `aggregate_daily_stats` hourly, but a fresh worker did not import the module defining that task. Add `app.worker.beat_tasks` to the Celery loader's include list. This imports the definition at startup without creating an eager circular import. The regression uses a fresh interpreter and `loader.init_worker()` so previous tests cannot accidentally populate its registry.

The loader behavior is documented by [Celery 5.4 configuration](https://docs.celeryq.dev/en/v5.4.0/userguide/configuration.html#include). The delivery experiment uses one scheduler, following [Celery's periodic task guidance](https://docs.celeryq.dev/en/v5.4.0/userguide/periodic-tasks.html).

## Evidence

Base: owner-merged main `779206989c0d0e8377e5c7cf3b1e706927e9717f`; registration fix is the three-line include/comment diff. This checkout does not contain the original developer checkout's uncommitted QR prototype; no prototype file was published by this change.

| Check | Observed result |
|---|---|
| Fresh-interpreter regression before fix | Failed: aggregate_daily_stats missing from actual worker registry |
| Same regression after fix | Passed:one test; latest run3.52s |
| Actual worker + Redis dispatch | One solo Celery worker consumed record_click and the scheduled aggregate_daily_stats task |
| Actual PostgreSQL write | Two daily aggregate rows, counts4 and2, unique IPs0 and synthetic top countryZZ |
| Scheduler behavior | One due entry dispatched by one real Celery Scheduler instance; production period remains3600 seconds |
| Migrations | Fresh disposable PostgreSQL upgraded through0001_initial and0002_daily_stats |
| Fixture cleanup | Spawned worker and only two explicitly labeled test containers removed; shared Supabase/Langfuse untouched |
| Source preservation | Original checkout's76 audit source hashes remained unchanged; the fix lives in an isolated managed worktree |

Runtime: Python3.12.13, Celery5.4.0, SQLAlchemy2.0.36, Docker29.7.2, cached postgres:16-alpine and redis:7-alpine images. Services bind only loopback25432 and26379 with label `qr.worker.registration=20261006`. Synthetic credentials are embedded solely for these disposable fixtures. Fixtures use no client IP; GeoIP exits without a remote request. Worker pool is solo on Windows, not a Linux prefork verification.

## Reproduce

Use a separate environment containing requirements-ci.txt dependencies (runtime alone no longer installs pytest). From the reviewed checkout root:

```powershell
python -m pytest tests/test_worker_registration.py -q
python -m scripts.verify_worker_registration up
python -m scripts.verify_worker_registration verify
python -m scripts.verify_worker_registration down
```

Ensure Docker is running and the two named test containers and loopback ports are unused. `up` refuses existing names/ports; service operations verify ownership labels and port bindings. Run one verification on fresh fixtures. Always run `down` after a failed verification as well. Raw JUnit, worker/migration logs and evidence are ignored under output/.

The experiment starts a real worker child process, waits for a targeted broker ping, dispatches a real click task and waits for its result, then ages the existing hourly Scheduler entry in the test process so it is due. `Scheduler.tick()` publishes the task through real Redis; the worker executes the production rollup function, and the controller reads actual PostgreSQL rows. No task execution is mocked or eager. The scheduler is an in-process instance for a single tick; this does not prove production scheduler process supervision.

## Limits and remaining parent scope

This startup fix performs no DB/network work during module import and changes no redirect code. No latency, throughput, cost or capacity improvement is claimed. AUD04/#45 still requires pooling, idempotent event ingestion, incremental/batched rollups, lag evidence and production deployment/shutdown policy. F01's unapproved budgets and privacy choices remain in INPUT_REQUIRED.md. Keep the parent issue and milestone open.

The original audit remains historical evidence. Its clean-module-import probe did not run the worker loader; after this fix a plain import alone may still omit the beat module. The meaningful repaired contract is registration **at actual worker startup**, verified by the new regression and real worker experiment.
