"""Capture dashboard screenshots via Playwright (visual verification + README assets).

Requires the web dev server (http://localhost:3000) and the API to be running.
    uv run python scripts/screenshots.py
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

# (path, filename, theme, viewport)
SHOTS = [
    ("/", "overview-light.png", "light", (1440, 900)),
    ("/", "overview-dark.png", "dark", (1440, 900)),
    ("/changes", "changes-light.png", "light", (1440, 900)),
    ("/competitors/anthropic", "competitor-dark.png", "dark", (1440, 1000)),
    ("/reports", "reports-dark.png", "dark", (1440, 900)),
    ("/settings", "settings-light.png", "light", (1440, 900)),
    ("/", "overview-mobile-dark.png", "dark", (390, 844)),
]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for path, name, theme, (w, h) in SHOTS:
            ctx = browser.new_context(
                viewport={"width": w, "height": h},
                device_scale_factor=2,
                color_scheme=theme,  # type: ignore[arg-type]
            )
            ctx.add_init_script(f"window.localStorage.setItem('theme', '{theme}');")
            page = ctx.new_page()
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1800)  # let charts animate in
            page.screenshot(path=str(OUT / name), full_page=(w >= 1000))
            print(f"captured {name}")
            ctx.close()
        browser.close()
    print(f"\nScreenshots written to {OUT}")


if __name__ == "__main__":
    main()
