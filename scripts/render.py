"""HTML-Ausgabe: statische Wochenplan-Seite (docs/index.html).

Aufbau: Kopf (Bezeichnung, KW/Zeitraum, Stand) → Wochenleiste Mo–Fr als Tabs
→ je Tag zuerst Empfehlungen und kcal-Kombis als Karten, danach die
vollständige Gerichteliste → Fußzeile (Quelle, Legende).
Ohne JavaScript stehen alle Tage untereinander; die Tabs werden erst per
Skript aktiviert (kein display:none im Grundzustand).
"""
import datetime as dt
import html

DEFAULT_TITLE = "Kantinen-Wochenplan"

# ---------------------------------------------------------------------------
# JavaScript und CSS als normale Strings (nicht im f-String), damit keine
# geschweiften Klammern verdoppelt werden müssen.
# ---------------------------------------------------------------------------

# Läuft im <head>, bevor gerendert wird: Theme aus localStorage (sonst
# Systemeinstellung) setzen, damit nichts flackert; „js"-Klasse schaltet die
# Tab-Leiste frei.
HEAD_JS = """<script>
(function () {
  var d = document.documentElement, t = null;
  d.classList.add('js');
  try { t = localStorage.getItem('theme'); } catch (e) {}
  if (t === 'dark' || (!t && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches)) d.dataset.theme = 'dark';
  else if (t === 'light') d.dataset.theme = 'light';
})();
</script>"""

# Theme-Umschalter + Tages-Tabs (Pfeiltasten, Home/End) + „Ganze Woche".
PAGE_JS = """<script>
(function () {
  var root = document.documentElement;

  // Hell/Dunkel
  var tb = document.getElementById('theme-toggle');
  if (tb) {
    var applyTheme = function (dark) {
      root.dataset.theme = dark ? 'dark' : 'light';
      tb.setAttribute('aria-pressed', dark ? 'true' : 'false');
      tb.querySelector('.t-ico').textContent = dark ? '\\u2600' : '\\u263E';
      tb.querySelector('.t-txt').textContent = dark ? 'Hell' : 'Dunkel';
      tb.title = dark ? 'Zum hellen Design wechseln' : 'Zum dunklen Design wechseln';
      try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (e) {}
    };
    applyTheme(root.dataset.theme === 'dark');
    tb.addEventListener('click', function () { applyTheme(root.dataset.theme !== 'dark'); });
  }

  // Tages-Tabs
  var tabs = [].slice.call(document.querySelectorAll('[role="tab"]'));
  var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });
  var wb = document.getElementById('week-toggle');
  if (!tabs.length || !wb) return;
  var week = false, current = 0;

  function show(i, focus, scroll) {
    current = i;
    tabs.forEach(function (t, k) {
      var on = k === i;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      panels[k].hidden = !week && !on;
    });
    if (focus) tabs[i].focus();
    if (scroll && week) panels[i].scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function setWeek(on) {
    week = on;
    root.classList.toggle('week', on);
    wb.setAttribute('aria-pressed', on ? 'true' : 'false');
    wb.querySelector('.w-txt').textContent = on ? 'Nur einen Tag zeigen' : 'Ganze Woche zeigen';
    show(current, false, false);
    try { localStorage.setItem('week', on ? '1' : '0'); } catch (e) {}
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { show(i, false, true); });
    t.addEventListener('keydown', function (e) {
      var n = null;
      if (e.key === 'ArrowRight') n = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') n = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') n = 0;
      else if (e.key === 'End') n = tabs.length - 1;
      if (n !== null) { e.preventDefault(); show(n, true, true); }
    });
  });
  wb.addEventListener('click', function () { setWeek(!week); });

  // Startzustand: Tag aus #Anker, sonst heutiger Tag, sonst erster Tag.
  var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; };
  var today = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  var start = -1;
  if (location.hash) start = panels.findIndex(function (pn) { return '#' + pn.id === location.hash; });
  if (start < 0) start = tabs.findIndex(function (t) { return t.dataset.date === today; });
  if (start < 0) start = 0;
  var w = false; try { w = localStorage.getItem('week') === '1'; } catch (e) {}
  current = start;
  setWeek(w);
})();
</script>"""

