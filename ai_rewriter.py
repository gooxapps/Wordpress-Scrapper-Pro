import json
import os
import re
import random

# --- CONFIGURATION ---
DATA_DIR = "data"
PROJECTS = ["results.json", "results_nullphp.json"]

SEO_KEYWORDS = {
    "Food & Delivery": ["Best Food Delivery App", "Restaurant POS System", "Fast Delivery Script", "Multi-restaurant"],
    "E-commerce": ["Online Store Builder", "Multivendor Marketplace", "Shopify Clone", "WooCommerce Alternative"],
    "Taxi & Transport": ["Uber Clone Script", "Ride Sharing App", "Taxi Booking Solution", "Fleet Management"],
    "Security & VPN": ["High Speed VPN", "Privacy Shield", "Anonymous Proxy", "Cyber Security"],
    "Social & Dating": ["Community Hub", "Tinder Clone", "Social Networking Script", "Chat Application"],
    "Education & Games": ["E-learning Platform", "Course Management", "Quiz Engine", "LMS Solution"],
    "Booking & Services": ["Appointment Scheduler", "Salon Booking App", "Service Marketplace", "Booking System"]
}

def ai_rewrite_title(title):
    # Catchy prefix additions
    prefixes = ["Premium", "Advanced", "Professional", "High-Performance", "Elite", "Ultimate"]
    suffixes = ["Solution", "Framework", "Eco-system", "Platform"]
    
    clean_title = title.replace("Nulled Script - ", "").replace("Nulled", "").strip()
    if random.random() > 0.7:
        return f"{random.choice(prefixes)} {clean_title}"
    return clean_title

def ai_rewrite_description(desc, category):
    if not desc:
        return f"<p>Experience the power of our {category} solution. Designed for high performance and scalability.</p>"
    
    # 1. Strip original HTML ads/links if needed
    clean_desc = re.sub(r'<a.*?>(.*?)</a>', r'\1', desc)
    
    # 2. Add SEO Intro
    keywords = SEO_KEYWORDS.get(category, ["Premium Script", "Best Solution"])
    intro = f"<p><strong>Looking for the {random.choice(keywords)}?</strong> This {category} platform is built to help you scale your business instantly.</p>"
    
    # 3. Add Feature List (Mock AI logic)
    features = [
        "Fully Responsive Mobile Design",
        "Secure & Optimized Codebase",
        "Easy Admin Panel Integration",
        "Lifetime Updates & Support"
    ]
    feature_list = "<h4>Key Features:</h4><ul>" + "".join([f"<li>{f}</li>" for f in features]) + "</ul>"
    
    return intro + clean_desc[:500] + "... " + feature_list

def process_rewrite():
    for filename in PROJECTS:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath): continue
        
        print(f"🤖 AI Rewriter starting on {filename}...")
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        for item in data:
            if item.get('ai_processed'): continue
            
            cat = item.get('category', 'Multi-Purpose')
            item['title'] = ai_rewrite_title(item.get('title', 'Untitled'))
            item['description_html'] = ai_rewrite_description(item.get('description_html', ''), cat)
            item['ai_processed'] = True
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Finished rewriting {len(data)} items in {filename}.")

if __name__ == "__main__":
    process_rewrite()
