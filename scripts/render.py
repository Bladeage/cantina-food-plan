"""HTML-Ausgaben: Wochenplan-Seite (docs/index.html) + E-Mail-Body (inline).

Aufbau je Tag: Menü (alle angebotenen Gerichte) → Empfehlungen → kcal-Vorschläge.
Kopfzeile: Bezeichnung + Kalenderwoche/Zeitraum, Fußzeile: Quelle.
"""
import datetime as dt
import html

DEFAULT_TITLE = "Kantinen-Wochenplan"


def _fmt(v, unit=""):
    if v is None:
        return "–"
    s = f"{v:.1f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
    return s.replace(".", ",") + unit


def _euro(v):
    return "–" if v is None else f"{v:.2f}".replace(".", ",") + " €"


def _dish_name(d):
    """Name ohne führende Station (die im Menü separat gezeigt wird)."""
    name, st = d["name"], d.get("station") or ""
    if st and name.startswith(st + " "):
        name = name[len(st):].strip()
    return name


def _week_info(plan):
    """('KW 31', '27.07. – 31.07.2026') aus den Tagesdaten."""
    dates = []
    for day in plan:
        try:
            dates.append(dt.datetime.strptime(day["date"], "%d.%m.%Y").date())
        except (ValueError, KeyError):
            continue
    if not dates:
        return "", ""
    a, b = min(dates), max(dates)
    span = a.strftime("%d.%m.") if a == b else f"{a.strftime('%d.%m.')} – {b.strftime('%d.%m.')}"
    return f"KW {a.isocalendar().week}", f"{span}{b.strftime('%Y')}"


def _host(url):
    """Anzeigename für einen Link (Host ohne Schema/www)."""
    return url.split("//")[-1].split("/")[0].removeprefix("www.") or url


REC_ORDER = (("ausgewogen", "ausgewogen"), ("protein", "proteinreich"), ("vegetarisch", "vegetarisch"))


def _grouped_recs(rec):
    """Empfehlungen nach Gericht gruppieren: empfiehlt mehr als eine Schiene
    dasselbe Gericht, werden die Labels zusammengefasst
    („ausgewogen / proteinreich: Menü 1")."""
    groups = []
    for key, label in REC_ORDER:
        name = rec.get(key)
        if not name:
            continue
        for g in groups:
            if g[1] == name:
                g[0].append(label)
                break
        else:
            groups.append(([label], name))
    return [(" / ".join(labels), name) for labels, name in groups]


def _dish_roles(rec, name):
    return [label for key, label in REC_ORDER if rec.get(key) == name]


CHIP_CLASS = {"ausgewogen": "chip-bal", "proteinreich": "chip-pro", "vegetarisch": "chip-veg"}


