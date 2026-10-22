import io
import pdfplumber
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def pdf_has_extractable_text(file_bytes: bytes) -> bool:
    """Returns False for scanned/image-only PDFs."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                return True
    return False


def convert_pdf_pages_to_images(file_bytes: bytes, max_pages: int = 5) -> list:
    """Convert PDF pages to PIL Images for Gemini Vision. Falls back to pdfplumber if poppler unavailable."""
    if PDF2IMAGE_AVAILABLE:
        try:
            return convert_from_bytes(file_bytes, first_page=1, last_page=max_pages, dpi=200)
        except Exception:
            pass

    # pdfplumber fallback (no poppler needed)
    images = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages:
                break
            try:
                images.append(page.to_image(resolution=200).original)
            except Exception:
                continue
    return images


def extract_text_from_image(file_bytes: bytes) -> str:
    if not TESSERACT_AVAILABLE:
        raise RuntimeError(
            "pytesseract not installed. Run: pip install pytesseract\n"
            "Also install Tesseract binary: https://github.com/tesseract-ocr/tesseract"
        )
    return pytesseract.image_to_string(Image.open(io.BytesIO(file_bytes))).strip()


def open_image(file_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(file_bytes))


def extract_text(file_bytes: bytes, file_name: str) -> str:
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    if ext in ("jpg", "jpeg", "png", "bmp", "tiff", "webp"):
        return extract_text_from_image(file_bytes)
    raise ValueError(f"Unsupported file type: .{ext}")
