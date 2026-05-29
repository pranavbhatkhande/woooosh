"""
Tombstone priority proof — proves deleted tasks stay deleted after sync.

Before fix: Pure LWW on updatedAt meant a stale device's edit could resurrect
            a tombstone from another device, causing data loss.
After fix:  mergeTasks() always prefers tombstone — a deleted task stays deleted
            regardless of updatedAt on the other device.

Demonstrates:
  1. Both devices sync to same state (3 tasks)
  2. Device A deletes task "Middle"
  3. Device B edits task "Middle" (stale device doesn't know it was deleted)
  4. Device A syncs — pushes tombstone to server
  5. Device B syncs — pulls from server, merges with tombstone priority
  6. Assert: "Middle" task is deleted on BOTH devices (not resurrected)

Produces demo/demo_tombstone_proof.mp4 with annotated screenshots.
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
             labels: [...items].map(el => (el.querySelector('.task-text')?.textContent || '').trim()),
             label: document.getElementById('syncLabel')?.textContent || '?' };
})()
"""


ALL_TASKS_JS = """
(() => {
    // Returns all tasks including tombstones
    const stored = JSON.parse(localStorage.getItem('wooooshTasks') || '[]');
    return {
        total: stored.length,
        live: stored.filter(t => !t._deleted).length,
        tombstones: stored.filter(t => t._deleted).length,
        tombstoneIds: stored.filter(t => t._deleted).map(t => t.id),
        tombstoneLabels: stored.filter(t => t._deleted).map(t => t.text || t.label || '?')
    };
})()
"""


async def info(page): return await page.evaluate(TASKS_JS)


async def all_tasks_info(page): return await page.evaluate(ALL_TASKS_JS)


async def settle(page, timeout_ms=8000):
    start = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start) * 1000 < timeout_ms:
        if await page.evaluate("document.getElementById('syncLabel')?.textContent") != 'Syncing…':
            return
        await page.wait_for_timeout(120)


async def add_task(page, text):
    await page.fill("#taskInput", text)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(300)


async def delete_task_by_label(page, label):
    """Find and delete a task by its text label."""
    # Find the task item containing the label
    selector = f".task-item:has(.task-title:contains('{label}'))"
    # Use JS to find the delete button
    tid = await page.evaluate("""
        (() => {
            const items = document.querySelectorAll('.task-item');
            for (const el of items) {
                const title = (el.querySelector('.task-text')?.textContent || '').trim();
                if (title === '%s') return el.dataset.id;
            }
            return null;
        })()
    """ % label.replace("'", "\\'"))
    if not tid:
        labels = await page.evaluate("([...document.querySelectorAll('.task-item')].map(el => (el.querySelector('.task-text')?.textContent || '').trim()))")
        raise ValueError(f"Task '{label}' not found. Available labels: {labels}")
    # Click the delete button for this task (first click arms confirmation)
    await page.evaluate("""
        (() => {
            const items = document.querySelectorAll('.task-item');
            for (const el of items) {
                if (el.dataset.id === '%s') {
                    const btn = el.querySelector('.btn-delete');
                    if (btn) btn.click();
                    break;
                }
            }
        })()
    """ % tid)
    await page.wait_for_timeout(500)
    # Second click confirms the delete (two-step delete pattern)
    await page.evaluate("""
        (() => {
            const items = document.querySelectorAll('.task-item');
            for (const el of items) {
                if (el.dataset.id === '%s') {
                    const btn = el.querySelector('.btn-delete-confirm');
                    if (btn) btn.click();
                    break;
                }
            }
        })()
    """ % tid)
    await page.wait_for_timeout(500); await settle(page)


async def edit_task_by_label(page, old_label, new_text):
    """Double-click a task's title and edit it."""
    tid = await page.evaluate("""
        (() => {
            const items = document.querySelectorAll('.task-item');
            for (const el of items) {
                const title = (el.querySelector('.task-text')?.textContent || '').trim();
                if (title === '%s') return el.dataset.id;
            }
            return null;
        })()
    """ % old_label.replace("'", "\\'"))
    if not tid:
        labels = await page.evaluate("([...document.querySelectorAll('.task-item')].map(el => (el.querySelector('.task-text')?.textContent || '').trim()))")
        raise ValueError(f"Task '{old_label}' not found for editing. Available labels: {labels}")
    # Enter edit mode via toggleEdit()
    await page.evaluate("toggleEdit(%s)" % tid)
    await page.wait_for_timeout(300)
    # Fill the edit input (the app uses .task-text.editing for the input)
    await page.fill(".task-text.editing", new_text)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(500); await settle(page)


