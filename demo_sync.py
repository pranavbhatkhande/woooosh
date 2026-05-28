"""
POC demo: two-device sync.
Starts sync server + HTTP file server, then uses Playwright to simulate
Device A and Device B with isolated localStorage — shows end-to-end sync.
"""
import asyncio
import json
import os
import subprocess
import sys
import time

from playwright.async_api import async_playwright
from PIL import Image  # for side-by-side compositing

OUT    = "/home/user/woooosh/demo"
CHROM  = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP    = "http://localhost:3000"
os.makedirs(OUT, exist_ok=True)

# ── PIL install check ──────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"], check=True)
    from PIL import Image, ImageDraw, ImageFont

def sidebyside(left_path, right_path, out_path, label_l="Device A", label_r="Device B"):
    """Composite two screenshots side by side with device labels."""
    L = Image.open(left_path).convert("RGBA")
    R = Image.open(right_path).convert("RGBA")
    # Resize both to same height
    h = max(L.height, R.height)
    L = L.resize((int(L.width * h / L.height), h), Image.LANCZOS)
    R = R.resize((int(R.width * h / R.height), h), Image.LANCZOS)

    bar_h = 36
    canvas = Image.new("RGBA", (L.width + R.width + 8, h + bar_h), (247, 248, 250, 255))
    # Label bars
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, L.width + 3, bar_h], fill=(79, 70, 229, 255))
    draw.rectangle([L.width + 4, 0, canvas.width, bar_h], fill=(16, 185, 129, 255))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    draw.text((16, 10), label_l, fill=(255,255,255,255), font=font)
    draw.text((L.width + 20, 10), label_r, fill=(255,255,255,255), font=font)
    # Paste screenshots
    canvas.paste(L, (0, bar_h))
    canvas.paste(R, (L.width + 8, bar_h))
    canvas.convert("RGB").save(out_path)
    return out_path

def make_video(frames, output, duration=3.0):
    f = f"{OUT}/_sync_frames.txt"
    with open(f, "w") as fh:
        for p in frames:
            fh.write(f"file '{p}'\nduration {duration}\n")
        fh.write(f"file '{frames[-1]}'\nduration 0.1\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f,
        "-vf", "scale=iw:ih:flags=lanczos,fps=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "fast",
        f"{OUT}/{output}.mp4"
    ], check=True, capture_output=True)
    print(f"  → {OUT}/{output}.mp4")

