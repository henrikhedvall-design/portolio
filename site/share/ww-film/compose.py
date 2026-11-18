"""Builds the Weekend Warriors hero film: drifting clouds behind the wordmark writing itself.
Usage: python3 compose.py out.mp4 [crf] [cloud travel in px per loop at 2400 px width]"""
import sys, subprocess, numpy as np
from PIL import Image
from clouds import frames
OUT=sys.argv[1]; CRF=sys.argv[2] if len(sys.argv)>2 else "21"; TRAVEL=float(sys.argv[3]) if len(sys.argv)>3 else 16
N=150
bg=np.asarray(Image.open("bg.png").convert("RGB"))
H,W=bg.shape[:2]
wr=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","-",*(["-c:v","libx264rgb","-preset","ultrafast","-crf","0",OUT] if OUT.endswith(".mkv") else ["-c:v","libx264","-preset","slow","-crf",CRF,"-pix_fmt","yuv420p","-movflags","+faststart","-an",OUT])],stdin=subprocess.PIPE)
for i,f in enumerate(frames(bg,N,TRAVEL)):
    ink=np.asarray(Image.open(f"ink/f{i:03d}.png").convert("RGBA")).astype(np.float32)
    a=ink[...,3:4]/255
    out=np.clip(np.rint(f*(1-a)+ink[...,:3]*a),0,255).astype(np.uint8)
    wr.stdin.write(out.tobytes())
    if i in (0,75,110,149): Image.fromarray(out).save(f"out{i:03d}.png")
wr.stdin.close(); wr.wait()
