"""Build the per-project detail pages (EN at /projects/<slug>/, PT at /pt/projects/<slug>/).

Content lives in _build/projects/<slug>.py (a PAGE dict with "en" and "pt" texts); diagrams and charts are
inline SVG so they follow the light/dark theme. Run from the repository root:

    python _build/build_projects.py
"""
import csv
import html
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent / "projects"

UI = {
    "en": dict(projects="Projects", back="← All projects", code="View code on GitHub", how="How it works",
               results="Results", run="Run it", decisions="Design decisions", demo="Demo", next="Next project",
               copy="Copy", copied="Copied", theme=("Light theme", "Dark theme"), stack="Stack", lang_label="Color theme",
               home="Home"),
    "pt": dict(projects="Projetos", back="← Todos os projetos", code="Ver código no GitHub", how="Como funciona",
               results="Resultados", run="Como rodar", decisions="Decisões de projeto", demo="Demonstração",
               next="Próximo projeto", copy="Copiar", copied="Copiado", theme=("Tema claro", "Tema escuro"), stack="Stack",
               lang_label="Tema de cores", home="Início"),
}


def esc(s):
    return html.escape(s, quote=False)


# ---------- inline SVG helpers ----------

def svg_pipeline(steps, caption):
    """steps: list of (title, detail lines). Horizontal boxes joined by arrows."""
    n = len(steps)
    bw, gap, h = 176, 34, 150
    width = n * bw + (n - 1) * gap
    out = ['<svg class="diagram" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (width, h + 10, esc(caption))]
    out.append('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
               '<path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>')
    for i, (title, lines) in enumerate(steps):
        x = i * (bw + gap)
        last = i == n - 1
        out.append('<rect x="%d" y="5" width="%d" height="%d" rx="4" fill="var(--surface)" stroke="%s" stroke-width="%s"/>'
                   % (x + 1, bw - 2, h - 10, "var(--accent)" if last else "var(--line)", "1.5" if last else "1"))
        out.append('<text x="%d" y="30" class="d-num">%02d</text>' % (x + 14, i + 1))
        out.append('<text x="%d" y="54" class="d-title">%s</text>' % (x + 14, esc(title)))
        for j, line in enumerate(lines):
            out.append('<text x="%d" y="%d" class="d-text">%s</text>' % (x + 14, 78 + j * 18, esc(line)))
        if not last:
            out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="var(--accent)" stroke-width="1.5" marker-end="url(#ah)"/>'
                       % (x + bw + 2, h // 2, x + bw + gap - 3, h // 2))
    out.append("</svg>")
    return "\n".join(out)


def svg_states(states, edges, caption):
    """states: list of (name, color var, note). edges: list of (from, to, label, kind) kind in fwd/back."""
    n = len(states)
    bw, gap = 150, 92
    width = n * bw + (n - 1) * gap
    hgt = 250
    y = 92
    pos = {}
    out = ['<svg class="diagram" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (width, hgt, esc(caption))]
    out.append('<defs><marker id="sh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
               '<path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs>')
    for i, (name, color, note) in enumerate(states):
        x = i * (bw + gap)
        pos[name] = x
        out.append('<rect x="%d" y="%d" width="%d" height="56" rx="28" fill="var(--surface)" stroke="%s" stroke-width="2"/>' % (x + 1, y, bw - 2, color))
        out.append('<circle cx="%d" cy="%d" r="6" fill="%s"/>' % (x + 24, y + 28, color))
        out.append('<text x="%d" y="%d" class="d-title">%s</text>' % (x + 38, y + 33, esc(name)))
        if note:
            out.append('<text x="%d" y="%d" class="d-text" text-anchor="middle">%s</text>' % (x + bw // 2, y + 80, esc(note)))
    back_level = 0
    for a, b, label, kind in edges:
        xa, xb = pos[a], pos[b]
        if kind == "fwd":
            x1, x2 = xa + bw, xb
            out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="var(--muted)" stroke-width="1.4" marker-end="url(#sh)"/>' % (x1 + 2, y + 28, x2 - 3, y + 28))
            out.append('<text x="%d" y="%d" class="d-edge" text-anchor="middle">%s</text>' % ((x1 + x2) // 2, y - 10, esc(label[0])))
            if len(label) > 1:
                out.append('<text x="%d" y="%d" class="d-edge" text-anchor="middle">%s</text>' % ((x1 + x2) // 2, y + 2 - 26, esc(label[1])))
        else:
            back_level += 1
            top = 44 if back_level == 1 else 18
            x1, x2 = xa + bw // 2, xb + bw // 2
            out.append('<path d="M%d %d V%d H%d V%d" fill="none" stroke="var(--muted)" stroke-dasharray="4 4" stroke-width="1.2" marker-end="url(#sh)"/>'
                       % (x1, y - 2, top, x2, y - 3))
            out.append('<text x="%d" y="%d" class="d-edge" text-anchor="middle">%s</text>' % ((x1 + x2) // 2, top - 6, esc(label[0])))
    out.append("</svg>")
    return "\n".join(out)


def svg_bars(items, caption, unit="", decimal="."):
    """Horizontal bar chart. items: list of (label, value) or (label, value, color css var)."""
    W, L, R, bh, gap = 900, 220, 70, 30, 14
    vmax = max(v for _, v, *_ in items) or 1
    H = len(items) * (bh + gap) + 10
    out = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, H, esc(caption))]
    for i, (label, v, *rest) in enumerate(items):
        y = 5 + i * (bh + gap)
        w = (W - L - R) * v / vmax
        color = rest[0] if rest else "var(--accent)"
        out.append('<text x="%d" y="%d" class="c-label" text-anchor="end">%s</text>' % (L - 12, y + bh / 2 + 5, esc(label)))
        out.append('<rect x="%d" y="%d" width="%.1f" height="%d" rx="3" fill="%s"/>' % (L, y, max(w, 2), bh, color))
        out.append('<text x="%.1f" y="%d" class="c-label">%s%s</text>' % (L + w + 8, y + bh / 2 + 5, (str(v) if isinstance(v, int) else "%.3f" % v).replace(".", decimal), unit))
    out.append("</svg>")
    return "\n".join(out)


def svg_trace(csv_path, cfg, caption, legend):
    """Torso angle (top) and hip velocity (bottom) of track 1 with state bands and thresholds."""
    rows = [r for r in csv.DictReader(open(csv_path, encoding="utf-8")) if r["track_id"] == "1"]
    t = [float(r["time"]) for r in rows]
    T = max(t)
    W, H1, H2, L, R, TOP, GAP = 900, 170, 110, 46, 12, 14, 34
    x = lambda v: L + (W - L - R) * v / T
    colors = {"UPRIGHT": "var(--ok)", "FALLING": "var(--warn)", "FALLEN": "var(--accent)", "ALERT": "var(--accent)"}
    out = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, TOP + H1 + GAP + H2 + 30, esc(caption))]
    # state bands
    start = 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i]["state"] != rows[start]["state"]:
            st = rows[start]["state"]
            x0, x1 = x(t[start]), x(t[i] if i < len(rows) else T)
            op = ".22" if st == "ALERT" else ".12"
            for (y0, hh) in ((TOP, H1), (TOP + H1 + GAP, H2)):
                out.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s" opacity="%s"/>' % (x0, y0, max(x1 - x0, 1), hh, colors[st], op))
            out.append('<text x="%.1f" y="%d" class="c-band">%s</text>' % (x0 + 4, TOP + 13, st))
            start = i

    def panel(y0, hh, key, vmax, thresholds, label, scale=1.0, vmin=0.0):
        out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="var(--line)"/>' % (L, y0, W - L - R, hh))
        yv = lambda v: y0 + hh - hh * (max(min(v, vmax), vmin) - vmin) / (vmax - vmin)
        if vmin < 0:
            out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--line)"/>' % (L, W - R, yv(0), yv(0)))
        for k in range(0, 5):
            v = vmin + (vmax - vmin) * k / 4
            out.append('<text x="%d" y="%.1f" class="c-axis" text-anchor="end">%g</text>' % (L - 6, yv(v) + 4, round(v, 2)))
        for v, name in thresholds:
            out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="var(--muted)" stroke-dasharray="5 4"/>' % (L, W - R, yv(v), yv(v)))
            out.append('<text x="%d" y="%.1f" class="c-axis" text-anchor="end">%s</text>' % (W - R - 4, yv(v) - 5, esc(name)))
        pts = []
        for r, tv in zip(rows, t):
            if r[key] in ("", None):
                if pts:
                    out.append('<polyline points="%s" fill="none" stroke="var(--text)" stroke-width="1.8"/>' % " ".join(pts))
                    pts = []
                continue
            pts.append("%.1f,%.1f" % (x(tv), yv(float(r[key]) * scale)))
        if pts:
            out.append('<polyline points="%s" fill="none" stroke="var(--text)" stroke-width="1.8"/>' % " ".join(pts))
        out.append('<text x="%d" y="%d" class="c-label">%s</text>' % (L + 6, y0 + hh - 8, esc(label)))

    panel(TOP, H1, "torso_angle", 100, cfg["angle_lines"], legend["angle"])
    panel(TOP + H1 + GAP, H2, "velocity", cfg["vmax"], cfg["vel_lines"], legend["velocity"], vmin=cfg.get("vmin", 0.0))
    y = TOP + H1 + GAP + H2
    for k in range(0, int(T) + 1):
        out.append('<text x="%.1f" y="%d" class="c-axis" text-anchor="middle">%d s</text>' % (x(k), y + 18, k))
    out.append("</svg>")
    return "\n".join(out)


# ---------- page ----------

def page(slug, P, lang, nxt):
    u = UI[lang]
    d = P[lang]
    depth = "../../" if lang == "en" else "../../../"
    home = depth if lang == "en" else depth + "pt/"
    other = ("../../../pt/projects/%s/" % slug) if lang == "en" else ("../../../projects/%s/" % slug)
    media = depth + "assets/projects/%s/" % slug
    canon = "https://karemdm.github.io/%sprojects/%s/" % ("" if lang == "en" else "pt/", slug)
    blocks = []

    stats = "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (k, v) for v, k in d["stats"])
    chips = "".join("<li>%s</li>" % c for c in P["stack"])
    links = '<a class="button button-primary" href="%s" rel="noopener">%s</a><a class="button" href="%s#projects">%s</a>' % (P["repo"], u["code"], home, u["back"])
    for extra in d.get("extra_links", []):
        links += '<a class="button" href="%s" rel="noopener">%s</a>' % extra

    video = ('<figure class="demo"><div class="demo-frame"><video src="%s%s" poster="%s%s" autoplay muted loop playsinline preload="metadata" '
             'aria-label="%s"></video></div><figcaption>%s</figcaption></figure>'
             % (media, P["video"], media, P["poster"], esc(d["video_alt"]), d["video_caption"]))

    sections = []
    n = 0

    def section(label, title, body):
        nonlocal n
        n += 1
        sections.append('<section class="section" id="s%d"><div class="section-label">%s</div><div>\n<h2><span class="sec-n">%02d</span>%s</h2>\n%s\n</div></section>'
                        % (n, label, n, title, body))

    # how it works
    body = "<p>%s</p>\n" % d["how_intro"]
    body += '<figure class="fig"><div class="scroll-x">%s</div><figcaption>Fig. 01 · %s</figcaption></figure>\n' % (
        svg_pipeline(d["pipeline"], d["pipeline_caption"]), d["pipeline_caption"])
    if "states" in d:
        body += "<p>%s</p>\n" % d["states_intro"]
        body += '<figure class="fig"><div class="scroll-x">%s</div><figcaption>Fig. 02 · %s</figcaption></figure>\n' % (
            svg_states(d["states"], d["edges"], d["states_caption"]), d["states_caption"])
    if "features" in d:
        body += '<dl class="defs">%s</dl>\n' % "".join("<div><dt>%s</dt><dd>%s</dd></div>" % f for f in d["features"])
    section(u["how"], d["how_title"], body)

    # evidence: trace chart or bar chart + frames
    body = ""
    if "bars" in d:
        body += "<p>%s</p>\n" % d["bars"]["intro"]
        body += '<figure class="fig">%s<figcaption>Fig. 03 · %s</figcaption></figure>\n' % (
            svg_bars(d["bars"]["items"], d["bars"]["caption"], decimal=d["bars"].get("decimal", ".")), d["bars"]["caption"])
    if "trace" in P:
        body += "<p>%s</p>\n" % d["trace_intro"]
        body += '<figure class="fig">%s<figcaption>Fig. 03 · %s</figcaption></figure>\n' % (
            svg_trace(ROOT / P["trace"]["csv"], P["trace"], d["trace_caption"], d["trace_legend"]), d["trace_caption"])
    if "frames" in P:
        figs = "".join('<figure><img src="%s%s" alt="%s" loading="lazy" width="640" height="360"><figcaption>%s</figcaption></figure>'
                       % (media, f, esc(c), c) for f, c in zip(P["frames"], d["frames"]))
        body += '<div class="frames">%s</div>\n' % figs
    if "results_table" in d:
        head, rows = d["results_table"]
        body += '<div class="scroll-x"><table class="data-table"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>\n' % (
            "".join("<th>%s</th>" % h for h in head),
            "".join("<tr>%s</tr>" % "".join('<td data-label="%s">%s</td>' % (h, c) for h, c in zip(head, r)) for r in rows))
    if "results_note" in d:
        body += '<p class="note">%s</p>\n' % d["results_note"]
    for extra, text in zip(P.get("more_demos", []), d.get("more_demos", [])):
        body += '<h3 class="sub">%s</h3>\n<p>%s</p>\n' % (text["title"], text["intro"])
        body += ('<figure class="demo"><div class="demo-frame"><video src="%s%s" poster="%s%s" muted loop playsinline preload="none" '
                 'aria-label="%s"></video></div><figcaption>%s</figcaption></figure>\n'
                 % (media, extra["video"], media, extra["poster"], esc(text["alt"]), text["caption"]))
        if "table" in text:
            head, rows = text["table"]
            body += '<div class="scroll-x"><table class="data-table"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>\n' % (
                "".join("<th>%s</th>" % h for h in head),
                "".join("<tr>%s</tr>" % "".join('<td data-label="%s">%s</td>' % (h, c) for h, c in zip(head, r)) for r in rows))
        if "note" in text:
            body += '<p class="note">%s</p>\n' % text["note"]
    section(u["results"], d["results_title"], body)

    # run
    def terminal(title, cmd, tabs=None):
        """One command block; ``tabs`` maps an OS label to its own command and adds a tab switcher."""
        if not tabs:
            return ('<div class="terminal"><div class="terminal-bar"><span>%s</span><button type="button" class="copy" data-copy>%s</button></div>'
                    '<pre><code>%s</code></pre></div>' % (esc(title), u["copy"], esc(cmd)))
        btns = "".join('<button type="button" role="tab" aria-selected="%s" data-tab="%d">%s</button>' % ("true" if i == 0 else "false", i, esc(k))
                       for i, k in enumerate(tabs))
        panes = "".join('<pre data-pane="%d"%s><code>%s</code></pre>' % (i, "" if i == 0 else " hidden", esc(v)) for i, v in enumerate(tabs.values()))
        return ('<div class="terminal" data-tabs><div class="terminal-bar"><span>%s</span><span class="os-tabs" role="tablist">%s</span>'
                '<button type="button" class="copy" data-copy>%s</button></div>%s</div>' % (esc(title), btns, u["copy"], panes))

    cmds = "".join(terminal(*item) if len(item) == 3 else terminal(item[0], item[1]) for item in d["run"])
    section(u["run"], d["run_title"], cmds)

    # decisions
    dec = "".join('<article class="card"><h3>%s</h3><p>%s</p></article>' % x for x in d["decisions"])
    section(u["decisions"], d["decisions_title"], '<div class="grid">%s</div>' % dec)

    if nxt:
        nav_next = '<a href="../%s/">%s: %s →</a>' % (nxt[0], u["next"], esc(nxt[1]))
    else:
        nav_next = ""
    return f"""<!doctype html>
<html lang="{'en' if lang == 'en' else 'pt-BR'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f5f3ec">
<title>{esc(P['title'])} | Karem Marcomini</title>
<meta name="description" content="{esc(d['summary'])}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(P['title'])} | Karem Marcomini">
<meta property="og:description" content="{esc(d['summary'])}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="https://karemdm.github.io/assets/projects/{slug}/{P['poster']}">
<link rel="alternate" hreflang="en" href="https://karemdm.github.io/projects/{slug}/">
<link rel="alternate" hreflang="pt-BR" href="https://karemdm.github.io/pt/projects/{slug}/">
<link rel="icon" href="https://avatars.githubusercontent.com/u/72208245?v=4">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script>
(function(){{var c='light';try{{c=localStorage.getItem('kdm.theme')==='dark'?'dark':'light'}}catch(e){{}}
document.documentElement.dataset.theme=c;}})();
</script>
<link rel="stylesheet" href="{depth}assets/site.css">
<link rel="stylesheet" href="{depth}assets/project.css">
</head>
<body>
<header class="site-header">
  <div class="container">
    <a class="brand" href="{home}">Karem Marcomini</a>
    <nav class="primary" aria-label="Primary">
      <a href="{home}#projects">{u['projects']}</a>
      <a href="{P['repo']}" rel="noopener">GitHub</a>
    </nav>
    <div class="lang-switch">{'<a href="./" aria-current="page" lang="en">EN</a><a href="%s" lang="pt-BR" hreflang="pt-BR">PT</a>' % other if lang == 'en' else '<a href="%s" lang="en" hreflang="en">EN</a><a href="./" aria-current="page" lang="pt-BR">PT</a>' % other}</div>
    <div class="theme-switch" role="group" aria-label="{u['lang_label']}">
      <button type="button" data-choice="light" aria-label="{u['theme'][0]}" title="{u['theme'][0]}"><svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
      <button type="button" data-choice="dark" aria-label="{u['theme'][1]}" title="{u['theme'][1]}"><svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></button>
    </div>
  </div>
</header>
<main class="container project">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">{u['home']}</a> / <a href="{home}#projects">{u['projects']}</a> / <span>{esc(P['title'])}</span></nav>
  <div class="p-hero">
    <p class="meta">{''.join('<span>%s</span>' % m for m in d['meta'])}</p>
    <h1>{esc(P['title'])}</h1>
    <p class="lede">{d['lede']}</p>
    <div class="btns">{links}</div>
  </div>
  {video}
  <dl class="stats">{stats}</dl>
  <ul class="chips p-stack" aria-label="{u['stack']}">{chips}</ul>
  {''.join(sections)}
  <nav class="next-project"><a href="{home}#projects">{u['back']}</a>{nav_next}</nav>
</main>
<footer>
  <div class="container">
    <span>&copy; Karem Daiane Marcomini</span>
  </div>
</footer>
<script>
(function(){{
  var root=document.documentElement,btns=document.querySelectorAll('.theme-switch button');
  function apply(c){{root.dataset.theme=c;btns.forEach(function(b){{b.setAttribute('aria-pressed',String(b.dataset.choice===c))}})}}
  btns.forEach(function(b){{b.addEventListener('click',function(){{try{{localStorage.setItem('kdm.theme',b.dataset.choice)}}catch(e){{}}apply(b.dataset.choice)}})}});
  apply(root.dataset.theme||'light');
  document.querySelectorAll('[data-copy]').forEach(function(b){{b.addEventListener('click',function(){{
    var code=b.closest('.terminal').querySelector('pre:not([hidden]) code').innerText;
    (navigator.clipboard?navigator.clipboard.writeText(code):Promise.reject()).then(function(){{var t=b.textContent;b.textContent='{u['copied']}';setTimeout(function(){{b.textContent=t}},1400)}}).catch(function(){{}});
  }})}});
  document.querySelectorAll('[data-tabs]').forEach(function(box){{box.querySelectorAll('[data-tab]').forEach(function(t){{t.addEventListener('click',function(){{
    box.querySelectorAll('[data-tab]').forEach(function(x){{x.setAttribute('aria-selected',String(x===t))}});
    box.querySelectorAll('[data-pane]').forEach(function(p){{p.hidden=p.dataset.pane!==t.dataset.tab}});
  }})}})}});
  var io='IntersectionObserver' in window?new IntersectionObserver(function(es){{es.forEach(function(e){{
    if(e.target.tagName==='VIDEO'){{e.isIntersecting?e.target.play().catch(function(){{}}):e.target.pause()}}
    else if(e.isIntersecting){{e.target.classList.add('is-seen');io.unobserve(e.target)}}
  }})}},{{threshold:.2}}):null;
  document.querySelectorAll('video,.fig,.frames figure,.stats div').forEach(function(el){{if(io){{if(el.tagName!=='VIDEO')el.classList.add('reveal');io.observe(el)}}}});
}})();
</script>
</body>
</html>
"""


def main():
    order = [p.stem for p in sorted(SRC.glob("*.py"))]
    pages = {}
    for slug in order:
        spec = importlib.util.spec_from_file_location(slug, SRC / (slug + ".py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        pages[mod.PAGE["slug"]] = mod.PAGE
    slugs = list(pages)
    for i, slug in enumerate(slugs):
        P = pages[slug]
        nxt = pages[slugs[(i + 1) % len(slugs)]] if len(slugs) > 1 else None
        for lang in ("en", "pt"):
            out = ROOT / ("projects" if lang == "en" else "pt/projects") / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(slug, P, lang, (nxt["slug"], nxt["title"]) if nxt else None), encoding="utf-8", newline="\n")
            print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
