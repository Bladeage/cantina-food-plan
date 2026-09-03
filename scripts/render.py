"""HTML-Ausgabe: statische Wochenplan-Seite (docs/index.html).

Aufbau: dunkle Kopfzeile (Bezeichnung, KW/Zeitraum, Stand) → Wochenleiste
Mo–Fr als Tabs → je Tag zuerst Empfehlungen und kcal-Kombis als Karten,
danach die vollständige Gerichteliste → Quellenblock → Fußzeile.
Ohne JavaScript stehen alle Tage untereinander; die Tabs werden erst per
Skript aktiviert (kein display:none im Grundzustand).

Gestaltung nach dem Haus-Design der Wissens-Seiten: gemeinsamer Token-Satz,
nur Systemschriften, alles inline, Druckansicht, abgesicherter
Einblend-Effekt, sichtbarer Tastaturfokus, kein Dunkelmodus.
"""
import datetime as dt
import html

DEFAULT_TITLE = "Kantinen-Wochenplan"

# ---------------------------------------------------------------------------
# JavaScript und CSS als normale Strings (nicht im f-String), damit keine
# geschweiften Klammern verdoppelt werden müssen.
# ---------------------------------------------------------------------------

# Läuft im <head>: Die Klasse „js" schaltet Wochenleiste und Einblend-Effekt
# frei. Ohne JavaScript bleibt beides aus, und alle Tage stehen untereinander.
HEAD_JS = """<!-- Setzt die Klasse "js" nur, wenn JavaScript wirklich läuft. Erst dann
     dürfen Abschnitte mit .reveal unsichtbar starten. -->
<script>document.documentElement.className+=" js";</script>"""

# Tages-Tabs (Pfeiltasten, Home/End, Roving-Tabindex), Schalter „Ganze Woche"
# und Einblenden beim Scrollen.
PAGE_JS = """<script>
// --- Tages-Tabs und Schalter "Ganze Woche zeigen" ---
(function () {
  var root = document.documentElement;
  var tabs = [].slice.call(document.querySelectorAll('[role="tab"]'));
  var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });
  var wb = document.getElementById('week-toggle');
  if (!tabs.length || !wb) { return; }
  var week = false, current = 0;

  function show(i, focus, scroll) {
    current = i;
    tabs.forEach(function (t, k) {
      var on = k === i;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      panels[k].hidden = !week && !on;
    });
    if (focus) { tabs[i].focus(); }
    if (scroll && week) { panels[i].scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  }
  function setWeek(on) {
    week = on;
    root.classList.toggle('week', on);
    wb.setAttribute('aria-pressed', on ? 'true' : 'false');
    wb.querySelector('.w-txt').textContent = on ? 'Nur einen Tag zeigen' : 'Ganze Woche zeigen';
    show(current, false, false);
    // Merker ist eine Bequemlichkeit: unter file:// kann localStorage fehlen.
    try { localStorage.setItem('week', on ? '1' : '0'); } catch (e) {}
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { show(i, false, true); });
    t.addEventListener('keydown', function (e) {
      var n = null;
      if (e.key === 'ArrowRight') { n = (i + 1) % tabs.length; }
      else if (e.key === 'ArrowLeft') { n = (i - 1 + tabs.length) % tabs.length; }
      else if (e.key === 'Home') { n = 0; }
      else if (e.key === 'End') { n = tabs.length - 1; }
      if (n !== null) { e.preventDefault(); show(n, true, true); }
    });
  });
  wb.addEventListener('click', function () { setWeek(!week); });

  // Startzustand: Tag aus #Anker, sonst heutiger Tag, sonst erster Tag.
  var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; };
  var today = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  var start = -1;
  if (location.hash) { start = panels.findIndex(function (pn) { return '#' + pn.id === location.hash; }); }
  if (start < 0) { start = tabs.findIndex(function (t) { return t.dataset.date === today; }); }
  if (start < 0) { start = 0; }
  var w = false;
  try { w = localStorage.getItem('week') === '1'; } catch (e) {}
  current = start;
  setWeek(w);
})();

// --- Abschnitte beim Scrollen einblenden ---
// Ausgeblendete Tagesabschnitte melden sich, sobald ein Tab sie einblendet.
(function () {
  var ziele = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(ziele, function (el) { el.classList.add('sichtbar'); });
    return;
  }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('sichtbar'); io.unobserve(e.target); }
    });
  }, { threshold: 0.08 });
  Array.prototype.forEach.call(ziele, function (el) { io.observe(el); });
})();
</script>"""

