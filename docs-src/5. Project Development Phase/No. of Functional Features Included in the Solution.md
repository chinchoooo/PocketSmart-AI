# No. of Functional Features Included in the Solution

{{HEADER:5 Marks}}

## Functional Features Overview

| S.No | Feature Name | Feature Description | Module / Component | Status (Done / In Progress / Pending) | Marks Contribution |
|---|---|---|---|---|---|
| 1 | User registration | Validated sign-up; bcrypt-hashed password | `auth.py`, `/register` | Done | Core |
| 2 | Login / logout / sessions | JWT in HttpOnly cookie, token blacklist, idle-session cleanup, `/session-info`, `/session-data` | `auth.py`, `main.py` | Done | Core |
| 3 | Home Interior planner | Budget split across lights, fans, furniture, dining tables and rooms | `/home-budget`, `gemini_utils.py` | Done | Core |
| 4 | Party planner | Budget split across venue, catering, decoration, entertainment, contingency; venue suggestions | `/party-budget`, `gemini_utils.py` | Done | Core |
| 5 | Jewelry planner (multimodal) | Occasion + preferences + optional outfit photo analysed by Gemini | `/jewelry-budget`, `gemini_utils.py` | Done | Core |
| 6 | Budget adherence engine | Recomputes totals, trims over-budget items, builds calculation table | `gemini_utils.py` | Done | Core |
| 7 | Shopping links | Per-item search links on 19 platforms chosen by category | `gemini_utils.py` | Done | Core |
| 8 | Recommendation history | Saved plans, list view and full-detail modal, per-user privacy | `database.py`, `history.html` | Done | Core |
| 9 | Dashboard | Welcome page, planner shortcuts, recent activity | `dashboard.html` | Done | Additional |
| 10 | Offline fallback and model fallback | Plan returned even if Gemini is down; automatic model chain | `gemini_utils.py` | Done | Additional |
| 11 | Input validation and upload checks | Budget, guests, quantities, text length, image type/size/content | `models.py`, `main.py` | Done | Core |
| 12 | Print / save plan | Browser print stylesheet | `styles.css` | Done | Additional |

### Feature Summary

| Metric | Count / Value |
|---|---|
| Total Features Planned | 12 |
| Total Features Implemented | 12 |
| Core / Must-Have Features | 9 |
| Additional / Nice-to-Have Features | 3 |
| Features Tested & Verified | 12 (43 automated tests plus browser end-to-end run) |

### Feature Category Breakdown

| S.No | Category | Features in Category | Example Features |
|---|---|---|---|
| 1 | User Interface (UI) | 3 | Dashboard, planner forms, results and history views |
| 2 | Backend / Logic | 3 | Budget adherence engine, planners, offline fallback |
| 3 | Database / Storage | 1 | Saved recommendation history (SQLite) |
| 4 | API / Integration | 2 | Gemini text + image, shopping links |
| 5 | Security / Authentication | 3 | Registration, JWT sessions, input and upload validation |
