# PocketSmart AI: Your Smart Budget & Recommendation Assistant

**AI/ML & GenAI Track project.** PocketSmart AI turns a budget into a personalised, shop-able plan for **home interiors, parties and jewelry** using Google Gemini (text and image), with a FastAPI backend, login and history.

## Team

| Name | Register No. |
|---|---|
| Aravinth K | 2024503001 |
| Krishna Kailash Yedida | 2024503575 |
| Kaushal N | 2024503555 |
| Rangesh V S | 2024503549 |
| Sanjay C | 2024503507 |

## Features

- **Home Interior Planner**: budget split across lights, ceiling fans, furniture, dining tables and rooms (IKEA, Amazon, Flipkart, Myntra, Ajio links).
- **Party Planner**: venue, catering, decoration, entertainment and contingency (Swiggy, Zomato, BookMyShow, OYO, MakeMyTrip, NoBroker links).
- **Jewelry Planner**: occasion and style, plus an optional outfit photo analysed by Gemini (Amazon, Flipkart, BlueStone, Tanishq, CaratLane, Melorra links).
- **Budget guarantee**: the server recomputes every total and trims items so a plan never exceeds the budget.
- **Reliability**: automatic Gemini model fallback chain and an offline fallback plan if the AI is unavailable.
- **Accounts**: register, login (bcrypt + JWT in an HttpOnly cookie), logout, sessions, dashboard and saved history.

## Quick start

```bash
git clone https://github.com/<your-github-username>/PocketSmart-AI.git
cd PocketSmart-AI
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
# edit .env: set GOOGLE_API_KEY (https://aistudio.google.com/apikey) and SECRET_KEY
python check_gemini.py           # optional: confirms Gemini works and picks a model
python tools/seed_demo_user.py   # optional: creates demo / Demo@12345
uvicorn main:app --reload
```

Open <http://localhost:8000>. Interactive API docs: <http://localhost:8000/docs>.
Without `GOOGLE_API_KEY` the app still runs and returns clearly labelled offline estimates.

Docker: `docker build -t pocketsmart-ai .` then `docker run -p 8000:8000 --env-file .env pocketsmart-ai`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests                      # 43 tests: auth, validation, planners, history, Gemini mocks
python tests/perf_load.py http://localhost:8000 25 20   # load test (server running)
```

## Live demo script (about 10 minutes)

1. Run `python check_gemini.py`, then start the server and open the landing page.
2. Register (or sign in as `demo` / `Demo@12345`). Show the dashboard.
3. **Home Planner**: budget 80000, 5 lights, 2 fans, 2 furniture, 1 dining table, Living Room + Kitchen. Point out the remaining budget and shop links.
4. **Party Planner**: budget 40000, 30 guests, Birthday, Banquet hall. Show categories, venue suggestions and the contingency.
5. **Jewelry Planner**: budget 20000, Wedding, upload an outfit photo. Show the outfit analysis.
6. Show a validation error (0 guests), then **History** and a plan opened from the list.
7. Log out; open `/dashboard` to show it redirects to login.

## Repository layout (follows the course template)

| Folder | Deliverables |
|---|---|
| `1. Brainstorming & Ideation` | Problem statements, empathy map, idea prioritization |
| `2. Requirement Analysis` | DFD, solution requirements, technology stack, customer journey map |
| `3. Project Design Phase` | Problem-solution fit, proposed solution, solution architecture |
| `4. Project Planning Phase` | Backlog, sprint schedule and estimation |
| `5. Project Development Phase` | Coding and solution, code layout, functional features (code is in the repo root) |
| `6.Project Testing` | Performance testing and raw evidence (pytest, load tests) |
| `7.Project Documentation` | Project executable files guide, full project documentation |
| `8.Project Demonstration` | Demo plan, team involvement, scalability, features, communication |

Application code: `main.py` (routes), `gemini_utils.py` (AI service), `auth.py`, `models.py`, `database.py`, `config.py`, `templates/`, `static/`, `tests/`.

Editable sources for every phase PDF live in `docs-src/` (set team ID, dates and links in `docs-src/project.json`, then run `python tools/build_docs.py`).

## Note on the Gemini model

The project brief names "Gemini 1.5 Flash Pro". That model does not exist and the 1.5 family is retired. Set `GEMINI_MODEL` in `.env` (default `gemini-3.8-flash`); the app falls back to other current models automatically.
