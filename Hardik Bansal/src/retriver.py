# pyrefly: ignore [missing-import]
import faiss
import pickle

from src.embeddings import create_embeddings


def retrieve(query):

    # Load index only when needed
    index = faiss.read_index(
        "vectorstore/index.faiss"
    )

    with open(
            "vectorstore/metadata.pkl",
            "rb"
    ) as f:

        chunks = pickle.load(f)

    query_embedding = create_embeddings(
        [query]
    )

    distance, indices = index.search(
        query_embedding,
        k=5
    )

    return [
        chunks[i]
        for i in indices[0]
    ]