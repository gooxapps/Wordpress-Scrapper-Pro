import requests
from bs4 import BeautifulSoup
import re
import csv
import time

urls = [
  "http://ghchq.org/",
  "https://ibadan.infoisinfo.ng/search/churches",
  "https://epifia.com/20-best-churches-in-ibadan-a-complete-guide-seventh-day-adventist-house-on-the-rock-baptist-more",
  "https://www.instagram.com/cci_ibadan/",
  "https://www.ibadanarchdiocese.org/parishes-by-alphabet",
  "https://uibaptistchurch.org/",
  "https://www.facebook.com/lbcibadan/",
  "https://globalharvestchurch.org/locations/global-harvest-church-liberty-ibadan/",
  "https://vicintchurch.org/"
]

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
        print(f"Scraping: {url}")
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
    results_data = []
    
    for url in urls:
        title, emails, phones = scrape_site(url)
        
        if emails or phones or title != "Unknown Site":
            results_data.append({
                'Business Name': title,
                'URL': url,
                'Emails': ', '.join(emails),
                'Phones': ', '.join(phones)
            })
        time.sleep(1) # Be polite
        
    filename = 'Churches_in_Ibadan.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Business Name', 'URL', 'Emails', 'Phones'])
        writer.writeheader()
        writer.writerows(results_data)
        
    print(f"\n[+] Scrape completed successfully!")
    print(f"[+] Saved {len(results_data)} records to {filename}")

if __name__ == "__main__":
    main()