def render_page(plan, meta):
    title = meta.get("title") or DEFAULT_TITLE
    kw, span = _week_info(plan)
    source = meta.get("source") or ""

    days_html = []
    for day in plan:
        rec = day["recommendations"]
        rows = []
        for d in day["dishes"]:
            p = d["portion"]
            roles = _dish_roles(rec, d["name"])
            if len(roles) > 1:
                chips = f'<span class="chip chip-multi">{" / ".join(roles)}</span>'
            elif roles:
                chips = f'<span class="chip {CHIP_CLASS[roles[0]]}">{roles[0]}</span>'
            else:
                chips = ""
            est = "*" if d["weight_estimated"] else ""
            rows.append(f"""
        <tr>
          <td class="dish"><span class="station">{html.escape(d['station'])}</span>
              <strong>{html.escape(_dish_name(d))}</strong>{chips}</td>
          <td class="num" data-l="Portion">{_fmt(d['weight_g'])}{est} g</td>
          <td class="num strong" data-l="kcal">{_fmt(p['kcal'])}</td>
          <td class="num" data-l="Fett">{_fmt(p.get('fat'), ' g')}</td>
          <td class="num dim" data-l="ges. FS">{_fmt(p.get('satfat'), ' g')}</td>
          <td class="num" data-l="KH">{_fmt(p.get('carbs'), ' g')}</td>
          <td class="num dim" data-l="Zucker">{_fmt(p.get('sugar'), ' g')}</td>
          <td class="num strong" data-l="Eiweiß">{_fmt(p.get('protein'), ' g')}</td>
          <td class="num dim" data-l="Salz">{_fmt(p.get('salt'), ' g')}</td>
          <td class="num price" data-l="extern">{_euro(d['price_extern'])}{'*' if d['price_extern_estimated'] else ''}</td>
        </tr>""")

        menu_block = f"""
    <div class="block">
      <h3 class="block-title">Menü <span class="count">{len(day['dishes'])} Gerichte</span></h3>
      <div class="table-wrap">
      <table>
        <thead><tr><th>Gericht</th><th>Portion</th><th>kcal</th><th>Fett</th><th>ges. FS</th>
        <th>KH</th><th>Zucker</th><th>Eiweiß</th><th>Salz</th><th>extern</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      </div>
    </div>""" if rows else """
    <div class="block"><h3 class="block-title">Menü</h3>
      <p class="empty">Für diesen Tag liegen keine Gerichte vor.</p></div>"""

        recs = _grouped_recs(rec)
        rec_block = f"""
    <div class="block">
      <h3 class="block-title">Empfehlung</h3>
      <div class="recs">{''.join(
            f'<div class="rec"><span class="rec-label">{labels}</span>'
            f'<span class="rec-name">{html.escape(name)}</span></div>'
            for labels, name in recs)}</div>
    </div>""" if recs else ""

        combos = day["combos"]
        combo_block = f"""
    <div class="block">
      <h3 class="block-title">kcal-Vorschläge</h3>
      <div class="combos">{''.join(f'''
        <div class="combo"><span class="combo-target">~{t} kcal{"†" if c.get("approx") else ""}</span>
          <span class="combo-items">{html.escape(" + ".join(c["items"]))}</span>
          <span class="combo-facts">{c["kcal"]} kcal · {_fmt(c["protein"])} g Eiweiß · {_euro(c["price_extern"])}</span></div>'''
            for t, c in combos.items())}</div>
    </div>""" if combos else ""

        days_html.append(f"""
  <section class="day">
    <header class="day-head">
      <h2>{day['weekday']}</h2><span class="date">{day['date']}</span>
    </header>{menu_block}{rec_block}{combo_block}
  </section>""")

    footer_source = (
        f'<p class="src">Quelle: <a href="{html.escape(source)}" rel="noreferrer noopener">'
        f'{html.escape(_host(source))}</a> – dort sind die Angaben im Original abrufbar.</p>'
        if source else "")

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · {kw}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --leaf:#5a8f27; --leaf-dk:#33531a; --ink:#20241c; --mut:#71766a; --line:#e6e8e0;
  --bal:#e7f0da; --bal-ink:#33531a; --pro:#fde8d7; --pro-ink:#8a4b12;
  --veg:#ddeee4; --veg-ink:#1f5c3c; --bg:#f6f7f2; --card:#ffffff; --zebra:#fafbf7;
  --shadow:0 1px 2px rgba(32,36,28,.05), 0 8px 24px -12px rgba(32,36,28,.12);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --leaf:#8fc45a; --leaf-dk:#a9d47c; --ink:#e6e8e0; --mut:#9aa090; --line:#3a3f35;
    --bal:#33531a; --bal-ink:#cde3b0; --pro:#5c3413; --pro-ink:#f5c9a2;
    --veg:#1f4632; --veg-ink:#b9dcc8; --bg:#181b16; --card:#22261f; --zebra:#262a22;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.5);
  }}
}}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.55 Inter,system-ui,sans-serif; padding:0 20px 72px }}
a {{ color:var(--leaf-dk) }}
/* Kopfzeile */
header.page {{ max-width:1120px; margin:0 auto; padding:48px 0 4px }}
.eyebrow {{ color:var(--leaf); font-size:11px; font-weight:700; text-transform:uppercase;
           letter-spacing:.14em; margin-bottom:8px }}
h1 {{ font-family:Fraunces,serif; font-size:clamp(28px,5vw,44px); margin:0;
     letter-spacing:-.01em; line-height:1.1 }}
