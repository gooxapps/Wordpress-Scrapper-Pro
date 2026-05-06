import asyncio
import json
import os
import aiohttp
import aiofiles
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import time
import random

# --- CONFIGURATION ---
CONCURRENT_WORKERS = 3  # Low for high success with Cloudflare
DATA_DIR = "data"
ASSETS_DIR = "assets/images"
RESULTS_FILE = os.path.join(DATA_DIR, "results.json")

os.makedirs(ASSETS_DIR, exist_ok=True)

# --- AI & LOGIC HELPERS ---
def categorize(title):
    title = title.lower()
    if any(k in title for k in ['delivery', 'food', 'restaurant', 'grocery']): return "Food & Delivery"
    if any(k in title for k in ['ecommerce', 'shop', 'store', 'multivendor']): return "E-commerce"
    if any(k in title for k in ['taxi', 'ride', 'uber', 'driver']): return "Taxi & Transport"
    if any(k in title for k in ['vpn', 'proxy', 'tunnel']): return "Security & VPN"
    if any(k in title for k in ['dating', 'social', 'chat', 'tinder']): return "Social & Dating"
    if any(k in title for k in ['quiz', 'game', 'education', 'learning']): return "Education & Games"
    if any(k in title for k in ['booking', 'hotel', 'salon', 'appointment']): return "Booking & Services"
    return "Multi-Purpose"

async def validate_link(session, url):
    if not url: return "Dead"
    try:
        async with session.head(url, timeout=5) as response:
            return "Active" if response.status < 400 else "Dead"
    except:
        return "Unknown"

async def download_image(session, url, item_id):
    if not url: return None
    if url.startswith("//"): url = "https:" + url
    if not url.startswith("http"): url = "https://nulledscripts.net" + url
    file_path = os.path.join(ASSETS_DIR, f"{item_id}.jpg")
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
                return f"assets/images/{item_id}.jpg"
    except:
        return None

async def repair_item(context, item, semaphore, results_map, session):
    async with semaphore:
        url = item['url']
        item_id = item['id']
        print(f"  [REPAIR] Target: {item_id}")
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        try:
            # 1. Cloudflare Bypass Navigation
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for "Checking your browser" to disappear (Max 15s)
            start_wait = time.time()
            while time.time() - start_wait < 15:
                title = await page.title()
                if "Checking your browser" not in title:
                    break
                await asyncio.sleep(2)
            
            # 2. Extract REAL Data
            title = await page.title()
            if "Checking your browser" in title:
                # If still stuck, try to find the h1
                h1 = await page.query_selector("h1")
                if h1: title = await h1.inner_text()

            # Clean Title
            title = title.split("|")[0].replace("NulledScripts", "").strip()
            
            # Description
            description = ""
            desc_node = await page.query_selector(".product-card")
            if desc_node: description = await desc_node.inner_html()
            
            # Image
            img_node = await page.query_selector(".s-product-thumb img")
            img_url = await img_node.get_attribute("src") if img_node else None
            local_img = await download_image(session, img_url, item_id)
            
            # Link Validation
            link_status = await validate_link(session, item.get('download_url'))
            
            # Update Item
            if title and "Checking your browser" not in title:
                results_map[item_id].update({
                    "title": title,
                    "description_html": description,
                    "image_local": local_img,
                    "category": categorize(title),
                    "link_status": link_status,
                    "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"  [✓] Repaired: {title[:40]}...")
            else:
                print(f"  [!] Failed to bypass protection for {item_id}")

            # Persistent Save
            async with aiofiles.open(RESULTS_FILE, "w") as f:
                await f.write(json.dumps(list(results_map.values()), indent=2))

        except Exception as e:
            print(f"  [!] Fatal Error {item_id}: {str(e)[:50]}")
        finally:
            await page.close()

async def main():
    if not os.path.exists(RESULTS_FILE): return

    async with aiofiles.open(RESULTS_FILE, "r") as f:
        results = json.loads(await f.read())
    
    results_map = {item['id']: item for item in results}
    
    # Repair items that have Cloudflare titles or are missing data
    to_repair = [item for item in results if "Checking your browser" in item.get('title', '') or not item.get('title')]
    
    if not to_repair:
        print("✨ No repairs needed. Everything looks clean!")
        return

    print(f"🚀 Repairing {len(to_repair)} items with Cloudflare Bypass & Intelligence...")

    semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        async with aiohttp.ClientSession() as session:
            tasks = [repair_item(context, item, semaphore, results_map, session) for item in to_repair]
            await asyncio.gather(*tasks)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
