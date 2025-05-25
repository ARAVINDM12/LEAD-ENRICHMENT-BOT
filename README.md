# LEAD-ENRICHMENT-BOT
AI-powered automation tool that takes a list of company names and enriches it with useful lead-generation data using public APIs and LLMs


🤖 Company Info Enrichment Tool
This project enriches company data from a CSV file by automatically scraping key metadata (like website, industry, HQ, size) and generating AI-based insights such as summaries, target customers, and automation ideas using Google Gemini.
Built with Python, Playwright, and Streamlit, this tool simplifies manual company research into a one-click process.

📸 Demo
You can find a local copy under assets/demo_video.mp4

📦 Features
      ✅ Auto-scrape website, industry, company size, HQ location
      🧠 AI-generated summary, customer profile, automation idea
      📂 CSV input → CSV output
      🧪 Command line + Streamlit web interface
      🔐 Environment variable support for API keys

🛠️ Tech Stack
Python 3.9+
Streamlit
Pandas
Playwright
Google Generative AI (google-generativeai)
Wikipedia API
BeautifulSoup
Requests
dotenv

📁 Folder Structure
company-enrichment-tool/
├── app.py # Main script ( Streamlit)
├── main4.py #(CLI)
├── scraper3.py # Company info scraper
├── llm3.py # LLM (Gemini) prompt + parser
├── sample_input.csv # Example input file
├── enriched_output2.csv # Example output file
├── requirements.txt # All dependencies
├── .env.example # Template for API keys
├── README.md # You're here!
└── assets/
      └── demo_video.mp4 #demo video


🚀 Setup Instructions
1. Clone the Repo
2. Install Dependencies
      pip install -r requirements.txt
3. Install Playwright Browsers
      playwright install
4. Create .env File
      Create a .env file in the root directory based on .env.example:


✅ How to Use
🔁 Option 1: CLI Mode
      python main4.py
      #This reads sample_input.csv, scrapes details, enriches with AI, and writes to enriched_output2.csv.

🌐 Option 2: Web UI (Streamlit)
      streamlit run app.py
      Upload a CSV with a column named company_name
      Click Run Enrichment
      Download enriched CSV

📄 CSV Format
✅ sample_input.csv

