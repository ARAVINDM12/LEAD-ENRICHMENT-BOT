import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import re
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# INSERT YOUR API KEY HERE
GEMINI_API_KEY = "AIzaSyBK6lJFxB6ftsCnLc8gy7F31K3Z709r2NQ"
genai.configure(api_key=GEMINI_API_KEY)


def extract_visible_text_requests(url):
    """Fetch page content using requests (fast, no JS rendering)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        return ' '.join(soup.stripped_strings)[:6000]  # Limit to ~6000 chars
    except Exception as e:
        print(f"⚠️ Failed to fetch content from {url} using requests: {e}")
        return ""


def extract_visible_text_playwright(url):
    """Fetch page content using Playwright (renders JS, bypasses Cloudflare)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
            java_script_enabled=True,
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="load", timeout=60000)
            print(f"Page loaded for {url}, waiting for JS rendering...")
            page.wait_for_timeout(15000)  # wait 15 seconds for JS/Cloudflare
            html = page.content()
        except PlaywrightTimeoutError:
            print(f"⚠️ Timeout reached loading {url} with Playwright, using partial content")
            html = page.content()
        finally:
            browser.close()

    soup = BeautifulSoup(html, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    text = " ".join(soup.stripped_strings)
    return text[:6000]


def extract_visible_text(url):
    """Decide which extraction method to use based on URL."""
    # Customize this check as needed:
    if "openai.com" in url.lower():
        return extract_visible_text_playwright(url)
    else:
        return extract_visible_text_requests(url)


def extract_json_from_text(text):
    """Try to extract JSON object from a text blob."""
    json_match = re.search(r'\{.*?\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
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

        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            # Try fallback extraction
            data = extract_json_from_text(result)

            if not data:
                print("⚠️ Failed to parse JSON from model response, falling back to N/A")
                return "N/A", "N/A", "N/A"

        summary = data.get("summary", "N/A")
        target_customer = data.get("target_customer", "N/A")
        ai_automation_idea = data.get("ai_automation_idea", "N/A")

        return summary, target_customer, ai_automation_idea

    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return "N/A", "N/A", "N/A"



