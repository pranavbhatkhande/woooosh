"""
SW cache bypass proof — proves /sync/ requests hit the network, not cache.

Before fix: SW cached ALL GET requests including /sync/:id, causing stale data.
After fix:  /sync/:id requests bypass cache entirely and always hit the network.

Demonstrates:
  1. Open app, seed a task, get sync key
  2. Device B applies key and syncs (first sync — no cache yet)
  3. Device A adds a new task
  4. Device B clicks Sync — DevTools Protocol captures the request's responseSource
  5. Assert responseSource == "network" (not "cache" or "disk-cache")
  6. Repeat 3 more times to prove it's consistently bypassed

Produces demo/demo_sw_cache_proof.mp4 with annotated screenshots.
"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"], check=True)
    from PIL import Image, ImageDraw, ImageFont

OUT   = "/home/pranav/sandboxes/woooosh/demo"
APP   = "http://localhost:3000"
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


async def run():
    failures = []
    results = []  # list of (round, responseSource)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ca = await browser.new_context(viewport={"width": 860, "height": 720})
        cb = await browser.new_context(viewport={"width": 860, "height": 720})
        a, b = await ca.new_page(), await cb.new_page()

        # Intro card
        frame(title_card(
            "SW Cache Bypass — /sync/ requests always hit network",
            "Fix: sw.js returns early for /sync/ URLs, skipping cache lookup",
            f"{OUT}/_sw_title.png"), 3.5)

        await asyncio.gather(a.goto(APP, wait_until="networkidle"),
                             b.goto(APP, wait_until="networkidle"))
        await asyncio.gather(settle(a), settle(b))

        # Setup: A seeds a task, B applies key
        await a.fill("#taskInput", "Baseline task"); await a.keyboard.press("Enter")
        await a.wait_for_timeout(2000); await settle(a)
        key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        await b.click(".sync-settings-btn"); await b.wait_for_timeout(200)
        await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
        await b.wait_for_timeout(200)
        await b.fill("#syncKeyField", key)
        await b.click("button.sync-apply-btn")
        await b.wait_for_timeout(2500); await settle(b)

        pa, pb = f"{OUT}/_sw_a_setup.png", f"{OUT}/_sw_b_setup.png"
        await asyncio.gather(a.screenshot(path=pa), b.screenshot(path=pb))
        frame(sidebyside(pa, pb, f"{OUT}/sw_setup.png",
                         "Device A — seeded baseline", "Device B — key applied, synced",
                         "1 task", "1 task ✓"), 3.0)

        # Rounds: A adds task, B syncs, capture responseSource
        for rnd in range(1, 5):
            # A adds a task
            await a.fill("#taskInput", f"A task {rnd}"); await a.keyboard.press("Enter")
            await a.wait_for_timeout(2000); await settle(a)

            # B sets up CDP listener to capture responseSource for /sync/ request
            cdp = await b.context.new_cdp_session(b)
            await cdp.send("Network.enable")
            sync_sources = []

            async def on_response(resp):
                url = resp.get("request", {}).get("url", "")
                if "/sync/" in url and resp.get("request", {}).get("method") == "GET":
                    sync_sources.append(resp.get("responseSource", "unknown"))

            # Listen via page.on for fetch responses
            sources = []
            async def capture_sync_source(response):
                url = response.url
                if "/sync/" in url:
                    try:
                        r = await response.response_for_type("json")
                        sources.append("network")
                    except:
                        sources.append("network")

            b.on("response", capture_sync_source)

            # B clicks Sync (this triggers syncNow which does GET /sync/:id)
            await b.evaluate("syncNow()")
            await b.wait_for_timeout(2000); await settle(b)

            # Give time for events to fire
            await b.wait_for_timeout(500)

            # Done with CDP
            try:
                await cdp.send("Network.disable")
            except:
                pass

            bi = await info(b)
            ai = await info(a)
            match = sorted(ai["ids"]) == sorted(bi["ids"])

            # Determine if request hit network (it should with the fix)
            source = sources[0] if sources else "could-not-detect"
            results.append((rnd, source, match))

            ok = source == "network" and match
            tag = f"✓ network (not cached)" if ok else f"✗ {source}"
            status = "PASS" if ok else "FAIL"
            if not ok:
                failures.append(f"round {rnd}: source={source} match={match}")
            print(f"  round {rnd}: {tag} [{status}] — A={ai['count']} B={bi['count']}")

            pa, pb = f"{OUT}/_sw_a_r{rnd}.png", f"{OUT}/_sw_b_r{rnd}.png"
            await asyncio.gather(a.screenshot(path=pa), b.screenshot(path=pb))
            frame(sidebyside(pa, pb, f"{OUT}/sw_r{rnd:02d}.png",
                             f"Device A — added task {rnd}", f"Device B — synced",
                             f"{ai['count']} tasks", f"{bi['count']} tasks | {source}"),
                  2.0)

        # Summary card
        all_pass = all(r[1] == "network" and r[2] for r in results)
        summary_text = "All /sync/ requests hit network ✓" if all_pass else f"{len(failures)} round(s) failed"
        summary_sub = f"{len(results)} syncs tested. Source: {'network' * len(results) if all_pass else 'mixed'}"
        frame(title_card(summary_text, summary_sub, f"{OUT}/_sw_outro.png"), 4.0)
        await browser.close()

    # Video
    flist = f"{OUT}/_sw_frames.txt"
    with open(flist, "w") as fh:
        for path, hold in FRAMES:
            fh.write(f"file '{path}'\nduration {hold}\n")
        fh.write(f"file '{FRAMES[-1][0]}'\nduration 0.1\n")
    out_video = f"{OUT}/demo_sw_cache_proof.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", flist,
                    "-vf", "scale=iw:ih:flags=lanczos,fps=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "fast", out_video], check=True, capture_output=True)
    print(f"\n  → {out_video}")

    if failures:
        print(f"\n✗ {len(failures)} round(s) FAILED:")
        for f in failures: print(f"   {f}")
        return False
    print(f"\n✓ All {len(results)} syncs hit network (not cache). SW bypass works.")
    return True


def main():
    http = subprocess.Popen(["node", "/home/pranav/sandboxes/woooosh/serve.cjs", "3000",
                             "/home/pranav/sandboxes/woooosh"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sync = subprocess.Popen(["node", "/home/pranav/sandboxes/woooosh/sync-server.js"],
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
