# modules/document_loader.py
"""Utilities for loading documents (images or PDFs) as Pillow images.
"""

import pathlib
from typing import List
from PIL import Image
import fitz  # PyMuPDF

def load_as_images(file_path: pathlib.Path) -> List[Image.Image]:
    """Load a file (image or PDF) and return a list of Pillow Image objects.

    - If the file is an image, returns a list with a single Image.
    - If the file is a PDF, renders each page to an image.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")

    suffix = file_path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        img = Image.open(file_path).convert("RGB")
        return [img]
    elif suffix == ".pdf":
        doc = fitz.open(str(file_path))
        images: List[Image.Image] = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=200)  # decent DPI for OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
