# README.md

# PrivateLedger AI

**Privacy‑First Offline Invoice & Receipt Organizer**

## Overview

PrivateLedger AI is a Streamlit‑based desktop application that helps freelancers manage receipts and invoices **without sending any data to the cloud**. All processing – OCR, AI‑driven extraction, file organization, and export – happens locally on your computer.

## Features
- Drag‑and‑drop upload of images (PNG, JPG, JPEG, WEBP) and PDFs (batch support).
- Local OCR via **Tesseract** (`pytesseract`).
- Optional local vision‑language model using **Ollama** for structured extraction.
- Review and edit extracted data in an editable table.
- Safe file renaming & folder organization (`organized_documents/YYYY/MM/`).
- Export verified records to CSV or Excel.
- Demo mode with synthetic invoices for testing.
- Full privacy: no network calls (unless you run Ollama locally), no telemetry.

## Prerequisites (macOS / Linux)

1. **Python ≥ 3.9** (we recommend a virtual environment).
2. **Tesseract OCR**
   ```bash
   # macOS
   brew install tesseract
   # Ubuntu/Debian
   sudo apt‑update && sudo apt‑install -y tesseract-ocr libtesseract-dev
   ```
3. **Ollama** (optional but recommended for higher accuracy). Install from https://ollama.com and pull a vision model, e.g.:
   ```bash
   curl -L https://ollama.com/install.sh | sh
   ollama pull llama3.1:8b‑vision   # or any *‑vision model
   ```
4. **Git** (to clone the repo if you haven't already).

## Installation

```bash
# Clone the repository (or copy the folder into your workspace)
git clone https://github.com/yourusername/privateledger-ai.git
cd privateledger-ai

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
# Activate the virtual environment if not already active
source .venv/bin/activate

# Start Streamlit
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`.

## Demo Mode

If you don't have real receipts, enable **Demo Mode** under *Settings → Demo Mode* to load synthetic invoice data and explore the full workflow.

## Configuration

- **Model selection** – edit `modules/local_ai.py` (or use the Settings page) to change the Ollama model name.
- **Default output folder** – set `DEFAULT_OUTPUT_DIR` in `modules/file_organizer.py`.
- **Database** – a lightweight SQLite file `privateledger.db` is created in the project root.

## Security & Privacy

- All processing (OCR, AI inference) happens locally; no network traffic is generated unless you run Ollama which operates as a local server.
- No telemetry, analytics, or third‑party tracking.
- Sensitive filenames are sanitized before being saved.

## Tests

```bash
pytest tests
```

## License

MIT – feel free to adapt and extend.

---

*Happy organizing!*