async def run():
    failures = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ca = await browser.new_context(viewport={"width": 860, "height": 720})
        cb = await browser.new_context(viewport={"width": 860, "height": 720})
        a, b = await ca.new_page(), await cb.new_page()

        # Intro card
        frame(title_card(
            "Tombstone Priority — deleted tasks stay deleted",
            "Fix: mergeTasks() always prefers tombstone over live task with same ID",
            f"{OUT}/_tb_title.png"), 3.5)

        await asyncio.gather(a.goto(APP, wait_until="networkidle"),
                             b.goto(APP, wait_until="networkidle"))
        await asyncio.gather(settle(a), settle(b))

        # Step 1: A seeds 3 tasks, B applies key
        for t in ["Top", "Middle", "Bottom"]:
            await add_task(a, t)
        await a.wait_for_timeout(2000); await settle(a)

        key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        await b.click(".sync-settings-btn"); await b.wait_for_timeout(200)
        await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
        await b.wait_for_timeout(200)
        await b.fill("#syncKeyField", key)
        await b.click("button.sync-apply-btn")
        await b.wait_for_timeout(2500); await settle(b)

        ai, bi = await info(a), await info(b)
        pa, pb = f"{OUT}/_tb_a_base.png", f"{OUT}/_tb_b_base.png"
        await asyncio.gather(a.screenshot(path=pa), b.screenshot(path=pb))
        frame(sidebyside(pa, pb, f"{OUT}/tb_base.png",
                         "Device A — 3 tasks", "Device B — synced 3 tasks",
                         "Top, Middle, Bottom", "Top, Middle, Bottom ✓"), 3.0)
        print(f"  Base: A={ai['count']} tasks, B={bi['count']} tasks")

        # Step 2: A deletes "Middle"
        await delete_task_by_label(a, "Middle")
        await a.wait_for_timeout(1500); await settle(a)
        # A syncs to push tombstone
        await a.evaluate("syncNow()")
        await a.wait_for_timeout(1500); await settle(a)

        ai = await info(a)
        aa = await all_tasks_info(a)
        pa = f"{OUT}/_tb_a_del.png"
        await a.screenshot(path=pa)
        print(f"  A deleted 'Middle': {ai['count']} live, {aa['tombstones']} tombstone(s)")

        # Step 3: B edits "Middle" (stale — doesn't know it was deleted)
        await edit_task_by_label(b, "Middle", "Middle (edited)")
        await b.wait_for_timeout(1000); await settle(b)
        bi = await info(b)
        pb = f"{OUT}/_tb_b_edit.png"
        await b.screenshot(path=pb)
        print(f"  B edited 'Middle' → 'Middle (edited)': {bi['count']} live tasks (stale)")

        pa2, pb2 = f"{OUT}/_tb_a_del2.png", f"{OUT}/_tb_b_edit2.png"
        await asyncio.gather(a.screenshot(path=pa2), b.screenshot(path=pb2))
        frame(sidebyside(pa2, pb2, f"{OUT}/tb_diverge.png",
                         "Device A — deleted 'Middle'", "Device B — edited 'Middle' (stale)",
                         f"{ai['count']} live, {aa['tombstones']} tombstone", f"{bi['count']} live (doesn't know deleted)"),
              3.0)

        # Step 4: B syncs — should pull tombstone and delete "Middle (edited)"
        await b.evaluate("syncNow()")
        await b.wait_for_timeout(2000); await settle(b)

        bi_after = await info(b)
        ba_after = await all_tasks_info(b)
        pb_after = f"{OUT}/_tb_b_sync.png"
        await b.screenshot(path=pb_after)
        print(f"  B after sync: {bi_after['count']} live, {ba_after['tombstones']} tombstone(s)")

        # Verify tombstone exists on B
        has_tombstone = ba_after['tombstones'] > 0
        middle_gone = "Middle (edited)" not in bi_after['labels'] and "Middle" not in bi_after['labels']
        count_correct = bi_after['count'] == 2  # Top + Bottom only

        tombstone_ok = has_tombstone and middle_gone and count_correct
        tag = "✓ tombstone wins — 'Middle' deleted on B" if tombstone_ok else "✗ tombstone lost"
        if not tombstone_ok:
            failures.append(f"tombstone failed: tombstones={ba_after['tombstones']} middle_gone={middle_gone} count={bi_after['count']}")
        print(f"  Result: {tag}")

        ai_final = await info(a)
        pa_final = f"{OUT}/_tb_a_final.png"
        await a.screenshot(path=pa_final)

        frame(sidebyside(pa_final, pb_after, f"{OUT}/tb_result.png",
                         "Device A — 'Middle' deleted", "Device B — 'Middle' deleted after sync",
                         f"{ai_final['count']} live tasks", f"{bi_after['count']} live tasks ✓ tombstone wins"),
              3.5)

        # Summary
        if failures:
            frame(title_card(
                "Tombstone test FAILED",
                f"{len(failures)} assertion(s) failed",
                f"{OUT}/_tb_outro.png"), 4.0)
        else:
            frame(title_card(
                "Tombstone Priority Verified ✓",
                "Deleted task stayed deleted. Stale device's edit was not resurrected.",
                f"{OUT}/_tb_outro.png"), 4.0)

        await browser.close()

    # Video
    flist = f"{OUT}/_tb_frames.txt"
    with open(flist, "w") as fh:
        for path, hold in FRAMES:
            fh.write(f"file '{path}'\nduration {hold}\n")
        fh.write(f"file '{FRAMES[-1][0]}'\nduration 0.1\n")
    out_video = f"{OUT}/demo_tombstone_proof.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", flist,
                    "-vf", "scale=iw:ih:flags=lanczos,fps=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "fast", out_video], check=True, capture_output=True)
    print(f"\n  → {out_video}")

    if failures:
        print(f"\n✗ {len(failures)} assertion(s) FAILED:")
        for f in failures: print(f"   {f}")
        return False
    print(f"\n✓ Tombstone priority works. Deleted task stays deleted across devices.")
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
