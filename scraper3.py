import wikipediaapi
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re

def clean_text(text):
    """Clean extracted text by removing citations, references, and extra whitespace."""
    # Remove bracketed citations like [1], [2]
    text = re.sub(r'\[.*?\]', '', text)
    # Normalize whitespace
    return ' '.join(text.split())

def fix_url(url):
    """Ensure URL is absolute and well-formed."""
    if not url:
        return 'N/A'
    url = url.strip()
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = 'https://en.wikipedia.org' + url
    if not url.startswith('http'):
        url = 'https://' + url
    return url

def get_company_details(company_name):
    info = {
        'Company Name': company_name,
        'Website': 'N/A',
        'Industry': 'N/A',
        'Company Size': 'N/A',
        'HQ Location': 'N/A'
    }

    wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='TaskLeadEnrichmentBot/1.0 (aravind@example.com)'
    )
    page = wiki.page(company_name)

    if not page.exists():
        print(f"🔎 Wikipedia page not found for {company_name}, trying Google Search fallback")
        try:
            query = f"{company_name} official website"
            for url in search(query, num_results=5):
                if company_name.lower() in url.lower():
                    info['Website'] = url
                    break
        except Exception as e:
            print(f"⚠️ Google Search failed for {company_name}: {e}")
        return info

    url = page.fullurl
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, 'html.parser')
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                header = row.find('th')
                data = row.find('td')
                if not header or not data:
                    continue

                key = header.text.strip().lower()
                val = clean_text(data.text)

                if 'headquarters' in key or 'headquarter' in key:
                    info['HQ Location'] = val
                elif 'industry' in key:
                    info['Industry'] = val
                elif 'number of employees' in key or 'employees' in key:
                    info['Company Size'] = val
                elif 'website' in key:
                    link = data.find('a')
                    if link and link.has_attr('href'):
                        info['Website'] = fix_url(link['href'])
                    else:
                        info['Website'] = val
    except Exception as e:
        print(f"⚠️ Error parsing infobox for {company_name}: {e}")

    # Fallback to parse raw Wikipedia text if still missing fields
    for field in ['Website', 'Industry', 'Company Size', 'HQ Location']:
        if info[field] == 'N/A':
            content = page.text.lower()
            lines = content.split('\n')
            for line in lines:
                if field == 'Website' and 'website' in line and info['Website'] == 'N/A':
                    possible_url = re.findall(r'https?://\S+', line)
                    if possible_url:
                        info['Website'] = possible_url[0]
                elif field == 'Industry' and 'industry' in line and info['Industry'] == 'N/A':
                    info['Industry'] = clean_text(line)
                elif field == 'Company Size' and ('employee' in line or 'number of employees' in line) and info['Company Size'] == 'N/A':
                    info['Company Size'] = clean_text(line)
                elif field == 'HQ Location' and ('headquarter' in line or 'headquarters' in line) and info['HQ Location'] == 'N/A':
                    info['HQ Location'] = clean_text(line)

    # Final sanity check for website: if still 'N/A', try Google search
    if info['Website'] == 'N/A':
        try:
            print(f"🔎 Using Google Search fallback for {company_name} to find website")
            query = f"{company_name} official website"
            for url in search(query, num_results=5):
                if company_name.lower() in url.lower():
                    info['Website'] = url
                    break
        except Exception as e:
            print(f"⚠️ Google Search failed for {company_name}: {e}")

    return info
