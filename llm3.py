import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import re
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

def extract_visible_text_requests(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        return ' '.join(soup.stripped_strings)[:6000]
    except Exception as e:
        print(f"⚠️ Requests failed for {url}: {e}")
        return ""

def extract_visible_text_scrapingbee(url):
    try:
        print(f"🔁 Using ScrapingBee for {url}")
        api_url = "https://app.scrapingbee.com/api/v1/"
        params = {
            "api_key": SCRAPINGBEE_API_KEY,
            "url": url,
            "render_js": "true"
        }
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        return ' '.join(soup.stripped_strings)[:6000]
    except Exception as e:
        print(f"⚠️ ScrapingBee failed for {url}: {e}")
        return ""

def extract_visible_text_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context =  browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/115.0 Safari/537.36",
                java_script_enabled=True,
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(15000)
            html = page.content()
            browser.close()
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        return ' '.join(soup.stripped_strings)[:6000]
    except Exception as e:
        print(f"⚠️ Playwright failed for {url}: {e}")
        return ""

def extract_visible_text(url):
    js_heavy_sites = ["openai.com", "example-js-site.com"]
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()

    # Use Playwright locally if installed and not on Streamlit Cloud
    use_playwright = "streamlit.app" not in os.environ.get("STREAMLIT_SERVER_URL", "")

    if any(site in hostname for site in js_heavy_sites):
        if use_playwright:
            text = extract_visible_text_playwright(url)
            if text:
                return text
            print("🧭 Falling back to ScrapingBee...")
        return extract_visible_text_scrapingbee(url)

    # Fast path for simple sites
    text = extract_visible_text_requests(url)
    if not text and any(site in hostname for site in js_heavy_sites):
        return extract_visible_text_scrapingbee(url)
    return text

def extract_json_from_text(text):
    json_match = re.search(r'\{.*?\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return None

def analyze_company_website(url, company_name):
    content = extract_visible_text(url)
    if not content:
        return "N/A", "N/A", "N/A"

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = f"""
You are an expert business analyst.

Analyze the company's website text below. Provide your answers strictly as JSON with keys: "summary", "target_customer", and "ai_automation_idea".

Company Name: "{company_name}"

Website Text:
{content}

Output JSON exactly like this example:
{{
  "summary": "OpenAI develops cutting-edge artificial intelligence models and tools.",
  "target_customer": "Businesses and developers who need advanced AI capabilities.",
  "ai_automation_idea": "Offer customized AI model fine-tuning services to improve client-specific workflows."
}}
"""
        response = model.generate_content(prompt)
        result = response.text.strip()
        data = extract_json_from_text(result)
        if not data:
            print("⚠️ Failed to parse JSON from model response.")
            return "N/A", "N/A", "N/A"

        summary = data.get("summary", "N/A")
        target_customer = data.get("target_customer", "N/A")
        ai_automation_idea = data.get("ai_automation_idea", "N/A")
        return summary, target_customer, ai_automation_idea

    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return "N/A", "N/A", "N/A"
