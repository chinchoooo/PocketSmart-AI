# Scalability & Future Plan

{{HEADER:1 Mark}}

## Current System Limitations

| S.No | Limitation | Impact | Priority to Address (High / Medium / Low) |
|---|---|---|---|
| 1 | Sessions and token blacklist are in memory | Users are signed out on restart; not shareable across several server processes | High |
| 2 | Shopping links are search URLs and prices are AI estimates | Prices may differ from live prices | High |
| 3 | SQLite and a single Uvicorn worker | Limits write concurrency and horizontal scaling | Medium |

## Scalability Plan

| S.No | Scalability Aspect | Current State | Proposed Upgrade / Solution |
|---|---|---|---|
| 1 | User Load | Single worker; 25 concurrent users tested with 0 % errors (offline mode) | Several Uvicorn/Gunicorn workers behind Nginx; container autoscaling |
| 2 | Data Storage | SQLite file | PostgreSQL with connection pooling; object storage (S3) for outfit images |
| 3 | Performance | Gemini call is synchronous per request, run in a threadpool | Cache repeated requests, use async Gemini client, background queue for long jobs |
| 4 | Security | bcrypt, JWT in HttpOnly cookie, upload validation | Redis session store and token revocation, rate limiting, HTTPS-only cookies, secrets manager |

## Future Roadmap

| Phase | Planned Feature / Enhancement | Target Timeline | Expected Impact |
|---|---|---|---|
| Phase 2 | Live product data via retailer APIs, price-drop alerts | 1-2 months | More accurate prices and deeper personalization |
| Phase 3 | Hosted deployment (Docker on Render/Railway), CI with GitHub Actions | 2-3 months | Public demo URL and automated testing |
| Phase 4 | New planners (travel, groceries), Google sign-in, PDF export, regional languages | 3-6 months | Wider audience and retention |
