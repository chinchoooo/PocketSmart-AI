# Project Demo Planning

{{HEADER:1 Mark}}

## Project Demo Planning

| S.No | Demo Section | Description | Duration (mins) | Responsible Member |
|---|---|---|---|---|
| 1 | Introduction & problem statement | Budget overload across home, party and jewelry shopping; project goal | 1 | Sanjay C |
| 2 | Architecture & tech stack | FastAPI + Gemini + SQLite diagram; budget-check engine; fallback design | 2 | Aravinth K |
| 3 | Account flow | Register, login, dashboard, session | 1 | Kaushal N |
| 4 | Home and Party planners (live) | Enter budget, show plan, remaining budget, shop links | 2 | Krishna Kailash Yedida |
| 5 | Jewelry planner with outfit photo (live) | Upload photo, outfit analysis, jewelry picks | 2 | Krishna Kailash Yedida |
| 6 | History, validation and testing | Reopen a plan, invalid input, show 43 tests and load-test results | 2 | Rangesh V S |
| 7 | Scalability, future plan, Q&A | Roadmap and answers | 2 | Whole team |

### Demo Flow Summary

| Step | Activity | Notes |
|---|---|---|
| 1 | Introduction & Problem Statement | Use PS-1 to PS-3 from Phase 1 |
| 2 | Solution Overview | Show architecture diagram and the "AI proposes, server verifies" idea |
| 3 | Live Feature Demonstration | Log in as `demo`; run Home, Party, Jewelry (with photo); open History; show a validation error |
| 4 | Q&A Session | Be ready to explain the Gemini fallback chain, budget trimming and JWT logout |

### Pre-demo checklist
- `.env` has a working `GOOGLE_API_KEY`; run `python check_gemini.py` the day before.
- `python tools/seed_demo_user.py` has been run; server started with `uvicorn main:app`.
- Keep an outfit photo (JPG/PNG under 5 MB) ready on the desktop.
- If Wi-Fi fails, the app still shows offline estimates; explain the fallback as a feature.
