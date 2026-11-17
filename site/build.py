#!/usr/bin/env python3
"""Builds the plain site into ./_plain, then publishes it (open, or password-protected when PROTECT is True) into ./docs (served by GitHub Pages), from ./pages, ./css, ./js and ./assets.

ASSETS maps the image ids used in the Claude design canvas to the file names in ./assets."""
import json, os, re, shutil, sys
import optimize

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "_plain")
DOMAIN = "henrikhedvall.com"  # e.g. "henrikhedvall.se" – set when known (used for CNAME and share image URLs)

ASSETS = {
    "2e2296073c579610e979548d8ea65aec": "oqto-hero.jpg", "0445cbdf439d529c4528df06bde41d32": "tink-hero.jpg",
    "75508b9ec8aafed6d13291fd1dc33ed1": "tink-circle-a.png", "b995ecd141694efdc8b48696545bfc49": "tink-circle-b.png",
    "233ee65b2141d99bdbb6690980ede10f": "ww-hero.mp4", "e9707fabde6acdb8dac9fd62a9b1cd87": "ww-hero-poster.jpg",
    "16fa00db29608fb33f843c4995f7481c": "klarna.jpg", "e5bff79d085d4e0ec60e4a1f3527f37a": "qapital.jpg",
    "b7f02dd23c21bd09813d00f3d07ad053": "atlar.jpg", "c01776bc0bd7ccddd66d72ed605c93e0": "romo-bygg.jpg",
    "c4459226de797c4df204a6b0b06ca3d5": "svartanatt.jpg", "fec15f3ac0007fd30fc3f6f249fd448c": "henrik.jpg",
    "aa1eb67f8c8be2493bbfd4aa54762e37": "oqto-type.jpg", "471465112e013b29ffcea0fa0ea3b559": "oqto-components.jpg",
    "c34dd534a3003ee261711ca87890d62c": "oqto-dark.jpg", "b7a1f7ae78d363ddf79c024ff4bfa8f4": "oqto-light.jpg",
    "c34b591a7f8fddf09f75926bdbe9cb4d": "oqto-screens.jpg", "a67261e7335ce425f5cbf03bea56eee6": "oqto-after.jpg",
    "24c4ba42e7d66d0e7984402ead110cda": "oqto-before.jpg", "a06f2b58758b6fb555fed11e960a2e03": "oqto-app.jpg",
    "637462e7e8cb1a3e784b541fafad197d": "tink-logo.jpg", "6e3a6e0409bc43d9788ccd3c57f38416": "tink-colours.jpg",
    "8ccadca1c7c70a65154867eb4540ba2f": "tink-poster.jpg", "9a65abafdb9345d5e481ffe969c22879": "tink-type.jpg",
    "3bca89cef68a116650a6c5ef6770cb4f": "tink-icons.jpg", "c1f94b98ab6d53cafc91e170a44835eb": "tink-dot-a.png",
    "f7b58a42b01e4846ca3732440ee7e58e": "tink-dot-b.png", "700febebcb68be373cda9b187586076e": "tink-onboarding.jpg",
    "1985dbdba6e3530443f5df8e166f4dcd": "tink-screens.jpg", "ac8a5f15eb231d84428fc1641a1aa236": "tink-dark.jpg",
    "f414974410411ce49392f4c3414bf53b": "ww-identity.png", "efab65d4d433ed4ba4f636274f9a9e99": "ww-calendar.jpg",
    "d7569c8d5cc400fd7471c27a4c2b9144": "ww-calendar-full.jpg", "dd36df8f9b4a2f8280afd473ea40f9b3": "ww-skier.png",
    "3b0aba6df729159ddd92d895620fe94c": "ww-chapter.mp4", "27f8f596ff1426df0556b45195ddebe2": "ww-chapter-poster.jpg",
    "c559b303cef21837a8244d9c09d533e3": "sas.jpg",
}

