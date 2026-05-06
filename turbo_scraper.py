import asyncio
import json
import os
import aiohttp
import aiofiles
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import time

# --- CONFIGURATION ---
TOTAL_PAGES = 65
CONCURRENT_WORKERS = 30  # Boosted for lightweight pages
DATA_DIR = "data"
ASSETS_DIR = "assets/images"
QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")
RESULTS_FILE = os.path.join(DATA_DIR, "results.json")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")
MEMORY_FILE = "SCRAPER_MEMORY.md"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Ad-blocking list
AD_DOMAINS = [
    "google-analytics.com", "googletagmanager.com", "googlesyndication.com",
    "adservice.google", "analytics.google.com", "doubleclick.net",
    "adnxs.com", "carbonads.net", "mgid.com", "popads.net", "popcash.net"
]

async def update_memory_md(phase1_done=False, phase2_count=0, total=0):
    progress = (phase2_count / total * 100) if total > 0 else 0
    content = f"""# 🧠 NulledScripts Turbo Scraper Memory

## 📊 Current Progress (Hyper-Speed Mode)
- **Status**: [{"x" if phase1_done else " "}] Phase 1: Link Harvesting
- **Status**: [{"x" if progress == 100 and phase1_done else " "}] Phase 2: Content Extraction ({phase2_count}/{total})
- **Completion**: {progress:.1f}%

---
*Ad-Shield Active | Speed Boost Active*
"""
    async with aiofiles.open(MEMORY_FILE, "w") as f:
        await f.write(content)

async def block_ads(route):
    if any(domain in route.request.url for domain in AD_DOMAINS) or \
       route.request.resource_type in ["image", "media", "font"]:
        await route.abort()
    else:
        await route.continue_()

async def download_image(session, url, item_id):
    if not url: return None
    if url.startswith("//"): url = "https:" + url
    if not url.startswith("http"): url = "https://nulledscripts.net" + url
    file_path = os.path.join(ASSETS_DIR, f"{item_id}.jpg")
    try:
        # Strict 3-second timeout for images
        async with session.get(url, timeout=3) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
                return file_path
    except:
        return None

async def scrape_item(context, url, semaphore, results, status_data, session, total_count):
    async with semaphore:
        item_id = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
        print(f"  [>] Starting: {item_id}")
        page = await context.new_page()
        # Enable Ad-Blocking
        await page.route("**/*", block_ads)
        
        try:
            # 1. Scrape Item Page
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            title_node = await page.query_selector(".product-header h2")
            title = await title_node.inner_text() if title_node else "No Title"
            
            card_node = await page.query_selector(".product-card")
            description = await card_node.inner_html() if card_node else ""
            
            preview_link = await page.get_attribute("a.btn-primary.new-window", "href")
            
            # Optional Image (Fast check)
            img_node = await page.query_selector(".s-product-thumb img")
            img_url = await img_node.get_attribute("src") if img_node else None
            
            # 2. Handle Download Link
            download_btn = await page.query_selector("a.custom-btn")
            final_download_url = None
            
            if download_btn:
                download_href = await download_btn.get_attribute("href")
                if not download_href.startswith("http"): download_href = "https://nulledscripts.net" + download_href
                
                print(f"    [~] Timer-Wait: {item_id}")
                try:
                    await page.goto(download_href, wait_until="domcontentloaded", timeout=15000)
                    # The site timer is 10s. We wait exactly for the button.
                    await page.wait_for_selector("#free-download-btn", timeout=15000)
                    final_download_url = await page.get_attribute("#free-download-btn", "href")
                except:
                    final_download_url = download_href
            
            local_img = await download_image(session, img_url, item_id)

            data = {
                "id": item_id, "url": url, "title": title.strip(),
                "description_html": description, "preview_url": preview_link,
                "download_url": final_download_url, "image_local": local_img
            }
            
            results.append(data)
            status_data[url] = "done"
            print(f"  [✓] Finished: {item_id} ({len(results)} total)")
            
            # Periodic saves
            if len(results) % 2 == 0:
                async with aiofiles.open(RESULTS_FILE, "w") as f:
                    await f.write(json.dumps(results, indent=2))
                async with aiofiles.open(STATUS_FILE, "w") as f:
                    await f.write(json.dumps(status_data))
                await update_memory_md(True, len(results), total_count)

        except Exception as e:
            print(f"  [!] Skipped {item_id}: {str(e)[:50]}")
        finally:
            await page.close()

async def main():
    start_time = time.time()
    
    if not os.path.exists(QUEUE_FILE):
        print("❌ No queue found.")
        return

    async with aiofiles.open(QUEUE_FILE, "r") as f:
        links = json.loads(await f.read())

    results, status_data = [], {url: "pending" for url in links}
    if os.path.exists(RESULTS_FILE):
        async with aiofiles.open(RESULTS_FILE, "r") as f: results = json.loads(await f.read())
    if os.path.exists(STATUS_FILE):
        async with aiofiles.open(STATUS_FILE, "r") as f: status_data = json.loads(await f.read())

    remaining = [url for url in links if status_data.get(url) != "done"]
    print(f"🚀 Phase 2: Hyper-Speed Mode ({len(remaining)} items, {CONCURRENT_WORKERS} workers)")

    semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        async with aiohttp.ClientSession() as session:
            tasks = [scrape_item(context, url, semaphore, results, status_data, session, len(links)) for url in remaining]
            await asyncio.gather(*tasks)

        await browser.close()

    print(f"🎯 Mission Accomplished in {(time.time() - start_time)/60:.2f} minutes!")
    await update_memory_md(True, len(results), len(links))

if __name__ == "__main__":
    asyncio.run(main())
