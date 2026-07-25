"""HTML-Ausgaben: GitHub-Pages-Seite + E-Mail-Body (inline-styled)."""
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


def _labels(d):
    out = []
    if "vegan" in d["labels"]:
        out.append("vegan")
    elif "vegetarisch" in d["labels"] or (d.get("_veg")):
        out.append("vegetarisch")
    if "protein" in d["labels"]:
        out.append("Protein Kick")
    return out


def render_page(plan, meta):
    days_html = []
    for day in plan:
        rec = day["recommendations"]
        rows = []
        for d in day["dishes"]:
            p = d["portion"]
            tags = []
            if d["name"] == rec.get("ausgewogen"):
                tags.append('<span class="chip chip-bal">ausgewogen</span>')
            if d["name"] == rec.get("protein"):
                tags.append('<span class="chip chip-pro">Protein</span>')
            if d["name"] == rec.get("vegetarisch"):
                tags.append('<span class="chip chip-veg">vegetarisch</span>')
            est = "*" if d["weight_estimated"] else ""
            img = f'<img class="dish-img" src="{html.escape(d["images"][0])}" alt="" loading="lazy">' if d["images"] else ""
            rows.append(f"""
      <tr>
        <td class="dish">{img}<div><span class="station">{html.escape(d['station'])}</span><br>
            <strong>{html.escape(_dish_name(d))}</strong> {' '.join(tags)}</div></td>
        <td class="num">{_fmt(d['weight_g'])}{est} g</td>
        <td class="num strong">{_fmt(p['kcal'])}</td>
        <td class="num">{_fmt(p.get('fat'), ' g')}</td>
        <td class="num">{_fmt(p.get('carbs'), ' g')}</td>
        <td class="num">{_fmt(p.get('sugar'), ' g')}</td>
        <td class="num strong">{_fmt(p.get('protein'), ' g')}</td>
        <td class="num">{_fmt(p.get('salt'), ' g')}</td>
        <td class="num price">{_euro(d['price_extern'])}{'*' if d['price_extern_estimated'] else ''}</td>
      </tr>""")

        combo_html = ""
        for target, c in day["combos"].items():
            combo_html += f"""
      <div class="combo"><span class="combo-target">~{target} kcal{"†" if c.get("approx") else ""}</span>
        <span class="combo-items">{html.escape(' + '.join(c['items']))}</span>
        <span class="combo-facts">{c['kcal']} kcal · {_fmt(c['protein'])} g Eiweiß · {_euro(c['price_extern'])}</span></div>"""

        days_html.append(f"""
  <section class="day">
    <h2>{day['weekday']} <span class="date">{day['date']}</span></h2>
    <table>
      <thead><tr><th>Gericht</th><th>Portion</th><th>kcal</th><th>Fett</th><th>KH</th>
      <th>Zucker</th><th>Eiweiß</th><th>Salz</th><th>extern</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    {f'<div class="combos">{combo_html}</div>' if combo_html else ''}
  </section>""")

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kantinen-Wochenplan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{ --leaf:#5a8f27; --leaf-dk:#33531a; --ink:#1d211a; --mut:#6d7266; --line:#e4e6df;
        --bal:#e7f0da; --pro:#fde8d7; --veg:#ddeee4; --bg:#fbfbf8; }}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.5 Inter,system-ui,sans-serif; padding:0 16px 64px }}
header {{ max-width:1080px; margin:0 auto; padding:40px 0 8px }}
h1 {{ font-family:Fraunces,serif; font-size:clamp(28px,5vw,44px); margin:0; color:var(--leaf-dk) }}
h1 em {{ font-style:normal; color:var(--leaf) }}
.meta {{ color:var(--mut); font-size:13px; margin-top:4px }}
.day {{ max-width:1080px; margin:36px auto 0; background:#fff; border:1px solid var(--line);
        border-radius:14px; padding:20px 22px; overflow-x:auto }}
h2 {{ font-family:Fraunces,serif; margin:0 0 12px; font-size:24px }}
h2 .date {{ color:var(--mut); font-size:15px; font-family:Inter,sans-serif; font-weight:500 }}
table {{ border-collapse:collapse; width:100%; min-width:760px }}
th {{ text-align:right; font-size:11px; text-transform:uppercase; letter-spacing:.06em;
     color:var(--mut); padding:6px 8px; border-bottom:2px solid var(--line) }}
th:first-child {{ text-align:left }}
td {{ padding:10px 8px; border-bottom:1px solid var(--line); vertical-align:middle }}
td.dish {{ display:flex; gap:12px; align-items:center; min-width:280px }}
.dish-img {{ width:52px; height:52px; object-fit:cover; border-radius:8px; flex:none }}
.station {{ color:var(--mut); font-size:12px }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap }}
.strong {{ font-weight:600 }}
.price {{ color:var(--leaf-dk); font-weight:600 }}
.chip {{ display:inline-block; font-size:11px; font-weight:600; border-radius:99px;
        padding:2px 9px; margin-left:4px; vertical-align:middle }}
