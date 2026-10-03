# Project Initialization and Planning Phase

{{HEADER:5 Marks}}

## Project Proposal (Proposed Solution) report

PocketSmart AI is a GenAI-powered, cross-platform budget and recommendation assistant. It converts a user's budget and preferences into a structured, shop-able plan for home interiors, parties and jewelry.

### Project Overview
| | |
|---|---|
| Objective | Help users plan purchases for home decor, parties and jewelry within a fixed budget, using Gemini to allocate money and recommend products across Indian platforms |
| Scope | Three planners (Home, Party, Jewelry), user accounts and sessions, recommendation history, shopping deep links, offline fallback; no payments or live price scraping |

### Problem Statement
| | |
|---|---|
| Description | Users overspend or waste hours because budgets are not allocated across categories and product data is scattered across many platforms |
| Impact | Solving this saves time and money, reduces decision stress and makes planned spending transparent |

### Proposed Solution
| | |
|---|---|
| Approach | A FastAPI backend builds a structured prompt from validated inputs and calls Gemini (text, or text plus outfit image). The reply is parsed, sanitised and re-checked: totals are recomputed and items are trimmed so the plan never exceeds the budget. Search links are generated server-side |
| Key Features | - Home, Party and Jewelry planners<br>- Multimodal outfit analysis for jewelry<br>- Budget adherence check and calculation table<br>- Shopping links per item (Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, ...)<br>- Register/login, JWT sessions, history and dashboard<br>- Offline fallback plan and Gemini model fallback chain |

### Resource Requirements
| Resource Type | Description | Specification / Allocation |
|---|---|---|
| **Hardware** | | |
| Computing Resources | CPU/GPU specifications, number of cores | Any laptop, 2 CPU cores, no GPU (inference runs in Google's cloud) |
| Memory | RAM specifications | 4 GB minimum (server uses about 90 MB) |
| Storage | Disk space for data, models and logs | 1 GB free; SQLite DB and uploaded images are small |
| **Software** | | |
| Frameworks | Python frameworks | FastAPI, Uvicorn, Jinja2 |
| Libraries | Additional libraries | google-genai, Pillow, bcrypt, python-jose, pydantic, python-dotenv, pytest |
| Development Environment | IDE | VS Code, Git, GitHub |
| **Data** | | |
| Data | Source, size, format | No training dataset; user inputs at run time (JSON/form) and Gemini API responses (JSON); stored in SQLite |
