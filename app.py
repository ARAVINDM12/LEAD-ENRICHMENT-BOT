import sys
if sys.platform.startswith("win"):
    import asyncio
    # Ensure the proactor event loop for subprocess support (usually default in Python 3.12)
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from playwright.sync_api import sync_playwright

import streamlit as st
import pandas as pd
from scraper3 import get_company_details
from llm3 import analyze_company_website


def enrich_companies(df):
    # Add missing columns if not present
    for col in ['Website', 'Industry', 'Company Size', 'HQ Location', 'Summary', 'Target Customer', 'AI Automation Idea']:
        if col not in df.columns:
            df[col] = 'N/A'

    websites, industries, sizes, locations = [], [], [], []
    summaries, customers, ideas = [], [], []

    for idx, row in df.iterrows():
        company = row['company_name']
        st.write(f"🔍 Fetching details for: **{company}**")

        # Step 1: Get details
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

        # Step 2: Analyze with LLM
        if details['Website'] != 'N/A':
            st.write(f"🤖 Analyzing {details['Website']}")
            summary, customer, idea = analyze_company_website(details['Website'], company)
        else:
            summary, customer, idea = "N/A", "N/A", "N/A"

        summaries.append(summary)
        customers.append(customer)
        ideas.append(idea)

    # Update df
    df['Website'] = websites
    df['Industry'] = industries
    df['Company Size'] = sizes
    df['HQ Location'] = locations
    df['Summary'] = summaries
    df['Target Customer'] = customers
    df['AI Automation Idea'] = ideas

    return df


def main():
    st.title("Company Info Enrichment Tool")
    st.write("Upload your CSV with a column `company_name` to enrich company data.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"Loaded {len(df)} companies")

        if st.button("Run Enrichment"):
            with st.spinner("Processing... this may take a while"):
                enriched_df = enrich_companies(df)
                st.success("Enrichment complete!")

                st.dataframe(enriched_df)

                # Allow download of CSV
                csv = enriched_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download enriched CSV",
                    data=csv,
                    file_name="enriched_companies.csv",
                    mime="text/csv"
                )


if __name__ == "__main__":
    main()
