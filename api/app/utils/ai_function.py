import json
from openai import OpenAI


# client = OpenAI()


def call_llm(text):
    prompt = f"""
    You are an expert veterinary medical data extraction system.

    Your task is to extract structured information from a veterinary report.

    Return ONLY valid JSON. Do not include explanations or text outside JSON.

    If unsure about a field, return null.
    
    --------------------------------
    OUTPUT FORMAT (STRICT JSON)
    --------------------------------

    {{
      "patient": {{
        "name": string | null,
        "species": string | null,
        "breed": string | null,
        "gender": string | null,
        "age": string | null
      }},
      "owner": {{
        "name": string | null,
        "last_name": string | null,
        "email": string | null
      }},
      "veterinarian": {{
        "name": string | null,
        "last_name": string | null
      }},
      "study": {{
        "type": string | null,
        "date": string | null
      }},
      "observations": string | null,
      "diagnosis": string | null,
      "recommendations": string | null,
      "results": [
        {{
          "key": string,
          "value": string,
          "unit": string | null,
          "reference_range": string | null
        }}
      ]
    }}

    --------------------------------
    EXTRACTION RULES
    --------------------------------

    1. LANGUAGE:
    - The input may be in Spanish, English, or Portuguese.
    - Always return values in ENGLISH when possible (except names).

    2. PATIENT:
    - Extract animal name.
    - Normalize species:
      - "canino", "perro" → "dog"
      - "felino", "gato" → "cat"
    - Breed: keep original but simplified (e.g., "Schnauzer miniatura" → "schnauzer")
    - Age: extract if present (e.g., "5 años", "3 months", "2y").
      - Normalize to English when possible (e.g., "5 years", "3 months")
  
    3. GENDER:
    - Keep original text (e.g., "macho castrado", "hembra").
    - DO NOT split neutering here.

    4. OWNER:
    - Extract best possible name.
    - If only one word exists, use as "name" and leave last_name null.

    5. VETERINARIAN:
    - Extract full name and split if possible.

    6. STUDY:
    - Detect type (e.g., radiography, blood test, ultrasound).
    - Convert date to ISO format YYYY-MM-DD if possible.

    7. SECTIONS:
    - observations → descriptive findings
    - diagnosis → medical conclusion
    - recommendations → suggested actions or notes

    DO NOT mix these sections.

    8. RESULTS:
    - Extract structured values ONLY if clearly present.
    - If none → return empty list []

    9. MISSING DATA:
    - If a field is missing → use null
    - Do NOT invent data

    10. OUTPUT:
    - Return ONLY JSON
    - No markdown
    - No explanations

    --------------------------------
    INPUT TEXT
    --------------------------------

    {text}
    """

    # response = client.chat.completions.create(
    #     model="gpt-5.4-mini",
    #     messages=[
    #         {"role": "system", "content": "You are a veterinary data extraction assistant."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     temperature=0,
    #     response_format={"type": "json_object"},
    #     timeout = 30
    # )
    #
    # result = json.loads(response.choices[0].message.content)
    # return result

    mocked_output = {
          "patient": {
            "name": "tomy",
            "species": "dog",
            "breed": "mixed",
            "gender": "hembra Castrado",
            "neutered": False,
            "age": "12"
          },
          "owner": {
            "name": "perla",
            "last_name": "dela",
            "email": None
          },
          "veterinarian": {
            "name": "papa",
            "last_name": "rober"
          },
          "study": {
            "type": "RX",
            "date": "2025-08-27"
          },
          "observations": "...",
          "diagnosis": "...",
          "recommendations": "...",
          "results": [
            {"key": "glucose", "value": "120", "unit": "mg/dL"}
          ]
        }
    return mocked_output
