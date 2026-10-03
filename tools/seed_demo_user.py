"""Create the demo evaluator account (username: demo / password: Demo@12345). Safe to re-run.

Run from the project root:  python tools/seed_demo_user.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make project modules importable

import auth  # noqa: E402
import database  # noqa: E402

database.init_db()
try:
    database.create_user("demo", "demo@pocketsmart.example", "Demo Evaluator", auth.hash_password("Demo@12345"))
    print("Created demo user: demo / Demo@12345")
except ValueError:
    print("Demo user already exists: demo / Demo@12345")