PAGES = [
    # source, output path, title, description, extra css, extra fonts, share image, reveal threshold
    ("main", "index.html", "Henrik Hedvall – Freelance product designer",
     "Freelance product designer with more than 15 years of experience, from agencies and startups to Klarna and Tink.",
     "main.css", "", "oqto-hero.jpg", "0.85"),
    ("oqto", "oqto/index.html", "Oqto product redesign and design system – Henrik Hedvall",
     "A redesign of Oqto’s accounting platform and mobile app, built on a new design system.",
     "oqto.css", "&amp;family=Geist+Mono:wght@500", "oqto-hero.jpg", "1.02"),
    ("tink", "tink/index.html", "Tink: identity, design system and app – Henrik Hedvall",
     "Six years as a designer at Tink, as it grew from a team of ten into Europe’s leading open banking platform.",
     "tink.css", "", "tink-hero.jpg", "1.02"),
    ("ww", "weekend-warriors/index.html", "Weekend Warriors ski film identity – Henrik Hedvall",
     "Lettering, identity and animated titles for a ski film.",
     "ww.css", "", "ww-hero-poster.jpg", "1.02"),
    ("more", "more-work/index.html", "More work: Atlar, Klarna, Qapital – Henrik Hedvall",
     "A selection of other things I have designed over the years, from fintech products to logos and record sleeves.",
     "", "", "atlar.jpg", "1.02"),
]

PG = "background: #F5F5F3; color: #111110; font-family: 'Familjen Grotesk', 'Helvetica Neue', Arial, sans-serif; font-size: 18px; line-height: 1.5; -webkit-font-smoothing: antialiased"
WRAP = "max-width: 1320px; margin: 0 auto; padding: 0 clamp(20px, 4vw, 60px); box-sizing: border-box"
BT = "border-top: 1px solid #D9D9D4"
H3 = "margin: 0; font-size: clamp(23px, 2.3vw, 32px); font-weight: 500; letter-spacing: -0.025em; line-height: 1.2"
COL2 = "flex: 1 1 640px; min-width: 0"
LBL = "flex: 0 1 300px; margin: 0; font-size: 16px; font-weight: 400; color: #5E5E5A"

TOKENS = {
    "SA": f'style="margin-top: clamp(96px, 11vw, 168px); padding: 20px 0 clamp(96px, 11vw, 168px); {BT}; display: flex; flex-wrap: wrap; gap: 32px 24px"',
    "SR": f'style="padding: 20px 0 clamp(96px, 11vw, 168px); {BT}; display: flex; flex-wrap: wrap; gap: 32px 24px"',
    "SC": f'style="padding: 20px 0 clamp(96px, 11vw, 168px); {BT}; display: flex; flex-direction: column; gap: clamp(48px, 5vw, 72px)"',
    "SC2": f'style="padding: 20px 0 clamp(96px, 11vw, 168px); {BT}; display: flex; flex-direction: column; gap: clamp(56px, 6vw, 88px)"',
    "LB": 'data-lb="1" tabindex="0" role="button" aria-label="Enlarge image"',
    "GRID2": 'style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(420px, 100%), 1fr)); gap: 24px"',
    "H3": f'style="{H3}"',
    "CONTACT": f'''<section style="padding: 20px 0 clamp(72px, 8vw, 120px); {BT}; display: flex; flex-wrap: wrap; gap: 32px 24px">
<h2 style="{LBL}">Contact</h2>
<div style="{COL2}; display: flex; flex-direction: column; gap: 8px; font-size: clamp(23px, 2.6vw, 36px); line-height: 1.22; letter-spacing: -0.025em">
<p style="margin: 0; color: #5E5E5A">Have a project in mind?</p>
<a href="mailto:[[CONTACT_ADDR]]" style="align-self: flex-start; border-bottom: 1px solid currentColor; padding-bottom: 2px">[[CONTACT_ADDR]]</a>
</div>
</section>''',
    "FOOTER": f'''<footer style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px 40px; padding: 28px 0 40px; {BT}; font-size: 16px; color: #5E5E5A">
<span>© 2026 Henrik Hedvall</span>
<a href="https://www.linkedin.com/in/henrikhedvall/" target="_blank" rel="noopener" style="color: #5E5E5A">LinkedIn</a>
</footer>''',
}


def m_h2(t):
    return f'<h2 style="{LBL}">{t}</h2>'


def m_bigp(t):
    return f'<p style="{COL2}; margin: 0; max-width: 24em; font-size: clamp(23px, 2.6vw, 36px); line-height: 1.22; letter-spacing: -0.025em; text-wrap: pretty">{t}</p>'


