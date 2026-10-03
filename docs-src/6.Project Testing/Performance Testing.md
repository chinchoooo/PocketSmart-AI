# Performance Testing

{{HEADER:5 Marks}}

## Step 1: Testing Overview

| Field | Details |
|---|---|
| Testing Tool Used | Custom Python load script `tests/perf_load.py` (httpx + threads, psutil for CPU/RAM sampling) |
| Type of Testing | Load testing (1, 10 and 25 concurrent virtual users, 20 s each) |
| Target Module / API | `POST /home-budget`, `POST /party-budget`, `POST /jewelry-budget`, `GET /recommendation-history` (rotating mix), after register + login |
| Test Environment | Local: Linux, 2 vCPU, 8 GB RAM, single Uvicorn worker, load generator on the same machine. **Offline-fallback mode (no `GOOGLE_API_KEY`)**, so results measure PocketSmart's own overhead (validation, budget engine, SQLite) and exclude Gemini network latency |
| Test Date | {{date}} |

## Step 2: Test Scenarios

| S.No | Test Scenario / Description | No. of Virtual Users | Duration (sec) | Expected Outcome |
|---|---|---|---|---|
| 1 | Baseline: one user cycling through all four endpoints | 1 | 20 | Fast responses, 0 errors |
| 2 | Typical classroom load | 10 | 20 | Avg < 2 s, 0 errors |
| 3 | Peak load | 25 | 20 | Avg < 2 s, max < 5 s, error rate < 1 % |
| 4 | Functional regression under test (pytest) | 1 | 18 | 43 of 43 tests pass |

## Step 3: Performance Test Results (25 virtual users)

| S.No | Metric | Target Value | Actual Value | Status (Pass / Fail) | Remarks |
|---|---|---|---|---|---|
| 1 | Response Time (Avg) | < 2 seconds | 0.104 s | Pass | 0.006 s at 1 user, 0.048 s at 10 users |
| 2 | Response Time (Max) | < 5 seconds | 2.055 s | Pass | p95 = 0.387 s; maximum most likely caused by bcrypt login and registration bursts at start-up |
| 3 | Throughput (Req/sec) | Not specified | 135 req/s | Pass | 159 req/s at 1 user, 172 req/s at 10 users |
| 4 | Error Rate | < 1% | 0.00 % | Pass | 0 failures in 2,724 requests (3,178 and 3,467 requests in the 1 and 10 user runs) |
| 5 | CPU Utilization | < 80% | avg 65 % of the 2-core machine (130 % of one core); peak 99 % | Partial | Average passes; peak is high because the load generator shares the same 2 cores |
| 6 | Memory Utilization | < 80% | 91 MB peak (about 1 % of 8 GB) | Pass | Server RSS grew only 74 MB to 91 MB across the runs |

## Step 4: Observations & Analysis

- PocketSmart's own processing is light: average latency stays at about 0.1 s even with 25 simultaneous users, and no request failed.
- In production the response time is dominated by the Gemini call (typically a few seconds). Blocking AI calls run in FastAPI's threadpool, so a slow Gemini reply for one user does not block others.
- Latency tails (max about 2 s) most likely come from bcrypt hashing at registration and login, which is intentionally slow for security.
- **Not measured:** live Gemini latency, because no API key was available during automated testing. The team should run `python check_gemini.py` and time a planner request with the real key before the demo and add the figure here.
- Scalability next steps: multiple Uvicorn workers, PostgreSQL, a shared session store (Redis) and response caching.

## Step 5: Screenshots / Evidence

Raw outputs are stored in `6.Project Testing/evidence/` (`load_1_users.txt`, `load_10_users.txt`, `load_25_users.txt`, `pytest_results.txt`).

```
virtual users      : 25
duration (s)       : 20.2
requests           : 2724
throughput (req/s) : 135.0
avg response (s)   : 0.104
p95 response (s)   : 0.387
max response (s)   : 2.055
error rate (%)     : 0.00
server CPU avg/max : 130% / 198% (of one core)
server RSS avg/max : 86 MB / 91 MB
```

Functional test run: `43 passed` (auth flow, validation edge cases, upload rejection, budget adherence, history privacy, Gemini success / failure / model fallback with mocks).

![Browser end-to-end run](assets/10_history_detail.png)
