import sys
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
import csv
import io
import time
from openpyxl.styles import Font, Alignment
from scraper3 import get_company_details
from llm3 import analyze_company_website

SAMPLE_FILE_PATH = "sample_input.csv"  # <-- Make sure this file exists

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
        status_text.write(f"🔍 Fetching & analyzing: **{company}** ({idx + 1}/{total})")
        progress_bar.progress((idx + 1) / total)
        time.sleep(0.1)

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
        cleaned_row = [str(cell).replace('\r', '') for cell in row]
        writer.writerow(cleaned_row)

    return output.getvalue().encode('utf-8')

def dataframe_to_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Enriched Data')

        workbook = writer.book
        worksheet = writer.sheets['Enriched Data']

        
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
    st.write("Upload your CSV or use a sample to enrich company data with metadata and LLM analysis.")

    # ——— Enhanced Sidebar ———
    st.sidebar.markdown("## 🛠️ Lead Enrichment Settings")
    st.sidebar.markdown("---")

    with st.sidebar.expander("📥 Choose input method", expanded=True):
        input_method = st.radio(
            "",
            ("Upload your own CSV", "Use sample input file"),
            index=0,
            key="input_method"
        )

    if input_method == "Use sample input file":
        with st.sidebar.expander("📄 Sample Input CSV", expanded=True):
            try:
                with open(SAMPLE_FILE_PATH, "rb") as f:
                    sample_data = f.read()
                st.download_button(
                    label="📥 Download Sample Input CSV",
                    data=sample_data,
                    file_name="sample_input.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_sample"
                )

            except Exception as e:
                st.error(f"❌ Could not load sample input for download: {e}")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style='font-size:12px; color:gray;'>
        ℹ️ Upload a CSV with a <code>company_name</code> column.<br>
        ℹ️ After uploading or selecting sample, press the 🚀 Run Enrichment button.
        </div>
        """,
        unsafe_allow_html=True
    )

    df = None

    if input_method == "Upload your own CSV":
        uploaded_file = st.file_uploader("📁 Upload CSV file", type=["csv"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Uploaded {len(df)} companies")
            except Exception as e:
                st.error(f"❌ Unable to read the CSV file: {e}")
                return
    else:
        # Show a dropdown with just one sample file to select explicitly
        sample_files = [SAMPLE_FILE_PATH]
        selected_sample = st.selectbox("Select a sample input file:", sample_files)

        if selected_sample:
            try:
                df = pd.read_csv(selected_sample)
                st.success(f"✅ Loaded {len(df)} companies from sample input `{selected_sample}`")
            except Exception as e:
                st.error(f"❌ Could not load sample input: {e}")
                return

    if df is not None:
        if 'company_name' not in df.columns:
            st.error("❌ CSV must contain a column named `company_name`.")
            return

        if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != input_method:
            st.session_state.enriched_df = None
            st.session_state.last_uploaded = input_method

        if 'enriched_df' not in st.session_state:
            st.session_state.enriched_df = None

        if st.session_state.enriched_df is None:
            if st.button("🚀 Run Enrichment"):
                with st.spinner("Processing... This may take a few minutes."):
                    try:
                        st.session_state.enriched_df = enrich_companies(df)
                        st.success("✅ Enrichment complete!")
                    except Exception as e:
                        st.error(f"❌ An error occurred during enrichment: {e}")
                        return
        else:
            st.info("✅ Enrichment already completed. Upload a new file or change source to re-run.")

        if st.session_state.enriched_df is not None:
            st.subheader("📊 Enrichment Results")
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
