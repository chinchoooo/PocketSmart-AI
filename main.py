"""PocketSmart AI - FastAPI application (routes, sessions, wiring).

Run:  uvicorn main:app --reload      (or)      python main.py
"""
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import auth
import config
import database
import gemini_utils
from models import (HomeBudgetInput, JewelryBudgetInput, PartyBudgetInput, RegisterUser,
                    Token, UserInDB)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pocketsmart")


# ----------------------------------------------------------------------------
# App setup
# ----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: create DB + folders, warn about AI config, start session cleanup."""
    database.init_db()
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if gemini_utils.gemini_configured():
        logger.info("Gemini enabled (primary model: %s)", config.GEMINI_MODEL)
    else:
        logger.warning("GOOGLE_API_KEY not set - planners will use offline fallback recommendations.")

    async def cleanup_loop() -> None:
        while True:
            await asyncio.sleep(300)  # every 5 minutes
            auth.cleanup_expired()

    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="PocketSmart: AI Budget Planner", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=config.BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=config.BASE_DIR / "templates")


@app.exception_handler(StarletteHTTPException)
async def auth_redirect_handler(request: Request, exc: StarletteHTTPException):
    """Browsers navigating to a protected page get redirected to /login; API calls get JSON."""
    if exc.status_code == 401 and request.method == "GET" and "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return await http_exception_handler(request, exc)


def page(request: Request, name: str, user: Optional[UserInDB] = None) -> HTMLResponse:
    return templates.TemplateResponse(request, name, {"user": user})


# ----------------------------------------------------------------------------
# Public pages and health
# ----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Landing page."""
    return page(request, "index.html", auth.get_optional_user(request))


