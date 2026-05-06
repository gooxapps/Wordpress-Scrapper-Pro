import json
import os
import shutil
import re

# --- CONFIGURATION ---
DATA_DIR = "data"
PORTFOLIO_DIR = "portfolio_showcase"
PROJECT_FILES = ["results.json", "results_nullphp.json"]

os.makedirs(PORTFOLIO_DIR, exist_ok=True)

def clean_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

def generate_readme(item):
    title = item.get('title', 'Project Showcase')
    desc = item.get('description_html', 'No description available.')
    # Strip HTML for README
    clean_desc = re.sub('<[^<]+?>', '', desc)
    
    category = item.get('category', 'Software')
    mirrors = item.get('mirrors', [])
    preview = item.get('preview_url', '#')
    source = item.get('url', '#')
    
    mirror_list = []
    for link in mirrors:
        try:
            domain = link.split('/')[2]
            mirror_list.append(f"* [Download Mirror ({domain})]({link})")
        except:
            mirror_list.append(f"* [Download Mirror]({link})")
    
    mirror_list_str = "\n".join(mirror_list) if mirror_list else f"* [Check Source]({source})"

    readme_content = f"""# {title}

![Project Category](https://img.shields.io/badge/Category-{category.replace(' ', '%20')}-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Scraped%20&%20Optimized-success?style=for-the-badge)

## 📝 Overview
{clean_desc}

## 🚀 Key Features
* **Full Source Code Access** (Via Mirrors)
* **High Performance Architecture**
* **Mobile & Desktop Optimized**
* **Production Ready**

## 🔗 Live Links
* [🌐 Live Demo / Preview]({preview})
* [📁 Original Project Source]({source})

## 📥 Download Mirrors
{mirror_list_str}

---
*This project is part of the Goox Apps Automated Portfolio Collection. All descriptions are AI-generated for clarity and SEO.*
"""
    return readme_content

def build_portfolio():
    print("🚀 Starting Portfolio Generation for GitHub Showcase...")
    total_folders = 0
    
    for filename in PROJECT_FILES:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path): continue
        
        with open(path, 'r') as f:
            data = json.load(f)
            
        for item in data:
            if not item.get('title'): continue
            
            folder_name = clean_filename(item['id'])[:100]  # Truncate to 100 chars
            proj_dir = os.path.join(PORTFOLIO_DIR, folder_name)
            os.makedirs(proj_dir, exist_ok=True)
            
            # 1. Create README.md
            with open(os.path.join(proj_dir, "README.md"), "w") as f:
                f.write(generate_readme(item))
            
            # 2. Copy Image if exists
            if item.get('image_local'):
                src_img = item['image_local']
                if os.path.exists(src_img):
                    shutil.copy(src_img, os.path.join(proj_dir, "thumbnail.jpg"))
            
            total_folders += 1
            if total_folders % 50 == 0:
                print(f"  [>] Generated {total_folders} project folders...")

    print(f"✅ Portfolio Build Complete! Created {total_folders} folders in '{PORTFOLIO_DIR}'.")
    print("💡 Now you can push the 'portfolio_showcase' folder to GitHub to show off your work!")

if __name__ == "__main__":
    build_portfolio()
