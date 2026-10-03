"""Drive the running app in a real browser (Playwright) and save screenshots as test/demo evidence.

Usage:  start the server (uvicorn main:app), then
        python tools/capture_screenshots.py [base_url] [output_dir]
Exits non-zero if a JavaScript error or failed step is detected.
"""
import os
import sys
import uuid
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "docs-src/assets")
OUT.mkdir(parents=True, exist_ok=True)


def make_outfit(path: Path) -> None:
    img = Image.new("RGB", (400, 500), (245, 240, 235))
    d = ImageDraw.Draw(img)
    d.polygon([(120, 60), (280, 60), (330, 480), (70, 480)], fill=(24, 60, 130))  # blue dress
    d.rectangle([180, 40, 220, 70], fill=(224, 190, 160))
    img.save(path)


def main() -> int:
    errors = []
    user = f"demo_{uuid.uuid4().hex[:6]}"
    outfit = OUT / "_outfit.png"
    make_outfit(outfit)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.getenv("CHROMIUM_PATH") or None)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        # The validation step deliberately triggers one 422; any other console error is a real failure.
        page.on("console", lambda m: errors.append(f"console: {m.text}")
                if m.type == "error" and "status of 422" not in m.text else None)

        def shot(name, full=True):
            page.add_style_tag(content=".site-header{position:static!important}")  # sticky header breaks full-page captures
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)

        page.goto(BASE + "/"); shot("01_landing")
        page.goto(BASE + "/register"); shot("02_register", False)
        page.fill("#username", user); page.fill("#email", f"{user}@example.com")
        page.fill("#password", "Demo-Pass-123"); page.fill("#confirm", "Demo-Pass-123")
        page.click("#register-form button[type=submit]"); page.wait_for_url("**/login?registered=1")
        shot("03_login", False)
        page.fill("#username", user); page.fill("#password", "Demo-Pass-123")
        page.click("#login-form button[type=submit]"); page.wait_for_url("**/dashboard")

        # Home planner
        page.goto(BASE + "/home-planner")
        page.fill("#total_budget", "80000"); page.fill("#additional_requirements", "Minimalist, warm lighting")
        page.click("form.form button[type=submit]"); page.wait_for_selector("#result .totals")
        shot("04_home_planner")

        # Party planner
        page.goto(BASE + "/party-planner")
        page.fill("#total_budget", "40000"); page.fill("#num_guests", "30")
        page.select_option("#party_type", "Birthday"); page.select_option("#venue_type", "Banquet hall")
        page.click("form.form button[type=submit]"); page.wait_for_selector("#result .totals")
        shot("05_party_planner")

        # Jewelry planner with outfit image
        page.goto(BASE + "/jewelry-planner")
        page.fill("#total_budget", "20000"); page.select_option("#occasion", "Wedding")
        page.fill("#preferences", "Gold, traditional"); page.set_input_files("#image", str(outfit))
        page.wait_for_selector("#preview:not([hidden])")
        page.click("form.form button[type=submit]"); page.wait_for_selector("#result .totals")
        shot("06_jewelry_planner")

        # Validation error shown to the user
        page.goto(BASE + "/party-planner")
        page.fill("#total_budget", "5000"); page.fill("#num_guests", "0")
        page.click("form.form button[type=submit]"); page.wait_for_selector(".field-error:not([hidden])")
        shot("07_validation_error", False)

        # Dashboard + history + detail modal
        page.goto(BASE + "/dashboard"); page.wait_for_selector("#recent li a"); shot("08_dashboard")
        page.goto(BASE + "/history"); page.wait_for_selector("#history .item"); shot("09_history")
        page.click("#history .item >> nth=0"); page.wait_for_selector("#detail-body .totals"); page.wait_for_timeout(300)
        shot("10_history_detail", False)

        # Logout returns to login; protected page now redirects
        page.keyboard.press("Escape")
        page.click("text=Log out"); page.wait_for_url("**/login")
        page.goto(BASE + "/dashboard"); page.wait_for_url("**/login")
        browser.close()
    outfit.unlink(missing_ok=True)
    if errors:
        print("FAILED - browser errors:\n  " + "\n  ".join(errors))
        return 1
    print(f"OK - UI flow passed for user {user}; screenshots in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
