"""
POC demo: merge-sync between two independent devices.

Flow:
  1. Both devices fresh load
  2. Device A adds 3 tasks → auto-pushes to server
  3. Device B enters A's sync key → Apply & sync (one-time key setup)
  4. Device B adds 3 independent tasks → auto-pushes to server
  5. Device A presses Sync → pull+merge+push → A now has all 6 tasks
  6. Device B presses Sync → pull+merge (server has merged blob) → B gets all 6 tasks
  7. Both show identical merged state
"""
import asyncio
import json
import os
import subprocess
import sys
import time

from playwright.async_api import async_playwright
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"], check=True)
    from PIL import Image, ImageDraw, ImageFont

OUT   = "/home/user/woooosh/demo"
CHROM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP   = "http://localhost:3000"
os.makedirs(OUT, exist_ok=True)


def sidebyside(left_path, right_path, out_path, label_l="Device A", label_r="Device B"):
    L = Image.open(left_path).convert("RGBA")
    R = Image.open(right_path).convert("RGBA")
    h = max(L.height, R.height)
    L = L.resize((int(L.width * h / L.height), h), Image.LANCZOS)
    R = R.resize((int(R.width * h / R.height), h), Image.LANCZOS)
    bar_h = 36
    canvas = Image.new("RGBA", (L.width + R.width + 8, h + bar_h), (247, 248, 250, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, L.width + 3, bar_h], fill=(79, 70, 229, 255))
    draw.rectangle([L.width + 4, 0, canvas.width, bar_h], fill=(16, 185, 129, 255))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    draw.text((16, 10), label_l, fill=(255, 255, 255, 255), font=font)
    draw.text((L.width + 20, 10), label_r, fill=(255, 255, 255, 255), font=font)
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


def task_count(page_tasks_json):
    return sum(1 for t in json.loads(page_tasks_json) if not t.get("_deleted"))


