"""
Diagnostic test — reproduces back-and-forth sync scenarios and logs every state.
Runs against http://localhost:3000 + sync server on :3001.
"""
import asyncio, json, subprocess, sys, time
from playwright.async_api import async_playwright

CHROM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP   = "http://localhost:3000"

def get_tasks_js():
    """JS that returns current visible task count and IDs from DOM + sync status label."""
    return """
    (() => {
        const items = document.querySelectorAll('.task-item');
        const label = document.getElementById('syncLabel')?.textContent || '?';
        const ids = [...items].map(el => el.dataset.id);
        return { count: items.length, label, ids };
    })()
    """

async def state(page, name):
    """Print current sync label + task list for a page."""
    info = await page.evaluate(get_tasks_js())
    print(f"  [{name}] status='{info['label']}' tasks={info['count']} ids={info['ids']}")
    return info

async def wait_sync_done(page, name, timeout=6000):
    """Wait until sync label is no longer 'Syncing…'."""
    start = asyncio.get_event_loop().time()
    while True:
        label = await page.evaluate("document.getElementById('syncLabel')?.textContent || '?'")
        if label != 'Syncing…':
            print(f"  [{name}] sync settled → '{label}'")
            return label
        if (asyncio.get_event_loop().time() - start) * 1000 > timeout:
            print(f"  [{name}] TIMEOUT waiting for sync to settle — still '{label}'")
            return label
        await page.wait_for_timeout(150)

