#!/usr/bin/env python3
"""
Agent de relance email — Nexus Growth

Lit une liste de leads/utilisateurs (CSV) déjà classés par segment, et pour
chaque segment choisit et envoie automatiquement le bon email de la bonne
séquence, au bon moment.

Segments supportés (voir ../templates/emails/) :
  - signup_no_transfer : inscrit sans premier transfert
  - abandoned_quote     : devis demandé, non exécuté
  - dormant_user        : inactif depuis >30 jours
  - newsletter_lead     : email capturé sans compte

Deux modes d'exécution :
  - DRY-RUN (par défaut, ou si BREVO_API_KEY absent) : écrit l'email complet
    dans ../emails_drafts/ au lieu de l'envoyer. Permet de valider le contenu
    avant tout envoi réel.
  - ENVOI RÉEL : si BREVO_API_KEY est renseigné dans .env, envoie via l'API
    transactionnelle Brevo (gratuit jusqu'à 300 emails/jour).

Usage :
    python agents/relance_agent.py --leads data/leads_sample.csv
    python agents/relance_agent.py --leads data/leads_sample.csv --send   # envoi réel si clé dispo
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates" / "emails"
DRAFTS_DIR = ROOT / "emails_drafts"

SITE_URL = os.environ.get("SITE_URL", "https://nexustechnologies.cloud")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hello@nexustechnologies.cloud")
SENDER_NAME = os.environ.get("SENDER_NAME", "Nexus")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")

# Décalage en jours depuis l'événement déclencheur pour choisir quel email
# de la séquence envoyer aujourd'hui. Adapter selon vos besoins réels.
SEGMENT_SCHEDULES = {
    "signup_no_transfer": {"date_field": "signup_date", "steps": [(1, 0), (3, 1), (7, 2)]},
    "abandoned_quote": {"date_field": "last_quote_date", "steps": [(0, 0), (1, 1)]},  # jours, approx pour H+2/H+24
    "dormant_user": {"date_field": "last_transfer_date", "steps": [(30, 0), (40, 1)]},
    "newsletter_lead": {"date_field": "signup_date", "steps": [(0, 0), (3, 1), (7, 2), (14, 3)]},
}


def parse_email_blocks(template_text: str) -> list[dict]:
    """Découpe un fichier template en blocs [EMAIL N — offset] Objet / Corps."""
    blocks = []
    chunks = re.split(r"\n\[EMAIL \d+.*?\]\n", template_text)
    for chunk in chunks[1:]:
        subject_match = re.search(r"Objet:\s*(.+)", chunk)
        subject = subject_match.group(1).strip() if subject_match else "Nexus"
        body = chunk.split("\n", 1)[1].strip() if "\n" in chunk else chunk.strip()
        blocks.append({"subject": subject, "body": body})
    return blocks


def load_template(segment: str) -> list[dict]:
    path = TEMPLATES_DIR / f"{segment}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Aucun template pour le segment '{segment}' ({path})")
    return parse_email_blocks(path.read_text(encoding="utf-8"))


def render(text: str, lead: dict) -> str:
    replacements = {
        "{{first_name}}": lead.get("first_name") or "là",
        "{{site_url}}": SITE_URL,
        "{{amount}}": lead.get("amount") or "votre montant",
        "{{destination}}": lead.get("destination") or "votre destination",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def days_since(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        d = dt.date.fromisoformat(date_str.strip())
    except ValueError:
        return None
    return (dt.date.today() - d).days


def pick_step(segment: str, lead: dict) -> int | None:
    schedule = SEGMENT_SCHEDULES.get(segment)
    if not schedule:
        return None
    elapsed = days_since(lead.get(schedule["date_field"]))
    if elapsed is None:
        return None
    eligible = [idx for (threshold, idx) in schedule["steps"] if elapsed >= threshold]
    return max(eligible) if eligible else None


def send_via_brevo(to_email: str, to_name: str, subject: str, body: str) -> bool:
    try:
        import requests
    except ImportError:
        print("[relance_agent] `requests` non installé, impossible d'envoyer via Brevo.", file=sys.stderr)
        return False

    html_body = "<br>".join(body.splitlines())
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": f"<div style='font-family:sans-serif;font-size:15px;line-height:1.5'>{html_body}</div>",
    }
    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"[relance_agent] Échec d'envoi Brevo pour {to_email}: {exc}", file=sys.stderr)
        return False


def write_draft(to_email: str, subject: str, body: str) -> Path:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_email = to_email.replace("@", "_at_")
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DRAFTS_DIR / f"{ts}_{safe_email}.md"
    path.write_text(f"À: {to_email}\nObjet: {subject}\n\n{body}\n", encoding="utf-8")
    return path


def process_leads(csv_path: Path, do_send: bool) -> None:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("[relance_agent] Aucun lead trouvé dans le CSV.")
        return

    for lead in rows:
        segment = (lead.get("segment") or "").strip()
        email = (lead.get("email") or "").strip()
        if not segment or not email:
            continue
        try:
            template = load_template(segment)
        except FileNotFoundError as exc:
            print(f"[relance_agent] {exc}", file=sys.stderr)
            continue

        step = pick_step(segment, lead)
        if step is None:
            print(f"[relance_agent] {email} ({segment}) : pas encore éligible à une relance.")
            continue
        if step >= len(template):
            step = len(template) - 1

        chosen = template[step]
        subject = render(chosen["subject"], lead)
        body = render(chosen["body"], lead)

        sent = False
        if do_send and BREVO_API_KEY:
            sent = send_via_brevo(email, lead.get("first_name", ""), subject, body)

        if sent:
            print(f"[relance_agent] ✅ Envoyé à {email} — segment={segment}, étape={step + 1}/{len(template)}")
        else:
            draft_path = write_draft(email, subject, body)
            reason = "dry-run" if not (do_send and BREVO_API_KEY) else "échec d'envoi, sauvegardé en brouillon"
            print(f"[relance_agent] 📝 Brouillon ({reason}) → {draft_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent de relance email Nexus Growth")
    parser.add_argument("--leads", type=str, required=True, help="Chemin vers le CSV des leads")
    parser.add_argument("--send", action="store_true", help="Envoyer réellement via Brevo (sinon dry-run)")
    args = parser.parse_args()

    csv_path = Path(args.leads)
    if not csv_path.is_absolute():
        csv_path = Path.cwd() / csv_path
    if not csv_path.exists():
        raise SystemExit(f"Fichier introuvable : {csv_path}")

    process_leads(csv_path, do_send=args.send)


if __name__ == "__main__":
    main()
