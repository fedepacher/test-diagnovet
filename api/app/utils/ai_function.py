"""
llm_service.py
--------------
Extracción de datos veterinarios desde texto usando OpenAI o Gemini.

Variables de entorno requeridas:
    LLM_PROVIDER   = "openai" | "gemini"   (default: "gemini")
    OPENAI_API_KEY = sk-...                 (solo si LLM_PROVIDER=openai)
    GEMINI_API_KEY = AIza...               (solo si LLM_PROVIDER=gemini)

Modelos gratuitos de Gemini (Google AI Studio):
    gemini-2.0-flash        → recomendado, muy rápido
    gemini-1.5-flash        → alternativa estable
    gemini-1.5-flash-8b     → más liviano, mayor cuota gratuita
"""

import json
import logging
import re
import time

from api.app.utils.settings import Settings


# ── Prompt compartido ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = "You are a veterinary data extraction assistant. Return only valid JSON."

EXTRACTION_PROMPT = """
You are an expert veterinary medical data extraction system.

Your task is to extract structured information from a veterinary report.

Return ONLY valid JSON. Do not include explanations or text outside JSON.

If unsure about a field, return null.

--------------------------------
OUTPUT FORMAT (STRICT JSON)
--------------------------------

{{
  "patient": {{
    "name": "string | null",
    "species": "string | null",
    "breed": "string | null",
    "gender": "string | null",
    "age": "string | null"
  }},
  "owner": {{
    "name": "string | null",
    "last_name": "string | null",
    "email": "string | null"
  }},
  "veterinarian": {{
    "name": "string | null",
    "last_name": "string | null"
  }},
  "study": {{
    "type": "string | null",
    "date": "string | null"
  }},
  "observations": "string | null",
  "diagnosis": "string | null",
  "recommendations": "string | null",
  "results": [
    {{
      "key": "string",
      "value": "string",
      "unit": "string | null",
      "reference_range": "string | null"
    }}
  ]
}}

--------------------------------
EXTRACTION RULES
--------------------------------

1. LANGUAGE:
   - Input may be in Spanish, English, or Portuguese.
   - Return values in ENGLISH when possible (except proper names).

2. PATIENT:
   - Normalize species: "canino"/"perro" → "dog", "felino"/"gato" → "cat"
   - Age: normalize to English (e.g. "5 años" → "5 years")
   - Gender: keep original text (e.g. "macho castrado")

3. OWNER:
   - If only one word exists, use as "name", leave last_name null.

4. VETERINARIAN:
   - Extract full name, split into name/last_name if possible.

5. STUDY:
   - type: e.g. "ultrasound", "echocardiography", "blood test", "x-ray"
   - date: ISO format YYYY-MM-DD if detectable

6. SECTIONS (do NOT mix):
   - observations → descriptive imaging/lab findings
   - diagnosis    → medical conclusion
   - recommendations → suggested treatments or follow-up actions

7. RESULTS:
   - Extract structured values ONLY if clearly present as key/value pairs.
   - If none → return empty list []

8. MISSING DATA → null. Do NOT invent data.

9. OUTPUT: ONLY JSON. No markdown. No explanations.

--------------------------------
INPUT TEXT
--------------------------------

{text}
"""

# Max RPM retries before giving up on a model
GEMINI_RPM_RETRIES = 2
GEMINI_RPM_WAIT    = 65  # seconds to wait between RPM retries

GEMINI_FALLBACK_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash"
]

def _clean_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else parts[0]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


class QuotaExhaustedError(Exception):
    """Raised when all models are out of quota and retrying won't help today."""
    pass


def _parse_retry_delay(error_str: str) -> int:
    match = re.search(r"retry.*?(\d+)\s*s", error_str, re.IGNORECASE)
    return int(match.group(1)) if match else 60


def _is_daily_quota(error_str: str) -> bool:
    """Return True if the quota is a daily limit (RPD), not per-minute (RPM)."""
    return "PerDay" in error_str or "per_day" in error_str.lower()


