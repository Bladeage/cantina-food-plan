# CLAUDE.md – Projektkontext & Handover

## Ziel
Wöchentlicher Speiseplan-Scraper für eine Kantinen-Web-App. Berechnet Nährwerte
pro Portion, empfiehlt pro Tag (ausgewogen/Protein/vegetarisch) und baut
~600- & ~1000-kcal-Kombis mit Extern-Preisen. Läuft via GitHub Actions
(**sonntags 17:35 Ortszeit**, plus Sicherheitsnetz 21:35, das sich bei schon
vorhandenem Tagesplan selbst überspringt; Plan für die kommende Woche), Ausgabe:
`docs/index.html` und `docs/plan.json`. **Kein E-Mail-Versand** (bewusst
entfernt, siehe unten).

## Vertraulichkeit (WICHTIG)
Das Repo ist ggf. **öffentlich**. Deshalb stehen **weder der Name der
Kantine/des Betreibers noch persönliche Daten (E-Mail-Adressen) im Code, in
Commits, im PR oder in Logs**. Konkrete Werte leben ausschließlich in
Actions-Secrets:
- `EUREST_BASE` – Basis-URL der Web-App (erforderlich)
- `PLAN_TITLE`, `SOURCE_URL` – optionale Bezeichnung/Quell-Link für Kopf- und
  Fußzeile. Achtung: landen in `docs/` (öffentlich), sofern nicht
  `PAGE_SHOW_DETAILS=0` gesetzt ist.
Beim Weiterentwickeln darauf achten, dass keine dieser Informationen in
Ausgaben, Kommentare, Commit-Messages oder Workflow-Logs gerät.

## Status: Parser live verifiziert (Stand 25.07.2026)
Gegen die echte Web-App via GitHub-Actions-Läufe bestätigt: 5 Tage (Mo–Fr),
6–10 Gerichte/Tag, Portionswerte korrekt (Referenzgericht 740 kcal / 42,6 g
Eiweiß). Entwicklung ohne Direktzugriff auf die Quelle (Egress im
Entwicklungs-Sandkasten blockiert) → Verifikation läuft über den
Actions-Runner: Workflow manuell mit **Debug**-Häkchen starten → Logs +
Artefakt `debug-html` prüfen.

## Verifizierte Fakten zur Quelle (aus echten Abrufen)
- Struktur: `GET {BASE}/ajaxview/main` = Tagesübersicht (2 Wochen, Mo–Fr),
  `GET {BASE}/ajaxpage_dailymenupage/<ID>` = Tagesseite, frei abrufbar.
- Tages-IDs zählen +1 pro Tag; Fallback über `SEED_ID`/`SEED_DATE`
  (Workflow-Env), falls die IDs nicht im HTML stehen.
- Tagesseiten-Markup (Klassen): `.dishDescriptionInner` (Name, ggf. nur
  „mit …"-Fortsetzung → Station wird vorangestellt), `.additives`
  (Allergen-Codes), `.co2-rating-value` (Portionsgewicht „0,x kg"),
  `.dishPriceInner` (Preis intern), `ul.nutrition-values > li` mit
  `.title`/`.value-unit` (Nährwerte pro 100 g inkl. fehlerhafter
  kJ-Angaben – werden ignoriert).
- Keine Bilder und keine maschinenlesbaren vegan/vegetarisch-Labels im
  Markup → Wortheuristik (`VEG_WORDS`/`MEAT_WORDS`).
- Bekannte Datenfehler der Quelle: unplausible Portionsgewichte (0,9 kg
  Salat), KH < Zucker, kJ-Werte falsch → Plausibilisierung existiert
  (`WEIGHT_RULES`, `IMPLAUSIBLE_KCAL`, kJ ignoriert, Zucker⊆KH).
- Transiente Leerantworten einzelner Tagesseiten kommen vor → `fetch()` mit
  Retries + erneuter Tagesabruf bei 0 Gerichten (bereits eingebaut).

## Architektur
- `scripts/fetch_menu.py` – Discovery, Parser, Scoring, Kombinatorik (Kern)
- `scripts/render.py` – HTML-Seite (`render_page`), reines Standard-Python
- `.github/workflows/wochenplan.yml` – je Slot ein Sommer-/Winter-Cron
  (15:35+19:35 UTC bei UTC+2, 16:35+20:35 UTC bei UTC+1); der Guard-Schritt
  lässt nur den zur aktuellen Zeitzone passenden durch und überspringt das
  Sicherheitsnetz bei vorhandenem Tagesplan. Manueller Start mit Option
  Debug; committet `docs/`.
- Zeitzone überall über `PLAN_TZ` (Standard `Europe/Berlin`), zusätzlich als
  `TZ` job-weit gesetzt; Sommer-/Winterzeit kommt aus der Zeitzonendatenbank.

## Nutzerpräferenzen (nicht wegoptimieren!)
- Preise immer **extern** anzeigen (Untermieter-Konditionen, ~×1,5)
- Drei Empfehlungsschienen pro Tag: ausgewogen / viel Protein / vegetarisch
- Kombi-Ziele exakt 600 & 1000 kcal; wenn unerreichbar: beste Annäherung
  mit `†` kennzeichnen (implementiert)
- Geschätzte Werte transparent mit `*` markieren
- Kein E-Mail-Versand mehr (auf Wunsch entfernt); die Seite ist die einzige
  Ausgabe und muss daher den vollständigen Plan zeigen
- Seitenaufbau: Wochenleiste mit Tages-Tabs (aktueller Tag vorausgewählt,
  ohne JavaScript alle Tage sichtbar); je Tag zuerst Empfehlungen und
  kcal-Kombis, danach die vollständige Gerichteliste
- Sprache aller Ausgaben: Deutsch