# Farb-Token: hell als Grundzustand, dunkel per Umschalter oder Systemwunsch.
DARK_TOKENS = """
  --bg:#171a15; --card:#21251e; --card-2:#282d24; --ink:#e8eae2; --mut:#a3a998;
  --line:#363b31; --line-2:#444a3e; --acc:#8fc45a; --acc-ink:#b5dc8a; --acc-soft:#2b3d1c;
  --bal:#33531a; --bal-ink:#d2e6b8; --pro:#5c3413; --pro-ink:#f7cfa8;
  --veg:#1f4632; --veg-ink:#bfe0cd;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -14px rgba(0,0,0,.6);
"""

CSS = """
:root {
  --bg:#f5f6f1; --card:#ffffff; --card-2:#f9faf5; --ink:#1f2319; --mut:#5d635a;
  --line:#e2e5dc; --line-2:#cfd3c7; --acc:#5a8f27; --acc-ink:#2f4d16; --acc-soft:#e9f1dc;
  --bal:#e4efd3; --bal-ink:#2f4d16; --pro:#fce4d0; --pro-ink:#84430c;
  --veg:#d9ece1; --veg-ink:#1a5236;
  --shadow:0 1px 2px rgba(31,35,25,.05), 0 10px 28px -14px rgba(31,35,25,.14);
  color-scheme:light;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme:dark; DARK } }
:root[data-theme="dark"] { color-scheme:dark; DARK }

* { box-sizing:border-box }
html { scroll-padding-top:12px }
@media (min-width: 761px) { .js { scroll-padding-top:118px } } /* sticky Wochenleiste */
body { margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.5 Inter,"Segoe UI",Roboto,Helvetica,Arial,system-ui,sans-serif;
       padding:0 20px 72px; -webkit-text-size-adjust:100% }
a { color:var(--acc-ink) }
h1,h2,h3,h4 { font-family:Fraunces,Georgia,"Times New Roman",serif; font-weight:700;
              letter-spacing:-.01em; margin:0 }
button { font:inherit; color:inherit }
button:focus-visible, a:focus-visible { outline:3px solid var(--acc); outline-offset:2px }
.wrap { max-width:1120px; margin:0 auto }
[hidden] { display:none !important }
.sr { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap }

/* Kopfzeile */
header.page { padding:44px 0 18px; display:flex; align-items:flex-start; gap:16px; flex-wrap:wrap }
.head-main { flex:1; min-width:min(100%, 18rem) }
.eyebrow { color:var(--acc-ink); font-size:11px; font-weight:700; text-transform:uppercase;
           letter-spacing:.14em; margin-bottom:8px }
h1 { font-size:clamp(28px,5vw,42px); line-height:1.1 }
.week { display:flex; flex-wrap:wrap; align-items:baseline; gap:6px 12px; margin-top:12px }
.week .kw { font-family:Fraunces,Georgia,serif; font-weight:700; font-size:20px; color:var(--acc-ink) }
.week .span { color:var(--mut); font-size:14px; font-weight:500 }
.stand { color:var(--mut); font-size:12.5px; margin-top:8px }
.pill-btn { flex:none; display:inline-flex; align-items:center; gap:7px; padding:8px 14px;
            font-size:12.5px; font-weight:600; background:var(--card); border:1px solid var(--line-2);
            border-radius:99px; cursor:pointer; box-shadow:var(--shadow);
            transition:border-color .15s, background .15s }
.pill-btn:hover { border-color:var(--acc) }
.pill-btn .t-ico { font-size:14px; line-height:1; color:var(--acc-ink) }
.pill-btn[aria-pressed="true"] { background:var(--acc-soft); border-color:var(--acc) }
/* Theme-Schalter braucht JavaScript, ohne JS bleibt er weg */
#theme-toggle { display:none }
.js #theme-toggle { display:inline-flex; margin-top:4px }

/* Wochenleiste (nur mit JavaScript sichtbar) */
.weekbar { display:none }
.js .weekbar { display:flex; flex-wrap:wrap; align-items:stretch; gap:10px 12px;
               position:sticky; top:0; z-index:5; padding:10px 0 12px; background:var(--bg) }
.tablist { flex:1 1 560px; display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:6px;
           padding:5px; background:var(--card); border:1px solid var(--line); border-radius:16px;
           box-shadow:var(--shadow) }
.tab { min-width:0; display:flex; flex-direction:column; align-items:flex-start; gap:2px;
       padding:9px 12px; border:1px solid transparent; border-radius:11px; background:transparent;
       cursor:pointer; text-align:left; line-height:1.3; transition:background .15s }
.tab:hover { background:var(--card-2) }
.tab[aria-selected="true"] { background:var(--acc-soft); border-color:var(--acc) }
.tab-wd { font-weight:700; font-size:14px }
.tab-date { color:var(--mut); font-size:12px; font-weight:500 }
.tab-hint { color:var(--mut); font-size:11.5px; max-width:100%; overflow:hidden;
            text-overflow:ellipsis; white-space:nowrap; margin-top:2px }
.tab[aria-selected="true"] .tab-hint, .tab[aria-selected="true"] .tab-date { color:var(--acc-ink) }
.wd-short { display:none }
#week-toggle { align-self:center }

/* Tageskarte */
.day { margin:14px 0 0; background:var(--card); border:1px solid var(--line); border-radius:18px;
       padding:20px 24px 22px; box-shadow:var(--shadow) }
.day + .day { margin-top:22px }
.day-head { display:flex; align-items:baseline; flex-wrap:wrap; gap:6px 12px; padding-bottom:12px;
            border-bottom:2px solid var(--line) }
h2 { font-size:26px }
.date { color:var(--mut); font-size:13px; font-weight:500; border:1px solid var(--line-2);
        border-radius:99px; padding:2px 10px }
.count { color:var(--mut); font-size:13px; margin-left:auto }
.block { margin-top:18px; min-width:0 }
.block-title { font-family:inherit; font-size:10.5px; font-weight:700; text-transform:uppercase;
               letter-spacing:.1em; color:var(--mut); margin:0 0 10px }
.empty { margin:0; color:var(--mut); font-size:13.5px; font-style:italic }

/* Kennzahlen (kcal, Eiweiß, Preis) */
.figs { display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:10px; font-size:12.5px; color:var(--mut) }
.fig b { font-family:Fraunces,Georgia,serif; font-weight:700; font-size:18px; color:var(--ink);
         font-variant-numeric:tabular-nums; margin-right:3px }
.fig.price b { color:var(--acc-ink) }

/* Empfehlungen */
.recs { display:grid; gap:10px; grid-template-columns:repeat(auto-fit, minmax(min(100%, 280px), 1fr)) }
.rec-card { border:1px solid var(--line); border-left:4px solid var(--acc); border-radius:12px;
            padding:12px 16px 14px; background:var(--card-2) }
.chips { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:6px }
.chip { display:inline-block; font-size:10.5px; font-weight:700; border-radius:99px;
        padding:2.5px 9px; letter-spacing:.02em; white-space:nowrap }
.chip-bal { background:var(--bal); color:var(--bal-ink) }
.chip-pro { background:var(--pro); color:var(--pro-ink) }
.chip-veg { background:var(--veg); color:var(--veg-ink) }
.rec-name { font-family:inherit; font-size:16px; font-weight:650; line-height:1.35 }
.station { display:block; color:var(--mut); font-size:11.5px; margin-top:2px }

/* kcal-Kombis */
.combos { display:grid; gap:10px; grid-template-columns:repeat(auto-fit, minmax(min(100%, 300px), 1fr)) }
.combo-card { border:1px dashed var(--line-2); border-radius:12px; padding:12px 16px 14px; background:var(--card-2) }
.combo-head { display:flex; align-items:baseline; justify-content:space-between; gap:10px; flex-wrap:wrap }
.combo-target { font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--mut) }
.combo-kcal { font-family:Fraunces,Georgia,serif; font-weight:700; font-size:24px; color:var(--acc-ink);
              font-variant-numeric:tabular-nums }
.combo-kcal small { font-size:13px; font-weight:500; color:var(--mut); font-family:Inter,system-ui,sans-serif; margin-left:3px }
.combo-items { list-style:none; margin:8px 0 0; padding:0; font-size:14px }
.combo-items li { display:flex; justify-content:space-between; gap:12px; padding:5px 0;
                  border-top:1px solid var(--line) }
.combo-items li span { color:var(--mut); font-size:12.5px; white-space:nowrap; font-variant-numeric:tabular-nums }
.combo-note { margin:8px 0 0; font-size:12px; color:var(--mut) }
.combo-card .figs { margin-top:6px }

/* Gerichteliste: Desktop = Tabelle */
.table-wrap { overflow-x:auto; margin:0 -8px; padding:0 8px }
table { border-collapse:collapse; width:100%; min-width:860px }
th { text-align:right; font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.08em;
     color:var(--mut); padding:0 9px 8px; border-bottom:1px solid var(--line); white-space:nowrap }
th:first-child { text-align:left }
th.key { color:var(--ink) }
td { padding:10px 9px; border-bottom:1px solid var(--line); vertical-align:middle }
tbody tr:last-child td { border-bottom:none }
tbody tr:hover td { background:color-mix(in srgb, var(--acc-soft) 55%, transparent) }
tr.is-rec td:first-child { box-shadow:inset 3px 0 0 var(--acc) }
td.dish { min-width:280px }
td.dish strong { font-weight:650 }
td.dish .chips { display:inline-flex; margin:0 0 0 8px; vertical-align:2px }
.num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap }
td.key { font-weight:700; font-size:15.5px }
td.key.price { color:var(--acc-ink) }
td.aux { color:var(--mut); font-size:13.5px }
td.aux:first-of-type { border-left:1px solid var(--line) }
.l { display:none }

/* Fußzeile */
footer { margin:36px 0 0; padding-top:18px; border-top:1px solid var(--line); color:var(--mut);
         font-size:12.5px; line-height:1.65 }
footer p { margin:0 0 6px }
footer dl { margin:8px 0 0; display:grid; grid-template-columns:auto 1fr; gap:2px 10px }
footer dt { font-weight:700; color:var(--ink) }
footer dd { margin:0 }

/* Schmale Screens: Tabs kompakt, Gerichte als Karten mit 3er-Kennzahlraster */
@media (max-width: 760px) {
  body { padding:0 12px 56px }
  header.page { padding-top:28px }
  .js .weekbar { position:static }
  .tablist { gap:3px; padding:4px; border-radius:13px }
  .tab { padding:8px 4px; align-items:center; border-radius:9px }
  .tab-hint { display:none }
  .wd-long { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0) }
  .wd-short { display:inline }
  .tab-date { font-size:11px }
  .day { padding:16px 14px 16px; border-radius:14px }
  h2 { font-size:23px }
  .count { margin-left:0; flex-basis:100% }
  .table-wrap { overflow:visible; margin:0; padding:0 }
  table, tbody { display:block; min-width:0 }
  thead { display:none }
  tbody tr { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:6px 8px;
             padding:12px 2px; border-bottom:1px solid var(--line) }
  tbody tr:last-child { border-bottom:none }
  tbody tr:hover td { background:transparent }
  tr.is-rec td:first-child { box-shadow:none }
  tr.is-rec { box-shadow:inset 3px 0 0 var(--acc); padding-left:10px }
  td { display:block; border:none; padding:0; text-align:left; white-space:normal }
  td.dish { grid-column:1 / -1; min-width:0; margin-bottom:2px }
  td.dish .chips { display:flex; margin:4px 0 0 }
  td.aux:first-of-type { border-left:none }
  .l { display:block; font-size:9.5px; font-weight:700; text-transform:uppercase;
       letter-spacing:.06em; color:var(--mut); line-height:1.2; margin-bottom:1px }
  td.key { font-family:Fraunces,Georgia,serif; font-size:19px; line-height:1.15;
           padding:6px 8px; background:var(--card-2); border-radius:8px }
  td.key .l { font-family:Inter,system-ui,sans-serif }
  td.aux { font-size:12.5px; padding:0 8px; color:var(--ink) }
  .fig b { font-size:17px }
}
@media print {
  body { padding:0; background:#fff }
  .weekbar, #theme-toggle { display:none !important }
  .day { box-shadow:none; break-inside:avoid }
  .day[hidden] { display:block !important }
}
""".replace("DARK", DARK_TOKENS.strip())


