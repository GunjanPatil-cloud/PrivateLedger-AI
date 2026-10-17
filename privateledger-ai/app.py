# app.py
"""Main Streamlit application for PrivateLedger AI.

Features:
- Dashboard with summary metrics
- Document upload and processing
- Review & edit extracted data
- File organization and export
- Demo mode with synthetic data
"""

import streamlit as st
import pathlib
import json
import pandas as pd
from modules import document_loader, ocr_engine, local_ai, data_validator, file_organizer, export_manager, database

# ---------- Configuration ----------
DEFAULT_OUTPUT_DIR = pathlib.Path("organized_documents")
DEFAULT_DB_PATH = pathlib.Path("privateledger.db")

# Initialize (or connect) database
if not DEFAULT_DB_PATH.exists():
    database.init_db(DEFAULT_DB_PATH)

# Session state
if "records" not in st.session_state:
    st.session_state.records = []  # List of dicts
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# ---------- Helper Functions ----------
def load_demo_data():
    """Load synthetic demo records.
    Returns a list of dicts with the same schema as extracted records.
    """
    demo = [
        {
            "vendor": "Acme Corp",
            "invoice_number": "INV-00123",
            "date": "2023-07-15",
            "subtotal": 120.00,
            "tax": 12.00,
            "total": 132.00,
            "currency": "USD",
            "category": "Software",
            "payment_method": "Credit Card",
            "description": "Monthly subscription",
            "filename": "demo1.pdf",
            "status": "pending",
        },
        {
            "vendor": "Office Supplies Ltd",
            "invoice_number": "OS-9876",
            "date": "2023-07-10",
            "subtotal": 45.50,
            "tax": 4.55,
            "total": 50.05,
            "currency": "USD",
            "category": "Office",
            "payment_method": "Cash",
            "description": "Stationery purchase",
            "filename": "demo2.jpg",
            "status": "pending",
        },
    ]
    return demo

def process_file(uploaded_file):
    """Process a single uploaded file: OCR + optional local AI extraction.
    Returns a dict with extracted fields.
    """
    # Save uploaded file to a temporary location
    temp_path = pathlib.Path("temp") / uploaded_file.name
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load images (PDF pages become images)
    images = document_loader.load_as_images(temp_path)
    # OCR each image and concatenate text
    raw_text = "\n".join([ocr_engine.ocr_image(img) for img in images])

    # Try local AI extraction if model is available
    if local_ai.is_model_available():
        extraction = local_ai.extract_fields(raw_text, images)
        if extraction:
            record = extraction
        else:
            # Fallback to OCR-only (empty structured fields)
            record = {"raw_text": raw_text}
    else:
        st.warning("Ollama model not available – using OCR‑only extraction.")
        record = {"raw_text": raw_text}

    # Add filename
    record["filename"] = uploaded_file.name
    # Validate and normalize fields
    record = data_validator.validate_and_normalize(record)
    return record

# ---------- UI Layout ----------
st.set_page_config(page_title="PrivateLedger AI", layout="wide")

st.sidebar.title("PrivateLedger AI")
page = st.sidebar.radio("Navigation", ["Dashboard", "Import Documents", "Review & Organize", "Expense Reports", "Settings & Privacy"])

# Privacy indicator
if local_ai.is_model_available():
    st.sidebar.success("Local AI model ready")
else:
    st.sidebar.info("Local AI model not detected")

# ----- Dashboard -----
if page == "Dashboard":
    st.header("Dashboard")
    # Load data from DB
    df = database.load_records(DEFAULT_DB_PATH)
    total_docs = len(df)
    total_expense = df["total"].sum() if not df.empty else 0
    pending = len(df[df["status"] == "pending"])
    # Expense breakdown by category
    breakdown = df.groupby("category")["total"].sum().reset_index() if not df.empty else pd.DataFrame()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documents Processed", total_docs)
    col2.metric("Total Expense", f"${total_expense:,.2f}")
    col3.metric("Pending Reviews", pending)
    col4.metric("Unique Vendors", df["vendor"].nunique() if not df.empty else 0)

    st.subheader("Expense Breakdown by Category")
    if not breakdown.empty:
        st.bar_chart(breakdown.set_index("category"))
    else:
        st.info("No expense data available yet.")

    st.subheader("Recent Documents")
    if not df.empty:
        st.dataframe(df.sort_values(by="date", ascending=False).head(5))
    else:
        st.info("No documents processed.")

# ----- Import Documents -----
elif page == "Import Documents":
    st.header("Import Documents")
    uploaded_files = st.file_uploader(
        "Upload receipts or invoices (images/PDF)",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        accept_multiple_files=True,
    )
    output_dir = st.text_input("Output folder (relative to project)", value=str(DEFAULT_OUTPUT_DIR))
    if st.button("Process Files") and uploaded_files:
        records = []
        for uf in uploaded_files:
            try:
                rec = process_file(uf)
                records.append(rec)
            except Exception as e:
                st.error(f"Error processing {uf.name}: {e}")
        # Save to session state and DB
        st.session_state.records.extend(records)
        database.insert_records(DEFAULT_DB_PATH, records)
        st.success(f"Processed {len(records)} file(s).")
        st.session_state.processed = True

# ----- Review & Organize -----
elif page == "Review & Organize":
    st.header("Review & Organize")
    # Load pending records from DB
    df = database.load_records(DEFAULT_DB_PATH)
    pending_df = df[df["status"] == "pending"].copy()
    if st.checkbox("Demo mode", key="demo_mode_checkbox"):
        st.session_state.demo_mode = True
        pending_df = pd.DataFrame(load_demo_data())
    if pending_df.empty:
        st.info("No records pending review.")
    else:
        edited = st.data_editor(pending_df, num_rows="dynamic")
        if st.button("Approve Selected"):
            # Update status to approved and move files
            approved = edited[edited["status"] != "pending"]
            for _, row in approved.iterrows():
                file_path = pathlib.Path(row["filename"])
                file_organizer.organize_file(file_path, row, pathlib.Path(output_dir))
                database.update_status(DEFAULT_DB_PATH, row["filename"], "approved")
            st.success(f"Approved {len(approved)} records and organized files.")

# ----- Expense Reports -----
elif page == "Expense Reports":
    st.header("Expense Reports")
    df = database.load_records(DEFAULT_DB_PATH)
    if df.empty:
        st.info("No data to export.")
    else:
        st.subheader("Export Verified Records")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export CSV"):
                csv_bytes = export_manager.export_csv(df)
                st.download_button("Download CSV", csv_bytes, file_name="expenses.csv", mime="text/csv")
        with col2:
            if st.button("Export Excel"):
                xlsx_bytes = export_manager.export_excel(df)
                st.download_button("Download XLSX", xlsx_bytes, file_name="expenses.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ----- Settings & Privacy -----
elif page == "Settings & Privacy":
    st.header("Settings & Privacy")
    st.markdown("**Local AI Model**")
    model_name = st.text_input("Ollama model name", value=local_ai.DEFAULT_MODEL)
    if st.button("Save Model Config"):
        local_ai.set_model_name(model_name)
        st.success("Model configuration saved.")
    st.markdown("---")
    st.markdown("**Privacy**: All processing is performed locally. No data is sent to external services. The application does not contain telemetry.")
    st.markdown("**Offline Test**: Disconnect from the internet, then click the *Dashboard* tab – the app should still load and allow you to view records that have already been processed.")

st.sidebar.caption("PrivateLedger AI – Offline‑First Financial Organizer")
