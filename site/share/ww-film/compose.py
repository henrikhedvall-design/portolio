"""Builds the Weekend Warriors hero film: drifting clouds behind the wordmark writing itself.
Usage: python3 compose.py out.mkv|out.mp4 [crf]
The cloud motion has two parts (see clouds.py): the soft cloud shapes are carried along a flow field, and patches of thicker
and thinner fog slide across them. Fine detail barely moves, because blended copies of sharp texture show as stripes."""
import sys, subprocess, numpy as np
from PIL import Image
from clouds import frames, drift, apply_gain
OUT=sys.argv[1]; CRF=sys.argv[2] if len(sys.argv)>2 else "22"
N=150
WARP=dict(travel=90,layers=4,detail_travel=20,sigma=10,lo=0.9,span=1.2)
DRIFT=dict(strength=0.10,layers=((340,330,-50,11),(150,210,-20,12)),dark=0.2)
bg=np.asarray(Image.open("bg.png").convert("RGB"))
H,W=bg.shape[:2]
wr=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","-",*(["-c:v","libx264rgb","-preset","ultrafast","-crf","0",OUT] if OUT.endswith(".mkv") else ["-c:v","libx264","-preset","slow","-crf",CRF,"-pix_fmt","yuv420p","-movflags","+faststart","-an",OUT])],stdin=subprocess.PIPE)
for i,(f,g) in enumerate(zip(frames(bg,N,**WARP),drift(bg,N,**DRIFT))):
    f=apply_gain(f,g)
    ink=np.asarray(Image.open(f"ink/f{i:03d}.png").convert("RGBA")).astype(np.float32)
    a=ink[...,3:4]/255
    out=np.clip(np.rint(f*(1-a)+ink[...,:3]*a),0,255).astype(np.uint8)
    wr.stdin.write(out.tobytes())
    if i in (0,75,110,149): Image.fromarray(out).save(f"out{i:03d}.png")
wr.stdin.close(); wr.wait()