# ---------------------------------------------------------------------------
# Formatierung
# ---------------------------------------------------------------------------

def _fmt(v, unit=""):
    if v is None:
        return "–"
    s = f"{v:.1f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
    return s.replace(".", ",") + unit


def _euro(v):
    return "–" if v is None else f"{v:.2f}".replace(".", ",") + " €"


def _esc(v):
    return html.escape(str(v if v is not None else ""))


def _dish_name(d):
    """Name ohne führende Station (die separat gezeigt wird)."""
    name, st = d.get("name") or "", d.get("station") or ""
    if st and name.startswith(st + " "):
        name = name[len(st):].strip()
    return name


def _full_name(name, by_name):
    """Anzeige außerhalb der Tabelle: kompletter Name inkl. Station."""
    d = by_name.get(name)
    return (d.get("name") or name) if d else name


def _short(text, n=30):
    """Kürzt an einer Wortgrenze für den Mini-Hinweis in der Wochenleiste."""
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(" ,&")
    return (cut or text[:n]) + "…"


def _week_info(plan):
    """('KW 31', '27.07. – 31.07.2026') aus den Tagesdaten."""
    dates = []
    for day in plan:
        try:
            dates.append(dt.datetime.strptime(day["date"], "%d.%m.%Y").date())
        except (ValueError, KeyError, TypeError):
            continue
    if not dates:
        return "", ""
    a, b = min(dates), max(dates)
    span = a.strftime("%d.%m.") if a == b else f"{a.strftime('%d.%m.')} – {b.strftime('%d.%m.')}"
    return f"KW {a.isocalendar().week}", f"{span}{b.strftime('%Y')}"


