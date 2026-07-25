#!/usr/bin/env python3
"""
Kantinen-Wochenplan
Holt den Speiseplan, berechnet Nährwerte pro Portion, wählt pro Tag
Empfehlungen (ausgewogen / Protein / vegetarisch) und baut kcal-Kombis
(~600 & ~1000 kcal). Ausgabe: docs/index.html, docs/plan.json, email_body.html
"""

import json
import os
import re
import sys
import time
import itertools
import datetime as dt
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Quell-URL kommt ausschließlich aus der Umgebung (Actions-Secret EUREST_BASE),
# damit sie nicht im (ggf. öffentlichen) Code steht.
BASE = os.environ.get("EUREST_BASE", "").rstrip("/")
if not BASE:
    print("FEHLER: EUREST_BASE ist nicht gesetzt (Secret/Umgebungsvariable mit "
          "der Basis-URL der Kantinen-Web-App).", file=sys.stderr)
    sys.exit(1)
MAIN_URL = f"{BASE}/ajaxview/main"
DAY_URL = BASE + "/ajaxpage_dailymenupage/{id}"
PRICE_FACTOR = float(os.environ.get("PRICE_FACTOR", "1.5"))
TARGETS = (600, 1000)
TOLERANCE = {600: 90, 1000: 130}
OUT_DIR = Path(os.environ.get("OUT_DIR", "docs"))
DEBUG = os.environ.get("DEBUG", "") == "1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/",
}

MEAT_WORDS = re.compile(
    r"h[äa]hn|geflügel|pute|rind|schwein|speck|schinken|salami|wurst|lamm|"
    r"fisch|lachs|thunfisch|garnele|krabbe|gyros|frikadelle vom|hack|bolognese|"
    r"leber|ente|kasseler|mett|bratwurst|currywurst|d[öo]ner|cevapcici",
    re.I,
)
VEG_WORDS = re.compile(r"vegan|vegetarisch|veggie|gemüse|falafel|tofu|halloumi|linsen|kichererbse", re.I)

WEIGHT_RULES = [  # (Regex, prüft: 'both'|'name'|'station', Gramm) – Reihenfolge = Priorität
    (re.compile(r"suppe", re.I), "both", 300),
    (re.compile(r"beilagensalat|obstsalat|side", re.I), "name", 150),
    (re.compile(r"topping|dessert|creme|pudding|quark|kuchen", re.I), "station", 150),
    (re.compile(r"bowl|salat", re.I), "both", 350),
]
FALLBACK_WEIGHT = 400  # Hauptgericht
IMPLAUSIBLE_KCAL = 1400  # darüber: Portionsgewicht vermutlich Datenfehler


def log(*a):
    print(*a, file=sys.stderr)


def fetch(url: str, attempts: int = 3) -> str:
    """Robuster GET mit Retries – fängt Netzwerkfehler und (zu) kurze
    Antworten der Quelle ab, die sonst zu leeren Tagen führen."""
    last = None
    for i in range(attempts):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            if len(r.text) < 200:
                raise ValueError(f"verdächtig kurze Antwort ({len(r.text)} Bytes)")
            return r.text
        except Exception as e:  # noqa: BLE001 – bewusst breit, um zu retryen
            last = e
            log(f"  fetch-Fehler ({url}): {e} – Versuch {i + 1}/{attempts}")
            time.sleep(2 * (i + 1))
    raise last


