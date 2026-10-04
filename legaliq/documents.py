from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import os

from docx import Document
from pypdf import PdfReader


# ============================================================
# OPTIONAL OCR IMPORTS
# ============================================================

try:
    import pytesseract
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True

except ImportError:
    OCR_AVAILABLE = False


# ============================================================
# WINDOWS OCR CONFIGURATION
# ============================================================

# Tesseract installation path
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Poppler installation path
# Change this only if you extracted Poppler somewhere else.
POPPLER_PATH = r"C:\Users\itsme\Downloads\Release-26.09.0-0\poppler-26.09.0\Library\bin"


if OCR_AVAILABLE:

    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text(uploaded_file) -> str:
    """
    Extract text from an uploaded TXT, PDF, or DOCX file.
    """

    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if name.endswith(".txt"):
        return raw.decode(
            "utf-8",
            errors="ignore"
        )

    if name.endswith(".pdf"):

        reader = PdfReader(
            BytesIO(raw)
        )

        pages = []

        for page in reader.pages:

            try:
                page_text = page.extract_text() or ""

            except Exception:
                page_text = ""

            if page_text.strip():
                pages.append(page_text)

        return "\n\n".join(pages)

    if name.endswith(".docx"):

        doc = Document(
            BytesIO(raw)
        )

        return "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        )

    raise ValueError(
        "Unsupported file type. "
        "Upload a PDF, DOCX, or TXT file."
    )


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Clean extracted legal text while preserving
    useful legal wording.
    """

    if not text:
        return ""

    # Remove null characters
    text = text.replace(
        "\x00",
        " "
    )

    # Normalize line endings
    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # Replace tabs
    text = text.replace(
        "\t",
        " "
    )

    # Remove excessive spaces
    text = re.sub(
        r"[ ]{2,}",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n[ ]*\n[ ]*\n+",
        "\n\n",
        text
    )

    # Remove spaces at beginning/end of lines
    text = "\n".join(
        line.strip()
        for line in text.split("\n")
    )

    return text.strip()


# ============================================================
# TEXT TRIMMING
# ============================================================

def trim_text(
    text: str,
    limit: int = 14000
) -> str:
    """
    Trim long text for display or model input.
    """

    clean = " ".join(
        text.split()
    )

    if len(clean) <= limit:
        return clean

    return clean[:limit] + "..."


# ============================================================
# CHUNKING
# ============================================================

def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[str]:
    """
    Split legal text into overlapping chunks.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(
            r"\n\s*\n",
            text
        )
        if paragraph.strip()
    ]

    chunks: list[str] = []

    current = ""

    for paragraph in paragraphs:

        # Handle very large paragraphs
        if len(paragraph) > chunk_size:

            if current:
                chunks.append(
                    current
                )

                current = ""

            start = 0

            while start < len(paragraph):

                end = start + chunk_size

                piece = paragraph[
                    start:end
                ].strip()

                if piece:
                    chunks.append(
                        piece
                    )

                start += max(
                    1,
                    chunk_size - overlap
                )

            continue

        proposed = (
            current
            + "\n\n"
            + paragraph
            if current
            else paragraph
        )

        if len(proposed) <= chunk_size:

            current = proposed

        else:

            if current:
                chunks.append(
                    current
                )

            if (
                overlap > 0
                and current
            ):

                overlap_text = current[
                    -overlap:
                ]

                current = (
                    overlap_text
                    + "\n\n"
                    + paragraph
                )

            else:
                current = paragraph

    if current.strip():
        chunks.append(
            current.strip()
        )

    return chunks


# ============================================================
# NORMAL PDF EXTRACTION
# ============================================================

def extract_pdf_pages(
    pdf_path: Path
) -> list[dict]:
    """
    Extract every PDF page separately using pypdf.
    """

    reader = PdfReader(
        str(pdf_path)
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        try:
            text = page.extract_text() or ""

        except Exception as exc:

            print(
                f"Warning: Could not extract "
                f"page {page_number}: {exc}"
            )

            text = ""

        text = clean_text(
            text
        )

        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages


# ============================================================
# OCR PDF EXTRACTION
# ============================================================

def extract_pdf_pages_with_ocr(
    pdf_path: Path
) -> list[dict]:
    """
    Extract text from scanned/image PDFs using OCR.

    Each PDF page is converted to an image and processed
    using Tesseract OCR.
    """

    if not OCR_AVAILABLE:

        print(
            "OCR libraries are not installed."
        )

        return []

    if not os.path.exists(
        TESSERACT_PATH
    ):

        print(
            "Tesseract was not found at:"
        )

        print(
            TESSERACT_PATH
        )

        return []

    if not os.path.exists(
        POPPLER_PATH
    ):

        print(
            "Poppler was not found at:"
        )

        print(
            POPPLER_PATH
        )

        return []

    print(
        "Starting OCR extraction..."
    )

    try:

        images = convert_from_path(
            str(pdf_path),
            dpi=200,
            poppler_path=POPPLER_PATH,
        )

    except Exception as exc:

        print(
            f"OCR PDF conversion failed: {exc}"
        )

        return []

    pages = []

    for page_number, image in enumerate(
        images,
        start=1
    ):

        print(
            f"OCR processing page "
            f"{page_number}/{len(images)}..."
        )

        try:

            text = pytesseract.image_to_string(
                image,
                config="--psm 6"
            )

        except Exception as exc:

            print(
                f"OCR failed on page "
                f"{page_number}: {exc}"
            )

            text = ""

        text = clean_text(
            text
        )

        if text:

            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages


# ============================================================
# LEGAL PDF CHUNK CREATION
# ============================================================

def create_legal_chunks(
    pdf_path: Path,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[dict]:
    """
    Convert a legal PDF into RAG-ready chunks.

    First attempts normal PDF text extraction.

    If no readable text is found, automatically
    falls back to OCR.
    """

    print(
        f"Extracting pages from: "
        f"{pdf_path.name}"
    )

    # --------------------------------------------------------
    # FIRST: NORMAL PDF EXTRACTION
    # --------------------------------------------------------

    pages = extract_pdf_pages(
        pdf_path
    )

    # --------------------------------------------------------
    # SECOND: OCR FALLBACK
    # --------------------------------------------------------

    if not pages:

        print(
            f"No readable text found in "
            f"{pdf_path.name}."
        )

        print(
            "Trying OCR..."
        )

        pages = extract_pdf_pages_with_ocr(
            pdf_path
        )

        if pages:

            print(
                f"OCR successfully extracted "
                f"{len(pages)} page(s)."
            )

        else:

            print(
                f"WARNING: OCR also failed for "
                f"{pdf_path.name}"
            )

            return []

    # --------------------------------------------------------
    # CREATE CHUNKS
    # --------------------------------------------------------

    document_name = (
        pdf_path.stem.replace(
            "_",
            " "
        )
    )

    all_chunks = []

    for page_data in pages:

        page_number = page_data[
            "page"
        ]

        page_text = page_data[
            "text"
        ]

        chunks = chunk_text(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for chunk_index, chunk in enumerate(
            chunks
        ):

            if not chunk.strip():
                continue

            all_chunks.append(
                {
                    "text": chunk,

                    "metadata": {
                        "source": document_name,
                        "filename": pdf_path.name,
                        "page": page_number,
                        "chunk": chunk_index,
                        "document_type": "legal_document",
                    },
                }
            )

    print(
        f"Extracted {len(pages)} "
        f"readable page(s), "
        f"created {len(all_chunks)} "
        f"chunk(s)."
    )

    return all_chunks