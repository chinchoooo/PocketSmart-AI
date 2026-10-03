# Coding & Solution

{{HEADER:5 Marks}}

## Solution Summary

| Field | Details |
|---|---|
| Repository Link / URL | {{repo_url}} |
| Programming Language(s) | Python 3.10+, JavaScript, HTML, CSS |
| Framework(s) Used | FastAPI, Jinja2, Pydantic; Google Gemini via `google-genai` |
| Key Features Implemented | Home, Party and Jewelry planners; multimodal outfit analysis; budget adherence check; shopping links; register/login/logout with JWT and bcrypt; session info and data; dashboard; history with full details; offline fallback; model fallback chain; Dockerfile; 43 automated tests; load test |
| Pending / Incomplete Features | Live price scraping or retailer APIs (links are search URLs); hosted deployment; Google sign-in; PDF export (browser print is available) |
| Setup / Run Instructions | `pip install -r requirements.txt`, copy `.env.example` to `.env` and add `GOOGLE_API_KEY`, then `uvicorn main:app --reload` and open http://localhost:8000. Full steps in README.md |

## Code Quality Checklist

| S.No | Criteria | Status (Yes / No) |
|---|---|---|
| 1 | Code is modular and organized into functions / classes | Yes |
| 2 | Meaningful variable and function names are used | Yes |
| 3 | Code includes comments / documentation where necessary | Yes |
| 4 | Error handling is implemented for critical operations | Yes |
| 5 | The application runs without critical errors | Yes |
| 6 | Code is committed to a version control repository | Yes |

## Additional Notes / Comments

- The project brief names "Gemini 1.5 Flash Pro". That model does not exist and the 1.5 family is retired. The model is configured with `GEMINI_MODEL` (default `gemini-3.8-flash`) and the app falls back through newer and older models automatically.
- All AI output is re-validated server-side; the model is never trusted for totals.
