"""Simple load test (threads + httpx) for the planner APIs, with CPU/memory sampling.

Measures PocketSmart's own overhead in OFFLINE-FALLBACK mode (no Gemini call), so results
exclude Gemini network latency. Usage:
    uvicorn main:app --port 8000     # in another terminal, ideally with GOOGLE_API_KEY unset
    python tests/perf_load.py [base_url] [users] [seconds]
"""
import statistics
import sys
import threading
import time
import uuid

import httpx
import psutil

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
USERS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
DURATION = int(sys.argv[3]) if len(sys.argv) > 3 else 20

HOME = {"total_budget": 60000, "num_lights": 4, "num_fans": 2, "num_furniture": 2, "num_dining_tables": 1,
        "has_living_room": True, "has_kitchen": True, "has_bedroom": False}
PARTY = {"total_budget": 30000, "num_guests": 25, "party_type": "Birthday", "venue_type": "Banquet Hall",
         "needs_catering": True, "needs_decoration": True, "needs_entertainment": True}
latencies, errors = [], []
lock = threading.Lock()


def worker(stop_at: float) -> None:
    name = f"load_{uuid.uuid4().hex[:8]}"
    with httpx.Client(base_url=BASE, timeout=30) as c:
        c.post("/register", json={"username": name, "email": f"{name}@example.com", "password": "Load-Test-123"})
        c.post("/token", data={"username": name, "password": "Load-Test-123"})
        i = 0
        while time.time() < stop_at:
            i += 1
            calls = [lambda: c.post("/home-budget", json=HOME), lambda: c.post("/party-budget", json=PARTY),
                     lambda: c.post("/jewelry-budget", data={"total_budget": "15000", "occasion": "Wedding"}),
                     lambda: c.get("/recommendation-history")]
            started = time.perf_counter()
            try:
                ok = calls[i % 4]().status_code == 200
            except httpx.HTTPError:
                ok = False
            elapsed = time.perf_counter() - started
            with lock:
                latencies.append(elapsed)
                if not ok:
                    errors.append(1)


def find_server_process():
    for proc in psutil.process_iter(["cmdline"]):
        cmd = " ".join(proc.info["cmdline"] or [])
        if "uvicorn" in cmd and "main:app" in cmd:
            return proc
    return None


def main() -> None:
    proc = find_server_process()
    cpu, mem = [], []
    stop_at = time.time() + DURATION
    threads = [threading.Thread(target=worker, args=(stop_at,)) for _ in range(USERS)]
    started = time.time()
    for t in threads:
        t.start()
    while time.time() < stop_at and proc:
        cpu.append(proc.cpu_percent(interval=1.0))
        mem.append(proc.memory_info().rss / 1e6)
    for t in threads:
        t.join()
    total = time.time() - started
    lat = sorted(latencies)
    print(f"virtual users      : {USERS}")
    print(f"duration (s)       : {total:.1f}")
    print(f"requests           : {len(lat)}")
    print(f"throughput (req/s) : {len(lat) / total:.1f}")
    print(f"avg response (s)   : {statistics.mean(lat):.3f}")
    print(f"p95 response (s)   : {lat[int(len(lat) * .95) - 1]:.3f}")
    print(f"max response (s)   : {lat[-1]:.3f}")
    print(f"error rate (%)     : {len(errors) / len(lat) * 100:.2f}")
    if cpu:
        print(f"server CPU avg/max : {statistics.mean(cpu):.0f}% / {max(cpu):.0f}% (of one core)")
        print(f"server RSS avg/max : {statistics.mean(mem):.0f} MB / {max(mem):.0f} MB")


if __name__ == "__main__":
    main()
