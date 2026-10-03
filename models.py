"""Input / output schemas (Pydantic) for PocketSmart AI.

Validation lives here so every endpoint rejects edge-case input
(negative budgets, absurd guest counts, over-long text) the same way.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

MAX_BUDGET = 100_000_000  # Rs. 10 crore - anything above is almost certainly a typo
MAX_TEXT = 500
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def _clean(text: Optional[str]) -> Optional[str]:
    """Trim whitespace and collapse empty strings to None."""
    if text is None:
        return None
    text = text.strip()
    return text or None


# ----------------------------- authentication --------------------------------
class RegisterUser(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=80)
    password: str

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_RE.match(value):
            raise ValueError("Username must be 3-30 characters: letters, digits, _ . -")
        return value

    @field_validator("password")
    @classmethod
    def valid_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(value.encode("utf-8")) > 72:  # bcrypt limit
            raise ValueError("Password must be at most 72 bytes")
        return value


class UserInDB(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@dataclass
class UserSession:
    """In-memory session record (one per logged-in user)."""
    username: str
    login_time: datetime
    last_activity: datetime
    token: str
    user_data: Dict[str, Any] = field(default_factory=dict)


# ----------------------------- planner inputs --------------------------------
class HomeBudgetInput(BaseModel):
    total_budget: float = Field(gt=0, le=MAX_BUDGET)
    num_lights: int = Field(default=0, ge=0, le=100)
    num_fans: int = Field(default=0, ge=0, le=50)
    num_furniture: int = Field(default=0, ge=0, le=100)
    num_dining_tables: int = Field(default=0, ge=0, le=20)
    has_living_room: bool = False
    has_kitchen: bool = False
    has_bedroom: bool = False
    additional_requirements: Optional[str] = Field(default=None, max_length=MAX_TEXT)

    @field_validator("additional_requirements")
    @classmethod
    def trim_text(cls, value: Optional[str]) -> Optional[str]:
        return _clean(value)

    @model_validator(mode="after")
    def needs_something(self) -> "HomeBudgetInput":
        wants = self.num_lights + self.num_fans + self.num_furniture + self.num_dining_tables
        if wants == 0 and not (self.has_living_room or self.has_kitchen or self.has_bedroom):
            raise ValueError("Choose at least one item quantity or room")
        return self


class PartyBudgetInput(BaseModel):
    total_budget: float = Field(gt=0, le=MAX_BUDGET)
    num_guests: int = Field(ge=1, le=5000)
    party_type: str = Field(min_length=2, max_length=40)
    venue_type: Optional[str] = Field(default=None, max_length=40)
    needs_catering: bool = True
    needs_decoration: bool = True
    needs_entertainment: bool = True
    additional_requirements: Optional[str] = Field(default=None, max_length=MAX_TEXT)

    @field_validator("additional_requirements", "venue_type")
    @classmethod
    def trim_text(cls, value: Optional[str]) -> Optional[str]:
        return _clean(value)

    @model_validator(mode="after")
    def needs_a_service(self) -> "PartyBudgetInput":
        if not (self.needs_catering or self.needs_decoration or self.needs_entertainment):
            raise ValueError("Select at least one of catering, decoration or entertainment")
        return self


class JewelryBudgetInput(BaseModel):
    total_budget: float = Field(gt=0, le=MAX_BUDGET)
    occasion: str = Field(min_length=2, max_length=40)
    preferences: Optional[str] = Field(default=None, max_length=MAX_TEXT)

    @field_validator("preferences")
    @classmethod
    def trim_text(cls, value: Optional[str]) -> Optional[str]:
        return _clean(value)
