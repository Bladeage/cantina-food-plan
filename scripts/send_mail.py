#!/usr/bin/env python3
"""Versendet email_body.html per SMTP, mit der vollständigen Wochenplan-Seite
(docs/index.html) als Anhang. Alle Empfänger werden per BCC angeschrieben
(nur im SMTP-Umschlag, nicht in den Headern), damit sie einander nicht sehen.

Konfiguration über Umgebungsvariablen: SMTP_HOST, SMTP_PORT (587), SMTP_USER,
SMTP_PASS, MAIL_FROM, MAIL_TO (kommagetrennt, erforderlich).

MAIL_FROM darf „Name <adresse@example.org>", eine reine Adresse oder auch nur
ein Anzeigename sein – im letzten Fall wird SMTP_USER als Adresse verwendet.
Umlaute im Anzeigenamen sind erlaubt und werden RFC-2047-kodiert.
"""
import datetime as dt
import os
import smtplib
import sys
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from pathlib import Path
from zoneinfo import ZoneInfo


def resolve_sender(raw_from: str, user: str) -> tuple[str, str]:
    """Liefert (Anzeigename, Adresse) für den Absender.

    Der Envelope-Absender muss eine reine Adresse sein. Steht in MAIL_FROM nur
    ein Anzeigename (z. B. „Menüplan"), wird SMTP_USER als Adresse genutzt –
    sonst scheitert smtplib an Umlauten im SMTP-Kommando.
    """
    name, addr = parseaddr(raw_from or "")
    if "@" not in addr:
        name, addr = (raw_from or "").strip(), user
    return name.strip(), addr.strip()


def parse_recipients(raw_to: str) -> list[str]:
    """Kommagetrennte Empfängerliste in reine Adressen zerlegen."""
    out = []
    for part in (raw_to or "").split(","):
        addr = parseaddr(part)[1].strip()
        if addr and addr not in out:
            out.append(addr)
    return out


def local_today() -> dt.date:
    """Heutiges Datum in der konfigurierten Zeitzone (Fallback: UTC).
    ZoneInfo berücksichtigt Sommer-/Winterzeit automatisch."""
    try:
        return dt.datetime.now(ZoneInfo(os.environ.get("PLAN_TZ", "Europe/Berlin"))).date()
    except Exception:  # noqa: BLE001 – z. B. fehlende tzdata
        return dt.datetime.now(dt.timezone.utc).date()


def week_number(today: dt.date | None = None) -> int:
    """KW des geplanten Wochenmontags – sonntags die *kommende* Woche."""
    today = today or local_today()
    monday = today + dt.timedelta(
        days=(7 - today.weekday()) % 7 if today.weekday() >= 5 else -today.weekday()
    )
    return monday.isocalendar().week


def build_message(body: str, sender: tuple[str, str], kw: int,
                  attachment: Path | None = None) -> MIMEMultipart:
    name, addr = sender
    msg = MIMEMultipart("mixed")
    msg["Subject"] = str(Header(f"🥗 Kantinen-Wochenplan KW {kw}", "utf-8"))
    # Anzeigename darf Umlaute enthalten – formataddr kodiert ihn RFC-konform.
    msg["From"] = formataddr((name, addr), charset="utf-8") if name else addr
    # Empfänger stehen bewusst NICHT in den Headern (BCC-Versand): sie kommen
    # nur in den SMTP-Umschlag.
    msg["To"] = msg["From"]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=addr.split("@")[-1] or None)
    msg.attach(MIMEText(body, "html", "utf-8"))

    if attachment and attachment.exists():
        part = MIMEBase("text", "html", charset="utf-8")
        part.set_payload(attachment.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment",
                        filename=f"wochenplan-kw{kw}.html")
        msg.attach(part)
    return msg


def main() -> int:
    host = os.environ.get("SMTP_HOST")
    if not host:
        print("SMTP_HOST nicht gesetzt – Mailversand übersprungen.")
        return 0

    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    if not user or not pw:
        print("SMTP_USER/SMTP_PASS nicht gesetzt – Mailversand übersprungen.")
        return 0

    recipients = parse_recipients(os.environ.get("MAIL_TO", ""))
    if not recipients:
        print("MAIL_TO nicht gesetzt – Mailversand übersprungen.")
        return 0

    body_path = Path("email_body.html")
    if not body_path.exists():
        print("email_body.html fehlt – nichts zu versenden.")
        return 0

    name, addr = resolve_sender(os.environ.get("MAIL_FROM", ""), user)
    kw = week_number()
    msg = build_message(body_path.read_text(encoding="utf-8"), (name, addr), kw,
                        Path("docs/index.html"))

    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=30) as s:
        s.starttls()
        s.ehlo()
        s.login(user, pw)
        # Nicht-ASCII in den Adressen selbst braucht die SMTPUTF8-Erweiterung.
        opts = []
        if any(not a.isascii() for a in [addr, *recipients]):
            if s.has_extn("smtputf8"):
                opts = ["SMTPUTF8"]
            else:
                print("WARNUNG: Adresse enthält Nicht-ASCII, Server kann kein "
                      "SMTPUTF8 – Versand könnte scheitern.")
        s.sendmail(addr, recipients, msg.as_string(), mail_options=opts)
    print(f"Mail an {len(recipients)} Empfänger versendet (BCC, KW {kw}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
