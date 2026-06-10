"""
v2.3 test suite — Today panel, lift PRs, seeded habits, and the two
cross-device merge fixes (habit completions deep-merge, prs sync).

Scenarios:
  1. Fresh boot: no console errors, Today panel shows today's plan,
     5 seeded habits, Lifts card shows deadlift 365.
  2. Seed dedupe: two fresh devices (independent seeds) pair via sync key
     → still exactly 5 habits on both, not 10.
  3. Completions deep-merge: A checks Mon on habit X, B checks Tue on the
     SAME habit without syncing in between → after both sync, both devices
     show BOTH days checked.
  4. PR sync: A sets squat=315 → B syncs → B's input shows 315.
  5. Tasks regression: add on A → sync → appears on B.
"""
import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright

CHROM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP   = "http://localhost:3000"
FAILS = []


def check(cond, msg):
    print(("  ✓ " if cond else "  ✗ FAIL: ") + msg)
    if not cond:
        FAILS.append(msg)


async def settle(page, timeout_ms=8000):
    start = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start) * 1000 < timeout_ms:
        lbl = await page.evaluate("document.getElementById('syncLabel')?.textContent || '?'")
        if lbl != 'Syncing…':
            return lbl
        await page.wait_for_timeout(120)
    return '?'


async def pair_b_to_a(a, b):
    key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
    await b.click(".sync-settings-btn"); await b.wait_for_timeout(200)
    await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
    await b.wait_for_timeout(200)
    await b.fill("#syncKeyField", key)
    await b.click("button.sync-apply-btn")
    await b.wait_for_timeout(2500)
    await settle(b)


