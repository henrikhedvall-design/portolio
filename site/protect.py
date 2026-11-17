"""Encrypts the plain build (./_plain) into a password-protected site (./docs).

Every page body and every image/film is encrypted with AES-256-GCM. The key is derived from the
password with PBKDF2-SHA256. Password and salt live in .secret.json, which is never published."""
import base64, hashlib, hmac, json, os, re, shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

GATE_CSS = """
.gate{min-height:100vh;min-height:100dvh;display:flex;align-items:center;justify-content:center;box-sizing:border-box;padding:24px;font-family:'Familjen Grotesk','Helvetica Neue',Arial,sans-serif;font-size:18px;line-height:1.5;color:#111110;-webkit-font-smoothing:antialiased}
.gate form{width:100%;max-width:360px;display:flex;flex-direction:column;gap:20px}
.gate h1{margin:0;font-size:16px;font-weight:600}
.gate p{margin:0;font-size:clamp(23px,2.6vw,30px);line-height:1.2;letter-spacing:-.025em;font-weight:500}
.gate label{display:flex;flex-direction:column;gap:8px;font-size:16px;color:#5E5E5A}
.gate input{font:inherit;color:inherit;background:transparent;border:0;border-bottom:1px solid #111110;border-radius:0;padding:8px 0;outline:none}
.gate input:focus-visible{border-color:var(--accent);box-shadow:0 1px 0 var(--accent)}
.gate button{align-self:flex-start;font:inherit;font-size:16px;color:#F5F5F3;background:var(--accent);border:0;border-radius:999px;padding:10px 22px;cursor:pointer}
.gate button:disabled{opacity:.6;cursor:default}
.gate .msg{min-height:1.5em;font-size:16px;color:#5E5E5A}
.gate[hidden]{display:none}
@media (prefers-color-scheme: dark){html:not(.lt) .gate{color:#EDEDE9}html:not(.lt) .gate input{border-color:#EDEDE9}html:not(.lt) .gate label,html:not(.lt) .gate .msg{color:#9C9C96}}
html.dk .gate{color:#EDEDE9}html.dk .gate input{border-color:#EDEDE9}html.dk .gate label,html.dk .gate .msg{color:#9C9C96}
"""

GATE_HTML = """<div class="gate" id="gate" hidden>
<form id="gate-form" autocomplete="off">
<h1>Henrik Hedvall</h1>
<p>This portfolio is password protected.</p>
<label>Password<input id="gate-pw" type="password" autocomplete="current-password" autocapitalize="none" autocorrect="off" spellcheck="false" required></label>
<button type="submit">Enter</button>
<div class="msg" id="gate-msg" role="status" aria-live="polite"></div>
</form>
</div>"""


def run(root, plain, pages, domain):
    sec = json.load(open(os.path.join(root, ".secret.json")))
    salt = base64.b64decode(sec["salt"])
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=sec["iter"]).derive(sec["password"].strip().lower().encode("utf-8"))
    aes = AESGCM(key)

    def enc(data):
        iv = hmac.new(key, b"iv" + hashlib.sha256(data).digest(), hashlib.sha256).digest()[:12]
        return iv + aes.encrypt(iv, data, None)

    def name(label):
        return hmac.new(key, label.encode(), hashlib.sha256).hexdigest()[:20]

    out = os.path.join(root, "docs")
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "a"))
    os.makedirs(os.path.join(out, "p"))
    shutil.copytree(os.path.join(plain, "css"), os.path.join(out, "css"))
    shutil.copytree(os.path.join(plain, "js"), os.path.join(out, "js"))
    shutil.copytree(os.path.join(plain, "fonts"), os.path.join(out, "fonts"))
    for f in ["favicon.svg", ".nojekyll", "CNAME", "apple-touch-icon.png", "404.html"]:
        if os.path.exists(os.path.join(plain, f)):
            shutil.copyfile(os.path.join(plain, f), os.path.join(out, f))
    with open(os.path.join(out, "robots.txt"), "w") as fh:
        fh.write("User-agent: *\nDisallow: /\n")

    ver = hashlib.sha256(b"".join(open(os.path.join(dp, f), "rb").read() for dp, _, fs in sorted(os.walk(out)) for f in sorted(fs) if f.endswith((".js", ".css")))).hexdigest()[:10]

    assets = {}
    for f in sorted(os.listdir(os.path.join(plain, "assets"))):
        ext = f.rsplit(".", 1)[1]
        data = open(os.path.join(plain, "assets", f), "rb").read()
        aid = name("asset:" + f + ":" + hashlib.sha256(data).hexdigest())  # name changes with content, so browsers never show a stale file
        assets[f] = aid + "." + ext
        open(os.path.join(out, "a", aid + ".bin"), "wb").write(enc(data))

    for src, path, title, desc, css, fonts, share, rvt in pages:
        html = open(os.path.join(plain, path), encoding="utf-8").read()
        depth = path.count("/")
        R = "../" * depth
        body = re.search(r"<body[^>]*>(.*)<script src=[^>]*site\.js", html, re.S).group(1).strip()
        def srcset(m):
            items = [i.strip().rsplit(" ", 1) for i in m.group(1).split(",")]
            return 'data-e-set="' + ",".join(assets[u.rsplit("assets/", 1)[1]] + " " + w.rstrip("w") for u, w in items) + '"'
        body = re.sub(r'\bsrcset="([^"]+)"\s+sizes="[^"]*"', srcset, body)
        body = re.sub(r'\s(?:loading="lazy"|decoding="async"|fetchpriority="high")', "", body)
        body, n = re.subn(r'\b(src|poster|href|data-lbsrc)="(?:\.\./)*assets/([^"]+)"', lambda m: f'data-e-{m.group(1)}="{assets[m.group(2)]}"', body)
        if "assets/" in body:
            raise SystemExit(f"{src}: unprotected asset reference left")
        pid = name("page:" + src)
        payload = json.dumps({"title": title, "html": body}, ensure_ascii=False).encode("utf-8")
        open(os.path.join(out, "p", pid + ".bin"), "wb").write(enc(payload))
        page_css = f'<link rel="stylesheet" href="{R}css/{css}?v={ver}">\n' if css else ""
        cfg = json.dumps({"salt": sec["salt"], "iter": sec["iter"], "page": pid, "root": R, "days": 30, "v": ver})
        shell = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Henrik Hedvall</title>
<link rel="icon" href="{R}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{R}apple-touch-icon.png">
<meta name="theme-color" content="#F5F5F3">
<link rel="preload" href="{R}fonts/familjen-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{R}css/base.css?v={ver}">
{page_css}<link rel="stylesheet" href="{R}css/site.css?v={ver}">
<style>{GATE_CSS}</style>
<script>(function(){{try{{var t=sessionStorage.getItem("theme")||localStorage.getItem("theme");if(t==="dk"||t==="lt")document.documentElement.classList.add(t)}}catch(e){{}}}})();</script>
</head>
<body data-rvt="{rvt}">
{GATE_HTML}
<div id="app"></div>
<noscript><p style="font-family: sans-serif; padding: 24px">This site needs JavaScript.</p></noscript>
<script>window.__P={cfg};</script>
<script src="{R}js/gate.js?v={ver}"></script>
</body>
</html>
'''
        os.makedirs(os.path.dirname(os.path.join(out, path)) or out, exist_ok=True)
        open(os.path.join(out, path), "w", encoding="utf-8").write(shell)
        print("protected", path, f"({n} assets)")
