# modules/ocr_engine.py
"""OCR utilities using pytesseract.
"""

import pytesseract
from PIL import Image

def ocr_image(image: Image.Image) -> str:
    """Run Tesseract OCR on a Pillow Image and return extracted text.
    """
    # Ensure image is RGB
    if image.mode != "RGB":
        image = image.convert("RGB")
    text = pytesseract.image_to_string(image)
    return text.strip()
