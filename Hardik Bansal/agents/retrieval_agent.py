from src.embeddings import create_embeddings
from src.vector_store import build_vector_store


def run(chunks):

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = create_embeddings(
        texts
    )

    build_vector_store(
        embeddings,
        chunks
    )

    return True