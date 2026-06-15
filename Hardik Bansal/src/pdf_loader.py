# pyrefly: ignore [missing-import]
import fitz
def load_pdf(file_path):
    doc = fitz.open(file_path)
    pages = []
    MAX_PAGES = 20
    for page_num, page in enumerate(doc):
        if page_num >= MAX_PAGES:
            break
        text = page.get_text()
        if text.strip():
            pages.append(
                {
                    "text": text,
                    "page": page_num + 1
                }
            )
    return pages