async def habit_state(page):
    return await page.evaluate("""
        (() => {
            const cards = [...document.querySelectorAll('.habit-card')];
            return cards.map(c => ({
                id: c.dataset.id,
                name: c.querySelector('.habit-name')?.textContent,
                checked: [...c.querySelectorAll('.habit-calendar-dot.completed')].length,
            }));
        })()
    """)


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROM,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ca = await browser.new_context(viewport={"width": 900, "height": 800})
        cb = await browser.new_context(viewport={"width": 900, "height": 800})
        a, b = await ca.new_page(), await cb.new_page()
        errors = {"A": [], "B": []}
        a.on("pageerror", lambda e: errors["A"].append(str(e)))
        b.on("pageerror", lambda e: errors["B"].append(str(e)))

        print("\n── 1. Fresh boot ──")
        await asyncio.gather(a.goto(APP, wait_until="networkidle"),
                             b.goto(APP, wait_until="networkidle"))
        await asyncio.gather(settle(a), settle(b))
        check(not errors["A"] and not errors["B"],
              f"no page errors on boot (A={errors['A']}, B={errors['B']})")

        today = await a.evaluate("document.querySelector('.today-day')?.textContent")
        expected_day = await a.evaluate("['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][new Date().getDay()]")
        check(today == expected_day, f"Today panel shows '{today}' (expected {expected_day})")
        focus = await a.evaluate("document.querySelectorAll('.today-value')[0]?.textContent")
        check(bool(focus and len(focus) > 3), f"Today focus populated: '{focus}'")

        # Habits view checks
        await a.evaluate("switchView('habits')")
        await a.wait_for_timeout(300)
        habits_a = await habit_state(a)
        check(len(habits_a) == 5, f"5 seeded habits on A (got {len(habits_a)})")
        names = [h["name"] for h in habits_a]
        check("Lift / BJJ" in names and "Post-dinner walk" in names,
              f"seeded habit names correct: {names}")
        dl = await a.evaluate("document.querySelectorAll('.lift-row')[2]?.querySelector('.lift-input')?.value")
        check(dl == "365", f"Lifts card shows deadlift current 365 (got {dl})")
        chip = await a.evaluate("document.querySelector('.today-chip-habits')?.textContent")
        check(chip == "Habits 0/5", f"habit chip shows 0/5 (got '{chip}')")

        print("\n── 2. Seed dedupe across two fresh devices ──")
        # Both devices booted fresh and seeded independently; pair B to A.
        await pair_b_to_a(a, b)
        await a.evaluate("syncNow()"); await a.wait_for_timeout(1500); await settle(a)
        await b.evaluate("syncNow()"); await b.wait_for_timeout(1500); await settle(b)
        await b.evaluate("switchView('habits')"); await b.wait_for_timeout(300)
        habits_a = await habit_state(a)
        habits_b = await habit_state(b)
        check(len(habits_a) == 5, f"A still has exactly 5 habits (got {len(habits_a)})")
        check(len(habits_b) == 5, f"B still has exactly 5 habits (got {len(habits_b)})")

        print("\n── 3. Habit completions deep-merge ──")
        # Use this week's Mon + Tue keys (both <= today only if today >= Tue;
        # use Monday + today to be safe on any weekday).
        keys = await a.evaluate("""
            (() => {
                const pad = n => String(n).padStart(2,'0');
                const k = d => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
                const today = new Date(); today.setHours(0,0,0,0);
                const since = today.getDay() === 0 ? 6 : today.getDay() - 1;
                const mon = new Date(today); mon.setDate(today.getDate() - since);
                return { mon: k(mon), today: k(today) };
            })()
        """)
        # A checks Monday on habit 1; B checks today on habit 1 — NO sync between.
        await a.evaluate(f"toggleHabitCompletion(1, '{keys['mon']}')")
        await b.evaluate(f"toggleHabitCompletion(1, '{keys['today']}')")
        await a.wait_for_timeout(2200); await settle(a)   # A auto-push (pull-merge-push)
        await b.wait_for_timeout(2200); await settle(b)   # B auto-push
        await a.evaluate("syncNow()"); await a.wait_for_timeout(1500); await settle(a)
        await b.evaluate("syncNow()"); await b.wait_for_timeout(1500); await settle(b)
        comp_a = await a.evaluate("JSON.stringify((habits.find(h=>h.id===1)||{}).completions||{})")
        comp_b = await b.evaluate("JSON.stringify((habits.find(h=>h.id===1)||{}).completions||{}))".replace('))', ')'))
        import json as _json
        ca_map, cb_map = _json.loads(comp_a), _json.loads(comp_b)
        if keys['mon'] == keys['today']:
            # It's Monday — both checked the same day; just verify it's set
            check(ca_map.get(keys['mon']) and cb_map.get(keys['mon']),
                  "same-day check-in synced (today is Monday)")
        else:
            check(bool(ca_map.get(keys['mon'])) and bool(ca_map.get(keys['today'])),
                  f"A has BOTH days after merge: {ca_map}")
            check(bool(cb_map.get(keys['mon'])) and bool(cb_map.get(keys['today'])),
                  f"B has BOTH days after merge: {cb_map}")

        print("\n── 4. PR sync ──")
        await a.evaluate("updatePr('squat', '315')")
        await a.wait_for_timeout(2200); await settle(a)
        await b.evaluate("syncNow()"); await b.wait_for_timeout(1500); await settle(b)
        sq_b = await b.evaluate("prs.squat?.current")
        check(sq_b == 315, f"B sees squat PR 315 after sync (got {sq_b})")
        sq_input = await b.evaluate("document.querySelectorAll('.lift-row')[0]?.querySelector('.lift-input')?.value")
        check(sq_input == "315", f"B's Lifts card input shows 315 (got {sq_input})")

        print("\n── 5. Tasks regression ──")
        await a.evaluate("switchView('tasks')"); await a.wait_for_timeout(200)
        await a.fill("#taskInput", "Regression task")
        await a.keyboard.press("Enter")
        await a.wait_for_timeout(2200); await settle(a)
        await b.evaluate("syncNow()"); await b.wait_for_timeout(1500); await settle(b)
        await b.evaluate("switchView('tasks')"); await b.wait_for_timeout(200)
        n_b = await b.evaluate("document.querySelectorAll('.task-item').length")
        check(n_b == 1, f"task synced A → B (B has {n_b} tasks)")

        check(not errors["A"] and not errors["B"],
              f"no page errors at end (A={errors['A']}, B={errors['B']})")
        await browser.close()

    print("\n" + "─" * 50)
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S):")
        for f in FAILS:
            print(f"  ✗ {f}")
        return 1
    print("ALL CHECKS PASSED ✓")
    return 0


def main():
    http_srv = subprocess.Popen(
        ["python3", "-m", "http.server", "3000", "--directory", "/home/user/woooosh"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sync_srv = subprocess.Popen(
        ["node", "/home/user/woooosh/sync-server.js"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        code = asyncio.run(run())
    finally:
        http_srv.terminate(); sync_srv.terminate()
    sys.exit(code)


if __name__ == "__main__":
    main()