# ── OpenAI ────────────────────────────────────────────────────────────────────
def _call_openai(text: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=Settings.openai_api_key)

    response = client.chat.completions.create(
        model=Settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": EXTRACTION_PROMPT.format(text=text)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
        timeout=30,
    )
    return json.loads(response.choices[0].message.content)


# ── Gemini ────────────────────────────────────────────────────────────────────
def _call_gemini(text: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=Settings.gemini_api_key)

    forced_model = Settings.gemini_model
    if forced_model:
        models_to_try = [forced_model] + [
            m for m in GEMINI_FALLBACK_MODELS if m != forced_model
        ]
    else:
        models_to_try = GEMINI_FALLBACK_MODELS

    any_daily_exceeded = False
    last_error = None

    for model_name in models_to_try:
        logging.info(f"[llm_service] Gemini model={model_name}")

        for rpm_attempt in range(1, GEMINI_RPM_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=EXTRACTION_PROMPT.format(text=text),
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0,
                        response_mime_type="application/json",
                    ),
                )
                return _clean_json(response.text)

            except Exception as e:
                err_str = str(e)
                is_quota = "429" in err_str or "quota" in err_str.lower()
                is_missing = "404" in err_str or "NOT_FOUND" in err_str

                if is_missing:
                    logging.warning(f"[llm_service] Model not found: {model_name}. Skipping.")
                    last_error = e
                    break  # skip to next model, no point retrying

                if is_quota:
                    logging.warning(f"[llm_service] Quota error on {model_name}: {err_str[:300]}")
                    if _is_daily_quota(err_str):
                        # Daily quota gone — no point retrying today
                        logging.warning(
                            f"[llm_service] Daily quota (RPD) exceeded on {model_name}. "
                            "Trying next model..."
                        )
                        any_daily_exceeded = True
                        last_error = e
                        break  # skip to next model immediately

                    else:
                        # Per-minute quota — wait and retry same model
                        retry_secs = _parse_retry_delay(err_str) or GEMINI_RPM_WAIT
                        if rpm_attempt < GEMINI_RPM_RETRIES:
                            logging.warning(
                                f"[llm_service] RPM quota exceeded on {model_name}. "
                                f"Waiting {retry_secs}s before retry "
                                f"({rpm_attempt}/{GEMINI_RPM_RETRIES})..."
                            )
                            time.sleep(retry_secs)
                            continue  # retry same model
                        else:
                            logging.warning(
                                f"[llm_service] RPM retries exhausted on {model_name}. "
                                "Trying next model..."
                            )
                            last_error = e
                            break  # move to next model

                # Unexpected error — raise immediately
                raise

    # All models failed
    if any_daily_exceeded:
        raise QuotaExhaustedError(
            "Daily quota (RPD) exceeded on all available Gemini models. "
            "Quota resets at midnight Pacific Time. "
            "Set LLM_PROVIDER=openai as an alternative."
        )

    raise RuntimeError(
        f"All Gemini models failed. Last error: {last_error}. "
        "Try again in a few minutes or set LLM_PROVIDER=openai."
    )


# ── Public entry point ────────────────────────────────────────────────────────
def call_llm(text: str) -> dict:
    """
    Extract structured veterinary data from plain text.

    Selects the provider based on the LLM_PROVIDER env var:
        "openai"  → OpenAI API  (requires OPENAI_API_KEY)
        "gemini"  → Gemini API  (requires GEMINI_API_KEY)  ← default

    Returns a dict matching the extraction schema.
    Raises on API or parsing errors.
    """
    provider = Settings.llm_provider.lower()
    logging.info(f"[llm_service] provider={provider}")

    if provider == "openai":
        return _call_openai(text)
    elif provider == "gemini":
        return _call_gemini(text)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER='{provider}'. Use 'openai' or 'gemini'."
        )