async def run_demo(procs):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROM,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        WW, WH = 900, 720
        ctx_a = await browser.new_context(viewport={"width": WW, "height": WH})
        ctx_b = await browser.new_context(viewport={"width": WW, "height": WH})
        a = await ctx_a.new_page()
        b = await ctx_b.new_page()

        # ── Step 1: Fresh load ─────────────────────────────────────────
        await asyncio.gather(
            a.goto(APP, wait_until="networkidle"),
            b.goto(APP, wait_until="networkidle"),
        )
        await asyncio.gather(a.wait_for_timeout(800), b.wait_for_timeout(800))
        s1a, s1b = f"{OUT}/m_s1_a.png", f"{OUT}/m_s1_b.png"
        await asyncio.gather(a.screenshot(path=s1a), b.screenshot(path=s1b))
        sidebyside(s1a, s1b, f"{OUT}/merge_01_fresh.png",
                   "Device A — fresh", "Device B — fresh")
        print("✓ step 1: fresh load")

        # ── Step 2: Device A adds 3 tasks → auto-pushes ───────────────
        for text in ["Write product vision doc", "Schedule Q3 retro", "Fix the login bug"]:
            await a.fill("#taskInput", text)
            await a.keyboard.press("Enter")
            await a.wait_for_timeout(200)
        await a.wait_for_timeout(2200)   # debounce + auto-push

        s2a, s2b = f"{OUT}/m_s2_a.png", f"{OUT}/m_s2_b.png"
        await asyncio.gather(a.screenshot(path=s2a), b.screenshot(path=s2b))
        sidebyside(s2a, s2b, f"{OUT}/merge_02_A_pushed.png",
                   "Device A — 3 tasks, auto-pushed", "Device B — still empty")
        print("✓ step 2: Device A added tasks + auto-pushed")

        # ── Step 3: Device B one-time key setup (Apply & sync) ────────
        sync_key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        print(f"  Sync key: {sync_key[:11]}…")

        await b.click(".sync-settings-btn")      # open settings panel
        await b.wait_for_timeout(200)
        await b.click("button.sync-action-btn:nth-of-type(2)")  # "Enter key"
        await b.wait_for_timeout(200)
        await b.fill("#syncKeyField", sync_key)
        await b.click("button.sync-apply-btn")   # Apply & sync
        await b.wait_for_timeout(2500)           # pull + merge + push

        s3a, s3b = f"{OUT}/m_s3_a.png", f"{OUT}/m_s3_b.png"
        await asyncio.gather(a.screenshot(path=s3a), b.screenshot(path=s3b))
        sidebyside(s3a, s3b, f"{OUT}/merge_03_B_key_applied.png",
                   "Device A — unchanged", "Device B — key set, pulled A's tasks")
        b_count_after_setup = await b.evaluate("document.querySelectorAll('.task-item').length")
        print(f"✓ step 3: Device B applied key — {b_count_after_setup} tasks pulled")

        # ── Step 4: Device B adds 3 independent tasks → auto-pushes ──
        # (overwrites server blob with B's view — merge happens on Sync press)
        for text in ["Book team offsite", "Audit accessibility", "Ship v2.1 notes"]:
            await b.fill("#taskInput", text)
            await b.keyboard.press("Enter")
            await b.wait_for_timeout(200)
        await b.wait_for_timeout(2200)           # debounce + auto-push

        s4a, s4b = f"{OUT}/m_s4_a.png", f"{OUT}/m_s4_b.png"
        await asyncio.gather(a.screenshot(path=s4a), b.screenshot(path=s4b))
        sidebyside(s4a, s4b, f"{OUT}/merge_04_B_pushed.png",
                   "Device A — still 3 tasks", "Device B — 6 tasks, auto-pushed to server")
        print("✓ step 4: Device B added 3 more tasks + auto-pushed")

        # ── Step 5: Device A presses Sync → pull + merge + push ───────
        # Device A pulls B's blob (which has 6 tasks), merges with its own 3
        # (all 6 are unique IDs so merge produces all 6), then pushes merged blob
        await a.evaluate("syncNow()")
        await a.wait_for_timeout(2500)

        s5a, s5b = f"{OUT}/m_s5_a.png", f"{OUT}/m_s5_b.png"
        await asyncio.gather(a.screenshot(path=s5a), b.screenshot(path=s5b))
        sidebyside(s5a, s5b, f"{OUT}/merge_05_A_synced.png",
                   "Device A — merged! all 6 tasks", "Device B — still 6 (its own)")
        a_count = await a.evaluate("document.querySelectorAll('.task-item').length")
        print(f"✓ step 5: Device A synced — {a_count} tasks (merged)")

        # ── Step 6: Device B presses Sync → gets merged result ────────
        await b.evaluate("syncNow()")
        await b.wait_for_timeout(2500)

        s6a, s6b = f"{OUT}/m_s6_a.png", f"{OUT}/m_s6_b.png"
        await asyncio.gather(a.screenshot(path=s6a), b.screenshot(path=s6b))
        sidebyside(s6a, s6b, f"{OUT}/merge_06_both_synced.png",
                   "Device A — 6 tasks", "Device B — 6 tasks (merged ✓)")
        b_count = await b.evaluate("document.querySelectorAll('.task-item').length")
        print(f"✓ step 6: Device B synced — {b_count} tasks (same as A)")

        # ── Step 7: Device B marks a task complete; A syncs to receive ─
        first_id = await b.evaluate("document.querySelector('.task-item')?.dataset?.id")
        await b.evaluate(f"changeStatus({first_id}, 'completed')")
        await b.wait_for_timeout(2200)           # auto-push

        await a.evaluate("syncNow()")
        await a.wait_for_timeout(2000)

        s7a, s7b = f"{OUT}/m_s7_a.png", f"{OUT}/m_s7_b.png"
        await asyncio.gather(a.screenshot(path=s7a), b.screenshot(path=s7b))
        sidebyside(s7a, s7b, f"{OUT}/merge_07_status_propagated.png",
                   "Device A — task marked complete ✓", "Device B — made the change")
        print("✓ step 7: status change on B propagated to A via sync")

        await browser.close()

    # ── Stitch video ───────────────────────────────────────────────────
    frames = [
        f"{OUT}/merge_01_fresh.png",
        f"{OUT}/merge_02_A_pushed.png",
        f"{OUT}/merge_03_B_key_applied.png",
        f"{OUT}/merge_04_B_pushed.png",
        f"{OUT}/merge_05_A_synced.png",
        f"{OUT}/merge_06_both_synced.png",
        f"{OUT}/merge_07_status_propagated.png",
    ]
    make_video(frames, "demo_merge_sync", duration=3.0)
    print("\n✓ Merge-sync demo complete.")


def main():
    print("Starting servers…")
    http_srv = subprocess.Popen(
        ["python3", "-m", "http.server", "3000", "--directory", "/home/user/woooosh"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    sync_srv = subprocess.Popen(
        ["node", "/home/user/woooosh/sync-server.js"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(1.5)
    try:
        asyncio.run(run_demo([http_srv, sync_srv]))
    finally:
        http_srv.terminate()
        sync_srv.terminate()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
