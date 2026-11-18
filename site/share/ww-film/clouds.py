"""Slow, looping cloud drift made from a still image.
The clouds are moved a few pixels along a smooth flow field; everything with fine detail (rock, snow, shoreline) is held still.
The loop is seamless: each frame blends a few copies of the image at different stages of the drift."""
import numpy as np, cv2

def cloud_mask(img, lo=2.2, span=3.0, peak=True):
    """0..1 map of where drifting is allowed: hand-placed cloud regions minus anything with fine detail."""
    h, w = img.shape[:2]; sx, sy = w / 2400, h / 1500
    m = np.zeros((h, w), np.float32)
    P = lambda pts: np.int32([[x * sx, y * sy] for x, y in pts])
    cv2.fillPoly(m, [P([(0, 290), (420, 330), (760, 370), (1060, 420), (1110, 560), (1050, 720), (1010, 960), (900, 1110), (620, 1220), (0, 1300)])], 1.0)   # fog bank on the left
    cv2.fillPoly(m, [P([(0, 0), (2400, 0), (2400, 120), (2050, 200), (1500, 230), (900, 250), (0, 240)])], 1.0)                                            # cloud band along the top
    if peak: cv2.ellipse(m, (int(1900 * sx), int(290 * sy)), (int(230 * sx), int(150 * sy)), 0, 0, 360, 1.0, -1)                                                   # cloud behind the peak
    cv2.ellipse(m, (int(1410 * sx), int(670 * sy)), (int(180 * sx), int(110 * sy)), -20, 0, 360, 1.0, -1)                                                 # wisp on the ridge
    m = cv2.GaussianBlur(m, (0, 0), 40 * sx)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    detail = cv2.GaussianBlur(np.abs(g - cv2.GaussianBlur(g, (0, 0), 3 * sx)), (0, 0), 10 * sx)
    still = np.clip((detail - lo) / span, 0, 1)             # rock, snow patches and shoreline
    still = cv2.GaussianBlur(cv2.dilate(still, np.ones((int(15 * sx) | 1,) * 2, np.uint8)), (0, 0), 12 * sx)
    return np.clip(m * (1 - still), 0, 1), detail

def flow_field(mask, travel, seed=3):
    """Per-pixel drift over one loop, in pixels. Mostly to the right and a little upwards, with slow variation so the clouds do not move as one sheet."""
    h, w = mask.shape; rng = np.random.default_rng(seed)
    def noise(scale):
        n = rng.random((max(2, h // scale + 2), max(2, w // scale + 2))).astype(np.float32)
        return cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    speed = 0.65 + 0.7 * noise(420)
    ang = np.deg2rad(-14 + 26 * (noise(520) - 0.5))
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    speed = speed * (0.55 + 0.45 * np.clip((y - 0.12) / 0.2, 0, 1))      # the high clouds drift more slowly than the fog
    fx = travel * speed * np.cos(ang) * mask; fy = travel * speed * np.sin(ang) * mask
    return fx.astype(np.float32), fy.astype(np.float32)

def frames(img, n, travel, layers=3, detail_travel=None, sigma=16, lo=2.2, span=3.0):
    """Yields n float32 frames of one seamless loop.
    Several copies of the image drift along the flow, each fading in as it enters and out as it leaves.
    Their phases are evenly spread, so the softness of the clouds stays the same through the whole loop.
    The image is split in two: the soft cloud shapes (a blurred copy) travel the full distance, while fine texture and edges
    travel only detail_travel. Blending shifted copies of something sharp shows as stripes; of something soft it does not."""
    h, w = img.shape[:2]
    mask, _ = cloud_mask(img, lo, span, peak=False)   # the small cloud behind the peak is not carried along: against open sky its soft shape and its detail drift apart into a halo
    k = w / 2400
    fx, fy = flow_field(mask, travel * k)
    if detail_travel is None: detail_travel = travel
    r = detail_travel / travel
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    src = img.astype(np.float32)
    low = cv2.GaussianBlur(src, (0, 0), sigma * k); high = src - low
    for i in range(n):
        out = np.zeros_like(src); total = 0.0
        for j in range(layers):
            p = (i / n + j / layers) % 1.0
            wgt = 0.5 - 0.5 * np.cos(2 * np.pi * p)
            if wgt < 1e-4: continue
            d = p - 0.5
            f = cv2.remap(low, gx - fx * d, gy - fy * d, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            f += cv2.remap(high, gx - fx * d * r, gy - fy * d * r, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT) if r > 0 else high
            out += wgt * f
            total += wgt
        yield out / total

def _noise(h, w, cell, seed):
    """Smooth fractal noise, zero mean and unit spread, with features of about `cell` pixels."""
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0
    for o in range(3):
        c = max(4, int(cell / 2 ** o))
        n = rng.standard_normal((h // c + 3, w // c + 3)).astype(np.float32)
        out += amp * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC); amp *= 0.5
    out -= out.mean(); return out / out.std()

def drift(img, n, strength=0.1, layers=((260, 330, -50, 11), (120, 210, -20, 12)), dark=1.0):
    """Yields n gain maps (float32, about 1) for one seamless loop: soft patches of thicker and thinner fog that slide across the cloud areas.
    Each layer is (feature size, travel x, travel y, seed), in pixels per loop at 2400 px width. A layer is drawn twice, half a loop apart,
    and cross-faded at constant contrast; the two copies are so far apart that they share no pattern, so the fade leaves no stripes."""
    h, w = img.shape[:2]; k = w / 2400
    mask, _ = cloud_mask(img, 0.9, 1.2)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    mask = mask * (0.45 + 0.55 * np.clip((y - 0.12) / 0.2, 0, 1))        # weaker on the high clouds
    warm = cv2.GaussianBlur(img[..., 0].astype(np.float32) - img[..., 2].astype(np.float32), (0, 0), 6 * k)
    mask = mask * np.clip((warm + 25) / 20, 0, 1)                        # only on the clouds themselves, which are warmer than the blue sky; on open sky the patches read as a glow
    pad = int(600 * k)
    fields = [(_noise(h + 2 * pad, w + 2 * pad, cell * k, seed), tx * k, ty * k) for cell, tx, ty, seed in layers]
    for i in range(n):
        tot = np.zeros((h, w), np.float32)
        for f, tx, ty in fields:
            acc = np.zeros((h, w), np.float32); pw = 0.0
            for j in range(2):
                p = (i / n + j / 2) % 1.0
                wg = 0.5 - 0.5 * np.cos(2 * np.pi * p)
                d = p - 0.5
                M = np.float32([[1, 0, -pad + tx * d], [0, 1, -pad + ty * d]])
                acc += wg * cv2.warpAffine(f, M, (w, h), flags=cv2.INTER_LINEAR); pw += wg * wg
            tot += acc / np.sqrt(pw)
        v = tot / np.sqrt(len(fields))
        v = np.where(v > 0, v, dark * v)          # dark < 1: the patches mostly lighten; dark patches read as smoke
        yield np.exp(strength * mask * v)

def apply_gain(frame, gain):
    """Brightens or darkens without shifting hue: where a channel would clip, the whole pixel is held back instead."""
    mx = np.maximum(frame.max(2), 1.0)
    want = mx * gain
    soft = np.where(want > 238, 238 + (255 - 238) * np.tanh((want - 238) / (255 - 238)), want)
    return frame * (np.minimum(soft, 255.0) / mx)[..., None]
