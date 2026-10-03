# Solution Requirements

{{HEADER:4 Marks}}

## Step 1: Functional Requirements (FR)

| S.No | Requirement Category | Requirement Description | Priority |
|---|---|---|---|
| 1 | Authentication | Users register with username, email and password (min 8 chars, stored as bcrypt hash) and log in to receive a 30-minute JWT in an HttpOnly cookie; logout blacklists the token | High |
| 2 | Authorization levels | Single role (registered user). Every planner, history and session endpoint requires a valid token; users can read only their own history | High |
| 3 | External interfaces | Google Gemini API (text + image) for recommendations; search-URL deep links to Amazon, Flipkart, IKEA, Myntra, Ajio, Swiggy, Zomato, BookMyShow, OYO, MakeMyTrip, NoBroker, BlueStone, Tanishq, CaratLane and others | High |
| 4 | Transactions processing | Each planner request is validated, sent to Gemini, checked against the budget and saved to the recommendations table; no payments are processed | High |
| 5 | Reporting | Itemised budget summary (total, planned spend, remaining), per-category calculation table, dashboard recent activity, history with full detail view, print / save | Medium |
| 6 | Business rules | Planned spend must never exceed the budget (excess items are removed); amounts are in INR; the party plan includes a contingency; image upload limited to JPG/PNG/WEBP up to 5 MB | High |
| 7 | Compliance to laws or regulations | Passwords hashed; API key kept in .env, never committed; only the data needed for the plan is stored; users can read only their own records (aligned with India's DPDP Act principles of purpose limitation) | Medium |
| 8 | Other | Offline fallback plan if Gemini is unavailable; automatic model fallback chain; input edge-case validation | High |

## Step 2: Non-Functional Requirements (NFR)

| S.No | NFR Category | Requirement Description | Target Metric / Acceptance Criteria |
|---|---|---|---|
| 1 | Performance & Speed | Application overhead is small; AI latency dominates | Avg app response < 2 s, max < 5 s (excl. Gemini); measured 0.10 s avg at 25 users |
| 2 | Scalability | Stateless request handling, threadpool for blocking AI calls, DB behind a thin module that can be swapped for PostgreSQL | 25 concurrent users with 0 % errors (tested) |
| 3 | Security & Data Privacy | bcrypt hashing, signed JWT, HttpOnly SameSite cookie, upload verification, AI output rendered as text (no HTML injection), prompt-injection fencing | No plaintext secrets; 100 % of protected routes return 401 without a token |
| 4 | Reliability & Availability | Never show an empty result: fallback plan when AI fails or returns invalid / over-budget output | 100 % of valid requests return a within-budget plan (43 automated tests) |
| 5 | Usability & Accessibility | Responsive layout, labelled form fields, visible focus, clear error messages, print stylesheet | Usable at 360 px width; keyboard navigable |
| 6 | Other | Maintainability and portability: modular code, .env configuration, Dockerfile | Runs with `pip install -r requirements.txt` and `uvicorn main:app` |
