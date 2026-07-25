"""HTML-Ausgaben: Wochenplan-Seite (docs/index.html) + E-Mail-Body (inline)."""
import html


def _fmt(v, unit=""):
    if v is None:
        return "–"
    s = f"{v:.1f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
    return s.replace(".", ",") + unit


def _euro(v):
    return "–" if v is None else f"{v:.2f}".replace(".", ",") + " €"


def _dish_name(d):
    """Name ohne führende Station (die im Table separat gezeigt wird)."""
    name, st = d["name"], d.get("station") or ""
    if st and name.startswith(st + " "):
        name = name[len(st):].strip()
    return name


REC_ORDER = (("ausgewogen", "ausgewogen"), ("protein", "proteinreich"), ("vegetarisch", "vegetarisch"))


def _grouped_recs(rec):
    """Empfehlungen nach Gericht gruppieren: empfiehlt mehr als eine Schiene
    dasselbe Gericht, werden die Labels zusammengefasst
    („ausgewogen / proteinreich: Menü 1")."""
    groups = []  # [(labels, gerichtname)] in Erst-Nennungs-Reihenfolge
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
        <td class="num">{_fmt(d['weight_g'])}{est} g</td>
        <td class="num strong">{_fmt(p['kcal'])}</td>
        <td class="num">{_fmt(p.get('fat'), ' g')}</td>
        <td class="num dim">{_fmt(p.get('satfat'), ' g')}</td>
        <td class="num">{_fmt(p.get('carbs'), ' g')}</td>
        <td class="num dim">{_fmt(p.get('sugar'), ' g')}</td>
        <td class="num strong">{_fmt(p.get('protein'), ' g')}</td>
        <td class="num dim">{_fmt(p.get('salt'), ' g')}</td>
        <td class="num price">{_euro(d['price_extern'])}{'*' if d['price_extern_estimated'] else ''}</td>
      </tr>""")

        rec_html = "".join(
            f'<div class="rec"><span class="rec-label">{labels}</span>'
            f'<span class="rec-name">{html.escape(name)}</span></div>'
            for labels, name in _grouped_recs(rec)
        )

        combo_html = "".join(f"""
      <div class="combo"><span class="combo-target">~{t} kcal{"†" if c.get("approx") else ""}</span>
        <span class="combo-items">{html.escape(' + '.join(c['items']))}</span>
        <span class="combo-facts">{c['kcal']} kcal · {_fmt(c['protein'])} g Eiweiß · {_euro(c['price_extern'])}</span></div>"""
            for t, c in day["combos"].items())

        days_html.append(f"""
  <section class="day">
    <header class="day-head">
      <h2>{day['weekday']}</h2><span class="date">{day['date']}</span>
    </header>
    {f'<div class="recs">{rec_html}</div>' if rec_html else ''}
    <div class="table-wrap">
    <table>
      <thead><tr><th>Gericht</th><th>Portion</th><th>kcal</th><th>Fett</th><th>ges. FS</th>
      <th>KH</th><th>Zucker</th><th>Eiweiß</th><th>Salz</th><th>extern</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    </div>
    {f'<div class="combos">{combo_html}</div>' if combo_html else ''}
  </section>""")

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kantinen-Wochenplan</title>
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
html {{ scroll-behavior:smooth }}
body {{ margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.55 Inter,system-ui,sans-serif; padding:0 20px 72px }}
header.page {{ max-width:1120px; margin:0 auto; padding:48px 0 6px }}
h1 {{ font-family:Fraunces,serif; font-size:clamp(30px,5vw,46px); margin:0;
     letter-spacing:-.01em; color:var(--ink) }}
h1 em {{ font-style:normal; color:var(--leaf) }}
.meta {{ color:var(--mut); font-size:13px; margin-top:8px; max-width:70ch }}
.day {{ max-width:1120px; margin:32px auto 0; background:var(--card);
        border:1px solid var(--line); border-radius:18px; padding:22px 24px 18px;
        box-shadow:var(--shadow) }}
.day-head {{ display:flex; align-items:baseline; gap:12px; margin-bottom:14px }}
h2 {{ font-family:Fraunces,serif; margin:0; font-size:26px; letter-spacing:-.01em }}
.date {{ color:var(--mut); font-size:13px; font-weight:500; border:1px solid var(--line);
        border-radius:99px; padding:2px 10px }}
.recs {{ display:flex; flex-wrap:wrap; gap:8px 18px; margin:0 0 14px }}
.rec {{ display:flex; align-items:baseline; gap:8px; font-size:13.5px }}
.rec-label {{ color:var(--leaf-dk); font-weight:700; font-size:11px;
             text-transform:uppercase; letter-spacing:.07em; white-space:nowrap }}
.rec-name {{ font-weight:600 }}
.table-wrap {{ overflow-x:auto; margin:0 -8px; padding:0 8px }}
table {{ border-collapse:collapse; width:100%; min-width:880px }}
th {{ text-align:right; font-size:10.5px; font-weight:700; text-transform:uppercase;
     letter-spacing:.08em; color:var(--mut); padding:7px 9px;
     border-bottom:2px solid var(--line) }}
th:first-child {{ text-align:left }}
td {{ padding:10px 9px; border-bottom:1px solid var(--line); vertical-align:middle }}
tbody tr:nth-child(even) td {{ background:var(--zebra) }}
tbody tr:last-child td {{ border-bottom:none }}
tbody tr:hover td {{ background:color-mix(in srgb, var(--bal) 45%, transparent) }}
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
.combos {{ margin-top:14px; display:grid; gap:8px }}
.combo {{ background:var(--bg); border:1px dashed var(--line); border-radius:12px;
         padding:10px 14px; display:flex; flex-wrap:wrap; gap:4px 16px; align-items:baseline }}
.combo-target {{ font-family:Fraunces,serif; font-weight:700; color:var(--leaf-dk); font-size:17px }}
.combo-items {{ flex:1; min-width:220px }}
.combo-facts {{ color:var(--mut); font-size:12.5px; white-space:nowrap }}
footer {{ max-width:1120px; margin:36px auto 0; color:var(--mut); font-size:12px; line-height:1.6 }}
</style></head><body>
<header class="page">
  <h1>Kantinen-<em>Wochenplan</em></h1>
  <div class="meta">Stand {meta['generated'].replace('T', ' ')} Uhr · Preise = extern
  (× {meta['price_factor']} wo nicht ausgewiesen) · * = geschätzt · † = beste Annäherung ans kcal-Ziel</div>
</header>
{''.join(days_html)}
<footer>Nährwerte pro Portion, berechnet aus den 100-g-Angaben der Kantinen-Web-App.
Angaben ohne Gewähr; Datenfehler der Quelle werden plausibilisiert (* = Schätzung).</footer>
</body></html>"""


