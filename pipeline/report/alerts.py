"""Optional alerting on high-significance changes.

All channels are gated behind env vars and ``COMPETE_ALERTS_ENABLED``. When
alerts are enabled but no channel is configured, messages are logged (dry-run)
so the path is observable without external services.
"""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

import httpx

from pipeline.config import Settings, get_settings
from pipeline.logging_setup import get_logger

log = get_logger(__name__)


@dataclass
class AlertItem:
    competitor: str
    signal_type: str
    title: str
    significance: int
    url: str | None = None


def slack_configured(s: Settings) -> bool:
    return bool(s.slack_webhook_url)


def email_configured(s: Settings) -> bool:
    return bool(s.smtp_host and s.smtp_user and s.smtp_password and s.alert_email_to)


def build_message(items: list[AlertItem]) -> str:
    lines = [f"🔔 compete: {len(items)} high-significance change(s) detected", ""]
    for it in items:
        link = f" - {it.url}" if it.url else ""
        lines.append(
            f"• [{it.signal_type}] {it.competitor}: {it.title} (sig {it.significance}){link}"
        )
    return "\n".join(lines)


def _send_slack(s: Settings, text: str) -> bool:
    try:
        resp = httpx.post(s.slack_webhook_url, json={"text": text}, timeout=10.0)  # type: ignore[arg-type]
        resp.raise_for_status()
        return True
    except Exception as exc:
        log.error("Slack alert failed: %s", exc)
        return False


def _send_email(s: Settings, subject: str, body: str) -> bool:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = s.smtp_user  # type: ignore[assignment]
        msg["To"] = s.alert_email_to  # type: ignore[assignment]
        msg.set_content(body)
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as server:  # type: ignore[arg-type]
            server.starttls()
            server.login(s.smtp_user, s.smtp_password)  # type: ignore[arg-type]
            server.send_message(msg)
        return True
    except Exception as exc:
        log.error("Email alert failed: %s", exc)
        return False


def notify(items: list[AlertItem], settings: Settings | None = None) -> dict[str, object]:
    """Dispatch alerts for the given items. Returns a result summary."""
    s = settings or get_settings()
    result: dict[str, object] = {"enabled": s.alerts_enabled, "considered": len(items)}

    if not s.alerts_enabled:
        log.info("alerts disabled; skipping (%d candidate items)", len(items))
        result["sent"] = []
        return result

    eligible = [i for i in items if i.significance >= s.alert_min_significance]
    result["eligible"] = len(eligible)
    if not eligible:
        result["sent"] = []
        return result

    text = build_message(eligible)
    sent: list[str] = []

    if slack_configured(s) and _send_slack(s, text):
        sent.append("slack")
    if email_configured(s) and _send_email(s, "compete: high-significance changes", text):
        sent.append("email")

    if not slack_configured(s) and not email_configured(s):
        log.info("[alerts dry-run] no channel configured. Would send:\n%s", text)
        sent.append("dry-run")

    result["sent"] = sent
    return result
