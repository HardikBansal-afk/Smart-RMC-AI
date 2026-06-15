# pyrefly: ignore [missing-import]
import faiss
import pickle
import os


def build_vector_store(
        embeddings,
        chunks):

    # Create folder if it doesn't exist
    os.makedirs(
        "vectorstore",
        exist_ok=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(
        embeddings
    )

    faiss.write_index(
        index,
        "vectorstore/index.faiss"
    )

    with open(
            "vectorstore/metadata.pkl",
            "wb"
    ) as f:

        pickle.dump(
            chunks,
            f
        )

    print(
        "Vector store created successfully"
    )