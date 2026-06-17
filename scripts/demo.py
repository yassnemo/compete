"""One-command demo launcher.

Seeds curated demo data, builds the dbt marts, then starts the API and the
Next.js dev server together. Ctrl+C stops both.

    uv run python scripts/demo.py            # full demo
    uv run python scripts/demo.py --skip-seed  # reuse existing warehouse

The web app's npm dependencies must be installed once (the script will run
`npm install` automatically if web/node_modules is missing).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WEB = REPO / "web"
IS_WIN = sys.platform.startswith("win")
NPM = "npm.cmd" if IS_WIN else "npm"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the compete demo (API + web).")
    parser.add_argument("--skip-seed", action="store_true", help="Reuse the existing warehouse.")
    args = parser.parse_args()

    if not args.skip_seed:
        print("→ Seeding demo data and building marts…")
        run([sys.executable, str(REPO / "scripts" / "seed_demo.py"), "--build"])

    if not (WEB / "node_modules").exists():
        print("→ Installing web dependencies (first run)…")
        run([NPM, "install"], cwd=WEB)

    print("\n→ Starting API (http://127.0.0.1:8000) and web (http://localhost:3000)…")
    print("  Press Ctrl+C to stop both.\n")

    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--port", "8000"], cwd=REPO
    )
    time.sleep(2)
    web = subprocess.Popen([NPM, "run", "dev"], cwd=WEB)

    try:
        web.wait()
    except KeyboardInterrupt:
        print("\n→ Shutting down…")
    finally:
        for proc in (web, api):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
