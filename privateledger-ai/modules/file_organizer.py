# modules/file_organizer.py
"""File organization and naming utilities for PrivateLedger AI.
Organizes documents into structured folders (e.g., organized_documents/YYYY/MM/).
"""

import datetime
import pathlib
import re
import shutil
from typing import Any, Mapping, Optional, Union

DEFAULT_OUTPUT_DIR = pathlib.Path("organized_documents")


def sanitize_filename_component(text: str) -> str:
    """Sanitize strings to be safe for filenames."""
    if not text:
        return ""
    # Replace spaces with underscores and remove problematic characters
    cleaned = re.sub(r"[^\w\-\.]", "_", str(text).strip())
    # Collapse multiple underscores
    return re.sub(r"_+", "_", cleaned).strip("_")


def organize_file(
    file_path: Union[str, pathlib.Path],
    record: Union[Mapping[str, Any], Any],
    output_dir: Optional[Union[str, pathlib.Path]] = None,
) -> pathlib.Path:
    """Organize and copy/move a document into organized_documents/YYYY/MM/.

    Parameters:
    - file_path: original path or filename
    - record: dict or Series containing metadata (date, vendor, invoice_number, etc.)
    - output_dir: destination root folder (defaults to DEFAULT_OUTPUT_DIR)

    Returns:
    - pathlib.Path pointing to the new organized file location.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    output_dir = pathlib.Path(output_dir)

    file_path = pathlib.Path(file_path)

    # Locate source file (check current location, then inside 'temp' directory)
    src_file = file_path
    if not src_file.exists():
        temp_candidate = pathlib.Path("temp") / file_path.name
        if temp_candidate.exists():
            src_file = temp_candidate

    # Determine Year/Month for subfolder structure
    date_val = str(record.get("date", "") if hasattr(record, "get") else getattr(record, "date", ""))
    date_match = re.search(r"(\d{4})[-/]?(\d{2})", date_val)
    if date_match:
        year, month = date_match.groups()
    else:
        now = datetime.date.today()
        year = now.strftime("%Y")
        month = now.strftime("%m")

    target_folder = output_dir / year / month
    target_folder.mkdir(parents=True, exist_ok=True)

    # Construct clean, descriptive filename
    ext = file_path.suffix or ".pdf"
    vendor = sanitize_filename_component(record.get("vendor", "") if hasattr(record, "get") else getattr(record, "vendor", ""))
    inv_num = sanitize_filename_component(record.get("invoice_number", "") if hasattr(record, "get") else getattr(record, "invoice_number", ""))
    formatted_date = sanitize_filename_component(date_val) or f"{year}-{month}"

    parts = [p for p in [formatted_date, vendor, inv_num] if p]
    if parts:
        new_name = "_".join(parts) + ext
    else:
        new_name = file_path.name

    dest_file = target_folder / new_name

    # Avoid overwriting by appending counter if needed
    counter = 1
    stem = dest_file.stem
    while dest_file.exists():
        dest_file = target_folder / f"{stem}_{counter}{ext}"
        counter += 1

    # Perform the copy/move or create placeholder for demo data
    if src_file.exists():
        shutil.copy2(src_file, dest_file)
    else:
        # Graceful handling if source file is synthetic/demo or missing
        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(f"Record metadata:\n{dict(record)}")

    return dest_file
