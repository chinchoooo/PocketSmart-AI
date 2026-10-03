# Technology Stack

{{HEADER:2 Marks}}

## Technology Stack Details

| S.No | Architecture Component / Layer | Technology Chosen | Justification / Purpose |
|---|---|---|---|
| 1 | Frontend / Client-Side | HTML5, CSS3, vanilla JavaScript, Jinja2 templates | No build step, fast to load, responsive; Jinja2 shares one base layout across 8 pages; AI text is rendered with `textContent` to prevent injection |
| 2 | Backend / Server-Side | Python 3, FastAPI, Uvicorn, Pydantic | Async-capable, automatic request validation and OpenAPI docs at `/docs`, team knows Python |
| 3 | Database / Data Storage | SQLite (standard-library `sqlite3`) | Zero-setup relational store for users and saved plans; schema in `database.py`; easily replaced by PostgreSQL |
| 4 | Cloud / Hosting / Deployment | Local Uvicorn server, Docker (`Dockerfile` provided) | Simple to run for the demo; container image deployable to Render, Railway or any cloud VM |
| 5 | Version Control & CI/CD | Git and GitHub, pytest | Collaboration for five members; automated test suite (43 tests) ready to plug into GitHub Actions |
| 6 | Third-Party APIs / Other Tools | Google Gemini API (`google-genai` SDK), Pillow, bcrypt, python-jose (JWT), python-dotenv | Gemini generates budget-aware text and reads outfit images (multimodal); Pillow validates uploads; bcrypt and JWT secure accounts; dotenv keeps keys out of code |
