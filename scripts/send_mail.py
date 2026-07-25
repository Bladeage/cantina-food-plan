#!/usr/bin/env python3
"""Versendet email_body.html per SMTP, mit der vollständigen Wochenplan-Seite
(docs/index.html) als Anhang. Alle Empfänger werden per BCC angeschrieben
(nur im SMTP-Umschlag, nicht in den Headern), damit sie einander nicht sehen.
Konfiguration über Umgebungsvariablen: SMTP_HOST, SMTP_PORT (587), SMTP_USER,
SMTP_PASS, MAIL_FROM, MAIL_TO (kommagetrennt, erforderlich)."""
import os
import smtplib
import sys
import datetime as dt
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

host = os.environ.get("SMTP_HOST")
if not host:
    print("SMTP_HOST nicht gesetzt – Mailversand übersprungen.")
    sys.exit(0)

user = os.environ.get("SMTP_USER")
pw = os.environ.get("SMTP_PASS")
if not user or not pw:
    print("SMTP_USER/SMTP_PASS nicht gesetzt – Mailversand übersprungen.")
    sys.exit(0)

to = os.environ.get("MAIL_TO", "").strip()
if not to:
    print("MAIL_TO nicht gesetzt – Mailversand übersprungen.")
    sys.exit(0)

body_path = Path("email_body.html")
if not body_path.exists():
    print("email_body.html fehlt – nichts zu versenden.")
    sys.exit(0)
body = body_path.read_text(encoding="utf-8")

# KW des geplanten Wochenmontags: sonntags ist das die *kommende* Woche.
today = dt.date.today()
monday = today + dt.timedelta(
    days=(7 - today.weekday()) % 7 if today.weekday() >= 5 else -today.weekday()
)
kw = monday.isocalendar().week

sender = os.environ.get("MAIL_FROM") or user

msg = MIMEMultipart("mixed")
msg["Subject"] = f"🥗 Kantinen-Wochenplan KW {kw}"
msg["From"] = sender
# Empfänger stehen bewusst NICHT in den Headern (BCC-Versand): sie kommen nur
# in den SMTP-Umschlag (sendmail unten), damit sie einander nicht sehen.
msg["To"] = sender
msg.attach(MIMEText(body, "html", "utf-8"))

# Vollständige Wochenplan-Seite anhängen (falls vorhanden)
page = Path("docs/index.html")
if page.exists():
    part = MIMEBase("text", "html", charset="utf-8")
    part.set_payload(page.read_bytes())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment",
                    filename=f"wochenplan-kw{kw}.html")
    msg.attach(part)

recipients = [a.strip() for a in to.split(",") if a.strip()]
with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=30) as s:
    s.starttls()
    s.login(user, pw)
    s.sendmail(sender, recipients, msg.as_string())
print(f"Mail an {len(recipients)} Empfänger versendet (BCC, KW {kw}).")
