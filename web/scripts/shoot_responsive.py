import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

BASE = os.environ.get("SHOOT_BASE", "http://localhost:3010")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots" / "responsive"
OUT.mkdir(parents=True, exist_ok=True)

ROUTES = [
    ("overview", "/dashboard"),
    ("changes", "/changes"),
    ("competitor", "/competitors/openai"),
    ("reports", "/reports"),
    ("settings", "/settings"),
]
WIDTHS = [("mobile", 390, 844), ("tablet", 768, 1024)]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for scheme in ("light",):
            for wname, w, h in WIDTHS:
                ctx = await browser.new_context(
                    viewport={"width": w, "height": h},
                    color_scheme=scheme,
                    device_scale_factor=2,
                    is_mobile=(wname == "mobile"),
                )
                page = await ctx.new_page()
                for rname, path in ROUTES:
                    await page.goto(BASE + path, wait_until="load")
                    await page.wait_for_timeout(2200)
                    f = OUT / f"{rname}-{wname}.png"
                    await page.screenshot(path=str(f), full_page=True, animations="disabled")
                    print("saved", f)
                await ctx.close()
        await browser.close()


asyncio.run(main())