def render_email(plan, meta):
    """Vollständige Inline-Style-Mail: Empfehlungen (gruppiert) + Kombis +
    alle Gerichte mit allen Makronährstoffen."""
    blocks = []
    for day in plan:
        rec = day["recommendations"]
        lines = "".join(
            f'<tr><td style="padding:3px 12px 3px 0;color:#33531a;font-size:11px;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap">{labels}</td>'
            f'<td style="padding:3px 0;font-size:13px"><b>{html.escape(name)}</b></td></tr>'
            for labels, name in _grouped_recs(rec)
        )
        combos = "".join(
            f'<div style="margin:6px 0;padding:8px 12px;background:#f4f6ef;border-radius:8px;font-size:13px">'
            f'<b style="color:#33531a">~{t} kcal{"†" if c.get("approx") else ""}:</b> {html.escape(" + ".join(c["items"]))}'
            f' <span style="color:#6d7266">({c["kcal"]} kcal · {c["protein"]} g EW · {c["price_extern"]:.2f} €)</span></div>'.replace(".", ",")
            for t, c in day["combos"].items()
        )
        # Alle Gerichte mit allen Makronährstoffen
        td_n = 'style="padding:5px 7px;font-size:12px;border-bottom:1px solid #e4e6df"'
        td_r = 'style="padding:5px 7px;font-size:12px;border-bottom:1px solid #e4e6df;text-align:right;white-space:nowrap"'
        th = 'style="padding:4px 7px;font-size:10px;color:#6d7266;text-transform:uppercase;letter-spacing:.05em;text-align:right;border-bottom:2px solid #e4e6df"'
        rows = "".join(
            f'<tr><td {td_n}><span style="color:#6d7266;font-size:10.5px">{html.escape(d["station"])}</span><br>'
            f'<b>{html.escape(_dish_name(d))}</b></td>'
            f'<td {td_r}>{_fmt(d["weight_g"])}{"*" if d["weight_estimated"] else ""} g</td>'
            f'<td {td_r}><b>{_fmt(d["portion"]["kcal"])}</b></td>'
            f'<td {td_r}>{_fmt(d["portion"].get("fat"))}</td>'
            f'<td {td_r}>{_fmt(d["portion"].get("carbs"))}</td>'
            f'<td {td_r}>{_fmt(d["portion"].get("sugar"))}</td>'
            f'<td {td_r}><b>{_fmt(d["portion"].get("protein"))}</b></td>'
            f'<td {td_r}><b style="color:#33531a">{_euro(d["price_extern"])}{"*" if d["price_extern_estimated"] else ""}</b></td></tr>'
            for d in day["dishes"]
        )
        dishes_tbl = (
            f'<table cellspacing="0" cellpadding="0" style="border-collapse:collapse;width:100%;margin-top:8px">'
            f'<tr><th {th.replace("text-align:right", "text-align:left")}>Gericht</th>'
            f'<th {th}>Portion</th><th {th}>kcal</th><th {th}>Fett&nbsp;g</th><th {th}>KH&nbsp;g</th>'
            f'<th {th}>Zucker&nbsp;g</th><th {th}>Eiweiß&nbsp;g</th><th {th}>extern</th></tr>{rows}</table>'
            if rows else ""
        )
        blocks.append(
            f'<h3 style="font-family:Georgia,serif;margin:24px 0 6px;color:#1d211a;font-size:19px">'
            f'{day["weekday"]} <span style="color:#6d7266;font-size:13px;font-family:Helvetica,Arial,sans-serif">{day["date"]}</span></h3>'
            f'<table cellspacing="0" cellpadding="0">{lines}</table>{combos}{dishes_tbl}'
        )
    return (
        '<div style="max-width:680px;margin:auto;font-family:Helvetica,Arial,sans-serif;color:#1d211a">'
        '<h2 style="font-family:Georgia,serif;color:#33531a;font-size:24px">🥗 Kantinen-Wochenplan</h2>'
        + "".join(blocks)
        + f'<p style="color:#6d7266;font-size:11.5px;margin-top:26px;line-height:1.6">Stand {meta["generated"].replace("T", " ")} Uhr · '
        'Nährwerte pro Portion · Preise extern (× Faktor wo nicht ausgewiesen) · * = geschätzt · † = beste Annäherung ans kcal-Ziel.<br>'
        'Vollständige Ansicht inkl. ges. Fettsäuren &amp; Salz: siehe angehängte HTML-Datei.</p></div>'
    )
