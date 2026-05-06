import asyncio
import aiohttp
import aiofiles
import json
import os
import time

# --- CONFIGURATION ---
DATA_DIR = "data"
ASSETS_DIR = "assets/images"
FILES = ["results.json", "results_nullphp.json"]
CONCURRENT_DOWNLOADS = 10

os.makedirs(ASSETS_DIR, exist_ok=True)

async def download_image(session, url, item_id, results_list, index):
    if not url: return
    if url.startswith("//"): url = "https:" + url
    
    file_path = os.path.join(ASSETS_DIR, f"{item_id}.jpg")
    if os.path.exists(file_path):
        results_list[index]['image_local'] = f"assets/images/{item_id}.jpg"
        return

    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
                results_list[index]['image_local'] = f"assets/images/{item_id}.jpg"
                print(f"  [✓] Downloaded: {item_id}")
    except Exception as e:
        print(f"  [!] Failed {item_id}: {str(e)[:50]}")

async def main():
    async with aiohttp.ClientSession() as session:
        for filename in FILES:
            path = os.path.join(DATA_DIR, filename)
            if not os.path.exists(path): continue
            
            print(f"🖼️ Syncing images for {filename}...")
            with open(path, 'r') as f:
                data = json.load(f)
            
            tasks = []
            semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)
            
            async def limited_download(url, item_id, data_list, idx):
                async with semaphore:
                    await download_image(session, url, item_id, data_list, idx)

            for i, item in enumerate(data):
                img_url = item.get('image_url') or item.get('image') # Support both keys
                if img_url and not item.get('image_local'):
                    tasks.append(limited_download(img_url, item['id'], data, i))
            
            if tasks:
                await asyncio.gather(*tasks)
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            print(f"✅ Sync complete for {filename}.")

if __name__ == "__main__":
    asyncio.run(main())
