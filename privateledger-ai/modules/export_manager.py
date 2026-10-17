# modules/export_manager.py
"""Export utilities for CSV and Excel files.
"""

import io
import pandas as pd


def export_csv(df: pd.DataFrame) -> bytes:
    """Export a DataFrame to CSV bytes.
    Returns the CSV content as bytes suitable for Streamlit download.
    """
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def export_excel(df: pd.DataFrame) -> bytes:
    """Export a DataFrame to an Excel (XLSX) binary.
    Returns the XLSX content as bytes.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Expenses")
    return buffer.getvalue()
