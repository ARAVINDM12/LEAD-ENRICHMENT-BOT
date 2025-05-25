import pandas as pd
from scraper3 import get_company_details
from llm3 import analyze_company_website

# Load CSV
df = pd.read_csv("sample_input.csv")

# Add missing columns
for col in ['Website', 'Industry', 'Company Size', 'HQ Location', 'Summary', 'Target Customer', 'AI Automation Idea']:
    if col not in df.columns:
        df[col] = 'N/A'

websites, industries, sizes, locations = [], [], [], []
summaries, customers, ideas = [], [], []

for idx, row in df.iterrows():
    company = row['company_name']
    print(f"\n🔍 Fetching details for: {company}")

    # Step 1: Scrape metadata
    if (pd.isna(row['Website']) or row['Website'] == 'N/A' or
        pd.isna(row['Industry']) or row['Industry'] == 'N/A' or
        pd.isna(row['Company Size']) or row['Company Size'] == 'N/A' or
        pd.isna(row['HQ Location']) or row['HQ Location'] == 'N/A'):
        details = get_company_details(company)
    else:
        details = {
            'Company Name': company,
            'Website': row['Website'],
            'Industry': row['Industry'],
            'Company Size': row['Company Size'],
            'HQ Location': row['HQ Location']
        }

    websites.append(details['Website'])
    industries.append(details['Industry'])
    sizes.append(details['Company Size'])
    locations.append(details['HQ Location'])

    # Step 2: Analyze using Gemini
    if details['Website'] != 'N/A':
        print(f"🤖 Running LLM analysis for: {details['Website']}")
        summary, customer, idea = analyze_company_website(details['Website'], company)
    else:
        summary, customer, idea = "N/A", "N/A", "N/A"

    summaries.append(summary)
    customers.append(customer)
    ideas.append(idea)

# Update DataFrame
df['Website'] = websites
df['Industry'] = industries
df['Company Size'] = sizes
df['HQ Location'] = locations
df['Summary'] = summaries
df['Target Customer'] = customers
df['AI Automation Idea'] = ideas

df.to_csv("enriched_output2.csv", index=False)
print("\n✅ Enrichment complete. Output saved to enriched_output.csv")