CSS = """
:root{
  /* Flaechen */
  --paper:#F1F3F0;        /* Seitengrund */
  --paper-2:#E7EAE5;      /* Sektionswechsel */
  --panel:#FFFFFF;        /* Karten */
  /* Schrift und Linien */
  --ink:#0F1C2B;          /* Fliesstext */
  --ink-soft:#425060;     /* Sekundaertext */
  --muted:#5B6773;        /* Beschriftungen */
  --line:#C9CFCA;
  --line-strong:#9AA294;
  /* Leitfarben */
  --nato:#0B4F9E;         /* Primaer, Links, Akzent */
  --nato-deep:#093A73;    /* Kopfzeile, Hover */
  --nato-soft:#E4ECF6;    /* Flaeche hinter Primaerakzent */
  --amber:#D98E04;        /* Hinweis, Fokusring */
  --amber-soft:#F7EBD2;
  --olive:#5F6B52;
  --teal:#0E7C7B;
  --brown:#8A5A2B;
  --red:#A8252E;
  --red-soft:#F3DEDF;
  --ok:#2E7D32;
  --ok-soft:#DDEBDE;
  --link:#0B4F9E;
  /* Schriften - auf Windows 11 vorhanden, nichts wird nachgeladen */
  --font-display:'Arial Narrow','Helvetica Neue Condensed',Arial,sans-serif;
  --font-body:Arial,'Segoe UI',system-ui,sans-serif;
  --font-mono:Consolas,'Courier New',monospace;
  /* Raster */
  --breite:900px;
  --radius:6px;
}
/* Seiteneigene Kennfarben, aus der Palette oben abgeleitet */
:root{
  --f-ausgewogen:var(--ok);       /* Empfehlungsschiene ausgewogen */
  --f-protein:var(--brown);       /* Empfehlungsschiene viel Protein */
  --f-vegetarisch:var(--olive);   /* Empfehlungsschiene vegetarisch */
}

/* ---------- Basis ---------- */
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
html.js{scroll-padding-top:64px} /* Platz fuer die klebende Wochenleiste */
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *{transition:none!important;animation:none!important}
}
body{background:var(--paper);color:var(--ink);
     font-family:var(--font-body);font-size:16px;line-height:1.6;
     -webkit-text-size-adjust:100%}
.wrap{max-width:var(--breite);margin:0 auto;padding:0 20px}
h1,h2,h3,h4,.disp{font-family:var(--font-display);text-transform:uppercase;
     letter-spacing:.03em;line-height:1.08}
code,.mono,kbd{font-family:var(--font-mono)}
a{color:var(--link)}
a:hover{color:var(--nato-deep)}
button{font:inherit;color:inherit;cursor:pointer}
[hidden]{display:none!important}
/* Tastaturfokus - gilt fuer ALLE bedienbaren Elemente */
:focus-visible{outline:3px solid var(--amber);outline-offset:2px}

/* ---------- Kopfzeile ---------- */
header.kopf{background:var(--ink);color:#EAF0F6;padding:48px 0 38px;
       position:relative;overflow:hidden}
header.kopf::before{content:"";position:absolute;inset:0;
  background-image:linear-gradient(#ffffff10 1px,transparent 1px),
                   linear-gradient(90deg,#ffffff10 1px,transparent 1px);
  background-size:44px 44px}
header.kopf .wrap{position:relative}
.eyebrow{font-family:var(--font-mono);font-size:12px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--amber);margin-bottom:14px}
h1{font-size:clamp(32px,5.5vw,54px);font-weight:700;color:#fff;overflow-wrap:anywhere}
.sub{max-width:620px;margin-top:14px;font-size:16.5px;color:#C4CFDA}
.hero-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}
.hero-tags span{font-family:var(--font-mono);font-size:12px;
  border:1px solid #ffffff35;padding:5px 10px;border-radius:3px;color:#DCE5EE}

/* ---------- Wochenleiste (nur mit JavaScript sichtbar) ---------- */
nav.weekbar{display:none}
.js nav.weekbar{display:block;position:sticky;top:0;z-index:50;background:var(--paper);
  border-bottom:1px solid var(--line)}
.navin{max-width:var(--breite);margin:0 auto;padding:10px 20px;
  display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.brand{font-family:var(--font-display);text-transform:uppercase;letter-spacing:.03em;
  font-weight:700;font-size:15px;white-space:nowrap;margin-right:6px}
.brand small{font-family:var(--font-mono);text-transform:none;letter-spacing:0;
  font-weight:400;color:var(--muted);font-size:12px}
.tablist{display:flex;flex-wrap:wrap;gap:6px}
.chip{white-space:nowrap;font-size:13px;color:var(--ink);text-decoration:none;
  background:var(--paper-2);border:1px solid var(--line);border-radius:14px;
  padding:4px 11px;line-height:1.4}
.chip:hover{background:var(--nato-soft);border-color:var(--nato);color:var(--nato-deep)}
.chip .tab-date{font-family:var(--font-mono);font-size:11.5px;color:var(--muted);margin-left:5px}
/* Ausgewaehlter Tag: Flaeche, kein opacity */
.chip[aria-selected="true"]{background:var(--nato);border-color:var(--nato);color:#fff}
.chip[aria-selected="true"] .tab-date{color:#DCE5EE}
.wd-short{display:none}
#week-toggle{margin-left:auto}
#week-toggle::before{content:"";display:inline-block;width:9px;height:9px;margin-right:7px;
  border:1px solid var(--line-strong);border-radius:2px;vertical-align:0;background:var(--panel)}
/* Aktiver Schalter: Flaeche plus Haken */
#week-toggle[aria-pressed="true"]{background:var(--nato-soft);border-color:var(--nato);color:var(--nato-deep)}
#week-toggle[aria-pressed="true"]::before{content:"\\2713";width:auto;height:auto;border:0;background:none;
  font-size:12px;line-height:1}

/* ---------- Bauteile ---------- */
section.day{padding:40px 0 8px}
section.day+section.day{border-top:1px solid var(--line)}
.kicker{display:flex;align-items:center;gap:10px;margin-bottom:10px;
  font-family:var(--font-mono);font-size:12px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--nato)}
.kicker::before{content:"";width:26px;height:2px;background:var(--amber);flex:none}
h2{font-size:clamp(26px,4.5vw,38px);font-weight:700;margin-bottom:14px}
h3{font-size:20px;margin:30px 0 10px}
.block{margin-top:6px;min-width:0}
.empty{font-size:14.5px;color:var(--ink-soft);background:var(--paper-2);
  border:1px dashed var(--line-strong);border-radius:var(--radius);padding:10px 14px}

/* Hinweiskasten */
.note{margin-top:18px;background:var(--nato-soft);border-left:3px solid var(--nato);
  padding:12px 16px;border-radius:0 var(--radius) var(--radius) 0;
  font-size:15px;max-width:660px}
.note b{color:var(--nato-deep)}
.note.warn{background:var(--amber-soft);border-left-color:var(--amber)}

/* Karten */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));
  gap:10px;margin-top:14px}
.card{background:var(--panel);border:1px solid var(--line);
  border-top:3px solid var(--nato);border-radius:var(--radius);padding:14px}
.card .num{font-family:var(--font-mono);font-size:11px;color:var(--muted);
  letter-spacing:.1em;text-transform:uppercase}
.card h4{font-family:var(--font-body);text-transform:none;letter-spacing:0;
  font-size:16px;font-weight:700;line-height:1.35;margin:8px 0 2px}
.card p{font-size:14px;color:var(--ink-soft);line-height:1.5}
.card.ausgewogen{border-top-color:var(--f-ausgewogen)}
.card.protein{border-top-color:var(--f-protein)}
.card.vegetarisch{border-top-color:var(--f-vegetarisch)}

/* Marken der Empfehlungsschienen */
.tags{display:inline-flex;flex-wrap:wrap;gap:5px;vertical-align:middle}
.tag{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.08em;
  text-transform:uppercase;color:#fff;border-radius:3px;padding:2px 7px;white-space:nowrap;
  background:var(--nato)}
.tag.ausgewogen{background:var(--f-ausgewogen)}
.tag.protein{background:var(--f-protein)}
.tag.vegetarisch{background:var(--f-vegetarisch)}

/* Kennzahlen (kcal, Eiweiss, Preis extern) */
.figs{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:10px;
  font-family:var(--font-mono);font-size:11px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted)}
.fig b{font-family:var(--font-display);font-size:21px;letter-spacing:0;color:var(--ink);
  font-variant-numeric:tabular-nums;margin-right:4px}
.fig.price b{color:var(--nato-deep)}

/* kcal-Kombis */
.combo .num{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.combo .ziel{font-family:var(--font-display);font-size:28px;letter-spacing:0;
  text-transform:none;color:var(--nato-deep);font-variant-numeric:tabular-nums}
.combo .ziel small{font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-left:4px}
.combo-items{list-style:none;margin-top:8px;font-size:14px}
.combo-items li{display:flex;justify-content:space-between;gap:12px;padding:5px 0;
  border-top:1px solid var(--line)}
.combo-items li span{font-family:var(--font-mono);color:var(--muted);font-size:12px;
  white-space:nowrap;font-variant-numeric:tabular-nums}
.combo-note{margin-top:8px;font-size:12.5px;color:var(--ink-soft)}
.combo .figs{margin-top:8px}

/* Tabellen */
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:0;min-width:760px}
th,td{border:1px solid var(--line);padding:7px 7px;text-align:right;
  vertical-align:middle;white-space:nowrap;font-variant-numeric:tabular-nums}
th{background:var(--paper-2);font-family:var(--font-display);
  text-transform:uppercase;letter-spacing:.03em;font-weight:700;font-size:12.5px;color:var(--ink-soft)}
th:first-child,td:first-child{text-align:left}
th.key{color:var(--ink)}
.tabellenrahmen{overflow-x:auto;margin-top:14px;background:var(--panel);
  border:1px solid var(--line);border-radius:var(--radius)}
.tabellenrahmen table{border:0}
td.dish{white-space:normal;min-width:230px}
td.dish strong{font-weight:700}
td.dish .tags{margin-left:8px}
.station{display:block;font-family:var(--font-mono);font-size:11px;color:var(--muted);
  letter-spacing:.04em}
td.key{font-weight:700;font-size:15px}
td.key.price{color:var(--nato-deep)}
td.aux{color:var(--muted);font-size:12.5px}
td.aux:first-of-type{border-left:2px solid var(--line-strong)}
/* Empfohlenes Gericht: Flaeche und Randstreifen, kein opacity */
tr.is-rec td{background:var(--nato-soft)}
tr.is-rec td:first-child{box-shadow:inset 3px 0 0 var(--nato)}
.l{display:none}

/* ---------- Quellen und Fusszeile ---------- */
section.quellenblock{padding:40px 0 8px;border-top:1px solid var(--line)}
.quellen{list-style:none;margin-top:14px;display:flex;flex-direction:column;gap:8px}
.quellen li{font-size:14px;border-left:2px solid var(--line);padding-left:12px}
.quellen .url{display:block;font-family:var(--font-mono);font-size:12px;
  color:var(--muted);word-break:break-all}
.quellen .url a{color:var(--muted)}
.legende{margin-top:14px;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;
  font-size:14px;max-width:660px}
.legende dt{font-family:var(--font-mono);font-weight:700;color:var(--nato-deep)}
footer{margin-top:56px;background:var(--ink);color:#B9C4CF;
  padding:34px 0 44px;font-size:13.5px}
footer a{color:#7FB2EE}
footer .disp{color:#fff;font-size:22px;margin-bottom:8px}
footer p+p{margin-top:12px}

/* ---------- Schmale Screens: Tabs kompakt, Gerichte als Karten (nur Bildschirm, im Druck bleibt die Tabelle) ---------- */
@media screen and (max-width:760px){
  header.kopf{padding:32px 0 28px}
  .brand{display:none}
  .tablist{flex:1 1 100%;display:grid;grid-template-columns:repeat(5,minmax(0,1fr))}
  .chip[role="tab"]{display:flex;flex-direction:column;align-items:center;padding:5px 2px;
    border-radius:var(--radius)}
  .chip .tab-date{margin-left:0;font-size:10.5px}
  .wd-long{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .wd-short{display:inline}
  #week-toggle{margin-left:0;flex:1 1 100%;text-align:left}
  section.day{padding:28px 0 8px}
  h3{margin-top:24px}
  .tabellenrahmen{overflow:visible;background:none;border:0;border-radius:0}
  table,tbody{display:block;min-width:0;width:100%}
  thead{display:none}
  tbody tr{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px 8px;
    padding:10px 12px;margin-top:8px;background:var(--panel);
    border:1px solid var(--line);border-radius:var(--radius)}
  tr.is-rec{border-left:3px solid var(--nato)}
  tr.is-rec td{background:transparent}
  tr.is-rec td:first-child{box-shadow:none}
  th,td{border:0;padding:0;text-align:left;white-space:normal}
  td.dish{grid-column:1 / -1;min-width:0;margin-bottom:2px}
  td.dish .tags{display:flex;margin:4px 0 0}
  td.aux:first-of-type{border-left:0}
  .l{display:block;font-family:var(--font-mono);font-size:10px;letter-spacing:.06em;
    text-transform:uppercase;color:var(--muted);line-height:1.3}
  td.key{font-family:var(--font-display);font-size:20px;line-height:1.15;
    padding:6px 8px;background:var(--paper-2);border-radius:var(--radius)}
  td.aux{font-size:13px;padding:0 8px;color:var(--ink-soft)}
}

/* ---------- Einblenden beim Scrollen ---------- */
.js .reveal{opacity:0;transform:translateY(10px);transition:opacity .5s,transform .5s}
.js .reveal.sichtbar{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){
  .js .reveal{opacity:1;transform:none}
}

/* ---------- Druckansicht ---------- */
@media print{
  @page{margin:14mm}
  html,body{background:#fff!important;color:#000!important;font-size:10pt}
  header.kopf,footer{background:#fff!important;color:#000!important;padding:0 0 10pt}
  header.kopf::before{display:none}
  h1{font-size:22pt;color:#000!important}
  .sub,.eyebrow{color:#333!important}
  .hero-tags span{color:#000!important;border-color:#999!important}
  nav,button,.no-print{display:none!important}
  /* Eingeblendete Abschnitte immer sichtbar, auch die per Tab ausgeblendeten Tage */
  .reveal,[class*="reveal"]{opacity:1!important;transform:none!important}
  section.day[hidden]{display:block!important}
  section.day{padding:10pt 0}
  section.day+section.day{break-before:page;border-top:0}
  .card,.note,.combo,.legende,tbody tr{break-inside:avoid}
  h2,h3{break-after:avoid}
  .cards{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
  .tabellenrahmen{overflow:visible;border:0;background:none}
  table{min-width:0;font-size:8pt}
  th,td{padding:2pt 3pt;border-color:#999}
  th{white-space:normal;font-size:7.5pt}
  td.dish{min-width:0}
  td.key{font-size:8.5pt}
  td.aux{font-size:7.5pt}
  th{background:#eee!important;color:#000!important}
  tr.is-rec td{background:#eef2f7!important}
  td.aux{color:#333}
  a{color:#000!important;text-decoration:underline}
  /* Im Quellenblock steht die Adresse schon im Text - nicht doppeln */
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:8.5pt;color:#444}
  .quellen a[href^="http"]::after{content:none}
  footer .disp{color:#000!important}
}
"""


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