# ---------------------------------------------------------------- Tage finden
def discover_days() -> list[dict]:
    """IDs + Daten der Tage aus der Übersichtsseite ziehen.
    Fallback: sequentielle IDs ab SEED_ID/SEED_DATE (Mo–Fr, +1 pro Tag)."""
    html = fetch(MAIN_URL)
    if DEBUG:
        Path("debug_main.html").write_text(html, encoding="utf-8")

    days = []
    # Datums-Pattern: "Montag 27.07.2026"
    date_re = re.compile(r"(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+(\d{2}\.\d{2}\.\d{4})")
    # 1) Direkt verlinkte oder als data-Attribut hinterlegte IDs suchen
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.find_all(True):
        text = el.get_text(" ", strip=True)
        m = date_re.search(text or "")
        if not m or len(text) > 40:  # nur die Tages-Links selbst, keine Container
            continue
        blob = str(el)
        idm = re.search(r"ajaxpage_dailymenupage/(\d+)", blob) or re.search(r'data-\w+="(\d{5,8})"', blob)
        if idm:
            days.append({"weekday": m.group(1), "date": m.group(2), "id": idm.group(1)})

    if not days:
        # 2) Fallback: bekannte Sequenz nutzen (146465 = Mo 27.07.2026, +1/Tag)
        seed_id = int(os.environ.get("SEED_ID", "146465"))
        seed_date = dt.datetime.strptime(os.environ.get("SEED_DATE", "27.07.2026"), "%d.%m.%Y").date()
        dates = [m.group(2) for m in date_re.finditer(html)]
        wdays = [m.group(1) for m in date_re.finditer(html)]
        for wd, d in zip(wdays, dates):
            delta = (dt.datetime.strptime(d, "%d.%m.%Y").date() - seed_date).days
            days.append({"weekday": wd, "date": d, "id": str(seed_id + delta)})
        if days:
            log("Hinweis: IDs nicht im HTML gefunden – sequentieller Fallback ab SEED_ID aktiv.")

    # Nur aktuelle Woche (Mo–Fr ab heute bzw. kommender Montag)
    today = dt.date.today()
    monday = today + dt.timedelta(days=(7 - today.weekday()) % 7 if today.weekday() >= 5 else -today.weekday())
    week = []
    for d in days:
        date = dt.datetime.strptime(d["date"], "%d.%m.%Y").date()
        if monday <= date <= monday + dt.timedelta(days=4):
            week.append(d)
    result = week or days[:5]
    # Deduplizieren, Reihenfolge erhalten
    seen, out = set(), []
    for d in result:
        if d["id"] not in seen:
            seen.add(d["id"])
            out.append(d)
    return out


# ------------------------------------------------------------- Tag parsen
# Tolerante Nährwert-Muster (case-insensitive). Reihenfolge = Priorität; das
# erste passende Muster gewinnt. Synonyme decken bekannte Schreibvarianten der
# Quelle ab (Energie/Kalorien, davon Zucker, gesättigte Fettsäuren, …).
NUTRI_PATTERNS = [
    ("kcal", r"([\d.,]+)\s*kcal"),  # Label egal – jede kcal-Angabe zählt
    ("satfat", r"(?:davon\s*)?(?:ges[äa]ttigte|ges\.?)\s*fetts[äa]uren\s*:?\s*([\d.,]+)\s*g"),
    ("sugar", r"(?:davon\s*)?zucker\s*:?\s*([\d.,]+)\s*g"),
    ("fat", r"(?<![\wä])fett\s*:?\s*([\d.,]+)\s*g"),  # nicht „Fettsäuren"
    ("carbs", r"kohlenhydrate?\s*:?\s*([\d.,]+)\s*g"),
    ("protein", r"eiwei(?:ß|ss)\s*:?\s*([\d.,]+)\s*g"),
    ("salt", r"salz\s*:?\s*([\d.,]+)\s*g"),
]


def _num(s: str) -> float:
    return float(s.replace(".", "").replace(",", ".")) if "," in s else float(s.replace(",", "."))


def extract_nutrients(text: str) -> dict:
    """Zieht die 100-g-Nährwerte tolerant aus einem Textblock (Fallback)."""
    per100 = {}
    for key, pat in NUTRI_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            per100[key] = _num(m.group(1))
    return per100


def _title_to_key(title: str) -> str | None:
    """Bildet einen Nährwert-Titel der Quelle auf einen internen Key ab."""
    t = title.lower()
    if "kilojoule" in t or t.strip() == "kj":
        return None
    if "kalorien" in t or "energie" in t:
        return "kcal"
    if "fettsäuren" in t or "fettsauren" in t:  # „Ges. Fettsäuren"
        return "satfat"
    if "fett" in t:
        return "fat"
    if "kohlenhydrat" in t:
        return "carbs"
    if "zucker" in t:
        return "sugar"
    if "eiwei" in t or "protein" in t:
        return "protein"
    if "salz" in t:
        return "salt"
    return None


