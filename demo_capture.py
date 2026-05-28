"""
Captures screenshots of the woooosh redesign across multiple states,
then stitches them into a demo video using ffmpeg.
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

OUT = "/home/user/woooosh/demo"
os.makedirs(OUT, exist_ok=True)

# Realistic demo tasks seeded into localStorage
now = datetime.utcnow()
def ts(minutes_ago=0):
    return (now - timedelta(minutes=minutes_ago)).isoformat() + "Z"

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

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        # ── Desktop screenshots ───────────────────────────────────────
        base = "file:///home/user/woooosh/index.html"
        page = await browser.new_page(viewport={"width": 1200, "height": 780})

        # Navigate first so localStorage is accessible, then seed and reload
        await page.goto(base, wait_until="networkidle")
        await page.evaluate(f"""
            localStorage.setItem('wooooshTasks', JSON.stringify({json.dumps(DEMO_TASKS)}));
        """)
        await page.reload(wait_until="networkidle")

        # 1. Full app – all tasks
        await page.goto(base, wait_until="networkidle")
        await page.wait_for_timeout(600)
        await page.screenshot(path=f"{OUT}/01_all_tasks.png", full_page=False)
        print("✓ 01_all_tasks")

        # 2. Hover over a task row to reveal actions
        row = page.locator(".task-item").first
        await row.hover()
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT}/02_row_hover.png", full_page=False)
        print("✓ 02_row_hover")

        # 3. Filter: Ideas view
        await page.click("#filterIdea")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT}/03_ideas_filter.png", full_page=False)
        print("✓ 03_ideas_filter")

        # 4. Filter: In progress view
        await page.click("#filterInProgress")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT}/04_inprogress_filter.png", full_page=False)
        print("✓ 04_inprogress_filter")

        # 5. Filter: Done view
        await page.click("#filterCompleted")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT}/05_done_filter.png", full_page=False)
        print("✓ 05_done_filter")

        # 6. Back to All – show how-to box open
        await page.click("#filterAll")
        await page.wait_for_timeout(200)
        await page.click("#toggleHowToBtn")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT}/06_howto_open.png", full_page=False)
        print("✓ 06_howto_open")

        # 7. Focused input state
        await page.click("#toggleHowToBtn")  # close how-to
        await page.click("#filterAll")
        await page.wait_for_timeout(200)
        await page.click("#taskInput")
        await page.fill("#taskInput", "Build a demo video of the new UI")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUT}/07_input_focused.png", full_page=False)
        print("✓ 07_input_focused")

        # 8. After adding the task (clear input, task appears)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(400)
        await page.screenshot(path=f"{OUT}/08_task_added.png", full_page=False)
        print("✓ 08_task_added")

        # ── Mobile screenshots ────────────────────────────────────────
        mobile = await browser.new_page(viewport={"width": 390, "height": 844})  # iPhone 14 size
        await mobile.goto(base, wait_until="networkidle")
        await mobile.evaluate(f"""
            localStorage.setItem('wooooshTasks', JSON.stringify({json.dumps(DEMO_TASKS)}));
        """)
        await mobile.reload(wait_until="networkidle")
        await mobile.wait_for_timeout(600)

        # 9. Mobile – default view
        await mobile.screenshot(path=f"{OUT}/09_mobile_default.png", full_page=False)
        print("✓ 09_mobile_default")

        # 10. Mobile – sidebar open
        await mobile.click(".menu-toggle")
        await mobile.wait_for_timeout(400)
        await mobile.screenshot(path=f"{OUT}/10_mobile_sidebar.png", full_page=False)
        print("✓ 10_mobile_sidebar")

        await browser.close()

    # ── Stitch into video ─────────────────────────────────────────────
    # Each screenshot shown for ~2.5s → ~4fps from pngs
    frames_file = f"{OUT}/frames.txt"
    screenshots = [
        "01_all_tasks", "02_row_hover", "03_ideas_filter", "04_inprogress_filter",
        "05_done_filter", "06_howto_open", "07_input_focused", "08_task_added",
        "09_mobile_default", "10_mobile_sidebar"
    ]

    # Write ffmpeg concat list (each frame shown 2.5s)
    with open(frames_file, "w") as f:
        for name in screenshots:
            f.write(f"file '{OUT}/{name}.png'\n")
            f.write("duration 2.5\n")
        # repeat last frame so ffmpeg doesn't cut it short
        f.write(f"file '{OUT}/{screenshots[-1]}.png'\n")
        f.write("duration 0.1\n")

    video_path = f"{OUT}/demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", frames_file,
        "-vf", "scale=1200:-2:flags=lanczos,fps=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "fast",
        video_path
    ], check=True, capture_output=True)
    print(f"\n✓ Video saved → {video_path}")

asyncio.run(capture())
