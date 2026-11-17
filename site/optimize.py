"""Post-processing for the built pages: responsive image variants and inline styles moved to classes."""
import hashlib, os, re
from PIL import Image

WIDTHS = [800, 1400]
NO_VARIANTS = re.compile(r"^(tink-circle-|tink-dot-|ww-skier|.*-poster\.)")
HALF = {"oqto-type", "tink-colours", "tink-poster", "atlar", "qapital", "klarna", "romo-bygg", "svartanatt", "sas"}
CARD = {"klarna", "qapital", "atlar", "romo-bygg", "svartanatt", "henrik"}
SIZES = {
    "full": "(min-width: 1440px) 1200px, 92vw",
    "half": "(min-width: 1440px) 600px, (min-width: 900px) 46vw, 92vw",
    "main": "(min-width: 1440px) 900px, (min-width: 1000px) 62vw, 92vw",
    "card": "(min-width: 1440px) 440px, (min-width: 700px) 46vw, 92vw",
}


def make_variants(src_dir, cache_dir, out_dir, keep_original=()):
    """Writes WebP variants of every raster image into out_dir. Returns {original name: [(file, width), ...]} (ascending)."""
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    variants = {}
    for f in sorted(os.listdir(src_dir)):
        path = os.path.join(src_dir, f)
        base, ext = f.rsplit(".", 1)
        if ext not in ("jpg", "png") or NO_VARIANTS.match(f):
            _copy(path, os.path.join(out_dir, f))
            continue
        if f in keep_original:
            _copy(path, os.path.join(out_dir, f))
        data = open(path, "rb").read()
        tag = hashlib.sha256(data).hexdigest()[:10]
        im = None
        full_only = base.endswith("-full")
        out = []
        with Image.open(path) as probe:
            W = probe.width
        for w in ([] if full_only else [w for w in WIDTHS if w < W * 0.8]) + [W]:
            name = f"{base}.webp" if w == W else f"{base}-{w}.webp"
            cached = os.path.join(cache_dir, f"{tag}-{name}")
            if not os.path.exists(cached):
                if im is None:
                    im = Image.open(path).convert("RGB")
                v = im if w == W else im.resize((w, round(im.height * w / W)), Image.LANCZOS)
                v.save(cached, "WEBP", quality=90 if ext == "png" else 80, method=6)
            _copy(cached, os.path.join(out_dir, name))
            out.append((name, w))
        variants[f] = out
    return variants


def _copy(a, b):
    with open(a, "rb") as fa, open(b, "wb") as fb:
        fb.write(fa.read())


def responsive_images(html, page, variants):
    first = [True]

    def rep(m):
        tag = m.group(0)
        sm = re.search(r'\ssrc="((?:\.\./)*assets/)([^"]+)"', tag)
        if not sm:
            return tag
        prefix, name = sm.group(1), sm.group(2)
        lb = re.search(r'\sdata-lbsrc="(?:\.\./)*assets/([^"]+)"', tag)
        if lb and lb.group(1) in variants:
            tag = tag.replace(lb.group(0), f' data-lbsrc="{prefix}{variants[lb.group(1)][-1][0]}"')
        if name not in variants:
            return tag
        vs = variants[name]
        base = name.rsplit(".", 1)[0]
        kind = "full"
        if page == "main":
            kind = "card" if base in CARD else "main"
        elif base in HALF:
            kind = "half"
        mid = next((v for v in vs if v[1] >= 1400), vs[-1])
        attrs = f' src="{prefix}{mid[0]}"'
        if len(vs) > 1:
            attrs += ' srcset="' + ", ".join(f"{prefix}{n} {w}w" for n, w in vs) + f'" sizes="{SIZES[kind]}"'
        if page != "main" and not lb:
            attrs += f' data-lbsrc="{prefix}{vs[-1][0]}"'
        attrs += ' fetchpriority="high"' if first[0] else ' loading="lazy"'
        attrs += ' decoding="async"'
        first[0] = False
        return tag.replace(sm.group(0), attrs, 1)

    return re.sub(r"<img\b[^>]*>", rep, html)


DARK = [
    (("background: #F5F5F3", "background: rgb(245, 245, 243)", "background-color: rgb(245, 245, 243)"), "background:#121211"),
    (("color: #111110", "color: rgb(17, 17, 16)"), "color:#EDEDE9"),
    (("color: #5E5E5A", "color: rgb(94, 94, 90)"), "color:#9C9C96"),
    (("#D9D9D4", "rgb(217, 217, 212)"), "border-color:#2A2A28"),
    (("background: #E7E7E3", "background: rgb(231, 231, 227)", "background-color: rgb(231, 231, 227)"), "background:#1C1C1A"),
]


READABLE = {
    "8a4162": "muted", "ab63ad": "clip", "5f1f52": "w400", "61b2a4": "w700", "324e4a": "stack", "6f19eb": "step-body",
    "8e4c8a": "media", "de52e3": "m0", "0e072a": "sec-end", "8a2133": "row", "ad02d1": "step-text", "9d4f72": "h3-small",
    "c93b2e": "note", "c2a321": "figure", "863cff": "caption", "ab72d8": "header", "4e75d6": "brand", "ff3247": "nav",
    "e1bd00": "years", "6cb5e0": "step-label", "0c2875": "card", "940390": "svc-head", "d5822d": "body-muted", "cc8f91": "job",
    "5f5724": "bar-start", "ac58fa": "top", "d4ebab": "top-body", "bba02c": "title", "f0cf39": "lead", "1f74c8": "next-link",
    "444791": "contact-body", "93c4ff": "muted-p", "579b24": "link-underline", "c001d9": "footer",
}


class Styles:
    """Collects inline style strings across pages and turns them into classes."""

    def __init__(self, names):
        self.names = dict(names)   # style string -> class name
        self.used = {}             # class name -> style string (in first-seen order)

    def cls(self, style):
        style = style.strip().rstrip(";")
        name = self.names.get(style)
        if not name:
            h = hashlib.sha256(style.encode()).hexdigest()[:6]
            name = "c-" + READABLE.get(h, h)
            self.names[style] = name
        self.used.setdefault(name, style)
        return name

    def apply(self, html):
        def rep(m):
            tag = m.group(0)
            sm = re.search(r'\sstyle="([^"]*)"', tag)
            if not sm:
                return tag
            name = self.cls(sm.group(1))
            tag = tag.replace(sm.group(0), "", 1)
            cm = re.search(r'\sclass="([^"]*)"', tag)
            if cm:
                return tag.replace(cm.group(0), f' class="{cm.group(1)} {name}"', 1)
            return re.sub(r"^<([a-zA-Z0-9-]+)", lambda t: f'<{t.group(1)} class="{name}"', tag, 1)

        head, sep, body = html.partition("<body")
        return head + sep + re.sub(r"<[a-zA-Z][^<>]*\sstyle=\"[^\"]*\"[^<>]*>", rep, body)

    def css(self):
        out, dark = [], []
        for name, style in self.used.items():
            out.append(f".{name}{{{style}}}")
            fixes = [fix for keys, fix in DARK if any(k in style for k in keys)]
            if fixes:
                dark.append((name, ";".join(f + " !important" for f in fixes)))
        rules = "\n".join(out) + "\n"
        rules += "@media (prefers-color-scheme: dark){\n" + "\n".join(f"html:not(.lt) .{n}{{{d}}}" for n, d in dark) + "\n}\n"
        rules += "\n".join(f"html.dk .{n}{{{d}}}" for n, d in dark) + "\n"
        return rules