.week {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:8px 12px; margin-top:12px }}
.week .kw {{ font-family:Fraunces,serif; font-weight:700; font-size:19px; color:var(--leaf-dk) }}
.week .span {{ color:var(--mut); font-size:14px; font-weight:500 }}
.meta {{ color:var(--mut); font-size:12.5px; margin-top:10px; max-width:72ch }}
/* Tageskarte */
.day {{ max-width:1120px; margin:28px auto 0; background:var(--card);
        border:1px solid var(--line); border-radius:18px; padding:20px 24px 20px;
        box-shadow:var(--shadow) }}
.day-head {{ display:flex; align-items:baseline; gap:12px;
            padding-bottom:12px; border-bottom:2px solid var(--line) }}
h2 {{ font-family:Fraunces,serif; margin:0; font-size:25px; letter-spacing:-.01em }}
.date {{ color:var(--mut); font-size:13px; font-weight:500; border:1px solid var(--line);
        border-radius:99px; padding:2px 10px }}
.block {{ margin-top:16px }}
.block-title {{ margin:0 0 8px; font-size:10.5px; font-weight:700; text-transform:uppercase;
               letter-spacing:.1em; color:var(--mut) }}
.block-title .count {{ font-weight:500; letter-spacing:.04em; text-transform:none;
                      opacity:.75; margin-left:6px }}
.empty {{ margin:0; color:var(--mut); font-size:13.5px; font-style:italic }}
/* Menü-Tabelle */
.table-wrap {{ overflow-x:auto; margin:0 -8px; padding:0 8px }}
table {{ border-collapse:collapse; width:100%; min-width:880px }}
th {{ text-align:right; font-size:10.5px; font-weight:700; text-transform:uppercase;
     letter-spacing:.08em; color:var(--mut); padding:0 9px 7px;
     border-bottom:1px solid var(--line) }}
th:first-child {{ text-align:left }}
td {{ padding:10px 9px; border-bottom:1px solid var(--line); vertical-align:middle }}
tbody tr:nth-child(even) {{ background:var(--zebra) }}
tbody tr:last-child td {{ border-bottom:none }}
tbody tr:hover {{ background:color-mix(in srgb, var(--bal) 45%, transparent) }}
td.dish {{ min-width:300px }}
.station {{ display:block; color:var(--mut); font-size:11.5px; margin-bottom:1px }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap }}
.strong {{ font-weight:650 }}
.dim {{ color:var(--mut) }}
.price {{ color:var(--leaf-dk); font-weight:650 }}
.chip {{ display:inline-block; font-size:10.5px; font-weight:700; border-radius:99px;
        padding:2.5px 10px; margin-left:8px; vertical-align:2px; letter-spacing:.02em }}
.chip-bal {{ background:var(--bal); color:var(--bal-ink) }}
.chip-pro {{ background:var(--pro); color:var(--pro-ink) }}
.chip-veg {{ background:var(--veg); color:var(--veg-ink) }}
.chip-multi {{ background:linear-gradient(100deg,var(--bal),var(--veg)); color:var(--bal-ink) }}
/* Empfehlungen */
.recs {{ display:flex; flex-direction:column; gap:7px }}
.rec {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:2px 10px; font-size:14px;
       background:color-mix(in srgb, var(--bal) 55%, transparent);
       border-radius:10px; padding:9px 12px }}
.rec-label {{ color:var(--bal-ink); font-weight:700; font-size:10.5px;
             text-transform:uppercase; letter-spacing:.08em }}
.rec-name {{ font-weight:600; flex:1; min-width:min(100%, 24ch) }}
/* kcal-Vorschläge */
.combos {{ display:grid; gap:8px }}
.combo {{ background:var(--bg); border:1px dashed var(--line); border-radius:12px;
         padding:10px 14px; display:flex; flex-wrap:wrap; gap:4px 16px; align-items:baseline }}
.combo-target {{ font-family:Fraunces,serif; font-weight:700; color:var(--leaf-dk); font-size:17px }}
.combo-items {{ flex:1; min-width:220px }}
.combo-facts {{ color:var(--mut); font-size:12.5px; white-space:nowrap }}
/* Fußzeile */
footer {{ max-width:1120px; margin:36px auto 0; padding-top:18px;
         border-top:1px solid var(--line); color:var(--mut); font-size:12px; line-height:1.65 }}
