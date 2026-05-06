import asyncio
import aiohttp
import json
import os
from bs4 import BeautifulSoup
import time

# --- CONFIGURATION ---
BASE_URL = "https://nullphpscript.com/categories/nulled-scripts/"
DATA_DIR = "data"
RESULTS_FILE = os.path.join(DATA_DIR, "results_nullphp.json")
QUEUE_FILE = os.path.join(DATA_DIR, "queue_nullphp.json")
CONCURRENT_LIMIT = 20

os.makedirs(DATA_DIR, exist_ok=True)

async def fetch(session, url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                return await response.text()
    except:
        return None

async def scrape_item(session, url, semaphore, results):
    async with semaphore:
        html = await fetch(session, url)
        if not html: return
        
        soup = BeautifulSoup(html, 'html.parser')
        item_id = url.strip('/').split('/')[-1]
        
        title = soup.find('h1', class_='post-title')
        title = title.get_text(strip=True) if title else "No Title"
        
        # Featured Image
        img_container = soup.find('div', class_='single-featured-image')
        img = img_container.find('img') if img_container else None
        img_url = img.get('src') if img else None
        
        # Content
        content = soup.find('div', class_='entry-content')
        content_html = str(content) if content else ""
        
        # Extract all links (mirrors)
        links = []
        if content:
            # Look for input values (this site uses them for mirror links)
            inputs = content.find_all('input', class_='nps-form-control')
            for inp in inputs:
                val = inp.get('value')
                if val and val.startswith('http'):
                    links.append(val)
            
            # Also look for regular <a> tags that might be demos
            all_a = content.find_all('a')
            for a in all_a:
                href = a.get('href')
                if href and ('lolinez.com' in href or 'demo' in a.get_text().lower()):
                    links.append(href)

        data = {
            "id": item_id,
            "url": url,
            "title": title,
            "description_html": content_html,
            "image_url": img_url,
            "image_local": f"assets/images/{item_id}.jpg" if img_url else None,
            "mirrors": list(set(links)),
            "category": "Nulled Script",
            "link_status": "Active" if links else "Dead",
            "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        results.append(data)
        print(f"  [✓] Scraped: {title[:50]}")
        
        # Periodic Save
        if len(results) % 5 == 0:
            with open(RESULTS_FILE, "w") as f:
                json.dump(results, f, indent=2)

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. DISCOVERY PHASE
        print("🔍 Starting Discovery Phase...")
        all_links = []
        for page_num in range(1, 51):  # Scan first 50 pages
            url = BASE_URL if page_num == 1 else f"{BASE_URL}page/{page_num}/"
            print(f"  [>] Scanning Page {page_num}...")
            html = await fetch(session, url)
            if not html: break
            
            soup = BeautifulSoup(html, 'html.parser')
            posts = soup.find_all('h2', class_='post-title')
            for p in posts:
                a = p.find('a')
                if a and a.get('href'):
                    all_links.append(a.get('href'))
        
        with open(QUEUE_FILE, "w") as f:
            json.dump(all_links, f, indent=2)
            
        print(f"✅ Found {len(all_links)} posts. Starting Harvest...")
        
        # 2. HARVEST PHASE
        results = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r") as f: results = json.load(f)
            
        existing_ids = {r['id'] for r in results}
        to_scrape = [l for l in all_links if l.strip('/').split('/')[-1] not in existing_ids]
        
        semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
        tasks = [scrape_item(session, l, semaphore, results) for l in to_scrape]
        await asyncio.gather(*tasks)
        
        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"🏁 Mission Accomplished! {len(results)} items in database.")

if __name__ == "__main__":
    asyncio.run(main())
