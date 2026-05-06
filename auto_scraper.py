import requests
from bs4 import BeautifulSoup
import re
import csv
import sys
import time
from googlesearch import search

def extract_emails(text):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_regex, text)))

def extract_phones(text):
    phone_regex = r'(?:\+?\d{1,3}[-\s.]?)?\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4,6}'
    matches = re.findall(phone_regex, text)
    valid_phones = [m for m in matches if len(re.sub(r'\D', '', m)) >= 8]
    return list(set(valid_phones))

def scrape_site(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else "Unknown Site"
        title = title.strip().replace('\n', ' ')

        text = soup.get_text(separator=' ')
        
        emails = extract_emails(text)
        phones = extract_phones(text)
        
        if not emails:
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if 'contact' in href or 'about' in href:
                    contact_url = link['href']
                    if not contact_url.startswith('http'):
                        if contact_url.startswith('/'):
                            contact_url = url.rstrip('/') + contact_url
                        else:
                            contact_url = url.rstrip('/') + '/' + contact_url
                    try:
                        c_resp = requests.get(contact_url, headers=headers, timeout=10)
                        c_text = BeautifulSoup(c_resp.text, 'html.parser').get_text(separator=' ')
                        emails.extend(extract_emails(c_text))
                        phones.extend(extract_phones(c_text))
                    except:
                        pass
                    break
        
        return title, list(set(emails)), list(set(phones))
    except Exception as e:
        print(f"[-] Error scraping {url}: {e}")
        return "Error loading site", [], []

def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_scraper.py <search_query>")
        sys.exit(1)
        
    query = sys.argv[1]
    print(f"[*] Starting auto-scraper for query: '{query}'")
    
    results_data = []
    print("[*] Searching Google for links...")
    
    try:
        urls = list(search(query, num_results=15, advanced=True))
    except Exception as e:
        print(f"[-] Search failed: {e}")
        sys.exit(1)
        
    print(f"[*] Found {len(urls)} search results. Starting deep scrape...")
    
    for idx, res in enumerate(urls):
        url = res.url
        print(f"[{idx+1}/{len(urls)}] Scraping: {url}")
        
        title, emails, phones = scrape_site(url)
        
        results_data.append({
            'Business Name': title if title and title != "Unknown Site" else res.title,
            'URL': url,
            'Emails': ', '.join(emails),
            'Phones': ', '.join(phones),
            'Snippet': res.description
        })
        time.sleep(1) # Be polite
        
    filename = query.replace(' ', '_').lower() + '_data.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Business Name', 'URL', 'Emails', 'Phones', 'Snippet'])
        writer.writeheader()
        writer.writerows(results_data)
        
    print(f"\n[+] Scrape completed successfully!")
    print(f"[+] Saved {len(results_data)} records to {filename}")

if __name__ == "__main__":
    main()