footer p {{ margin:0 0 6px }}
footer .src {{ font-size:12.5px }}
/* Schmale Screens: Tabellenzeilen werden zu Gericht-Karten */
@media (max-width: 760px) {{
  body {{ padding:0 12px 56px }}
  .day {{ padding:18px 16px 16px; border-radius:14px }}
  .table-wrap {{ overflow:visible; margin:0; padding:0 }}
  table {{ min-width:0 }}
  thead {{ display:none }}
  tbody tr {{ display:flex; flex-wrap:wrap; gap:3px 14px; padding:10px 8px;
             border-bottom:1px solid var(--line); border-radius:10px }}
  tbody tr:last-child {{ border-bottom:none }}
  tbody tr td {{ display:block; border:none; padding:0 }}
  td.dish {{ flex:1 1 100%; min-width:0; margin-bottom:3px }}
  td.num {{ display:inline-flex; align-items:baseline; gap:5px; font-size:13px }}
  td.num::before {{ content:attr(data-l); color:var(--mut); font-size:9.5px;
                   font-weight:700; text-transform:uppercase; letter-spacing:.06em }}
  .combo-facts {{ white-space:normal }}
}}
</style></head><body>
<header class="page">
  <div class="eyebrow">Kantinenplan</div>
  <h1>{html.escape(title)}</h1>
  <div class="week"><span class="kw">{kw}</span><span class="span">{span}</span></div>
  <div class="meta">Stand {meta['generated'].replace('T', ' ')} Uhr · Nährwerte pro Portion ·
  Preise = extern (× {meta['price_factor']} wo nicht ausgewiesen) · * = geschätzt ·
  † = beste Annäherung ans kcal-Ziel</div>
</header>
{''.join(days_html)}
<footer>
  {footer_source}
  <p>Nährwerte pro Portion, berechnet aus den 100-g-Angaben der Quelle. Angaben ohne
  Gewähr; Datenfehler werden plausibilisiert (* = geschätzt).</p>