def _short(text, n=40):
    """Kürzt an einer Wortgrenze für den Tooltip in der Wochenleiste."""
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


# Schlüssel in den Daten → (CSS-Klasse, Anzeigetext)
REC_ORDER = (("ausgewogen", "ausgewogen", "ausgewogen"),
             ("protein", "protein", "viel Protein"),
             ("vegetarisch", "vegetarisch", "vegetarisch"))


def _grouped_recs(rec):
    """Empfehlungen nach Gericht gruppieren: empfiehlt mehr als eine Schiene
    dasselbe Gericht, werden die Marken zusammengefasst
    ([('ausgewogen', 'ausgewogen'), ('protein', 'viel Protein')], 'Menü 1')."""
    groups = []
    for key, cls, label in REC_ORDER:
        name = rec.get(key)
        if not name:
            continue
        for g in groups:
            if g[1] == name:
                g[0].append((cls, label))
                break
        else:
            groups.append(([(cls, label)], name))
    return groups


def _dish_roles(rec, name):
    return [(cls, label) for key, cls, label in REC_ORDER if rec.get(key) == name]


def _tags(roles):
    return ('<span class="tags">'
            + "".join(f'<span class="tag {cls}">{label}</span>' for cls, label in roles)
            + "</span>") if roles else ""


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
        for roles, name in groups:
            d = by_name.get(name)
            shown = _full_name(name, by_name)
            st = (d or {}).get("station") or ""
            station = f'<p class="station">{_esc(st)}</p>' if st and not shown.startswith(st) else ""
            cards.append(f'<article class="card {roles[0][0]}"><div class="num">{_tags(roles)}</div>'
                         f'<h4>{_esc(shown)}</h4>{station}{_figs(d)}</article>')
        body = f'<div class="cards">{"".join(cards)}</div>'
    return f'<div class="block"><h3>Empfehlung des Tages</h3>{body}</div>'


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
            f'<article class="card combo"><div class="num"><span>Ziel {_esc(target)} kcal</span>'
            f'<span class="ziel">{_fmt(c.get("kcal"))}{"†" if approx else ""}<small>kcal</small></span></div>'
            f'<ol class="combo-items">{"".join(items)}</ol>'
            f'<div class="figs"><span class="fig"><b>{_fmt(c.get("protein"), " g")}</b>Eiweiß</span>'
            f'<span class="fig price"><b>{_euro(c.get("price_extern"))}</b>extern</span></div>'
            f'{note}</article>')
    body = (f'<div class="cards">{"".join(cards)}</div>' if cards
            else '<p class="empty">Für diesen Tag gibt es keine kcal-Kombis.</p>')
    return f'<div class="block"><h3>kcal-Kombis</h3>{body}</div>'