@app.get("/health")
def health():
    return {"status": "ok", "gemini_configured": gemini_utils.gemini_configured(), "model": config.GEMINI_MODEL}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if auth.get_optional_user(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return page(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if auth.get_optional_user(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return page(request, "register.html")


# ----------------------------------------------------------------------------
# Authentication: /register /token /logout
# ----------------------------------------------------------------------------
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: RegisterUser):
    """Create an account (password stored as a bcrypt hash)."""
    try:
        database.create_user(user.username, user.email, user.full_name, auth.hash_password(user.password))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return {"message": "Account created. Please sign in."}


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Issue a JWT (returned in the body and set as an HttpOnly cookie)."""
    user = auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token({"sub": user.username})
    auth.start_session(user.username, token)
    response = JSONResponse({"access_token": token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token", value=token, httponly=True, samesite="lax",
        secure=config.COOKIE_SECURE, max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@app.post("/logout")
def logout(request: Request):
    """Blacklist the token, end the session, return to /login."""
    token = auth.get_token(request)
    if token:
        auth.blacklist_token(token)
        for name, session in list(auth.active_sessions.items()):
            if session.token == token:
                del auth.active_sessions[name]
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


# ----------------------------------------------------------------------------
# Session endpoints: /session-info /session-data
# ----------------------------------------------------------------------------
@app.get("/session-info")
def get_session_info(current_user: UserInDB = Depends(auth.get_current_active_user)):
    session = auth.active_sessions[current_user.username]
    now = datetime.now(timezone.utc)
    return {
        "username": session.username,
        "login_time": session.login_time,
        "last_activity": session.last_activity,
        "session_duration_minutes": int((now - session.login_time).total_seconds() // 60),
        "user_data": session.user_data,
    }


@app.post("/session-data")
def update_session_data(data: Dict[str, Any], current_user: UserInDB = Depends(auth.get_current_active_user)):
    """Store small bits of per-session state (e.g. last planner inputs)."""
    if len(data) > 20:
        raise HTTPException(status_code=422, detail="Too many keys (max 20)")
    session = auth.active_sessions[current_user.username]
    session.user_data.update(data)
    return {"message": "Session data updated", "data": session.user_data}


# ----------------------------------------------------------------------------
# Authenticated pages
# ----------------------------------------------------------------------------
def _protected_page(template: str):
    def handler(request: Request, current_user: UserInDB = Depends(auth.get_current_active_user)):
        return page(request, template, current_user)
    return handler


for _path, _template in [("/dashboard", "dashboard.html"), ("/home-planner", "home_planner.html"),
                         ("/party-planner", "party_planner.html"), ("/jewelry-planner", "jewelry_planner.html"),
                         ("/history", "history.html")]:
    app.add_api_route(_path, _protected_page(_template), methods=["GET"], response_class=HTMLResponse,
                      include_in_schema=False)


# ----------------------------------------------------------------------------
# Planner APIs (POST). /generate-* are aliases kept for the project spec.
# Plain `def` routes run in FastAPI's threadpool, so slow Gemini calls never block other users.
# ----------------------------------------------------------------------------
def _remember(user: UserInDB, key: str, summary: Dict[str, Any]) -> None:
    auth.active_sessions[user.username].user_data[key] = {"timestamp": datetime.now(timezone.utc).isoformat(), **summary}


def _finish(user: UserInDB, kind: str, input_data: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Persist the plan to history and return it with its id."""
    result["id"] = database.save_to_history(user.username, kind, input_data, result)
    return result


@app.post("/home-budget")
@app.post("/generate-home")
def plan_home_budget(budget_input: HomeBudgetInput, current_user: UserInDB = Depends(auth.get_current_active_user)):
    """Home interior recommendations."""
    _remember(current_user, "last_home_budget", {
        "budget": budget_input.total_budget,
        "requirements": {"lights": budget_input.num_lights, "fans": budget_input.num_fans,
                         "furniture": budget_input.num_furniture, "dining_tables": budget_input.num_dining_tables}})
    result = gemini_utils.get_home_recommendations(budget_input)
    return _finish(current_user, "home", budget_input.model_dump(), result)


@app.post("/party-budget")
@app.post("/generate-party")
def plan_party_budget(budget_input: PartyBudgetInput, current_user: UserInDB = Depends(auth.get_current_active_user)):
    """Party plan: venue, catering, decoration, entertainment."""
    _remember(current_user, "last_party_budget", {
        "budget": budget_input.total_budget, "party_type": budget_input.party_type, "guests": budget_input.num_guests})
    result = gemini_utils.get_party_recommendations(budget_input)
    return _finish(current_user, "party", budget_input.model_dump(), result)


def save_upload_file(upload: UploadFile) -> str:
    """Validate (type, size, real image) and store an uploaded outfit photo; return its path."""
    extension = config.ALLOWED_IMAGE_TYPES.get(upload.content_type or "")
    if not extension:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG or WEBP image")
    data = upload.file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = config.UPLOAD_DIR / f"{uuid.uuid4().hex}{extension}"
    path.write_bytes(data)
    try:
        with Image.open(path) as img:
            img.verify()
    except (UnidentifiedImageError, OSError):
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=415, detail="File is not a valid image")
    return str(path)


@app.post("/jewelry-budget")
@app.post("/generate-jewelry")
def plan_jewelry_budget(
    total_budget: float = Form(...),
    occasion: str = Form(...),
    preferences: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: UserInDB = Depends(auth.get_current_active_user),
):
    """Jewelry recommendations from text and an optional outfit image."""
    try:
        budget_input = JewelryBudgetInput(total_budget=total_budget, occasion=occasion, preferences=preferences)
    except ValidationError as exc:  # form fields bypass body validation, so report it ourselves
        raise HTTPException(status_code=422, detail=[{"msg": e["msg"]} for e in exc.errors()])
    image_path = save_upload_file(image) if image is not None and image.filename else None
    _remember(current_user, "last_jewelry_budget", {
        "budget": budget_input.total_budget, "occasion": budget_input.occasion, "has_image": image_path is not None})
    result = gemini_utils.get_jewelry_recommendations(budget_input, image_path)
    input_data = budget_input.model_dump()
    input_data["has_image"] = image_path is not None
    return _finish(current_user, "jewelry", input_data, result)


# ----------------------------------------------------------------------------
# History: /recommendation-history /recommendation-details/{id}
# ----------------------------------------------------------------------------
@app.get("/recommendation-history")
def get_recommendation_history(limit: int = 100, current_user: UserInDB = Depends(auth.get_current_active_user)):
    """Newest-first list of the user's saved plans (summary only)."""
    history = []
    for record in database.list_history(current_user.username, max(1, min(limit, 200))):
        result = record["full_result"]
        history.append({
            "id": record["id"], "timestamp": record["timestamp"], "type": record["type"],
            "input": record["input"],
            "summary": {"total_budget": result.get("total_budget"), "remaining_budget": result.get("remaining_budget"),
                        "source": result.get("source"),
                        "categories": [c["category"] for c in result.get("budget_breakdown", [])]},
        })
    return {"history": history}


@app.get("/recommendation-details/{recommendation_id}")
def get_recommendation_details(recommendation_id: str, current_user: UserInDB = Depends(auth.get_current_active_user)):
    """Full stored result for one plan (only the owner can read it)."""
    record = database.get_recommendation(current_user.username, recommendation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return record


if __name__ == "__main__":
    import uvicorn

    print("Starting PocketSmart: AI Budget Planner on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
