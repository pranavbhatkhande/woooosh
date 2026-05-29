"""
Comprehensive sync demo — 7 distinct test phases, 20+ sync operations.

Captures side-by-side screenshots at every key moment and stitches them
into a single MP4 video with a clear title card between phases.

Phase 1  — Fresh load, both empty
Phase 2  — Device A adds tasks → auto-push
Phase 3  — Device B one-time key setup (Apply & sync) → pulls A's tasks
Phase 4  — Device B adds independent tasks → auto-push
Phase 5  — Device A syncs → merge (all tasks visible)
Phase 6  — Device B syncs → receives merged result (both identical)
Phase 7  — Status change on B → A syncs to receive it
Phase 8  — Delete on A (tombstone) → B syncs → task gone on B
Phase 9  — 6-round back-and-forth (A adds, B adds, both sync, verify match)
Phase 10 — Rapid fire: A syncs 5 times in a row (stress-test idempotency)
Phase 11 — Final state: both show identical task lists

Requires:
  - Playwright (chromium)
  - Pillow
  - ffmpeg
  - app running on http://localhost:3000
  - sync server on http://localhost:3001
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

OUT   = "/home/pranav/sandboxes/woooosh/demo"
APP   = "http://localhost:3000"

os.makedirs(OUT, exist_ok=True)

FRAMES   = []   # list of (path, hold_seconds)
FAILURES = []   # test failures collected


# ── Image helpers ─────────────────────────────────────────────────────────────

def sidebyside(left_path, right_path, out_path,
               label_l="Device A", label_r="Device B",
               status_l=None, status_r=None):
    L = Image.open(left_path).convert("RGBA")
    R = Image.open(right_path).convert("RGBA")
    h = max(L.height, R.height)
    L = L.resize((int(L.width * h / L.height), h), Image.LANCZOS)
    R = R.resize((int(R.width * h / R.height), h), Image.LANCZOS)
    bar_h = 44
    canvas = Image.new("RGBA", (L.width + R.width + 8, h + bar_h), (247, 248, 250, 255))
    draw = ImageDraw.Draw(canvas)

    col_a = (79, 70, 229, 255)   # indigo
    col_b = (16, 185, 129, 255)  # green
    draw.rectangle([0, 0, L.width + 3, bar_h], fill=col_a)
    draw.rectangle([L.width + 4, 0, canvas.width, bar_h], fill=col_b)

    try:
        font     = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except Exception:
        font = font_sm = ImageFont.load_default()

    draw.text((16, 8), label_l, fill=(255, 255, 255, 255), font=font)
    if status_l:
        draw.text((16, 26), status_l, fill=(200, 220, 255, 255), font=font_sm)

    draw.text((L.width + 20, 8), label_r, fill=(255, 255, 255, 255), font=font)
    if status_r:
        draw.text((L.width + 20, 26), status_r, fill=(200, 255, 220, 255), font=font_sm)

    canvas.paste(L, (0, bar_h))
    canvas.paste(R, (L.width + 8, bar_h))
    canvas.convert("RGB").save(out_path)
    return out_path


def title_card(text, sub="", out_path=None, width=1808, height=764):
    """Create a plain title-card frame."""
    img  = Image.new("RGB", (width, height), (30, 30, 46))
    draw = ImageDraw.Draw(img)
    try:
        font    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font = font_sm = ImageFont.load_default()

    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    draw.text(((width - tw) // 2, height // 2 - 36), text, fill=(255, 255, 255), font=font)
    if sub:
        bb2 = draw.textbbox((0, 0), sub, font=font_sm)
        sw = bb2[2] - bb2[0]
        draw.text(((width - sw) // 2, height // 2 + 20), sub, fill=(150, 160, 200), font=font_sm)
    if out_path is None:
        out_path = f"{OUT}/_title_{abs(hash(text))}.png"
    img.save(out_path)
    return out_path


def frame(path, hold=3.0):
    FRAMES.append((path, hold))
    return path


def add_title(text, sub="", hold=2.5):
    p = title_card(text, sub)
    frame(p, hold)


# ── Browser helpers ───────────────────────────────────────────────────────────

TASKS_JS = """
(() => {
    const items = document.querySelectorAll('.task-item');
    const label = document.getElementById('syncLabel')?.textContent || '?';
    const ids   = [...items].map(el => el.dataset.id);
    return { count: items.length, label, ids };
})()
"""


async def st(page, name):
    info = await page.evaluate(TASKS_JS)
    print(f"  [{name}] status='{info['label']}' tasks={info['count']} ids={info['ids']}")
    return info


async def wait_sync(page, name, timeout_ms=8000):
    start = asyncio.get_event_loop().time()
    while True:
        lbl = await page.evaluate("document.getElementById('syncLabel')?.textContent || '?'")
        if lbl != 'Syncing…':
            print(f"  [{name}] settled → '{lbl}'")
            return lbl
        if (asyncio.get_event_loop().time() - start) * 1000 > timeout_ms:
            print(f"  [{name}] TIMEOUT still '{lbl}'")
            return lbl
        await page.wait_for_timeout(150)


async def shot(a, b, slug, label_l, label_r, status_l=None, status_r=None):
    pa = f"{OUT}/_a_{slug}.png"
    pb = f"{OUT}/_b_{slug}.png"
    await asyncio.gather(a.screenshot(path=pa), b.screenshot(path=pb))
    out = f"{OUT}/{slug}.png"
    sidebyside(pa, pb, out, label_l, label_r, status_l, status_r)
    return out


def check(cond, msg):
    if not cond:
        FAILURES.append(msg)
        print(f"  ✗ FAIL: {msg}")
    else:
        print(f"  ✓ {msg}")


# ── Main demo ─────────────────────────────────────────────────────────────────

async def run_demo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        WW, WH = 900, 720
        ctx_a = await browser.new_context(viewport={"width": WW, "height": WH})
        ctx_b = await browser.new_context(viewport={"width": WW, "height": WH})
        a, b  = await ctx_a.new_page(), await ctx_b.new_page()

        errors = {"A": [], "B": []}
        a.on("console", lambda m: errors["A"].append(m.text) if m.type == "error" else None)
        b.on("console", lambda m: errors["B"].append(m.text) if m.type == "error" else None)

        # ════════════════════════════════════════════════════════════════
        # PHASE 1 — Fresh load
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 1 — Fresh start", "Both devices loading the app")
        await asyncio.gather(
            a.goto(APP, wait_until="networkidle"),
            b.goto(APP, wait_until="networkidle"),
        )
        await asyncio.gather(a.wait_for_timeout(1200), b.wait_for_timeout(1200))
        await asyncio.gather(wait_sync(a, "A"), wait_sync(b, "B"))
        p1 = await shot(a, b, "01_fresh",
                        "Device A — fresh load", "Device B — fresh load")
        frame(p1, 3.0)
        print("✓ Phase 1: fresh load")

        # ════════════════════════════════════════════════════════════════
        # PHASE 2 — Device A adds 4 tasks → auto-push
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 2 — Device A adds tasks", "Auto-push fires after 1.5s debounce")
        for text in ["Write product vision doc", "Schedule Q3 retro",
                     "Fix the login bug", "Review design mockups"]:
            await a.fill("#taskInput", text)
            await a.keyboard.press("Enter")
            await a.wait_for_timeout(200)
        await a.wait_for_timeout(2500)           # debounce + push
        await wait_sync(a, "A")
        a_s2 = await st(a, "A")
        check(a_s2["count"] == 4, f"A has 4 tasks after adding (got {a_s2['count']})")
        p2 = await shot(a, b, "02_A_pushed",
                        "Device A — 4 tasks, auto-pushed ✓",
                        "Device B — still empty",
                        status_l="4 tasks pushed to server")
        frame(p2, 3.5)
        print("✓ Phase 2: A added & pushed 4 tasks")

        # ════════════════════════════════════════════════════════════════
        # PHASE 3 — Device B one-time key setup
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 3 — Device B applies A's sync key", "One-time setup: Apply & sync")
        sync_key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        assert sync_key, "No sync key on A!"
        print(f"  Sync key: {sync_key[:11]}…")

        await b.click(".sync-settings-btn")
        await b.wait_for_timeout(300)
        await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
        await b.wait_for_timeout(300)
        await b.fill("#syncKeyField", sync_key)
        await b.click("button.sync-apply-btn")
        await b.wait_for_timeout(3500)
        await wait_sync(b, "B")
        b_s3 = await st(b, "B")
        check(b_s3["count"] == 4, f"B pulled A's 4 tasks (got {b_s3['count']})")
        p3 = await shot(a, b, "03_B_key_applied",
                        "Device A — unchanged (4 tasks)",
                        "Device B — key applied, pulled A's tasks ✓",
                        status_r="4 tasks received from server")
        frame(p3, 4.0)
        print("✓ Phase 3: B applied key and pulled A's tasks")

        # ════════════════════════════════════════════════════════════════
        # PHASE 4 — Device B adds independent tasks → auto-push
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 4 — Device B adds its own tasks", "Independent work before merge")
        for text in ["Book team offsite", "Audit accessibility", "Ship v2.1 release notes"]:
            await b.fill("#taskInput", text)
            await b.keyboard.press("Enter")
            await b.wait_for_timeout(200)
        await b.wait_for_timeout(2500)
        await wait_sync(b, "B")
        b_s4 = await st(b, "B")
        check(b_s4["count"] == 7, f"B has 7 tasks after adding 3 more (got {b_s4['count']})")
        p4 = await shot(a, b, "04_B_pushed",
                        "Device A — still 4 tasks",
                        "Device B — 7 tasks, auto-pushed ✓",
                        status_r="7 tasks pushed to server")
        frame(p4, 3.5)
        print("✓ Phase 4: B added & pushed 3 more tasks (7 total)")

        # ════════════════════════════════════════════════════════════════
        # PHASE 5 — Device A syncs → gets B's 3 new tasks (merge to 7)
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 5 — Device A presses Sync", "Pull + per-task merge + push")
        await a.evaluate("syncNow()")
        await a.wait_for_timeout(3500)
        await wait_sync(a, "A")
        a_s5 = await st(a, "A")
        check(a_s5["count"] == 7, f"A merged to 7 tasks (got {a_s5['count']})")
        p5 = await shot(a, b, "05_A_merged",
                        "Device A — merged! 7 tasks ✓",
                        "Device B — 7 tasks (its own)",
                        status_l="Pulled B's 3 tasks, now 7 total")
        frame(p5, 4.0)
        print("✓ Phase 5: A synced — merged to 7 tasks")

        # ════════════════════════════════════════════════════════════════
        # PHASE 6 — Device B syncs → receives merged result
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 6 — Device B syncs", "Both devices now identical")
        await b.evaluate("syncNow()")
        await b.wait_for_timeout(3500)
        await wait_sync(b, "B")
        b_s6 = await st(b, "B")
        check(b_s6["count"] == 7, f"B also has 7 tasks after sync (got {b_s6['count']})")
        check(sorted(a_s5["ids"]) == sorted(b_s6["ids"]), "A and B have identical task IDs")
        p6 = await shot(a, b, "06_both_synced",
                        "Device A — 7 tasks ✓",
                        "Device B — 7 tasks ✓  (identical)",
                        status_l="Synced", status_r="Synced — same as A")
        frame(p6, 4.5)
        print("✓ Phase 6: both have 7 identical tasks")

        # ════════════════════════════════════════════════════════════════
        # PHASE 7 — Status change on B → A syncs to receive it
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 7 — Status change propagation", "B marks task → A syncs → sees change")
        first_id = await b.evaluate("document.querySelector('.task-item')?.dataset?.id")
        assert first_id, "No task items on B"
        await b.evaluate(f"changeStatus({first_id}, 'action')")
        await b.wait_for_timeout(2500)
        await wait_sync(b, "B")
        print(f"  B marked task {first_id} as 'action', auto-pushed")

        await a.evaluate("syncNow()")
        await a.wait_for_timeout(3500)
        await wait_sync(a, "A")
        a_cls = await a.evaluate(
            f"document.querySelector('.task-item[data-id=\"{first_id}\"]')?.className || ''"
        )
        check("status-action" in (a_cls or ""),
              f"Status change propagated from B to A (classes: {a_cls})")
        p7 = await shot(a, b, "07_status_propagated",
                        "Device A — received status change ✓",
                        "Device B — made the change",
                        status_l="task marked 'action' by B")
        frame(p7, 4.0)
        print("✓ Phase 7: status propagated B → A")

        # ════════════════════════════════════════════════════════════════
        # PHASE 8 — Delete on A (tombstone) → B syncs → task gone
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 8 — Delete propagation", "A deletes via tombstone → B syncs → gone")
        a_state_p8 = await st(a, "A-pre-delete")
        del_id = a_state_p8["ids"][0]
        await a.evaluate(f"""
            const idx = tasks.findIndex(t => String(t.id) === '{del_id}');
            if (idx !== -1) tasks[idx] = {{ id: tasks[idx].id, _deleted: true, updatedAt: new Date().toISOString() }};
            saveAndRender();
        """)
        await a.wait_for_timeout(2500)
        await wait_sync(a, "A")
        a_s8 = await st(a, "A-after-delete")
        check(a_s8["count"] == 6, f"A has 6 tasks after delete (got {a_s8['count']})")

        await b.evaluate("syncNow()")
        await b.wait_for_timeout(3500)
        await wait_sync(b, "B")
        b_s8 = await st(b, "B-after-delete-sync")
        check(del_id not in b_s8["ids"],
              f"Deleted task {del_id} gone on B after sync")
        check(b_s8["count"] == 6, f"B has 6 tasks (same as A) (got {b_s8['count']})")
        p8 = await shot(a, b, "08_delete_propagated",
                        "Device A — 6 tasks (deleted one) ✓",
                        "Device B — also 6 tasks ✓ (tombstone synced)",
                        status_l="Deleted 1 task, synced")
        frame(p8, 4.0)
        print("✓ Phase 8: delete propagated via tombstone")

        # ════════════════════════════════════════════════════════════════
        # PHASE 9 — 6-round back and forth
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 9 — 6 rounds of back-and-forth", "Both add tasks every round, then sync")
        expected_count = 6   # current count after phase 8

        round_frames = []
        for rnd in range(1, 7):
            # A adds a task
            await a.fill("#taskInput", f"R{rnd}-from-A")
            await a.keyboard.press("Enter")
            await a.wait_for_timeout(2500)
            await wait_sync(a, f"A-r{rnd}")

            # B adds a task
            await b.fill("#taskInput", f"R{rnd}-from-B")
            await b.keyboard.press("Enter")
            await b.wait_for_timeout(2500)
            await wait_sync(b, f"B-r{rnd}")

            expected_count += 2   # one from A, one from B

            # A syncs
            await a.evaluate("syncNow()")
            await a.wait_for_timeout(3500)
            await wait_sync(a, f"A-sync-r{rnd}")
            a_r = await st(a, f"A-round{rnd}")

            # B syncs
            await b.evaluate("syncNow()")
            await b.wait_for_timeout(3500)
            await wait_sync(b, f"B-sync-r{rnd}")
            b_r = await st(b, f"B-round{rnd}")

            ids_match = sorted(a_r["ids"]) == sorted(b_r["ids"])
            count_ok  = a_r["count"] == expected_count and b_r["count"] == expected_count
            check(ids_match, f"Round {rnd}: A and B have identical task IDs")
            check(count_ok,  f"Round {rnd}: both have {expected_count} tasks (A={a_r['count']}, B={b_r['count']})")

            rf = await shot(a, b, f"09_round{rnd:02d}",
                            f"Device A — Round {rnd} — {a_r['count']} tasks",
                            f"Device B — Round {rnd} — {b_r['count']} tasks",
                            status_l=f"A={a_r['count']} ✓" if count_ok else f"A={a_r['count']} ✗",
                            status_r=f"B={b_r['count']} ✓" if ids_match else f"B={b_r['count']} ✗ mismatch")
            round_frames.append(rf)
            frame(rf, 2.5)
            print(f"✓ Phase 9 round {rnd}: A={a_r['count']}, B={b_r['count']}, ids_match={ids_match}")

        print("✓ Phase 9: 6 back-and-forth rounds complete")

        # ════════════════════════════════════════════════════════════════
        # PHASE 10 — A syncs 5× in a row (idempotency stress test)
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 10 — Rapid sync (idempotency)", "A presses Sync 5× in a row — count must stay constant")
        pre_count = (await st(a, "A-pre-stress"))["count"]
        for i in range(1, 6):
            await a.evaluate("syncNow()")
            await a.wait_for_timeout(2500)
            await wait_sync(a, f"A-stress-{i}")
            post = (await st(a, f"A-stress-{i}"))["count"]
            check(post == pre_count, f"Stress sync {i}: task count stable at {pre_count} (got {post})")

        p10 = await shot(a, b, "10_stress_done",
                         f"Device A — {pre_count} tasks (unchanged after 5 syncs) ✓",
                         "Device B — unchanged",
                         status_l="5× sync idempotent ✓")
        frame(p10, 3.5)
        print("✓ Phase 10: 5 rapid syncs — count stable")

        # ════════════════════════════════════════════════════════════════
        # PHASE 11 — Final state verification
        # ════════════════════════════════════════════════════════════════
        add_title("Phase 11 — Final state verification", "One last sync on both, confirm identical")
        await a.evaluate("syncNow()")
        await a.wait_for_timeout(3500)
        await wait_sync(a, "A-final")
        await b.evaluate("syncNow()")
        await b.wait_for_timeout(3500)
        await wait_sync(b, "B-final")
        a_fin = await st(a, "A-final")
        b_fin = await st(b, "B-final")
        check(sorted(a_fin["ids"]) == sorted(b_fin["ids"]),
              f"Final: A and B have identical task IDs ({a_fin['count']} tasks)")
        p11 = await shot(a, b, "11_final",
                         f"Device A — final state: {a_fin['count']} tasks ✓",
                         f"Device B — final state: {b_fin['count']} tasks ✓",
                         status_l="Synced ✓", status_r="Synced ✓ — identical to A")
        frame(p11, 5.0)
        print("✓ Phase 11: final state verified")

        await browser.close()

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    if FAILURES:
        print(f"FAILURES ({len(FAILURES)}):")
        for f in FAILURES:
            print(f"  ✗ {f}")
    else:
        print("ALL CHECKS PASSED ✓")
    print(f"{'─'*50}\n")

    # ── Stitch video ─────────────────────────────────────────────────────
    flist = f"{OUT}/_frames.txt"
    with open(flist, "w") as fh:
        for path, hold in FRAMES:
            fh.write(f"file '{path}'\nduration {hold}\n")
        last_path, last_hold = FRAMES[-1]
        fh.write(f"file '{last_path}'\nduration 0.1\n")

    out_video = f"{OUT}/demo_comprehensive.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", flist,
        "-vf", "scale=iw:ih:flags=lanczos,fps=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "fast",
        out_video,
    ], check=True, capture_output=True)
    print(f"  → {out_video}")
    return len(FAILURES) == 0


def main():
    print("Starting servers…")
    http_srv = subprocess.Popen(
        ["node", "/home/pranav/sandboxes/woooosh/serve.cjs", "3000", "/home/pranav/sandboxes/woooosh"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    sync_srv = subprocess.Popen(
        ["node", "/home/pranav/sandboxes/woooosh/sync-server.js"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    ok = False
    try:
        ok = asyncio.run(run_demo())
    finally:
        http_srv.terminate()
        sync_srv.terminate()
        print("Servers stopped.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
