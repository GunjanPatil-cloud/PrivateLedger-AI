# modules/database.py
"""SQLite database management for PrivateLedger AI.
"""

import sqlite3
import pathlib
from typing import List, Dict, Any, Union
import pandas as pd

DEFAULT_COLUMNS = [
    "id",
    "vendor",
    "invoice_number",
    "date",
    "subtotal",
    "tax",
    "total",
    "currency",
    "category",
    "payment_method",
    "description",
    "filename",
    "status",
]


def init_db(db_path: Union[str, pathlib.Path]) -> None:
    """Initialize the SQLite database with the records table if it doesn't exist."""
    db_path = str(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor TEXT,
                invoice_number TEXT,
                date TEXT,
                subtotal REAL,
                tax REAL,
                total REAL,
                currency TEXT,
                category TEXT,
                payment_method TEXT,
                description TEXT,
                filename TEXT,
                status TEXT DEFAULT 'pending',
                raw_text TEXT
            )
            """
        )
        conn.commit()


def load_records(db_path: Union[str, pathlib.Path]) -> pd.DataFrame:
    """Load all records from SQLite into a pandas DataFrame."""
    db_path = str(db_path)
    if not pathlib.Path(db_path).exists():
        init_db(db_path)

    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query("SELECT * FROM records", conn)
            if df.empty:
                return pd.DataFrame(columns=DEFAULT_COLUMNS)
            return df
    except Exception:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)


def insert_records(db_path: Union[str, pathlib.Path], records: List[Dict[str, Any]]) -> None:
    """Insert a list of record dicts into the database."""
    if not records:
        return

    db_path = str(db_path)
    if not pathlib.Path(db_path).exists():
        init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for rec in records:
            cursor.execute(
                """
                INSERT INTO records (
                    vendor, invoice_number, date, subtotal, tax, total,
                    currency, category, payment_method, description, filename, status, raw_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.get("vendor", ""),
                    rec.get("invoice_number", ""),
                    rec.get("date", ""),
                    float(rec.get("subtotal", 0.0) or 0.0),
                    float(rec.get("tax", 0.0) or 0.0),
                    float(rec.get("total", 0.0) or 0.0),
                    rec.get("currency", ""),
                    rec.get("category", ""),
                    rec.get("payment_method", ""),
                    rec.get("description", ""),
                    rec.get("filename", ""),
                    rec.get("status", "pending"),
                    rec.get("raw_text", ""),
                ),
            )
        conn.commit()


def update_status(db_path: Union[str, pathlib.Path], filename: str, status: str) -> None:
    """Update status of records matching the given filename."""
    db_path = str(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE records SET status = ? WHERE filename = ?",
            (status, filename),
        )
        conn.commit()