def _step(first, title, text):
    return f'''<div style="display: flex; flex-wrap: wrap; gap: 32px 24px">
{first}
<div style="{COL2}; display: flex; flex-direction: column; gap: 12px">
<h3 style="{H3}">{title}</h3>
<p style="margin: 0; max-width: 32em; color: #5E5E5A; text-wrap: pretty">{text}</p>
</div>
</div>'''


def m_step(label, title, text):
    return _step(f'<div style="flex: 0 1 300px; font-size: 16px; color: var(--accent); font-variant-numeric: tabular-nums">{label}</div>', title, text)


def m_step1(label, title, text):
    return _step(f'''<div style="flex: 0 1 300px; display: flex; flex-direction: column; gap: 4px; font-size: 16px">
<h2 style="margin: 0; font-size: 16px; font-weight: 400; color: #5E5E5A">Process</h2>
<span style="color: var(--accent); font-variant-numeric: tabular-nums">{label}</span>
</div>''', title, text)


def m_rv(n, extra=""):
    return f'data-rv="{n}" {TOKENS["LB"]} class="rv" style="overflow: hidden{extra}"'


def m_img(n, file, alt, w, h):
    return f'<div {m_rv(n)}><img class="zm" src="[[A]]{file}" alt="{alt}" width="{w}" height="{h}"></div>'


def m_top(title, lead, meta):
    rows = ""
    for pair in meta.split(";"):
        if not pair.strip():
            continue
        k, v = pair.split("=", 1)
        dd = "margin: 0; font-variant-numeric: tabular-nums" if k == "Period" else "margin: 0"
        rows += f'<div style="display: flex; flex-direction: column">\n<dt style="color: #5E5E5A">{k}</dt>\n<dd style="{dd}">{v}</dd>\n</div>\n'
    left = (f'<dl class="r2 meta" style="flex: 0 1 300px; margin: 0; padding-top: 14px; display: flex; flex-direction: column; gap: 16px; font-size: 16px">\n{rows}</dl>'
            if rows else '<div aria-hidden="true" style="flex: 0 1 300px"></div>')
    return f'''<section style="padding: clamp(72px, 9vw, 128px) 0 clamp(56px, 6vw, 88px); display: flex; flex-wrap: wrap; gap: 32px 24px">
{left}
<div class="r1" style="{COL2}; display: flex; flex-direction: column; gap: clamp(28px, 3vw, 44px)">
<h1 style="margin: 0; font-size: clamp(44px, 7.4vw, 108px); line-height: 0.98; font-weight: 500; letter-spacing: -0.04em; text-wrap: balance">{title}</h1>
<p style="margin: 0; max-width: 26em; font-size: clamp(21px, 2vw, 27px); line-height: 1.32; letter-spacing: -0.02em; text-wrap: pretty">{lead}</p>
</div>
</section>'''


def m_next(href, title, sub):
    return f'''<section style="padding: 20px 0 clamp(72px, 8vw, 120px); {BT}; display: flex; flex-wrap: wrap; gap: 32px 24px">
<h2 style="{LBL}">Next project</h2>
<div style="{COL2}; display: flex; flex-direction: column; gap: 12px">
<a href="[[R]]{href}" style="align-self: flex-start; font-size: clamp(36px, 6vw, 88px); line-height: 1.02; font-weight: 500; letter-spacing: -0.04em; color: var(--accent); border-bottom: 1px solid var(--accent); padding-bottom: 4px">{title}</a>
<p style="margin: 0; font-size: 16px; color: #5E5E5A">{sub}</p>
</div>
</section>'''


def m_fig(n, file, alt, name, meta):
    return f'''<figure style="margin: 0; display: flex; flex-direction: column; gap: 16px">
<div {m_rv(n, "; background: #E7E7E3")}><img class="zm" src="[[A]]{file}" alt="{alt}" width="2000" height="1500"></div>
<figcaption style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 24px; font-size: 16px"><span>{name}</span><span style="color: #5E5E5A">{meta}</span></figcaption>
</figure>'''


