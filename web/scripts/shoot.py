import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

import os

BASE = os.environ.get("SHOOT_BASE", "http://localhost:3002")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

SHOTS = [
    ("landing", "/", 1440, 900),
    ("landing-mobile", "/", 390, 844),
    ("dashboard", "/dashboard", 1440, 900),
    ("docs", "/docs", 1440, 900),
    ("settings", "/settings", 1440, 900),
]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for scheme in ("light", "dark"):
            for name, path, w, h in SHOTS:
                ctx = await browser.new_context(
                    viewport={"width": w, "height": h},
                    color_scheme=scheme,
                    device_scale_factor=2,
                )
                page = await ctx.new_page()
                await page.goto(BASE + path, wait_until="load")
                # Scroll through so GSAP ScrollTrigger reveals fire, then return to top.
                await page.evaluate(
                    """async () => {
                        const step = window.innerHeight * 0.6;
                        for (let y = 0; y <= document.body.scrollHeight; y += step) {
                            window.scrollTo(0, y);
                            await new Promise(r => setTimeout(r, 220));
                        }
                        window.scrollTo(0, 0);
                    }"""
                )
                await page.wait_for_timeout(2600)
                f = OUT / f"{name}-{scheme}.png"
                full = "mobile" in name or name == "landing"
                await page.screenshot(
                    path=str(f), full_page=full, animations="disabled", timeout=90000
                )
                print("saved", f)
                await ctx.close()
        await browser.close()


asyncio.run(main())