def _iso_date(day):
    """'31.08.2026' → '2026-08-31' für den Tages-Vergleich im Browser."""
    try:
        return dt.datetime.strptime(day.get("date", ""), "%d.%m.%Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""


def _stamp(meta):
    """Zeitstempel deutsch formatiert („27.07.2026, 17:35 Uhr")."""
    raw = str(meta.get("generated", ""))
    try:
        return dt.datetime.fromisoformat(raw).strftime("%d.%m.%Y, %H:%M Uhr")
    except ValueError:  # unerwartetes Format – unverändert durchreichen
        return (raw.replace("T", " ") + " Uhr") if any(c.isdigit() for c in raw) else raw


def _host(url):
    """Anzeigename für einen Link (Host ohne Schema/www)."""
    return url.split("//")[-1].split("/")[0].removeprefix("www.") or url


REC_ORDER = (("ausgewogen", "ausgewogen"), ("protein", "proteinreich"), ("vegetarisch", "vegetarisch"))
CHIP_CLASS = {"ausgewogen": "chip-bal", "proteinreich": "chip-pro", "vegetarisch": "chip-veg"}


def _grouped_recs(rec):
    """Empfehlungen nach Gericht gruppieren: empfiehlt mehr als eine Schiene
    dasselbe Gericht, werden die Labels zusammengefasst
    (['ausgewogen', 'proteinreich'], 'Menü 1')."""
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
    return groups


def _dish_roles(rec, name):
    return [label for key, label in REC_ORDER if rec.get(key) == name]


def _chips(labels):
    return ('<span class="chips">'
            + "".join(f'<span class="chip {CHIP_CLASS[l]}">{l}</span>' for l in labels)
            + "</span>") if labels else ""


def _figs(d):
    """Die drei Schlüsselwerte eines Gerichts: kcal, Eiweiß, Preis extern."""
    if not d:
        return ""
    p = d.get("portion") or {}
    est = "*" if d.get("price_extern_estimated") and d.get("price_extern") is not None else ""
    return (f'<div class="figs"><span class="fig"><b>{_fmt(p.get("kcal"))}</b>kcal</span>'
            f'<span class="fig"><b>{_fmt(p.get("protein"), " g")}</b>Eiweiß</span>'
            f'<span class="fig price"><b>{_euro(d.get("price_extern"))}{est}</b>extern</span></div>')


# ---------------------------------------------------------------------------
# Bausteine je Tag
# ---------------------------------------------------------------------------

def _rec_block(rec, by_name):
    groups = _grouped_recs(rec)
    if not groups:
        body = '<p class="empty">Für diesen Tag gibt es keine Empfehlung.</p>'
    else:
        cards = []
        for labels, name in groups:
            d = by_name.get(name)
            shown = _full_name(name, by_name)
            st = (d or {}).get("station") or ""
            station = f'<span class="station">{_esc(st)}</span>' if st and not shown.startswith(st) else ""
            cards.append(f'<article class="rec-card">{_chips(labels)}'
                         f'<h4 class="rec-name">{_esc(shown)}</h4>{station}{_figs(d)}</article>')
        body = f'<div class="recs">{"".join(cards)}</div>'
    return f'<div class="block"><h3 class="block-title">Empfehlung des Tages</h3>{body}</div>'


def _combo_block(combos, by_name):
    def order(item):
        try:
            return (0, int(item[0]))
        except (TypeError, ValueError):
            return (1, str(item[0]))

    cards = []
    for target, c in sorted((combos or {}).items(), key=order):
        approx = bool(c.get("approx"))
        items = []
        for name in c.get("items") or []:
            d = by_name.get(name)
            kcal = _fmt(d["portion"].get("kcal")) + " kcal" if d and d.get("portion") else ""
            items.append(f'<li>{_esc(_full_name(name, by_name))}<span>{kcal}</span></li>')
        note = ('<p class="combo-note">† Ziel nicht exakt erreichbar, beste Annäherung</p>'
                if approx else "")
        cards.append(
            f'<article class="combo-card"><div class="combo-head">'
            f'<span class="combo-target">Ziel {_esc(target)} kcal</span>'
            f'<span class="combo-kcal">{_fmt(c.get("kcal"))}{"†" if approx else ""}<small>kcal</small></span></div>'
            f'<ol class="combo-items">{"".join(items)}</ol>'
            f'<div class="figs"><span class="fig"><b>{_fmt(c.get("protein"), " g")}</b>Eiweiß</span>'
            f'<span class="fig price"><b>{_euro(c.get("price_extern"))}</b>extern</span></div>'
            f'{note}</article>')
    body = (f'<div class="combos">{"".join(cards)}</div>' if cards
            else '<p class="empty">Für diesen Tag gibt es keine kcal-Kombis.</p>')
    return f'<div class="block"><h3 class="block-title">kcal-Kombis</h3>{body}</div>'


def _dish_row(d, rec):
    p = d.get("portion") or {}
    roles = _dish_roles(rec, d.get("name"))
    w = d.get("weight_g")
    weight = "–" if w is None else _fmt(w) + ("*" if d.get("weight_estimated") else "") + " g"
    price = _euro(d.get("price_extern"))
    if d.get("price_extern_estimated") and d.get("price_extern") is not None:
        price += "*"

    def key(label, val, extra=""):
        return f'<td class="num key{extra}"><span class="l">{label}</span>{val}</td>'

    def aux(label, val):
        return f'<td class="num aux"><span class="l">{label}</span>{val}</td>'

    return (f'<tr{" class=is-rec" if roles else ""}>'
            f'<td class="dish"><span class="station">{_esc(d.get("station"))}</span>'
            f'<strong>{_esc(_dish_name(d))}</strong>{_chips(roles)}</td>'
            + key("kcal", _fmt(p.get("kcal")))
            + key("Eiweiß", _fmt(p.get("protein"), " g"))
            + key("Preis extern", price, " price")
            + aux("Portion", weight)
            + aux("Fett", _fmt(p.get("fat"), " g"))
            + aux("ges. FS", _fmt(p.get("satfat"), " g"))
            + aux("KH", _fmt(p.get("carbs"), " g"))
            + aux("Zucker", _fmt(p.get("sugar"), " g"))
            + aux("Salz", _fmt(p.get("salt"), " g"))
            + "</tr>")


def _menu_block(dishes, rec):
    if not dishes:
        return ('<div class="block"><h3 class="block-title">Alle Gerichte</h3>'
                '<p class="empty">Für diesen Tag liegen keine Gerichte vor.</p></div>')
    rows = "".join(_dish_row(d, rec) for d in dishes)
    return (f'<div class="block"><h3 class="block-title">Alle Gerichte</h3>'
            f'<div class="table-wrap"><table>'
            f'<thead><tr><th>Gericht</th><th class="key">kcal</th><th class="key">Eiweiß</th>'
            f'<th class="key">Preis extern</th><th>Portion</th><th>Fett</th><th>ges. FS</th>'
            f'<th>KH</th><th>Zucker</th><th>Salz</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></div>')


def _tab_hint(day, by_name):
    """Kurzer Hinweis im Tab: ausgewogene Empfehlung, sonst Anzahl Gerichte."""
    name = (day.get("recommendations") or {}).get("ausgewogen")
    if name:
        return _short(_full_name(name, by_name))
    n = len(day.get("dishes") or [])
    return f"{n} Gericht{'e' if n != 1 else ''}" if n else "keine Gerichte"


# ---------------------------------------------------------------------------
# Seite
# ---------------------------------------------------------------------------

def render_page(plan, meta):
    title = meta.get("title") or DEFAULT_TITLE
    kw, span = _week_info(plan)
    source = meta.get("source") or ""
    factor = _fmt(meta.get("price_factor"))

    tabs, panels = [], []
    for i, day in enumerate(plan, 1):
        dishes = day.get("dishes") or []
        rec = day.get("recommendations") or {}
        by_name = {d["name"]: d for d in dishes if d.get("name")}
        weekday = str(day.get("weekday") or f"Tag {i}")
        n = len(dishes)
        count = f"{n} Gericht{'e' if n != 1 else ''}"
        date_short = str(day.get("date") or "")[:6]

        tabs.append(
            f'<button class="tab" role="tab" type="button" id="tab-{i}" aria-controls="tag-{i}" '
            f'aria-selected="false" tabindex="-1" data-date="{_iso_date(day)}">'
            f'<span class="tab-wd"><span class="wd-long">{_esc(weekday)}</span>'
            f'<span class="wd-short" aria-hidden="true">{_esc(weekday[:2])}</span></span>'
            f'<span class="tab-date">{_esc(date_short)}</span>'
            f'<span class="tab-hint">{_esc(_tab_hint(day, by_name))}</span></button>')

        panels.append(
            f'<section class="day" id="tag-{i}" role="tabpanel" aria-labelledby="tab-{i}">'
            f'<header class="day-head"><h2>{_esc(weekday)}</h2>'
            f'<span class="date">{_esc(day.get("date"))}</span><span class="count">{count}</span></header>'
            f'{_rec_block(rec, by_name)}{_combo_block(day.get("combos"), by_name)}'
            f'{_menu_block(dishes, rec)}</section>')

    weekbar = (
        f'<nav class="weekbar" aria-label="Wochenübersicht">'
        f'<div class="tablist" role="tablist" aria-label="Wochentage">{"".join(tabs)}</div>'
        f'<button id="week-toggle" class="pill-btn" type="button" aria-pressed="false">'
        f'<span class="t-ico" aria-hidden="true">≡</span><span class="w-txt">Ganze Woche zeigen</span></button>'
        f'</nav>') if tabs else ""

    days = "".join(panels) if panels else \
        '<section class="day"><p class="empty">Es liegt kein Wochenplan vor.</p></section>'

    footer_source = (
        f'<p class="src">Quelle: <a href="{_esc(source)}" rel="noreferrer noopener">'
        f'{_esc(_host(source))}</a>. Dort sind die Angaben im Original abrufbar.</p>'
        if source else "")

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{_esc(title)}{" · " + kw if kw else ""}</title>
{HEAD_JS}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="wrap">
<header class="page">
  <div class="head-main">
    <div class="eyebrow">Kantinenplan</div>
    <h1>{_esc(title)}</h1>
    <div class="week"><span class="kw">{kw}</span><span class="span">{span}</span></div>
    <div class="stand">Stand {_esc(_stamp(meta))} · Nährwerte pro Portion · Preise extern</div>
  </div>
  <button id="theme-toggle" class="pill-btn" type="button" aria-pressed="false"
          title="Zum dunklen Design wechseln"><span class="t-ico" aria-hidden="true">☾</span><span class="t-txt">Dunkel</span></button>
</header>
{weekbar}
<main>
{days}
</main>
<footer>
  {footer_source}
  <p>Nährwerte pro Portion, berechnet aus den 100-g-Angaben der Quelle. Alle Angaben ohne
  Gewähr; offensichtliche Datenfehler werden plausibilisiert.</p>
  <dl>
    <dt>*</dt><dd>geschätzt: Portionsgewicht ohne Angabe bzw. externer Preis aus internem Preis × {factor}</dd>
    <dt>†</dt><dd>kcal-Ziel nicht exakt erreichbar, gezeigt wird die beste Annäherung</dd>
  </dl>
</footer>
</div>
{PAGE_JS}
</body></html>"""
