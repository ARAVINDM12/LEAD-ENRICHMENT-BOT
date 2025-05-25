import sys
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
import csv
import io
import time  # <-- import time for sleep

from scraper3 import get_company_details
from llm3 import analyze_company_website

def enrich_companies(df):
    for col in ['Website', 'Industry', 'Company Size', 'HQ Location', 'Summary', 'Target Customer', 'AI Automation Idea']:
        if col not in df.columns:
            df[col] = 'N/A'

    websites, industries, sizes, locations = [], [], [], []
    summaries, customers, ideas = [], [], []

    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(df)
    for idx, row in df.iterrows():
        company = row['company_name']
        # Update status and progress every row for smoothness
        status_text.write(f"🔍 Fetching & analyzing: **{company}** ({idx + 1}/{total})")
        progress_bar.progress((idx + 1) / total)
        time.sleep(0.1)  # small sleep to allow UI to update smoothly

        # Check if key columns are missing or 'N/A', fetch details if so
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

        if details['Website'] != 'N/A':
            summary, customer, idea = analyze_company_website(details['Website'], company)
        else:
            summary, customer, idea = "N/A", "N/A", "N/A"

        summaries.append(summary)
        customers.append(customer)
        ideas.append(idea)

    status_text.empty()
    progress_bar.empty()

    df['Website'] = websites
    df['Industry'] = industries
    df['Company Size'] = sizes
    df['HQ Location'] = locations
    df['Summary'] = summaries
    df['Target Customer'] = customers
    df['AI Automation Idea'] = ideas

    return df

def dataframe_to_csv_download(df):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    writer.writerow(df.columns)
    for _, row in df.iterrows():
        cleaned_row = [str(cell).replace('\r', '') for cell in row]  # Retain newlines
        writer.writerow(cleaned_row)

    return output.getvalue().encode('utf-8')

def dataframe_to_excel_download(df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Enriched Data')

        workbook = writer.book
        worksheet = writer.sheets['Enriched Data']

        from openpyxl.styles import Font, Alignment
        header_font = Font(bold=True)
        for cell in worksheet[1]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')

        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    cell_value = str(cell.value)
                    if cell_value:
                        max_length = max(max_length, len(cell_value))
                except:
                    pass
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column].width = adjusted_width

    output.seek(0)
    return output.read()

def main():
    st.set_page_config(page_title="Lead Enrichment Tool", layout="wide")
    st.title("🏢 Lead Enrichment Tool")
    st.write("Upload your CSV with a column named `company_name` to automatically enrich it with metadata and LLM analysis.")

    uploaded_file = st.file_uploader("📁 Upload CSV file", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Unable to read the CSV file: {e}")
            return

        # Reset enrichment if new file uploaded
        if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            st.session_state.enriched_df = None
            st.session_state.last_uploaded = uploaded_file.name

        st.write(f"✅ Loaded {len(df)} companies")

        if 'company_name' not in df.columns:
            st.error("❌ Uploaded CSV must contain a column named `company_name`.")
            return

        # Initialize session state variable
        if 'enriched_df' not in st.session_state:
            st.session_state.enriched_df = None

        if st.session_state.enriched_df is None:
            if st.button("🚀 Run Enrichment"):
                with st.spinner("Processing... This may take a few minutes."):
                    try:
                        st.session_state.enriched_df = enrich_companies(df)
                    except Exception as e:
                        st.error(f"❌ An error occurred during enrichment: {e}")
                        return
                    st.success("✅ Enrichment complete!")
        else:
            st.info("✅ Enrichment already completed! You can download the results below or upload a new file to start again.")

        # Show results and download buttons only if enriched data exists
        if st.session_state.enriched_df is not None:
            st.subheader("Enrichment Results")
            st.dataframe(st.session_state.enriched_df)

            st.markdown("---")

            csv_data = dataframe_to_csv_download(st.session_state.enriched_df)
            excel_data = dataframe_to_excel_download(st.session_state.enriched_df)

            st.download_button(
                label="⬇️ Download enriched CSV",
                data=csv_data,
                file_name="enriched_companies.csv",
                mime="text/csv"
            )

            st.download_button(
                label="⬇️ Download enriched Excel (.xlsx)",
                data=excel_data,
                file_name="enriched_companies.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