def m_hero(_=""):
    words = ["Henrik", "Hedvall,", "product", "designer."]
    out = ""
    for wi, wd in enumerate(words):
        base = 700 if wi < 2 else 400
        sign = -1 if wi < 2 else 1
        chars = ""
        for ch in wd:
            dot = wi == len(words) - 1 and ch == "."
            chars += f'<span class="{"c dot" if dot else "c"}" data-c="{base},{sign}" style="font-weight: {base}">{ch}</span>'
        out += f'<span aria-hidden="true" class="w" style="animation-delay: {wi * 90}ms">{chars}</span>'
        out += "<br>" if wi == 1 else (" " if wi != len(words) - 1 else "")
    return out


SVC_ICONS = [
    '<g class="spin"><g class="turn"><path class="s" d="M12 4v16" pathLength="1"></path><path class="s dl" d="M4 12h16" pathLength="1"></path></g></g><circle class="nd" cx="19" cy="5" r="2.6"></circle>',
    '<path class="s k dm d1" d="M12 3l3.4 3.4-3.4 3.4-3.4-3.4z" pathLength="1"></path><path class="s dm d2" d="M6.4 8.6l3.4 3.4-3.4 3.4-3.4-3.4z" pathLength="1"></path><path class="s dm d3" d="M17.6 8.6l3.4 3.4-3.4 3.4-3.4-3.4z" pathLength="1"></path><path class="s dm d4" d="M12 14.2l3.4 3.4-3.4 3.4-3.4-3.4z" pathLength="1"></path>',
    '<path class="s cv" d="M4.5 19.5C11 19.5 11 5 19.5 5" pathLength="1"></path><path class="s hl" d="M19.5 5H12.4" pathLength="1"></path><circle class="s kb" cx="11" cy="5" r="1.4" pathLength="1"></circle><circle class="nd g st" cx="4.5" cy="19.5" r="2.4"></circle><rect class="nd st" x="17.4" y="2.9" width="4.2" height="4.2" rx="1.1"></rect>',
    '<circle class="s l" cx="9" cy="12" r="5.5" pathLength="1"></circle><circle class="s r k" cx="15" cy="12" r="5.5" pathLength="1"></circle>',
]


def m_svc(n, title, text):
    bt = "" if n == "0" else f"; {BT}"
    return f'''<div class="svc-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr)); gap: 12px 24px; padding: 28px 0{bt}">
<div data-svc="{n}" class="svc" style="display: flex; align-items: flex-start; gap: 16px; font-size: clamp(21px, 1.9vw, 26px)">
<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">{SVC_ICONS[int(n)]}</svg>
<h3 style="margin: 0; font-size: clamp(21px, 1.9vw, 26px); font-weight: 500; letter-spacing: -0.02em; line-height: 1.2">{title}</h3>
</div>
<p style="margin: 0; color: #5E5E5A; text-wrap: pretty">{text}</p>
</div>'''


def m_job(name, years, line=""):
    bt = f"; {BT}" if line else ""
    return f'''<div style="display: flex; justify-content: space-between; gap: 24px; padding: 14px 0{bt}">
<span>{name}</span>
<span style="color: #5E5E5A; font-variant-numeric: tabular-nums">{years}</span>
</div>'''


TOKENS["OQTO_OVERLAY"] = open(os.path.join(ROOT, "pages", "_oqto_overlay.html"), encoding="utf-8").read().strip()

CONFIG = json.load(open(os.path.join(ROOT, "site.config.json")))

MACROS = {"H2": m_h2, "BIGP": m_bigp, "STEP": m_step, "STEP1": m_step1, "RV": m_rv, "IMG": m_img,
          "TOP": m_top, "SVC": m_svc, "JOB": m_job, "NEXT": m_next, "FIG": m_fig, "HERO": m_hero}


def expand(src):
    def rep(m):
        args = m.group(2).split("|") if m.group(2) else []
        return MACROS[m.group(1)](*[a.strip() for a in args])
    prev = None
    while prev != src:
        prev = src
        src = re.sub(r"@([A-Z0-9]+)\{([^{}]*)\}", rep, src)
    for k, v in TOKENS.items():
        src = src.replace(f"[[{k}]]", v)
    return src


