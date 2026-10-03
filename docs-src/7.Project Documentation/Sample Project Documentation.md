# PocketSmart AI: Your Smart Budget & Recommendation Assistant

## Project Description

PocketSmart AI uses Generative AI to turn a budget into a personalised, shop-able plan for **home interiors, parties and jewelry**. A FastAPI backend sends validated user input (text, numbers and an optional outfit image) to Google Gemini, then re-checks the answer so the plan never exceeds the budget, and attaches search links for Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO and other platforms. Users register, sign in, and revisit saved plans from their history.

## Scenarios

**Scenario 1: Home Interior Planning.** The user opens the Home Budget Planner, enters a budget, quantities of lights, ceiling fans, furniture and dining tables, and selects rooms. Gemini recommends cost-effective options for each category across IKEA, Amazon, Flipkart, Myntra and Ajio, balanced for function, style and price.

**Scenario 2: AI-Based Party Budget Planning.** In the Party Planner the user enters budget, guest count, party type and venue. The budget is allocated across venue, catering, decoration and entertainment, with links to Swiggy, Zomato, BookMyShow, OYO and more, plus a contingency amount.

**Scenario 3: Jewelry Recommendations.** The Jewelry Planner takes a budget, occasion and style preferences, and optionally an outfit photo. Gemini analyses colours and formality and suggests matching pieces from Amazon, Flipkart, BlueStone, Tanishq, CaratLane and others.

## Technical Architecture

Three tiers: a responsive HTML/CSS/JS front end (Jinja2 templates), a FastAPI back end (routes, JWT sessions, validation, budget engine) and external services (Gemini API, shop search URLs) with SQLite for storage. See *3. Project Design Phase / Solution Architecture* for the diagram.

## Pre-requisites

1. Python 3.10+ - https://www.python.org
2. FastAPI - https://fastapi.tiangolo.com
3. Google AI Studio account and Gemini API key - https://aistudio.google.com/apikey
4. Git and a GitHub account
5. Basic HTML, CSS and JavaScript

## Project Workflow

| Milestone | Activities | Where in the code |
|---|---|---|
| 1. Gemini AI Initialization | 1.1 Create Google AI Studio account; 1.2 generate and store the API key in `.env`; 1.3 validate text and image connectivity | `.env.example`, `config.py`, `check_gemini.py` |
| 2. Core Functionalities Development | 2.1 FastAPI initialization and imports; 2.2 planner endpoints with Gemini prompts; 2.3 login/register routing; 2.4 modular structure with `/token`, `/session-info`, `/session-data` | `main.py`, `gemini_utils.py`, `auth.py`, `models.py` |
| 3. Backend - FastAPI Integration | 3.1 `/home-budget`, `/party-budget`, `/jewelry-budget` (aliases `/generate-*`) and auth routes; 3.2 `/recommendation-details/{id}`; 3.3 CORS, `/history`; 3.4 startup task and `__main__` | `main.py` |
| 4. UI Development | 4.1 landing page, forms, card-style results; dynamic rendering with JavaScript | `templates/`, `static/` |
| 5. Testing & Optimization | 5.1 real-world inputs across the planners; 5.2 response quality and budget adherence; 5.3 prompt tuning and validation; 5.4 fallback recommendations | `tests/`, `gemini_utils.py` |

## Milestone 1: Gemini AI Initialization

1. Sign in at https://aistudio.google.com and choose **Get API key** then **Create API key**.
2. Copy the key into `.env` as `GOOGLE_API_KEY` (never commit `.env`).
3. Run `python check_gemini.py`. It sends a text prompt and a text + image prompt, tries the configured model and then fallback models, and prints which model to use.

Note: the original brief refers to "Gemini 1.5 Flash Pro". That model name does not exist and the 1.5 family is retired, so the model is configurable (`GEMINI_MODEL`).

## Milestone 2 and 3: Backend

- `config.py` loads settings; `models.py` validates inputs; `database.py` stores users and plans; `auth.py` handles bcrypt, JWT and sessions.
- `gemini_utils.py` builds one prompt per planner, calls Gemini (JSON mode), sanitises the reply, recomputes totals, trims over-budget items, builds shopping links and falls back to default plans if needed.
- `main.py` exposes the routes: `/register`, `/login`, `/token`, `/logout`, `/session-info`, `/session-data`, `/home-planner`, `/party-planner`, `/jewelry-planner`, `/home-budget`, `/party-budget`, `/jewelry-budget`, `/recommendation-history`, `/recommendation-details/{id}`, `/history`, `/dashboard`, `/health`. Interactive API docs are at `/docs`.

## Milestone 4: UI Development

![Landing page](assets/01_landing.png)

![Register page](assets/02_register.png)

![Login page](assets/03_login.png)

![Dashboard](assets/08_dashboard.png)

## Milestone 5: Testing & Optimization

### Home Interior Planner and recommendations

![Home planner](assets/04_home_planner.png)

### Party Planner and recommendations

![Party planner](assets/05_party_planner.png)

### Jewelry Planner (with outfit image) and recommendations

![Jewelry planner](assets/06_jewelry_planner.png)

### Input validation

![Validation error](assets/07_validation_error.png)

### Recommendation history and details

![History](assets/09_history.png)

![History detail](assets/10_history_detail.png)

These screenshots were captured by the automated browser test `tools/capture_screenshots.py` running **in offline-fallback mode** (no API key), which is why results are labelled "Offline estimate". With a Gemini key the label reads "Gemini AI" and the items come from the model.

## Conclusion

PocketSmart AI combines FastAPI with Google Gemini to give budget-aware recommendations for home interiors, parties and jewelry. The server verifies every plan against the budget, falls back gracefully if the AI is unavailable, protects user data with hashed passwords and signed sessions, and links each item to the platforms where it can be bought.
