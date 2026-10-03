# Solution Architecture

{{HEADER:5 Marks}}

## Solution Architecture Diagram

```
                          Presentation / Client Layer
        Browser: HTML + CSS + JavaScript (Jinja2 pages: landing, login, register,
        dashboard, home / party / jewelry planners, history)
                                        |  ^
                          HTTPS/JSON    v  |   cookie: HttpOnly JWT
                              API Layer (FastAPI + Uvicorn)
        Routes: /register /token /logout /home-budget /party-budget /jewelry-budget
                /recommendation-history /recommendation-details/{id} /session-*
        CORS middleware, request validation (Pydantic), exception handling
                                        |  ^
        +-------------------------------+--+--------------------------------+
        v                               v                                   v
  Auth Service                   Core Logic Service                  External API
  [auth.py: bcrypt hashing,      [gemini_utils.py: prompt builder,    Integrations
   JWT issue/verify, token        JSON parsing, budget validation,    [Google Gemini API
   blacklist, session store]      shopping-link builder, offline      (text + image);
                                  fallback plans]                      shop search URLs]
        |                               |
        +---------------+---------------+
                        v
                 Data / Storage Layer
        [SQLite: users, recommendations  |  static/uploads: outfit images]
```

## Component Description Table

| Component Name | Description / Role in Architecture | Technologies Used |
|---|---|---|
| Presentation Layer | Responsive pages and forms; renders plans as tables and cards; history modal; print view | HTML5, CSS3, JavaScript, Jinja2 |
| API Layer (`main.py`) | Routing, validation, sessions, CORS, error handling, aliases `/generate-home`, `/generate-party`, `/generate-jewelry` | FastAPI, Uvicorn, Pydantic |
| Auth Service (`auth.py`) | Hashes passwords, issues and verifies JWTs, blacklists tokens on logout, tracks active sessions and cleans up idle ones | bcrypt, python-jose |
| Core Logic / AI Service (`gemini_utils.py`) | Builds prompts, calls Gemini with model fallback, parses JSON, recomputes totals, trims to budget, adds shopping links, supplies offline fallback | google-genai, Pillow |
| Models (`models.py`) | Input and session schemas with edge-case validation | Pydantic |
| Database (`database.py`) | Persists users and saved plans (schema with foreign key and index) | SQLite |
| External APIs | Gemini for recommendations; platform search URLs for shopping | Google Gemini API, URL templates |
