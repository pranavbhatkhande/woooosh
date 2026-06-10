"""Mobile layout screenshots on Pranav's device sizes."""
import asyncio, subprocess, time
from playwright.async_api import async_playwright

CHROM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
APP = "http://localhost:3000"
DEVICES = [
    ("iphone_promax", 430, 932, 3),
    ("galaxy_ultra",  412, 915, 3.5),
    ("trifold_open",  840, 980, 2.5),
]


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROM,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        for name, w, h, dsf in DEVICES:
            ctx = await browser.new_context(
                viewport={"width": w, "height": h},
                device_scale_factor=dsf, is_mobile=True, has_touch=True)
            pg = await ctx.new_page()
            await pg.goto(APP, wait_until="networkidle")
            await pg.wait_for_timeout(1200)
            # seed a couple of tasks + a habit check so views look real
            for t in ["Review PR backlog", "Prep 5/3/1 sheet"]:
                await pg.fill("#taskInput", t)
                await pg.keyboard.press("Enter")
                await pg.wait_for_timeout(150)
            await pg.evaluate("""
                const pad = n => String(n).padStart(2,'0');
                const d = new Date();
                toggleHabitCompletion(1, `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`);
                switchView('tasks');
            """)
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=f"demo/mobile_{name}_tasks.png")
            await pg.evaluate("switchView('habits')")
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=f"demo/mobile_{name}_habits.png")
            await ctx.close()
            print(f"  ✓ {name} ({w}x{h})")
        await browser.close()


def main():
    http_srv = subprocess.Popen(
        ["python3", "-m", "http.server", "3000", "--directory", "/home/user/woooosh"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sync_srv = subprocess.Popen(
        ["node", "/home/user/woooosh/sync-server.js"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    try:
        asyncio.run(run())
    finally:
        http_srv.terminate(); sync_srv.terminate()


if __name__ == "__main__":
    main()
