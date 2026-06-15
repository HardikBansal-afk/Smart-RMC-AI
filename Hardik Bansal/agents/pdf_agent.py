from src.pdf_loader import load_pdf
from src.chunker import create_chunks


def run(files):

    chunks = []

    for file_path in files:

        pages = load_pdf(file_path)

        for page in pages:

            page_chunks = create_chunks(
                page["text"]
            )

            for chunk in page_chunks:

                chunks.append(
                    {
                        "text": chunk,
                        "page": page["page"],
                        "document": file_path
                    }
                )

    return chunks