def theme_css(P):
    return f"""{P}{{--accent:#46765F;color-scheme:dark}}
{P},:where({P}) body{{background:#121211 !important}}
:where({P}) .pg{{background:#121211 !important;color:#EDEDE9 !important}}
:where({P}) .hdr{{background:#121211;box-shadow:0 0 0 100vmax #121211}}
:where({P}) ::selection{{background:#2F5D4B;color:#F5F5F3}}
:where({P}) a{{color:#EDEDE9}}
:where({P}) .ic .s{{stroke:#9C9C96 !important}}
:where({P}) .ic .s.k{{stroke:var(--accent) !important}}
:where({P}) .ic .nd.g{{fill:#9C9C96 !important}}
:where({P}) .bleed{{background:#2F5D4B;box-shadow:0 0 0 100vmax #2F5D4B}}
"""


NOT_FOUND = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Page not found – Henrik Hedvall</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/css/base.css">
<script>(function(){try{var t=sessionStorage.getItem("theme")||localStorage.getItem("theme");if(t==="dk"||t==="lt")document.documentElement.classList.add(t)}catch(e){}})();</script>
</head>
<body>
<main class="pg nf">
<p class="nf-name"><a href="/">Henrik Hedvall</a></p>
<h1>This page does not exist.</h1>
<p><a class="nf-link" href="/">Back to the start page</a></p>
</main>
</body>
</html>
'''


def header(is_main):
    home = "#page" if is_main else "[[R]]"
    pre = "" if is_main else "[[R]]"
    links = "\n".join(f'<a href="{pre}#{k}">{t}</a>' for k, t in [("work", "Work"), ("services", "Services"), ("about", "About"), ("contact", "Contact")])
    return f'''<header class="hdr" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px 40px; padding: 36px 0">