async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROM,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--enable-logging", "--v=1"]
        )

        ctx_a = await browser.new_context(viewport={"width": 900, "height": 720})
        ctx_b = await browser.new_context(viewport={"width": 900, "height": 720})

        # Capture browser console errors
        errors = {"A": [], "B": []}
        ctx_a_page = await ctx_a.new_page()
        ctx_b_page = await ctx_b.new_page()
        ctx_a_page.on("console", lambda m: errors["A"].append(m.text) if m.type == "error" else None)
        ctx_b_page.on("console", lambda m: errors["B"].append(m.text) if m.type == "error" else None)
        a, b = ctx_a_page, ctx_b_page

        print("\n══════════════════════════════════════════════")
        print("SCENARIO 1: A creates tasks → B gets key → A syncs again")
        print("══════════════════════════════════════════════")

        # Fresh load
        await asyncio.gather(
            a.goto(APP, wait_until="networkidle"),
            b.goto(APP, wait_until="networkidle"),
        )
        await asyncio.gather(a.wait_for_timeout(1000), b.wait_for_timeout(1000))
        print("→ Both loaded.")
        await state(a, "A-init"); await state(b, "B-init")

        # A adds 3 tasks
        for text in ["Task Alpha", "Task Beta", "Task Gamma"]:
            await a.fill("#taskInput", text)
            await a.keyboard.press("Enter")
            await a.wait_for_timeout(150)
        print("→ A added 3 tasks. Waiting for auto-push (1.5s debounce + network)…")
        await a.wait_for_timeout(2500)
        await wait_sync_done(a, "A")
        await state(a, "A-after-push")

        # Get sync key from A
        sync_key = await a.evaluate("localStorage.getItem('wooooshSyncKey')")
        assert sync_key, "No sync key on A!"
        print(f"  A sync key: {sync_key[:11]}…")

        # B enters key → Apply & sync
        print("→ B: opening sync panel, entering key…")
        await b.click(".sync-settings-btn")
        await b.wait_for_timeout(300)
        await b.evaluate("document.querySelectorAll('button.sync-action-btn')[1].click()")
        await b.wait_for_timeout(300)
        await b.fill("#syncKeyField", sync_key)
        await b.click("button.sync-apply-btn")
        print("  B: clicked Apply & sync, waiting…")
        await b.wait_for_timeout(3500)
        await wait_sync_done(b, "B")
        b_state = await state(b, "B-after-key")
        assert b_state["count"] == 3, f"FAIL: B should have 3 tasks after key entry, got {b_state['count']}"
        print("  ✓ B has 3 tasks (A's tasks pulled)")

        # === THE FAILING SCENARIO: A syncs AGAIN ===
        print("\n→ A: pressing Sync (this is the step that reportedly fails)…")
        await a.evaluate("syncNow()")
        await a.wait_for_timeout(3000)
        label = await wait_sync_done(a, "A")
        a_state = await state(a, "A-after-sync-again")

        if label == "Offline":
            print(f"  ✗ FAIL: A is Offline after sync! Console errors: {errors['A']}")
        elif a_state["count"] != 3:
            print(f"  ✗ FAIL: A has wrong task count: {a_state['count']} (expected 3)")
        else:
            print("  ✓ A synced successfully, still has 3 tasks")

        print("\n══════════════════════════════════════════════")
        print("SCENARIO 2: B adds tasks independently → A+B both sync → must merge")
        print("══════════════════════════════════════════════")

        # B adds 3 independent tasks
        for text in ["Task Delta", "Task Epsilon", "Task Zeta"]:
            await b.fill("#taskInput", text)
            await b.keyboard.press("Enter")
            await b.wait_for_timeout(150)
        print("→ B added 3 tasks. Waiting for auto-push…")
        await b.wait_for_timeout(2500)
        await wait_sync_done(b, "B")
        await state(b, "B-after-B-push")

        # A presses Sync → should get 6 tasks
        print("→ A: pressing Sync — should get B's 3 tasks merged in…")
        await a.evaluate("syncNow()")
        await a.wait_for_timeout(3000)
        label = await wait_sync_done(a, "A")
        a_state = await state(a, "A-after-merge-sync")

        if label == "Offline":
            print(f"  ✗ FAIL: A is Offline! Console errors: {errors['A']}")
        elif a_state["count"] != 6:
            print(f"  ✗ FAIL: A should have 6 tasks, has {a_state['count']}")
        else:
            print("  ✓ A has 6 tasks (merged)")

        # B presses Sync → should also see 6 tasks
        print("→ B: pressing Sync — should get merged blob from A…")
        await b.evaluate("syncNow()")
        await b.wait_for_timeout(3000)
        await wait_sync_done(b, "B")
        b_state = await state(b, "B-after-merge-sync")

        if b_state["count"] != 6:
            print(f"  ✗ FAIL: B should have 6 tasks, has {b_state['count']}")
        else:
            print("  ✓ B has 6 tasks (same as A)")

        # Verify identical task IDs
        assert sorted(a_state["ids"]) == sorted(b_state["ids"]), \
            f"FAIL: A and B have different task IDs!\n  A: {a_state['ids']}\n  B: {b_state['ids']}"
        print("  ✓ A and B have identical task IDs")

        print("\n══════════════════════════════════════════════")
        print("SCENARIO 3: Status change on B → A syncs to get it")
        print("══════════════════════════════════════════════")

        first_id = await b.evaluate("document.querySelector('.task-item')?.dataset?.id")
        assert first_id, "No task items on B"
        await b.evaluate(f"changeStatus({first_id}, 'action')")
        await b.wait_for_timeout(2500)
        await wait_sync_done(b, "B")
        print(f"  B marked task {first_id} as action, auto-pushed")

        await a.evaluate("syncNow()")
        await a.wait_for_timeout(3000)
        await wait_sync_done(a, "A")
        a_task_status = await a.evaluate(f"document.querySelector('.task-item[data-id=\"{first_id}\"]')?.classList?.value")
        print(f"  A's task {first_id} classes: {a_task_status}")
        if a_task_status and "status-action" in a_task_status:
            print("  ✓ Status change propagated from B to A")
        else:
            print(f"  ✗ FAIL: Status not propagated. Classes: {a_task_status}")

        print("\n══════════════════════════════════════════════")
        print("SCENARIO 4: Delete on A → B syncs → task gone")
        print("══════════════════════════════════════════════")

        # Delete a task on A (using JS to avoid confirm dialog)
        del_id = a_state["ids"][0]
        await a.evaluate(f"""
            const idx = tasks.findIndex(t => String(t.id) === '{del_id}');
            if (idx !== -1) tasks[idx] = {{ id: tasks[idx].id, _deleted: true, updatedAt: new Date().toISOString() }};
            saveAndRender();
        """)
        await a.wait_for_timeout(2500)
        await wait_sync_done(a, "A")
        a_state2 = await state(a, "A-after-delete")
        print(f"  A deleted task {del_id}, now has {a_state2['count']} tasks")

        # B syncs → should not see deleted task
        await b.evaluate("syncNow()")
        await b.wait_for_timeout(3000)
        await wait_sync_done(b, "B")
        b_state2 = await state(b, "B-after-delete-sync")
        b_has_deleted = del_id in b_state2["ids"]
        if b_has_deleted:
            print(f"  ✗ FAIL: B still shows deleted task {del_id}")
        else:
            print(f"  ✓ Deleted task gone on B too ({b_state2['count']} tasks)")

        print("\n══════════════════════════════════════════════")
        print("SCENARIO 5: Multiple rounds back and forth")
        print("══════════════════════════════════════════════")

        for round_num in range(1, 4):
            # A adds a task
            await a.fill("#taskInput", f"Round {round_num} — from A")
            await a.keyboard.press("Enter")
            await a.wait_for_timeout(2500)
            await wait_sync_done(a, "A")

            # B adds a task
            await b.fill("#taskInput", f"Round {round_num} — from B")
            await b.keyboard.press("Enter")
            await b.wait_for_timeout(2500)
            await wait_sync_done(b, "B")

            # A syncs
            await a.evaluate("syncNow()")
            await a.wait_for_timeout(3000)
            await wait_sync_done(a, "A")
            a_r = await state(a, f"A-round{round_num}")

            # B syncs
            await b.evaluate("syncNow()")
            await b.wait_for_timeout(3000)
            await wait_sync_done(b, "B")
            b_r = await state(b, f"B-round{round_num}")

            if sorted(a_r["ids"]) == sorted(b_r["ids"]):
                print(f"  ✓ Round {round_num}: A={a_r['count']} tasks, B={b_r['count']} tasks — identical")
            else:
                print(f"  ✗ Round {round_num}: MISMATCH  A={a_r['ids']}  B={b_r['ids']}")

        if errors["A"]:
            print(f"\n⚠ Console errors on A: {errors['A']}")
        if errors["B"]:
            print(f"⚠ Console errors on B: {errors['B']}")

        await browser.close()

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
        asyncio.run(run_tests())
    finally:
        http_srv.terminate(); sync_srv.terminate()
        print("\nServers stopped.")

if __name__ == "__main__":
    main()
