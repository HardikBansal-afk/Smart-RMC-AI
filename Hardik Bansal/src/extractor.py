# pyrefly: ignore [missing-import]
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

genai.configure(
    api_key=api_key
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def extract_information(context):

    prompt = f"""
You are an engineering document extractor.

Extract:

1. qty
2. item
3. technical_specification
4. moc
5. make

If unavailable return empty string.

Return ONLY a valid JSON array.

Example:

[
{{
"qty":"2",
"item":"Mechanical Seal Assembly",
"technical_specification":"",
"moc":"",
"make":"Triveni"
}}
]

Context:

{context}
"""

    response = model.generate_content(prompt)

    result = response.text

    result = (
        result
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(result)

    except:
        return []