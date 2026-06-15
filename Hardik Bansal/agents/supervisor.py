from agents.pdf_agent import run as pdf_agent
from agents.retrieval_agent import run as retrieval_agent
from agents.extraction_agent import run as extraction_agent
from agents.validation_agent import run as validation_agent
from agents.excel_agent import run as excel_agent


def run(files):

    print(
        "PDF Agent..."
    )

    chunks = pdf_agent(
        files
    )

    print(
        "Retrieval Agent..."
    )

    retrieval_agent(
        chunks
    )

    print(
        "Extraction Agent..."
    )

    rows = extraction_agent()

    print(
        "Validation Agent..."
    )

    rows = validation_agent(
        rows
    )

    print(
        "Excel Agent..."
    )

    path = excel_agent(
        rows
    )

    return path