async def run_demo(procs):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROM,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        WW, WH = 900, 720

        # Two isolated browser contexts = two independent localStorage stores
        ctx_a = await browser.new_context(viewport={"width": WW, "height": WH})
        ctx_b = await browser.new_context(viewport={"width": WW, "height": WH})
        a = await ctx_a.new_page()
        b = await ctx_b.new_page()

        # ── Step 1: Both devices fresh load ───────────────────────────
        await asyncio.gather(
            a.goto(APP, wait_until="networkidle"),
            b.goto(APP, wait_until="networkidle"),
        )
        await asyncio.gather(a.wait_for_timeout(800), b.wait_for_timeout(800))

        s1a = f"{OUT}/sync_s1_deviceA.png"
        s1b = f"{OUT}/sync_s1_deviceB.png"
        await asyncio.gather(a.screenshot(path=s1a), b.screenshot(path=s1b))
        sidebyside(s1a, s1b, f"{OUT}/sync_01_fresh_load.png",
                   "Device A — fresh", "Device B — fresh")
        print("✓ step 1: fresh load")

        # ── Step 2: Device A adds tasks ───────────────────────────────
        for text in [
            "Write the product vision doc",
            "Schedule Q3 retrospective",
            "Fix the login redirect bug",
        ]:
            await a.fill("#taskInput", text)
            await a.keyboard.press("Enter")
            await a.wait_for_timeout(200)

        await a.wait_for_timeout(1800)  # let debounce fire + server sync

        s2a = f"{OUT}/sync_s2_deviceA.png"
        s2b = f"{OUT}/sync_s2_deviceB.png"
        await asyncio.gather(a.screenshot(path=s2a), b.screenshot(path=s2b))
        sidebyside(s2a, s2b, f"{OUT}/sync_02_A_added_tasks.png",
                   "Device A — 3 tasks added", "Device B — still empty")
        print("✓ step 2: Device A added tasks")

        # ── Step 3: Get sync key from Device A ────────────────────────
        sync_key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        print(f"  Sync key: {sync_key[:11]}…")

        # Open sync panel on Device A to show the key UI
        await a.click(".sync-settings-btn")
        await a.wait_for_timeout(200)
        await a.click("button.sync-action-btn")   # "Show key"
        await a.wait_for_timeout(300)
        s3a = f"{OUT}/sync_s3_deviceA.png"
        s3b = f"{OUT}/sync_s3_deviceB.png"
        await asyncio.gather(a.screenshot(path=s3a), b.screenshot(path=s3b))
        sidebyside(s3a, s3b, f"{OUT}/sync_03_A_shows_key.png",
                   "Device A — showing sync key", "Device B — about to enter it")
        print("✓ step 3: Device A shows sync key")

        # ── Step 4: Device B enters the sync key ──────────────────────
        await b.click(".sync-settings-btn")
        await b.wait_for_timeout(200)
        # Click "Enter key" button
        await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
        await b.wait_for_timeout(200)
        await b.fill("#syncKeyField", sync_key)
        await b.wait_for_timeout(300)
        s4a = f"{OUT}/sync_s4_deviceA.png"
        s4b = f"{OUT}/sync_s4_deviceB.png"
        await asyncio.gather(a.screenshot(path=s4a), b.screenshot(path=s4b))
        sidebyside(s4a, s4b, f"{OUT}/sync_04_B_entering_key.png",
                   "Device A — unchanged", "Device B — key entered, about to apply")
        print("✓ step 4: Device B entering key")

        # ── Step 5: Device B applies key → data pulls from server ─────
        await b.click("button.sync-apply-btn")
        await b.wait_for_timeout(2500)   # let pull complete + re-render
        s5a = f"{OUT}/sync_s5_deviceA.png"
        s5b = f"{OUT}/sync_s5_deviceB.png"
        await asyncio.gather(a.screenshot(path=s5a), b.screenshot(path=s5b))
        sidebyside(s5a, s5b, f"{OUT}/sync_05_synced.png",
                   "Device A — original", "Device B — synced! ✓")
        print("✓ step 5: Device B synced!")

        # ── Step 6: Device A adds a new task; Device B polls ──────────
        await a.fill("#taskInput", "Book team offsite venue")
        await a.keyboard.press("Enter")
        await a.wait_for_timeout(2200)   # debounce + server push

        # Simulate Device B "reopening the app" (calls syncFromServer)
        await b.evaluate("syncFromServer()")
        await b.wait_for_timeout(1500)

        s6a = f"{OUT}/sync_s6_deviceA.png"
        s6b = f"{OUT}/sync_s6_deviceB.png"
        await asyncio.gather(a.screenshot(path=s6a), b.screenshot(path=s6b))
        sidebyside(s6a, s6b, f"{OUT}/sync_06_live_update.png",
                   "Device A — 4th task added", "Device B — received live update")
        print("✓ step 6: live update propagated")

        # ── Step 7: Device B actionizes a task → syncs back to A ──────
        # Hover and click Actionize on the first task
        await b.hover(".task-item:first-child .task-row")
        await b.wait_for_timeout(200)
        actionize = b.locator(".task-item:first-child .btn-actionize")
        await actionize.click()
        await b.wait_for_timeout(2200)   # push

        await a.evaluate("syncFromServer()")
        await a.wait_for_timeout(1500)

        s7a = f"{OUT}/sync_s7_deviceA.png"
        s7b = f"{OUT}/sync_s7_deviceB.png"
        await asyncio.gather(a.screenshot(path=s7a), b.screenshot(path=s7b))
        sidebyside(s7a, s7b, f"{OUT}/sync_07_B_edits_A_receives.png",
                   "Device A — received B's change", "Device B — actionized task")
        print("✓ step 7: edit on B propagated to A")

        await browser.close()

    # ── Stitch into video ──────────────────────────────────────────────
    frames = [
        f"{OUT}/sync_01_fresh_load.png",
        f"{OUT}/sync_02_A_added_tasks.png",
        f"{OUT}/sync_03_A_shows_key.png",
        f"{OUT}/sync_04_B_entering_key.png",
        f"{OUT}/sync_05_synced.png",
        f"{OUT}/sync_06_live_update.png",
        f"{OUT}/sync_07_B_edits_A_receives.png",
    ]
    make_video(frames, "demo_sync", duration=3.0)
    print("\n✓ Sync demo video complete.")

def main():
    print("Starting servers…")
    # HTTP server for the app files
    http_srv = subprocess.Popen(
        ["python3", "-m", "http.server", "3000", "--directory", "/home/user/woooosh"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    # Node.js sync server
    sync_srv = subprocess.Popen(
        ["node", "/home/user/woooosh/sync-server.js"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(1.5)  # let both servers start

    try:
        asyncio.run(run_demo([http_srv, sync_srv]))
    finally:
        http_srv.terminate()
        sync_srv.terminate()
        print("Servers stopped.")

if __name__ == "__main__":
    main()