.chip-bal {{ background:var(--bal); color:var(--leaf-dk) }}
.chip-pro {{ background:var(--pro); color:#8a4b12 }}
.chip-veg {{ background:var(--veg); color:#1f5c3c }}
.combos {{ margin-top:14px; display:grid; gap:8px }}
.combo {{ background:var(--bg); border:1px dashed var(--line); border-radius:10px;
         padding:10px 14px; display:flex; flex-wrap:wrap; gap:6px 16px; align-items:baseline }}
.combo-target {{ font-family:Fraunces,serif; font-weight:700; color:var(--leaf-dk); font-size:17px }}
.combo-items {{ flex:1; min-width:200px }}
.combo-facts {{ color:var(--mut); font-size:13px; white-space:nowrap }}
footer {{ max-width:1080px; margin:32px auto 0; color:var(--mut); font-size:12px }}
</style></head><body>
<header>
  <h1>Kantinen-<em>Wochenplan</em></h1>
  <div class="meta">Stand {meta['generated'].replace('T', ' ')} Uhr · Preise = extern
  (× {meta['price_factor']} wo nicht ausgewiesen) · * = geschätzt · † = beste Annäherung ans kcal-Ziel</div>
</header>
{''.join(days_html)}
<footer>Nährwerte pro Portion, berechnet aus den 100-g-Angaben der Kantinen-Web-App.
Angaben ohne Gewähr; Datenfehler der Quelle werden plausibilisiert (* = Schätzung).</footer>
</body></html>"""


def render_email(plan, meta):
    """Vollständige Inline-Style-Mail: Empfehlungen + Kombis + alle Gerichte
    pro Tag (damit die Mail auch ohne Pages-Seite komplett nutzbar ist)."""
    blocks = []
    for day in plan:
        rec = day["recommendations"]
        lines = "".join(
            f'<tr><td style="padding:2px 10px 2px 0;color:#6d7266;font-size:13px">{label}</td>'
            f'<td style="padding:2px 0;font-size:13px"><b>{html.escape(rec[key])}</b></td></tr>'
            for key, label in (("ausgewogen", "Ausgewogen"), ("protein", "Protein"), ("vegetarisch", "Vegetarisch"))
            if key in rec
        )
        combos = "".join(
            f'<div style="margin:6px 0;padding:8px 12px;background:#f4f6ef;border-radius:8px;font-size:13px">'
            f'<b style="color:#33531a">~{t} kcal{"†" if c.get("approx") else ""}:</b> {html.escape(" + ".join(c["items"]))}'
            f' <span style="color:#6d7266">({c["kcal"]} kcal · {c["protein"]} g EW · {c["price_extern"]:.2f} €)</span></div>'.replace(".", ",")
            for t, c in day["combos"].items()
        )
        # Alle Gerichte des Tages als kompakte Tabelle
        td_n = 'style="padding:4px 8px;font-size:12px;border-bottom:1px solid #e4e6df"'
        td_r = 'style="padding:4px 8px;font-size:12px;border-bottom:1px solid #e4e6df;text-align:right;white-space:nowrap"'
        th = 'style="padding:4px 8px;font-size:11px;color:#6d7266;text-align:right;border-bottom:2px solid #e4e6df"'
        rows = "".join(
            f'<tr><td {td_n}><span style="color:#6d7266;font-size:11px">{html.escape(d["station"])}</span><br>'
            f'<b>{html.escape(_dish_name(d))}</b></td>'
            f'<td {td_r}>{_fmt(d["weight_g"])}{"*" if d["weight_estimated"] else ""} g</td>'
            f'<td {td_r}><b>{_fmt(d["portion"]["kcal"])}</b></td>'
            f'<td {td_r}>{_fmt(d["portion"].get("protein"), " g")}</td>'
            f'<td {td_r}><b style="color:#33531a">{_euro(d["price_extern"])}{"*" if d["price_extern_estimated"] else ""}</b></td></tr>'
            for d in day["dishes"]
        )
        dishes_tbl = (
            f'<table cellspacing="0" cellpadding="0" style="border-collapse:collapse;width:100%;margin-top:8px">'
            f'<tr><th {th.replace("text-align:right","text-align:left")}>Gericht</th>'
            f'<th {th}>Portion</th><th {th}>kcal</th><th {th}>Eiweiß</th><th {th}>extern</th></tr>{rows}</table>'
            if rows else ""
        )
        blocks.append(
            f'<h3 style="font-family:Georgia,serif;margin:22px 0 6px;color:#1d211a">'
            f'{day["weekday"]} <span style="color:#6d7266;font-size:14px">{day["date"]}</span></h3>'
            f'<table cellspacing="0" cellpadding="0">{lines}</table>{combos}{dishes_tbl}'
        )
    return (
        '<div style="max-width:640px;margin:auto;font-family:Helvetica,Arial,sans-serif;color:#1d211a">'
        '<h2 style="font-family:Georgia,serif;color:#33531a">Kantinen-Wochenplan</h2>'
        + "".join(blocks)
        + f'<p style="color:#6d7266;font-size:12px;margin-top:24px">Stand {meta["generated"].replace("T", " ")} Uhr · '
        'Preise extern (× Faktor wo nicht ausgewiesen) · * = geschätzt · † = beste Annäherung ans kcal-Ziel.<br>'
        'Vollständige Ansicht: siehe angehängte HTML-Datei.</p></div>'
    )
