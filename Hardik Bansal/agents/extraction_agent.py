import pickle

from src.extractor import extract_information


def run():

    with open(
            "vectorstore/metadata.pkl",
            "rb"
    ) as f:

        chunks = pickle.load(f)

    # Merge all chunk texts
    context = "\n".join(
        [
            chunk["text"]
            for chunk in chunks[:30]
        ]
    )

    rows = extract_information(
        context
    )

    return rows