def _dish_row(d, rec):
    p = d.get("portion") or {}
    roles = _dish_roles(rec, d.get("name"))
    w = d.get("weight_g")
    weight = "–" if w is None else _fmt(w) + ("*" if d.get("weight_estimated") else "") + " g"
    price = _euro(d.get("price_extern"))
    if d.get("price_extern_estimated") and d.get("price_extern") is not None:
        price += "*"

    def key(label, val, extra=""):
        return f'<td class="key{extra}"><span class="l">{label}</span>{val}</td>'

    def aux(label, val):
        return f'<td class="aux"><span class="l">{label}</span>{val}</td>'

    return (f'<tr{" class=is-rec" if roles else ""}>'
            f'<td class="dish"><span class="station">{_esc(d.get("station"))}</span>'
            f'<strong>{_esc(_dish_name(d))}</strong>{_tags(roles)}</td>'
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
        return ('<div class="block"><h3>Alle Gerichte</h3>'
                '<p class="empty">Für diesen Tag liegen keine Gerichte vor.</p></div>')
    rows = "".join(_dish_row(d, rec) for d in dishes)
    return (f'<div class="block"><h3>Alle Gerichte</h3>'
            f'<div class="tabellenrahmen"><table>'
            f'<thead><tr><th scope="col">Gericht</th><th scope="col" class="key">kcal</th>'
            f'<th scope="col" class="key">Eiweiß</th><th scope="col" class="key">Preis extern</th>'
            f'<th scope="col">Portion</th><th scope="col">Fett</th><th scope="col">ges. FS</th>'
            f'<th scope="col">KH</th><th scope="col">Zucker</th><th scope="col">Salz</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></div>')


def _tab_hint(day, by_name):
    """Kurzer Hinweis (Tooltip) im Tab: ausgewogene Empfehlung, sonst Anzahl."""
    name = (day.get("recommendations") or {}).get("ausgewogen")
    if name:
        return "Ausgewogen: " + _short(_full_name(name, by_name))
    n = len(day.get("dishes") or [])
    return f"{n} Gericht{'e' if n != 1 else ''}" if n else "keine Gerichte"


def _source_block(source, factor):
    """Quellenblock: Quelle (falls gesetzt), Aufbereitungshinweis, Legende."""
    quelle = (
        f'<ul class="quellen"><li><b>Speiseplan der Kantine</b> – Web-App des Betreibers; '
        f'dort stehen die Gerichte mit Preisen und Nährwerten je 100 g im Original.'
        f'<span class="url"><a href="{_esc(source)}" rel="noreferrer noopener">{_esc(source)}</a></span>'
        f'</li></ul>' if source else "")
    return (
        f'<section class="quellenblock reveal" id="quellen">'
        f'<p class="kicker">Quellen</p><h2>Woher die Angaben stammen</h2>'
        f'{quelle}'
        f'<p class="note"><b>Diese Seite ist eine automatische Aufbereitung.</b> Verbindlich sind '
        f'die Angaben der Quelle; bei Abweichungen gilt der dort veröffentlichte Speiseplan. '
        f'Nährwerte sind pro Portion berechnet aus den 100-g-Angaben der Quelle. Alle Angaben ohne '
        f'Gewähr; offensichtliche Datenfehler werden plausibilisiert.</p>'
        f'<dl class="legende">'
        f'<dt>*</dt><dd>geschätzt: Portionsgewicht ohne Angabe bzw. externer Preis aus internem Preis × {factor}</dd>'
        f'<dt>†</dt><dd>kcal-Ziel nicht exakt erreichbar, gezeigt wird die beste Annäherung</dd>'
        f'</dl></section>')


# ---------------------------------------------------------------------------
# Seite
# ---------------------------------------------------------------------------

def render_page(plan, meta):
    title = meta.get("title") or DEFAULT_TITLE
    kw, span = _week_info(plan)
    source = meta.get("source") or ""
    factor = _fmt(meta.get("price_factor"))
    stamp = _stamp(meta)

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
            f'<button class="chip" role="tab" type="button" id="tab-{i}" aria-controls="tag-{i}" '
            f'aria-selected="false" tabindex="-1" data-date="{_iso_date(day)}" '
            f'title="{_esc(_tab_hint(day, by_name))}">'
            f'<span class="wd-long">{_esc(weekday)}</span>'
            f'<span class="wd-short" aria-hidden="true">{_esc(weekday[:2])}</span>'
            f'<span class="tab-date">{_esc(date_short)}</span></button>')

        panels.append(
            f'<section class="day reveal" id="tag-{i}" role="tabpanel" aria-labelledby="tab-{i}">'
            f'<p class="kicker">Tag {i} · {_esc(day.get("date"))} · {count}</p>'
            f'<h2>{_esc(weekday)}</h2>'
            f'{_rec_block(rec, by_name)}{_combo_block(day.get("combos"), by_name)}'
            f'{_menu_block(dishes, rec)}</section>')

    weekbar = (
        f'<nav class="weekbar" aria-label="Wochenübersicht"><div class="navin">'
        f'<span class="brand">{_esc(kw or "Woche")}{f" <small>{_esc(span)}</small>" if span else ""}</span>'
        f'<div class="tablist" role="tablist" aria-label="Wochentage">{"".join(tabs)}</div>'
        f'<button id="week-toggle" class="chip" type="button" aria-pressed="false">'
        f'<span class="w-txt">Ganze Woche zeigen</span></button>'
        f'</div></nav>') if tabs else ""

    days = "".join(panels) if panels else \
        '<section class="day"><p class="empty">Es liegt kein Wochenplan vor.</p></section>'

    tags = "".join(f"<span>{_esc(t)}</span>" for t in (
        kw, span, f"Stand {stamp}" if stamp else "", "Nährwerte pro Portion",
        f"Preise extern (×{factor})" if factor != "–" else "Preise extern") if t)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)}{" · " + kw if kw else ""}</title>
{HEAD_JS}
<style>{CSS}</style>
</head>
<body>

<header class="kopf">
  <div class="wrap">
    <p class="eyebrow">Kantinen-Wochenplan{" &middot; " + _esc(kw) if kw else ""}</p>
    <h1>{_esc(title)}</h1>
    <p class="sub">Speiseplan Montag bis Freitag mit Nährwerten pro Portion, drei Empfehlungen
      je Tag (ausgewogen, viel Protein, vegetarisch) und Kombis für 600 und 1000 kcal.</p>
    <div class="hero-tags">{tags}</div>
  </div>
</header>

{weekbar}

<main class="wrap">
{days}
{_source_block(source, factor)}
</main>

<footer>
  <div class="wrap">
    <p class="disp">{_esc(title)}</p>
    <p>Stand: {_esc(stamp) or "unbekannt"} &middot; automatisch erzeugte Aufbereitung des
      Speiseplans, kein Original. Die Seite läuft ohne Internet, es wird nichts nachgeladen.</p>
    <p>Maßgeblich sind ausschließlich die Angaben der Quelle. Preise sind die externen Preise
      (Gäste ohne Hauskonditionen), Nährwerte gelten pro Portion.</p>
  </div>
</footer>
{PAGE_JS}
</body>
</html>
"""
