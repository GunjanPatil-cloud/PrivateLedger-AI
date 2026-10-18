# modules/local_ai.py
"""Local AI utilities interfacing with an Ollama vision model.

The implementation tries to detect whether Ollama is running locally and provides
a thin wrapper around the HTTP API. For simplicity, the extraction function
returns ``None`` (fallback to OCR‑only) if the model is unavailable or if an
error occurs.
"""

import subprocess
import json
import base64
import requests
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional

# Default model – can be changed via the Settings page in the UI.
DEFAULT_MODEL = "llava"
_model_name = DEFAULT_MODEL


def set_model_name(name: str) -> None:
    """Update the model name used for extraction.

    The UI calls this when the user saves a new model name.
    """
    global _model_name
    _model_name = name.strip() or DEFAULT_MODEL


def get_model_name() -> str:
    return globals().get("_model_name", DEFAULT_MODEL)


def is_model_available() -> bool:
    """Check whether Ollama is reachable on the default local port.

    We invoke ``ollama list`` – it succeeds (exit code 0) if the server is
    running. If the command is not found or returns a non‑zero exit code we treat
    the model as unavailable.
    """
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=2)
        return result.returncode == 0
    except Exception:
        return False


def _encode_images(images: List["PIL.Image.Image"]) -> List[str]:
    """Encode Pillow images to base64 strings suitable for Ollama payloads.
    """
    encoded: List[str] = []
    for img in images:
        # Convert to PNG in memory then base64‑encode.
        with BytesIO() as buf:
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            encoded.append(b64)
    return encoded


def extract_fields(raw_text: str, images: List["PIL.Image.Image"]) -> Optional[Dict]:
    """Send the raw OCR text (and optional images) to the local Ollama model.

    The model is expected to return a JSON object with the required fields.  If
    any step fails we return ``None`` so the caller can fall back to OCR‑only
    handling.
    """
    if not is_model_available():
        return None

    model = get_model_name()
    # Build a concise prompt that asks for JSON output.
    prompt = (
        "You are an AI assistant that extracts structured financial data from a receipt or invoice. "
        "Return a JSON object with the following keys: vendor, invoice_number, date, subtotal, tax, total, "
        "currency, category, payment_method, description. If a field cannot be determined, set its value to null. "
        "Only output raw JSON – no explanations."
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "system": "You are a helpful assistant.",
        "images": _encode_images(images) if images else [],
        "stream": False,
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Ollama returns a ``response`` field that contains the text output.
        raw_output = data.get("response", "")
        # Try to parse the JSON – it may be wrapped in newline characters.
        return json.loads(raw_output)
    except Exception:
        # Any error (network, JSON decode, etc.) results in a graceful fallback.
        return None