</footer>
</body></html>"""


def render_email(plan, meta):
    """Vollständige Inline-Style-Mail, gleiche Gliederung wie die Seite:
    Kopf (Bezeichnung + KW/Zeitraum) → je Tag Menü → Empfehlung → kcal-Vorschläge
    → Fußzeile mit Quelle."""
    title = meta.get("title") or DEFAULT_TITLE
    kw, span = _week_info(plan)
    source = meta.get("source") or ""
    C_MUT, C_LEAF, C_INK, C_LINE = "#6d7266", "#33531a", "#1d211a", "#e4e6df"
    lbl = (f'font-size:10px;font-weight:700;text-transform:uppercase;'
           f'letter-spacing:.09em;color:{C_MUT};margin:16px 0 6px')

    blocks = []
    for day in plan:
        rec = day["recommendations"]
        td_n = f'style="padding:5px 7px;font-size:12px;border-bottom:1px solid {C_LINE}"'
        td_r = f'style="padding:5px 7px;font-size:12px;border-bottom:1px solid {C_LINE};text-align:right;white-space:nowrap"'
        th = (f'style="padding:0 7px 4px;font-size:10px;color:{C_MUT};text-transform:uppercase;'
              f'letter-spacing:.05em;text-align:right;border-bottom:1px solid {C_LINE}"')
        rows = "".join(
            f'<tr><td {td_n}><span style="color:{C_MUT};font-size:10.5px">{html.escape(d["station"])}</span><br>'
            f'<b>{html.escape(_dish_name(d))}</b></td>'
            f'<td {td_r}>{_fmt(d["weight_g"])}{"*" if d["weight_estimated"] else ""} g</td>'
            f'<td {td_r}><b>{_fmt(d["portion"]["kcal"])}</b></td>'
            f'<td {td_r}>{_fmt(d["portion"].get("fat"))}</td>'
            f'<td {td_r}>{_fmt(d["portion"].get("carbs"))}</td>'
            f'<td {td_r}>{_fmt(d["portion"].get("sugar"))}</td>'
            f'<td {td_r}><b>{_fmt(d["portion"].get("protein"))}</b></td>'
            f'<td {td_r}><b style="color:{C_LEAF}">{_euro(d["price_extern"])}'
            f'{"*" if d["price_extern_estimated"] else ""}</b></td></tr>'
            for d in day["dishes"]
        )
        menu = (
            f'<div style="{lbl}">Menü</div>'
            f'<table cellspacing="0" cellpadding="0" style="border-collapse:collapse;width:100%">'
            f'<tr><th {th.replace("text-align:right", "text-align:left")}>Gericht</th>'
            f'<th {th}>Portion</th><th {th}>kcal</th><th {th}>Fett&nbsp;g</th><th {th}>KH&nbsp;g</th>'
            f'<th {th}>Zucker&nbsp;g</th><th {th}>Eiweiß&nbsp;g</th><th {th}>extern</th></tr>{rows}</table>'
            if rows else
            f'<div style="{lbl}">Menü</div><p style="margin:0;font-size:13px;color:{C_MUT};'
            f'font-style:italic">Für diesen Tag liegen keine Gerichte vor.</p>'
        )

        recs = _grouped_recs(rec)
        rec_html = (
            f'<div style="{lbl}">Empfehlung</div>' + "".join(
                f'<div style="margin:0 0 5px;padding:8px 12px;background:#eef4e4;border-radius:8px;font-size:13px">'
                f'<span style="color:{C_LEAF};font-size:10px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:.08em">{labels}</span><br><b>{html.escape(name)}</b></div>'
                for labels, name in recs)
        ) if recs else ""

        combo_html = (
            f'<div style="{lbl}">kcal-Vorschläge</div>' + "".join(
                f'<div style="margin:0 0 5px;padding:8px 12px;background:#f4f6ef;border-radius:8px;font-size:13px">'
                f'<b style="color:{C_LEAF}">~{t} kcal{"†" if c.get("approx") else ""}:</b> '
                f'{html.escape(" + ".join(c["items"]))} <span style="color:{C_MUT}">'
                f'({c["kcal"]} kcal · {_fmt(c["protein"])} g EW · {_euro(c["price_extern"])})</span></div>'
                for t, c in day["combos"].items())
        ) if day["combos"] else ""

        blocks.append(
            f'<h3 style="font-family:Georgia,serif;margin:28px 0 0;color:{C_INK};font-size:19px;'
            f'padding-bottom:8px;border-bottom:2px solid {C_LINE}">{day["weekday"]} '
            f'<span style="color:{C_MUT};font-size:13px;font-family:Helvetica,Arial,sans-serif">'
            f'{day["date"]}</span></h3>{menu}{rec_html}{combo_html}'
        )

    src = (f'<p style="margin:0 0 6px"><b>Quelle:</b> <a href="{html.escape(source)}" '
           f'style="color:{C_LEAF}">{html.escape(_host(source))}</a> – dort sind die Angaben '
           f'im Original abrufbar.</p>' if source else "")

    return (
        f'<div style="max-width:680px;margin:auto;font-family:Helvetica,Arial,sans-serif;color:{C_INK}">'
        f'<div style="color:{C_LEAF};font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.14em;margin-bottom:4px">Kantinenplan</div>'
        f'<h1 style="font-family:Georgia,serif;color:{C_INK};font-size:25px;margin:0">🥗 {html.escape(title)}</h1>'
        f'<p style="margin:8px 0 0"><b style="font-family:Georgia,serif;color:{C_LEAF};font-size:17px">{kw}</b>'
        f'<span style="color:{C_MUT};font-size:13px">&nbsp;&nbsp;{span}</span></p>'
        + "".join(blocks)
        + f'<div style="margin-top:28px;padding-top:14px;border-top:1px solid {C_LINE};'
        f'color:{C_MUT};font-size:11.5px;line-height:1.6">{src}'
        f'<p style="margin:0 0 6px">Stand {meta["generated"].replace("T", " ")} Uhr · Nährwerte pro '
        f'Portion · Preise extern (× Faktor wo nicht ausgewiesen) · * = geschätzt · '
        f'† = beste Annäherung ans kcal-Ziel.</p>'
        f'<p style="margin:0">Vollständige Ansicht inkl. ges. Fettsäuren &amp; Salz: '
        f'siehe angehängte HTML-Datei.</p></div></div>'
    )
