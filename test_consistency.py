"""
Consistency diagnosis — proves the Netlify sync bug and its fix.

The production bug only appears on an *eventually consistent* backend
(Netlify Blobs with default consistency). Our local sync-server.js can now
simulate that via SYNC_STALE_MS.

PHASE A  (SYNC_STALE_MS=4000 — eventual consistency):
    Rapid back-and-forth WITHIN the stale window. Expect the two devices to
    DIVERGE — exactly the "back and forth stopped working" symptom.

PHASE B  (SYNC_STALE_MS=0 — strong consistency, == the deployed fix):
    Same rapid back-and-forth. Expect PERFECT convergence every round.

Exit code 0 only if: Phase A reproduced divergence AND Phase B converged.
"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

CHROM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP   = "http://localhost:3000"

TASKS_JS = """
(() => {
    const items = document.querySelectorAll('.task-item');
    return { count: items.length, ids: [...items].map(el => el.dataset.id),
             label: document.getElementById('syncLabel')?.textContent || '?' };
})()
"""


async def info(page):
    return await page.evaluate(TASKS_JS)


async def wait_settle(page, timeout_ms=8000):
    start = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start) * 1000 < timeout_ms:
        lbl = await page.evaluate("document.getElementById('syncLabel')?.textContent || '?'")
        if lbl != 'Syncing…':
            return lbl
        await page.wait_for_timeout(120)
    return '?'


async def add_task(page, text):
    await page.fill("#taskInput", text)
    await page.keyboard.press("Enter")


async def sync_to_converge(a, b, max_syncs, gap_ms):
    """Alternately sync A and B (rapidly, no waiting out any stale window)
    until their task-id sets match, or max_syncs is exhausted.
    Returns (converged: bool, syncs_used: int)."""
    for i in range(1, max_syncs + 1):
        await a.evaluate("syncNow()"); await a.wait_for_timeout(gap_ms); await wait_settle(a)
        await b.evaluate("syncNow()"); await b.wait_for_timeout(gap_ms); await wait_settle(b)
        ai, bi = await info(a), await info(b)
        if sorted(ai["ids"]) == sorted(bi["ids"]):
            return True, i
    return False, max_syncs


async def run_phase(label, stale_ms, rounds, max_syncs, gap_ms):
    """Start a server with the given staleness, run `rounds` of fair
    back-and-forth (both add a task, then sync-to-converge). Returns
    (converged_every_round: bool, rounds_converged: int, rounds: int)."""
    print(f"\n{'='*60}\nPHASE {label}  (SYNC_STALE_MS={stale_ms})\n{'='*60}")
    env = dict(os.environ, SYNC_STALE_MS=str(stale_ms))
    srv = subprocess.Popen(["node", "/home/user/woooosh/sync-server.js"],
                           env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)

    rounds_converged = 0
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(executable_path=CHROM,
                args=["--no-sandbox", "--disable-dev-shm-usage"])
            ca = await browser.new_context(viewport={"width": 800, "height": 700})
            cb = await browser.new_context(viewport={"width": 800, "height": 700})
            a, b = await ca.new_page(), await cb.new_page()

            await asyncio.gather(a.goto(APP, wait_until="networkidle"),
                                 b.goto(APP, wait_until="networkidle"))
            await asyncio.gather(wait_settle(a), wait_settle(b))

            # A seeds 2 tasks, waits for auto-push + propagation past the window
            await add_task(a, "Seed A-1"); await a.wait_for_timeout(250)
            await add_task(a, "Seed A-2")
            await a.wait_for_timeout(2000)
            await wait_settle(a)
            await a.wait_for_timeout(stale_ms + 500)

            # B applies A's key (one-time setup) → first sync
            key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
            await b.click(".sync-settings-btn"); await b.wait_for_timeout(200)
            await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
            await b.wait_for_timeout(200)
            await b.fill("#syncKeyField", key)
            await b.click("button.sync-apply-btn")
            await b.wait_for_timeout(stale_ms + 1500)
            await wait_settle(b)
            bi = await info(b)
            print(f"  After key setup: B has {bi['count']} tasks "
                  f"(first sync {'OK' if bi['count'] == 2 else 'FAILED'})")

            # ── Fair back-and-forth: both add, then sync-to-converge ──────
            for rnd in range(1, rounds + 1):
                await add_task(a, f"A-r{rnd}")
                await a.wait_for_timeout(150)
                await add_task(b, f"B-r{rnd}")
                await b.wait_for_timeout(150)

                converged, used = await sync_to_converge(a, b, max_syncs, gap_ms)
                ai, bi = await info(a), await info(b)
                if converged:
                    rounds_converged += 1
                    print(f"  round {rnd}: ✓ converged in {used} sync(s) "
                          f"— both have {ai['count']} tasks")
                else:
                    print(f"  round {rnd}: ✗ FAILED to converge in {max_syncs} syncs "
                          f"(A={ai['count']}, B={bi['count']})")
            await browser.close()
    finally:
        srv.terminate()
    return rounds_converged == rounds, rounds_converged, rounds


async def main_async():
    # PHASE A — eventual consistency. Rapid sync-to-converge can't outrun the
    # 8s stale window, so rounds should FAIL to converge → reproduces the bug.
    all_conv_A, conv_A, total_A = await run_phase(
        "A — EVENTUAL", stale_ms=8000, rounds=5, max_syncs=3, gap_ms=250)

    # PHASE B — strong consistency (the deployed fix). Every round must
    # converge, across many rounds.
    all_conv_B, conv_B, total_B = await run_phase(
        "B — STRONG", stale_ms=0, rounds=20, max_syncs=4, gap_ms=250)

    print(f"\n{'#'*60}")
    ok_repro = conv_A < total_A          # at least one round failed → bug shown
    ok_fix   = all_conv_B                 # every round converged → fix works
    print(f"Phase A (eventual): {conv_A}/{total_A} rounds converged "
          f"→ bug reproduced: {ok_repro}")
    print(f"Phase B (strong):   {conv_B}/{total_B} rounds converged "
          f"→ fix works: {ok_fix}")
    print(f"{'#'*60}")
    if ok_repro and ok_fix:
        print("\n✓✓ DIAGNOSIS CONFIRMED: eventual consistency caused the bug;"
              "\n    strong consistency (the Netlify fix) resolves it"
              " for every round.\n")
        return 0
    print("\n✗ Inconclusive — see logs above.\n")
    return 1


def main():
    http = subprocess.Popen(
        ["python3", "-m", "http.server", "3000", "--directory", "/home/user/woooosh"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    try:
        code = asyncio.run(main_async())
    finally:
        http.terminate()
    sys.exit(code)


if __name__ == "__main__":
    main()
