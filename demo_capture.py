"""
Captures mobile-specific screenshots: iOS Safari viewport, Android Chrome,
tap-to-expand, bottom nav, FAB — then stitches into a demo video.
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

OUT = "/home/pranav/sandboxes/woooosh/demo"
os.makedirs(OUT, exist_ok=True)

now = datetime.utcnow()
def ts(m=0): return (now - timedelta(minutes=m)).isoformat() + "Z"

DEMO_TASKS = [
    {"id": 1001, "text": "Redesign the onboarding flow", "status": "inProgress",
     "created": ts(180), "scheduledFor": None, "isEditing": False, "isScheduling": False},
    {"id": 1002, "text": "Write Q3 strategy document", "status": "action",
     "created": ts(300), "scheduledFor": None, "isEditing": False, "isScheduling": False},
    {"id": 1003, "text": "Set up error monitoring in production", "status": "scheduled",
     "created": ts(500), "scheduledFor": (now + timedelta(days=2)).isoformat() + "Z",
     "isEditing": False, "isScheduling": False},
    {"id": 1004, "text": "Explore new analytics integrations", "status": "idea",
     "created": ts(60), "scheduledFor": None, "isEditing": False, "isScheduling": False},
    {"id": 1005, "text": "Review pull requests before EOD", "status": "reminder",
     "created": ts(120), "scheduledFor": None, "isEditing": False, "isScheduling": False},
    {"id": 1006, "text": "Update API documentation", "status": "action",
     "created": ts(240), "scheduledFor": None, "isEditing": False, "isScheduling": False},
    {"id": 1007, "text": "Ship v2.1 release notes", "status": "completed",
     "created": ts(1440), "scheduledFor": None, "isEditing": False, "isScheduling": False},
    {"id": 1008, "text": "Audit accessibility on key screens", "status": "idea",
     "created": ts(90), "scheduledFor": None, "isEditing": False, "isScheduling": False},
]

BASE = "file:///home/pranav/sandboxes/woooosh/index.html"

async def seed(page):
    await page.goto(BASE, wait_until="networkidle")
    await page.evaluate(f"localStorage.setItem('wooooshTasks', JSON.stringify({json.dumps(DEMO_TASKS)}))")
    await page.reload(wait_until="networkidle")

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        # ── Desktop: 1440×900 (wide, "real" SaaS viewport) ──────────────
        desk = await browser.new_page(viewport={"width": 1440, "height": 900})
        await seed(desk)
        await desk.wait_for_timeout(500)
        await desk.screenshot(path=f"{OUT}/d01_desktop_all.png")
        print("✓ d01 desktop all-tasks")

        await desk.locator(".task-item").nth(1).hover()
        await desk.wait_for_timeout(300)
        await desk.screenshot(path=f"{OUT}/d02_desktop_hover.png")
        print("✓ d02 desktop hover")

        await desk.click("#filterAction")
        await desk.wait_for_timeout(300)
        await desk.screenshot(path=f"{OUT}/d03_desktop_actions_filter.png")
        print("✓ d03 desktop actions filter")

        await desk.click("#filterAll")
        await desk.fill("#taskInput", "Improve search relevance scoring")
        await desk.wait_for_timeout(300)
        await desk.screenshot(path=f"{OUT}/d04_desktop_input.png")
        print("✓ d04 desktop input")

        # ── iPhone 14 Pro (390×844) ──────────────────────────────────────
        iphone = await browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True)
        await seed(iphone)
        await iphone.wait_for_timeout(500)
        await iphone.screenshot(path=f"{OUT}/m01_iphone_default.png")
        print("✓ m01 iPhone default")

        # Tap a task row to reveal actions
        await iphone.tap(".task-item:nth-child(1) .task-row")
        await iphone.wait_for_timeout(400)
        await iphone.screenshot(path=f"{OUT}/m02_iphone_row_expanded.png")
        print("✓ m02 iPhone row expanded")

        # Tap a bottom tab — Ideas
        await iphone.tap("#bt-idea")
        await iphone.wait_for_timeout(300)
        await iphone.screenshot(path=f"{OUT}/m03_iphone_ideas_tab.png")
        print("✓ m03 iPhone ideas tab")

        # Active tab — In progress
        await iphone.tap("#bt-inProgress")
        await iphone.wait_for_timeout(300)
        await iphone.screenshot(path=f"{OUT}/m04_iphone_inprogress_tab.png")
        print("✓ m04 iPhone in-progress tab")

        # FAB tapped — input focused at top
        await iphone.tap("#bt-all")
        await iphone.wait_for_timeout(200)
        await iphone.tap(".fab")
        await iphone.wait_for_timeout(500)
        await iphone.screenshot(path=f"{OUT}/m05_iphone_fab_input.png")
        print("✓ m05 iPhone FAB → input focused")

        # Sidebar overlay
        await iphone.tap(".menu-toggle")
        await iphone.wait_for_timeout(400)
        await iphone.screenshot(path=f"{OUT}/m06_iphone_sidebar.png")
        print("✓ m06 iPhone sidebar open")

        # ── Android Pixel 7 (412×915) ────────────────────────────────────
        android = await browser.new_page(viewport={"width": 412, "height": 915}, has_touch=True)
        await seed(android)
        await android.wait_for_timeout(500)
        await android.screenshot(path=f"{OUT}/a01_android_default.png")
        print("✓ a01 Android default")

        await android.tap(".task-item:nth-child(2) .task-row")
        await android.wait_for_timeout(400)
        await android.screenshot(path=f"{OUT}/a02_android_row_expanded.png")
        print("✓ a02 Android row expanded")

        await browser.close()

    # ── Stitch into two videos ───────────────────────────────────────
    def make_video(frames, output, duration=2.5):
        frames_file = f"{OUT}/_frames_{output}.txt"
        with open(frames_file, "w") as f:
            for name in frames:
                f.write(f"file '{OUT}/{name}.png'\n")
                f.write(f"duration {duration}\n")
            f.write(f"file '{OUT}/{frames[-1]}.png'\nduration 0.1\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", frames_file,
            "-vf", "scale=iw:ih:flags=lanczos,fps=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "fast",
            f"{OUT}/{output}.mp4"
        ], check=True, capture_output=True)
        print(f"✓ Video → {OUT}/{output}.mp4")

    make_video(
        ["d01_desktop_all","d02_desktop_hover","d03_desktop_actions_filter","d04_desktop_input"],
        "demo_desktop"
    )
    make_video(
        ["m01_iphone_default","m02_iphone_row_expanded","m03_iphone_ideas_tab",
         "m04_iphone_inprogress_tab","m05_iphone_fab_input","m06_iphone_sidebar",
         "a01_android_default","a02_android_row_expanded"],
        "demo_mobile", duration=2.2
    )

asyncio.run(capture())
