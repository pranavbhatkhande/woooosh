"""
"Ad infinitum" sync demo — 25 rounds of back-and-forth, always converging.

Runs against the local sync server in STRONG consistency mode (SYNC_STALE_MS=0),
which is exactly what the deployed Netlify function now uses
(getStore({ consistency: "strong" })).

Each round:
  • Device A adds a task
  • Device B adds a task
  • Both sync until their task lists are identical
  • A side-by-side frame is captured

Produces demo/demo_infinite.mp4 and asserts every round converges.
"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"], check=True)
    from PIL import Image, ImageDraw, ImageFont

OUT   = "/home/user/woooosh/demo"
CHROM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP   = "http://localhost:3000"
ROUNDS = 25
os.makedirs(OUT, exist_ok=True)

FRAMES = []


def _font(sz, bold=True):
    base = "/usr/share/fonts/truetype/dejavu/"
    try:
        return ImageFont.truetype(base + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)
    except Exception:
        return ImageFont.load_default()


def sidebyside(lp, rp, out, label_l, label_r, sub_l="", sub_r=""):
    L = Image.open(lp).convert("RGBA")
    R = Image.open(rp).convert("RGBA")
    h = max(L.height, R.height)
    L = L.resize((int(L.width * h / L.height), h), Image.LANCZOS)
    R = R.resize((int(R.width * h / R.height), h), Image.LANCZOS)
    bar = 46
    cv = Image.new("RGBA", (L.width + R.width + 8, h + bar), (247, 248, 250, 255))
    d = ImageDraw.Draw(cv)
    d.rectangle([0, 0, L.width + 3, bar], fill=(79, 70, 229, 255))
    d.rectangle([L.width + 4, 0, cv.width, bar], fill=(16, 185, 129, 255))
    d.text((16, 7), label_l, fill=(255, 255, 255, 255), font=_font(14))
    d.text((16, 27), sub_l, fill=(210, 220, 255, 255), font=_font(11, False))
    d.text((L.width + 20, 7), label_r, fill=(255, 255, 255, 255), font=_font(14))
    d.text((L.width + 20, 27), sub_r, fill=(210, 255, 225, 255), font=_font(11, False))
    cv.paste(L, (0, bar)); cv.paste(R, (L.width + 8, bar))
    cv.convert("RGB").save(out)
    return out


def title_card(text, sub, out, w=1808, h=766):
    img = Image.new("RGB", (w, h), (30, 30, 46))
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), text, font=_font(34))
    d.text(((w - (bb[2] - bb[0])) // 2, h // 2 - 40), text, fill=(255, 255, 255), font=_font(34))
    if sub:
        bb2 = d.textbbox((0, 0), sub, font=_font(18, False))
        d.text(((w - (bb2[2] - bb2[0])) // 2, h // 2 + 18), sub, fill=(150, 160, 200), font=_font(18, False))
    img.save(out)
    return out


def frame(p, hold): FRAMES.append((p, hold))


TASKS_JS = """
(() => {
    const items = document.querySelectorAll('.task-item');
    return { count: items.length, ids: [...items].map(el => el.dataset.id),
             label: document.getElementById('syncLabel')?.textContent || '?' };
})()
"""


async def info(page): return await page.evaluate(TASKS_JS)


async def settle(page, timeout_ms=8000):
    start = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start) * 1000 < timeout_ms:
        if await page.evaluate("document.getElementById('syncLabel')?.textContent") != 'Syncing…':
            return
        await page.wait_for_timeout(120)


async def converge(a, b, max_syncs=4, gap=250):
    for i in range(1, max_syncs + 1):
        await a.evaluate("syncNow()"); await a.wait_for_timeout(gap); await settle(a)
        await b.evaluate("syncNow()"); await b.wait_for_timeout(gap); await settle(b)
        ai, bi = await info(a), await info(b)
        if sorted(ai["ids"]) == sorted(bi["ids"]):
            return True, i
    return False, max_syncs


async def run():
    failures = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROM,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ca = await browser.new_context(viewport={"width": 860, "height": 720})
        cb = await browser.new_context(viewport={"width": 860, "height": 720})
        a, b = await ca.new_page(), await cb.new_page()

        # Intro card
        frame(title_card("woooosh sync — 25 rounds, always converging",
                         "Strong consistency (matches the fixed Netlify backend)",
                         f"{OUT}/_inf_title.png"), 3.0)

        await asyncio.gather(a.goto(APP, wait_until="networkidle"),
                             b.goto(APP, wait_until="networkidle"))
        await asyncio.gather(settle(a), settle(b))

        # Setup: A seeds a task, B applies key
        await a.fill("#taskInput", "Kickoff task"); await a.keyboard.press("Enter")
        await a.wait_for_timeout(2000); await settle(a)
        key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        await b.click(".sync-settings-btn"); await b.wait_for_timeout(200)
        await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
        await b.wait_for_timeout(200)
        await b.fill("#syncKeyField", key)
        await b.click("button.sync-apply-btn")
        await b.wait_for_timeout(2500); await settle(b)

        pa, pb = f"{OUT}/_inf_a_setup.png", f"{OUT}/_inf_b_setup.png"
        await asyncio.gather(a.screenshot(path=pa), b.screenshot(path=pb))
        frame(sidebyside(pa, pb, f"{OUT}/inf_setup.png",
                         "Device A — seeded 1 task", "Device B — key applied, synced",
                         "shared sync key", "pulled A's task"), 3.0)

        # Rounds
        for rnd in range(1, ROUNDS + 1):
            await a.fill("#taskInput", f"A round {rnd}"); await a.keyboard.press("Enter")
            await a.wait_for_timeout(150)
            await b.fill("#taskInput", f"B round {rnd}"); await b.keyboard.press("Enter")
            await b.wait_for_timeout(150)

            ok, used = await converge(a, b)
            ai, bi = await info(a), await info(b)
            match = sorted(ai["ids"]) == sorted(bi["ids"])
            if not (ok and match and ai["count"] == bi["count"]):
                failures.append(f"round {rnd}: A={ai['count']} B={bi['count']} match={match}")
                tag = "✗ MISMATCH"
            else:
                tag = f"✓ identical ({ai['count']} tasks, {used} sync{'s' if used>1 else ''})"
            print(f"  round {rnd:2d}: {tag}")

            pa, pb = f"{OUT}/_inf_a_r{rnd}.png", f"{OUT}/_inf_b_r{rnd}.png"
            await asyncio.gather(a.screenshot(path=pa), b.screenshot(path=pb))
            frame(sidebyside(pa, pb, f"{OUT}/inf_r{rnd:02d}.png",
                             f"Device A — round {rnd}", f"Device B — round {rnd}",
                             f"{ai['count']} tasks", f"{bi['count']} tasks ✓"),
                  1.6)

        # Outro
        final = await info(a)
        frame(title_card(f"All {ROUNDS} rounds converged ✓",
                         f"Final state: {final['count']} tasks, identical on both devices",
                         f"{OUT}/_inf_outro.png"), 4.0)
        await browser.close()

    # Video
    flist = f"{OUT}/_inf_frames.txt"
    with open(flist, "w") as fh:
        for path, hold in FRAMES:
            fh.write(f"file '{path}'\nduration {hold}\n")
        fh.write(f"file '{FRAMES[-1][0]}'\nduration 0.1\n")
    out_video = f"{OUT}/demo_infinite.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", flist,
                    "-vf", "scale=iw:ih:flags=lanczos,fps=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "fast", out_video], check=True, capture_output=True)
    print(f"\n  → {out_video}")

    if failures:
        print(f"\n✗ {len(failures)} round(s) FAILED:")
        for f in failures: print(f"   {f}")
        return False
    print(f"\n✓ All {ROUNDS} rounds converged. Sync works ad infinitum.")
    return True


def main():
    http = subprocess.Popen(["python3", "-m", "http.server", "3000",
                             "--directory", "/home/user/woooosh"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Strong consistency (default): SYNC_STALE_MS unset → 0
    sync = subprocess.Popen(["node", "/home/user/woooosh/sync-server.js"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    ok = False
    try:
        ok = asyncio.run(run())
    finally:
        http.terminate(); sync.terminate()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
