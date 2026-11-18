"""Captures the write-on as PNG frames. Usage: python3 capture.py <out dir> '<setup json>' [frame,frame,...]"""
import asyncio, sys, os, json
from playwright.async_api import async_playwright
OUT=sys.argv[1]; CFG=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}; os.makedirs(OUT,exist_ok=True)
W=CFG.get("W",2640); H=CFG.get("H",1650)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
        pg=await b.new_page(viewport={"width":W,"height":H}); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+os.path.abspath("render.html")); await pg.evaluate("c=>setup(c)",CFG)
        frames=[int(x) for x in sys.argv[3].split(",")] if len(sys.argv)>3 else range(150)
        for n in frames:
            info=await pg.evaluate(f"frame({n}/30)")
            await pg.screenshot(path=f"{OUT}/f{n:03d}.png",clip={"x":0,"y":0,"width":W,"height":H},omit_background=CFG.get("bg") is False)
            if n%30==0 or len(sys.argv)>3: print(n,json.dumps({k:(round(v,3) if isinstance(v,float) else v) for k,v in info.items()}))
        print("errors",errs); await b.close()
asyncio.run(main())
