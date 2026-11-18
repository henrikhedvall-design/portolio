"""Slow, looping cloud drift made from a still image.
The clouds are moved a few pixels along a smooth flow field; everything with fine detail (rock, snow, shoreline) is held still.
The loop is seamless: each frame blends a few copies of the image at different stages of the drift."""
import numpy as np, cv2

def cloud_mask(img):
    """0..1 map of where drifting is allowed: hand-placed cloud regions minus anything with fine detail."""
    h, w = img.shape[:2]; sx, sy = w / 2400, h / 1500
    m = np.zeros((h, w), np.float32)
    P = lambda pts: np.int32([[x * sx, y * sy] for x, y in pts])
    cv2.fillPoly(m, [P([(0, 290), (420, 330), (760, 370), (1060, 420), (1110, 560), (1050, 720), (1010, 960), (900, 1110), (620, 1220), (0, 1300)])], 1.0)   # fog bank on the left
    cv2.fillPoly(m, [P([(0, 0), (2400, 0), (2400, 120), (2050, 200), (1500, 230), (900, 250), (0, 240)])], 1.0)                                            # cloud band along the top
    cv2.ellipse(m, (int(1900 * sx), int(290 * sy)), (int(230 * sx), int(150 * sy)), 0, 0, 360, 1.0, -1)                                                   # cloud behind the peak
    cv2.ellipse(m, (int(1410 * sx), int(670 * sy)), (int(180 * sx), int(110 * sy)), -20, 0, 360, 1.0, -1)                                                 # wisp on the ridge
    m = cv2.GaussianBlur(m, (0, 0), 40 * sx)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    detail = cv2.GaussianBlur(np.abs(g - cv2.GaussianBlur(g, (0, 0), 3 * sx)), (0, 0), 10 * sx)
    still = np.clip((detail - 2.2) / 3.0, 0, 1)             # rock, snow patches and shoreline
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

def frames(img, n, travel, layers=3):
    """Yields n float32 frames of one seamless loop.
    Several copies of the image drift along the flow, each fading in as it enters and out as it leaves.
    Their phases are evenly spread, so the softness of the clouds stays the same through the whole loop."""
    h, w = img.shape[:2]
    mask, _ = cloud_mask(img)
    fx, fy = flow_field(mask, travel * w / 2400)
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    src = img.astype(np.float32)
    for i in range(n):
        out = np.zeros_like(src); total = 0.0
        for k in range(layers):
            p = (i / n + k / layers) % 1.0
            wgt = 0.5 - 0.5 * np.cos(2 * np.pi * p)
            if wgt < 1e-4: continue
            d = p - 0.5
            out += wgt * cv2.remap(src, gx - fx * d, gy - fy * d, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            total += wgt
        yield out / total