<a href="{home}" style="font-size: 16px; font-weight: 600">Henrik Hedvall</a>
<nav aria-label="Main menu" style="display: flex; flex-wrap: wrap; gap: 8px 36px; font-size: 16px">
{links}
</nav>
</header>'''


def build():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    variants = optimize.make_variants(os.path.join(ROOT, "assets"), os.path.join(ROOT, "_variants"), os.path.join(DIST, "assets"),
                                      keep_original={p[6] for p in PAGES})
    shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(DIST, "fonts"))
    styles = optimize.Styles({PG: "c-page", WRAP: "c-wrap", H3: "c-h3", LBL: "c-eyebrow",
                              **{re.search(r'style="([^"]*)"', TOKENS[k]).group(1): n for k, n in
                                 [("SA", "c-sec-first"), ("SR", "c-sec-row"), ("SC", "c-sec-col"), ("SC2", "c-sec-col-wide"), ("GRID2", "c-grid2")]}})
    os.makedirs(os.path.join(DIST, "css"))
    base = open(os.path.join(ROOT, "css", "base.css"), encoding="utf-8").read()
    base += "@media (prefers-color-scheme: dark){\n" + theme_css("html:not(.lt)") + "}\n" + theme_css("html.dk")
    open(os.path.join(DIST, "css", "base.css"), "w", encoding="utf-8").write(base)
    for f in os.listdir(os.path.join(ROOT, "css")):
        if f != "base.css":
            shutil.copyfile(os.path.join(ROOT, "css", f), os.path.join(DIST, "css", f))
    shutil.copytree(os.path.join(ROOT, "js"), os.path.join(DIST, "js"))
    open(os.path.join(DIST, "favicon.svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#F5F5F3"/><circle cx="16" cy="16" r="7" fill="#2F5D4B"/></svg>')
    open(os.path.join(DIST, ".nojekyll"), "w").write("")
    from PIL import Image, ImageDraw
    icon = Image.new("RGB", (720, 720), "#F5F5F3")
    ImageDraw.Draw(icon).ellipse((205, 205, 515, 515), fill="#2F5D4B")
    icon.resize((180, 180), Image.LANCZOS).save(os.path.join(DIST, "apple-touch-icon.png"))
    open(os.path.join(DIST, "404.html"), "w", encoding="utf-8").write(NOT_FOUND)
    if DOMAIN:
        urls = [f"https://{DOMAIN}/" + (os.path.dirname(p[1]) + "/" if "/" in p[1] else "") for p in PAGES]
        open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
        open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: https://{DOMAIN}/sitemap.xml\n")
    if DOMAIN:
        open(os.path.join(DIST, "CNAME"), "w").write(DOMAIN + "\n")
    for src, out, title, desc, css, fonts, share, rvt in PAGES:
        depth = out.count("/")
        R = "../" * depth
        is_main = src == "main"
        body = open(os.path.join(ROOT, "pages", src + ".html"), encoding="utf-8").read()
        bar = "" if is_main else '<div aria-hidden="true" class="bar" style="transform: scaleX(0)"></div>\n'
        page_css = f'<link rel="stylesheet" href="{R}css/{css}">\n' if css else ""
        og_img = f'<meta property="og:image" content="https://{DOMAIN}/assets/{share}">\n' if DOMAIN else ""
        url = f"https://{DOMAIN}/" + (os.path.dirname(out) + "/" if "/" in out else "")
        seo = f'<link rel="canonical" href="{url}">\n<meta property="og:url" content="{url}">\n' if DOMAIN else ""
        if is_main and DOMAIN:
            seo += '<script type="application/ld+json">' + json.dumps({
                "@context": "https://schema.org", "@graph": [
                    {"@type": "Person", "@id": f"https://{DOMAIN}/#henrik", "name": "Henrik Hedvall", "jobTitle": "Freelance product designer",
                     "url": f"https://{DOMAIN}/", "image": f"https://{DOMAIN}/assets/henrik.webp",
                     "sameAs": ["https://www.linkedin.com/in/henrikhedvall/"],
                     "address": {"@type": "PostalAddress", "addressLocality": "Åre", "addressCountry": "SE"},
                     "knowsAbout": ["Product design", "Design systems", "UX design", "UI design", "Fintech"]},
                    {"@type": "WebSite", "@id": f"https://{DOMAIN}/#site", "url": f"https://{DOMAIN}/", "name": "Henrik Hedvall", "inLanguage": "en",
                     "publisher": {"@id": f"https://{DOMAIN}/#henrik"}}]}, ensure_ascii=False) + "</script>\n"
        html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
{og_img}{seo}<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F5F5F3">
<link rel="icon" href="{R}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{R}apple-touch-icon.png">
<link rel="preload" href="{R}fonts/familjen-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{R}css/base.css">
{page_css}<link rel="stylesheet" href="{R}css/site.css">
<script>(function(){{try{{var t=sessionStorage.getItem("theme")||localStorage.getItem("theme");if(t==="dk"||t==="lt")document.documentElement.classList.add(t)}}catch(e){{}}}})();</script>
<noscript><style>.rv{{opacity:1!important}}.rv .zm,.rv .st,.rv .bl{{transform:none!important}}.rv .st span{{opacity:1!important}}.rv .ck path{{stroke-dashoffset:0!important}}.ic .s{{stroke-dashoffset:0!important}}.ic .nd{{transform:none!important}}</style></noscript>
</head>
<body data-rvt="{rvt}">
<div class="pg" id="page" style="{PG}">
{bar}<div style="{WRAP}">

{header(is_main)}

{body}

</div>
</div>
<script src="{R}js/site.js" defer></script>
</body>
</html>
'''
        html = expand(html).replace("[[CONTACT_ADDR]]", CONFIG["contact"]).replace("[[A]]", R + "assets/").replace("[[R]]", R or "./")
        html = styles.apply(optimize.responsive_images(html, src, variants))
        left = re.findall(r"\[\[[A-Z0-9]+\]\]|@[A-Z0-9]+\{|/_blob/|\{\{", html)
        if left:
            sys.exit(f"{src}: unresolved {sorted(set(left))}")
        os.makedirs(os.path.dirname(os.path.join(DIST, out)) or DIST, exist_ok=True)
        open(os.path.join(DIST, out), "w", encoding="utf-8").write(html)
        print("built", out, len(html))
    open(os.path.join(DIST, "css", "site.css"), "w", encoding="utf-8").write(styles.css())


PROTECT = False  # True: publish the password-protected build (needs .secret.json). False: publish the open site.

if __name__ == "__main__":
    build()
    if PROTECT:
        import protect
        protect.run(ROOT, DIST, PAGES, DOMAIN)
    else:
        out = os.path.join(ROOT, "docs")
        shutil.rmtree(out, ignore_errors=True)
        shutil.copytree(DIST, out)
        gate = os.path.join(out, "js", "gate.js")
        if os.path.exists(gate):
            os.remove(gate)  # only used by the protected build
        print("published open site to docs/")
