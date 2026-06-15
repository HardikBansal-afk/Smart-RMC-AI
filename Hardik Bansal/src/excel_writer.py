import pandas as pd
import os

def save_excel(data):

    os.makedirs("outputs", exist_ok=True)

    df = pd.DataFrame(data)

    df.to_excel(
        "outputs/final_output.xlsx",
        index=False
    )

    return "outputs/final_output.xlsx"