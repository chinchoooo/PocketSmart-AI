"""Test setup: isolated temp database, no Gemini key (forces offline fallback unless a test mocks it)."""
import os
import tempfile
import uuid

_tmp = tempfile.mkdtemp(prefix="pocketsmart-test-")
os.environ["DATABASE_PATH"] = os.path.join(_tmp, "test.db")
os.environ["GOOGLE_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="session")
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def user_client(client):
    """A TestClient logged in as a fresh, uniquely named user."""
    name = f"user_{uuid.uuid4().hex[:8]}"
    password = "S3cure-pass!"
    r = client.post("/register", json={"username": name, "email": f"{name}@example.com", "password": password})
    assert r.status_code == 201, r.text
    with TestClient(main.app) as c:
        r = c.post("/token", data={"username": name, "password": password})
        assert r.status_code == 200, r.text
        c.username = name
        yield c