def parse_nutrition_list(container) -> dict:
    """Liest die 100-g-Nährwerte strukturiert aus <ul class="nutrition-values">.
    Robuster als Textextraktion – ordnet Werte per Titel zu (ignoriert kJ)."""
    per100 = {}
    for li in container.select("ul.nutrition-values li"):
        title_el = li.select_one(".title")
        val_el = li.select_one(".value-unit")
        if not title_el or not val_el:
            continue
        key = _title_to_key(title_el.get_text(" ", strip=True))
        if not key:
            continue
        m = re.search(r"[\d.,]+", val_el.get_text(" ", strip=True))
        if m:
            per100.setdefault(key, _num(m.group(0)))
    return per100


def parse_day(html: str, day: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    dishes = []
    # Anker: „Nährwerte pro/je 100 g" in beliebiger Schreibweise
    anchors = soup.find_all(string=re.compile(r"N[äa]hrwert", re.I))
    if DEBUG:
        log(f"  [debug] {day.get('date','?')}: {len(anchors)} Nährwert-Anker gefunden")
    for anchor in anchors:
        # Container hochlaufen, bis Name + Nährwerte (kcal) enthalten sind
        node = anchor.parent
        best = None
        for _ in range(8):
            if node is None:
                break
            txt = node.get_text(" ", strip=True)
            if "kcal" in txt.lower():
                best = node
                if "€" in txt:  # Preis mit drin → vollständiger Gericht-Container
                    break
            node = node.parent
        node = best
        if node is None:
            continue
        txt = node.get_text(" ", strip=True)
        if DEBUG and not dishes:
            log(f"  [debug] Beispiel-Container: {txt[:200]!r}")

        dish: dict = {"station": "", "name": "", "labels": [], "images": []}

        # Station = nächstliegende h2-Überschrift (nicht die „Nährwerte"-Zeile)
        head = node.find("h2")
        if head is None or "Nährwert" in head.get_text():
            head = anchor.find_previous("h2")
        if head is not None and "Nährwert" not in head.get_text():
            dish["station"] = head.get_text(" ", strip=True)

        # Name: direkter Text von .dishDescriptionInner (ohne Allergene/CO2/Gewicht).
        name = ""
        desc = node.select_one(".dishDescriptionInner") or node.select_one(".dishDescription")
        if desc is not None:
            name = " ".join("".join(desc.find_all(string=True, recursive=False)).split())
        if not name:  # Fallback: Textheuristik bis zur Allergen-Klammer
            body = txt.split("Nährwert")[0]
            name = re.split(r"\(\s*[\dA-Z]", body)[0]
            name = re.sub(r"\d+[.,]\d+\s*(kg|€).*", "", name).strip(" -–|")
            name = " ".join(name.split())
        # Kombinierbare Gerichte liefern nur die Fortsetzung („mit …", „& …").
        # Dann Station voranstellen, damit der Name auch ohne Kontext (Mail,
        # Kombis) vollständig ist. Im HTML-Table wird die Station-Doppelung
        # wieder entfernt (siehe render.py).
        if dish["station"] and re.match(r"^(mit|und|&|,|dazu|inkl)\b", name, re.I):
            name = f"{dish['station']} {name}".strip()
        dish["name"] = name[:120] or "Unbenanntes Gericht"

        # Gewicht: bevorzugt aus .co2-rating-value (z. B. „0,3 kg")
        weight_g = None
        w_el = node.select_one(".co2-rating-value")
        wm = re.search(r"([\d.,]+)\s*kg", w_el.get_text() if w_el else txt)
        if wm:
            weight_g = _num(wm.group(1)) * 1000

        # Preis intern aus .dishPriceInner; „extern X €" hat Vorrang, falls vorhanden
        p_int = None
        p_el = node.select_one(".dishPriceInner")
        if p_el:
            pm = re.search(r"([\d.,]+)\s*€", p_el.get_text())
            if pm:
                p_int = _num(pm.group(1))
        if p_int is None:  # Fallback: letzter Preis im Container-Text
            allp = re.findall(r"([\d.,]+)\s*€", txt)
            if allp:
                p_int = _num(allp[-1])
        em = re.search(r"extern\s*([\d.,]+)\s*€", txt, re.I)
        p_ext = _num(em.group(1)) if em else None
        dish["price_intern"] = p_int
        dish["price_extern"] = p_ext if p_ext is not None else (round(p_int * PRICE_FACTOR, 2) if p_int else None)
        dish["price_extern_estimated"] = p_ext is None

        # Nährwerte je 100 g: strukturiert aus <ul class="nutrition-values">,
        # Fallback auf tolerante Textextraktion.
        per100 = parse_nutrition_list(node)
        if "kcal" not in per100:
            idx = txt.lower().find("nährwert")
            per100 = {**extract_nutrients(txt[idx:] if idx >= 0 else txt), **per100}
        if "kcal" not in per100:
            if DEBUG:
                log(f"  [debug] übersprungen (keine kcal): {dish['name']!r}")
            continue
        # KH-Plausibilität (Zucker ⊆ KH)
        if per100.get("carbs", 0) < per100.get("sugar", 0):
            per100["carbs"] = per100["sugar"]

        # Portionsgewicht schätzen, falls fehlend oder unplausibel
        def guess_weight():
            fields = {"station": [dish["station"]], "name": [dish["name"]],
                      "both": [dish["station"], dish["name"]]}
            for pat, scope, g in WEIGHT_RULES:
                if any(t and pat.search(t) for t in fields[scope]):
                    return g
            return FALLBACK_WEIGHT

        estimated = False
        if weight_g is None or per100["kcal"] * weight_g / 100 > IMPLAUSIBLE_KCAL:
            estimated = True
            weight_g = guess_weight()

        dish["weight_g"] = round(weight_g)
        dish["weight_estimated"] = estimated
        dish["per100"] = per100
        dish["portion"] = {k: round(v * weight_g / 100, 1) for k, v in per100.items()}
        dish["portion"]["kcal"] = round(per100["kcal"] * weight_g / 100)

        # Kennzeichnungen aus Icons/Alt-Texten/Klassen + Bilder
        for img in node.find_all("img"):
            src = img.get("src", "")
            alt = (img.get("alt") or img.get("title") or "").lower()
            cls = " ".join(img.get("class", [])).lower()
            blob = f"{src.lower()} {alt} {cls}"
            if "co2" in blob:
                continue
            for tag in ("vegan", "vegetarisch", "protein", "bio", "regional", "halal", "glutenfrei", "scharf"):
                if tag in blob and tag not in dish["labels"]:
                    dish["labels"].append(tag)
            if any(x in blob for x in ("icon", "label", "kennzeich", "svg")):
                continue
            if src:
                dish["images"].append(requests.compat.urljoin(BASE + "/", src))
        for cls_el in node.find_all(class_=re.compile("vegan|vegetarisch|protein", re.I)):
            for tag in ("vegan", "vegetarisch", "protein"):
                if re.search(tag, " ".join(cls_el.get("class", [])), re.I) and tag not in dish["labels"]:
                    dish["labels"].append(tag)

        if not any(d["name"] == dish["name"] and d["station"] == dish["station"] for d in dishes):
            dishes.append(dish)

    if DEBUG:
        Path(f"debug_day_{day['id']}.html").write_text(html, encoding="utf-8")
    return dishes


# ------------------------------------------------------------- Empfehlungen
def is_veg(d: dict) -> bool:
    ref = f"{d['station']} {d['name']}"
    if "vegan" in d["labels"] or "vegetarisch" in d["labels"]:
        return True
    return bool(VEG_WORDS.search(ref)) and not MEAT_WORDS.search(ref)


SIDE_STATION_RE = re.compile(r"topping|dessert|suppe|beilage", re.I)
SIDE_NAME_RE = re.compile(r"beilagensalat|obstsalat|suppe|dessert", re.I)


def is_main(d: dict) -> bool:
    return (d["portion"]["kcal"] >= 300
            and not SIDE_STATION_RE.search(d["station"] or "")
            and not SIDE_NAME_RE.search(d["name"]))


def balanced_score(d: dict) -> float:
    p = d["portion"]
    kcal = max(p["kcal"], 1)
    score = 0.0
    score += 3 if 350 <= kcal <= 800 else 0
    score += min(p.get("protein", 0) / 10, 4)            # bis 40 g Protein belohnen
    fat_ratio = p.get("fat", 0) * 9 / kcal
    score += 2 if fat_ratio < 0.35 else (1 if fat_ratio < 0.45 else 0)
    score -= max(0, (p.get("sugar", 0) - 15) / 10)
    score -= max(0, (p.get("salt", 0) - 5) / 2)
    score += 1 if is_veg(d) else 0                       # leichter Bonus
    return round(score, 2)


def combos(dishes: list[dict]) -> dict:
    out = {}
    for target in TARGETS:
        best, best_diff = None, 10**9
        for r in (1, 2, 3):
            for combo in itertools.combinations(dishes, r):
                if not any(is_main(d) for d in combo):
                    continue
                kcal = sum(d["portion"]["kcal"] for d in combo)
                diff = abs(kcal - target)
                protein = sum(d["portion"].get("protein", 0) for d in combo)
                if best is None or (diff, -protein) < (best_diff, -best[1]):
                    best, best_diff = (combo, protein, kcal), diff
        if best:
            combo, protein, kcal = best
            out[str(target)] = {
                "kcal": kcal,
                "protein": round(protein, 1),
                "price_extern": round(sum(d["price_extern"] or 0 for d in combo), 2),
                "items": [d["name"] for d in combo],
                "approx": best_diff > TOLERANCE[target],  # außerhalb der Toleranz
            }
    return out


def recommend(dishes: list[dict]) -> dict:
    mains = [d for d in dishes if is_main(d)] or dishes
    rec = {}
    if mains:
        rec["ausgewogen"] = max(mains, key=balanced_score)["name"]
        rec["protein"] = max(mains, key=lambda d: d["portion"].get("protein", 0))["name"]
        veg = [d for d in mains if is_veg(d)]
        if veg:
            rec["vegetarisch"] = max(veg, key=balanced_score)["name"]
    return rec


# ------------------------------------------------------------- Hauptlauf
def main():
    days = discover_days()
    if not days:
        log("FEHLER: Keine Tage gefunden. DEBUG=1 setzen und debug_main.html prüfen.")
        sys.exit(1)
    log(f"{len(days)} Tage gefunden: " + ", ".join(f"{d['weekday']} {d['date']} (#{d['id']})" for d in days))

    plan = []
    for day in days:
        dishes = []
        for attempt in range(2):  # ein erneuter Versuch bei leerem Ergebnis
            try:
                dishes = parse_day(fetch(DAY_URL.format(id=day["id"])), day)
            except Exception as e:
                log(f"WARNUNG: {day['date']} Abruf fehlgeschlagen ({e})")
                dishes = []
            if dishes:
                break
            if attempt == 0:
                log(f"  {day['date']}: 0 Gerichte – erneuter Versuch …")
                time.sleep(3)
        plan.append({**day, "dishes": dishes, "recommendations": recommend(dishes), "combos": combos(dishes)})
        log(f"  {day['weekday']} {day['date']}: {len(dishes)} Gerichte")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = {"generated": dt.datetime.now().isoformat(timespec="minutes"), "price_factor": PRICE_FACTOR}
    (OUT_DIR / "plan.json").write_text(json.dumps({"meta": meta, "days": plan}, ensure_ascii=False, indent=2), encoding="utf-8")

    from render import render_page, render_email  # lokale Templates
    (OUT_DIR / "index.html").write_text(render_page(plan, meta), encoding="utf-8")
    Path("email_body.html").write_text(render_email(plan, meta), encoding="utf-8")
    log(f"Fertig: {OUT_DIR/'index.html'}, {OUT_DIR/'plan.json'}, email_body.html")


if __name__ == "__main__":
    main()
