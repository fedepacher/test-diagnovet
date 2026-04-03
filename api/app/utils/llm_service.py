"""
llm_service.py
--------------
LLM abstraction for veterinary data extraction and image classification.

Architecture:
    LLMProvider (ABC)
        ├── GeminiProvider   — Google Gemini (free tier available)
        └── OpenAIProvider   — OpenAI API

    LLMFactory — singleton that instantiates the provider once based on settings

Usage:
    from llm_service import LLMFactory

    llm = LLMFactory.get()
    result = llm.extract(text)           # returns structured dict
    keep   = llm.is_medical_image(bytes) # returns bool
"""

import base64
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Optional

from api.app.utils.settings import Settings

# ── Prompts ───────────────────────────────────────────────────────────────────

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
   - Preserve the ORIGINAL language of the document for all text fields.
    - Do NOT translate any content.

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

IMAGE_PROMPT = (
    "Is this image a medically relevant veterinary diagnostic image "
    "(such as an ultrasound, echocardiogram, X-ray, CT scan, blood smear, "
    "or similar clinical imaging)? "
    "Answer ONLY 'yes' or 'no'."
)

# ── Gemini config ─────────────────────────────────────────────────────────────

GEMINI_FALLBACK_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]

GEMINI_RPM_RETRIES = 2
GEMINI_RPM_WAIT    = 65


# ── Exceptions ────────────────────────────────────────────────────────────────

class QuotaExhaustedError(Exception):
    """All models exceeded their daily quota."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else parts[0]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _parse_retry_delay(error_str: str) -> int:
    match = re.search(r"retry.*?(\d+)\s*s", error_str, re.IGNORECASE)
    return int(match.group(1)) if match else 60


def _is_daily_quota(error_str: str) -> bool:
    return "PerDay" in error_str or "per_day" in error_str.lower()


# ── Abstract base ─────────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """Base class for all LLM providers."""

    @abstractmethod
    def extract(self, text: str) -> dict:
        """Extract structured veterinary data from plain text."""

    @abstractmethod
    def is_medical_image(self, image_bytes: bytes) -> bool:
        """Return True if the image is a medically relevant diagnostic scan."""


# ── Gemini implementation ─────────────────────────────────────────────────────

class GeminiProvider(LLMProvider):

    def __init__(self):
        from google import genai
        from google.genai import types
        self._genai  = genai
        self._types  = types
        self._client = genai.Client(api_key=Settings.gemini_api_key)
        logging.info("[LLMFactory] GeminiProvider initialized")

    def _models_to_try(self) -> list[str]:
        forced = Settings.gemini_model
        if forced:
            return [forced] + [m for m in GEMINI_FALLBACK_MODELS if m != forced]
        return GEMINI_FALLBACK_MODELS

    def _generate(self, contents, config) -> str:
        """
        Try each model in the fallback chain with RPM retry logic.
        Raises QuotaExhaustedError or RuntimeError when all models fail.
        """
        any_daily_exceeded = False
        last_error = None

        for model_name in self._models_to_try():
            logging.info(f"[GeminiProvider] model={model_name}")

            for attempt in range(1, GEMINI_RPM_RETRIES + 1):
                try:
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config,
                    )
                    return response.text

                except Exception as e:
                    err = str(e)
                    is_missing = "404" in err or "NOT_FOUND" in err
                    is_quota   = "429" in err or "quota" in err.lower()

                    if is_missing:
                        logging.warning(f"[GeminiProvider] Model not found: {model_name}. Skipping.")
                        last_error = e
                        break

                    if is_quota:
                        logging.warning(f"[GeminiProvider] Quota error on {model_name}: {err[:300]}")
                        if _is_daily_quota(err):
                            logging.warning(f"[GeminiProvider] RPD exceeded on {model_name}. Trying next model.")
                            any_daily_exceeded = True
                            last_error = e
                            break
                        else:
                            wait = _parse_retry_delay(err) or GEMINI_RPM_WAIT
                            if attempt < GEMINI_RPM_RETRIES:
                                logging.warning(f"[GeminiProvider] RPM exceeded. Waiting {wait}s ({attempt}/{GEMINI_RPM_RETRIES}).")
                                time.sleep(wait)
                                continue
                            else:
                                logging.warning(f"[GeminiProvider] RPM retries exhausted on {model_name}.")
                                last_error = e
                                break

                    raise  # unexpected error

        if any_daily_exceeded:
            raise QuotaExhaustedError(
                "Daily quota exceeded on all Gemini models. "
                "Resets at midnight Pacific Time. Use LLM_PROVIDER=openai as fallback."
            )
        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    def extract(self, text: str) -> dict:
        config = self._types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0,
            response_mime_type="application/json",
        )
        raw = self._generate(EXTRACTION_PROMPT.format(text=text), config)
        return _clean_json(raw)

    def is_medical_image(self, image_bytes: bytes) -> bool:
        try:
            config   = self._types.GenerateContentConfig(temperature=0)
            contents = [
                self._types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                IMAGE_PROMPT,
            ]
            raw = self._generate(contents, config)
            return raw.strip().lower().startswith("yes")
        except Exception as e:
            logging.warning(f"[GeminiProvider] Image classification failed: {e}. Keeping image.")
            return True  # fail open


# ── OpenAI implementation ─────────────────────────────────────────────────────

class OpenAIProvider(LLMProvider):

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=Settings.openai_api_key)
        self._model  = Settings.openai_model
        logging.info(f"[LLMFactory] OpenAIProvider initialized (model={self._model})")

    def extract(self, text: str) -> dict:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": EXTRACTION_PROMPT.format(text=text)},
            ],
            temperature=0,
            response_format={"type": "json_object"},
            timeout=30,
        )
        return json.loads(response.choices[0].message.content)

    def is_medical_image(self, image_bytes: bytes) -> bool:
        try:
            b64 = base64.b64encode(image_bytes).decode()
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": IMAGE_PROMPT},
                    ],
                }],
                temperature=0,
                max_tokens=5,
                timeout=15,
            )
            return response.choices[0].message.content.strip().lower().startswith("yes")
        except Exception as e:
            logging.warning(f"[OpenAIProvider] Image classification failed: {e}. Keeping image.")
            return True


# ── Factory (singleton) ───────────────────────────────────────────────────────

class LLMFactory:
    """
    Instantiates and caches the configured LLM provider.
    Always call LLMFactory.get() — returns the same instance on every call.
    """
    _instance: Optional[LLMProvider] = None

    @classmethod
    def get(cls) -> LLMProvider:
        if cls._instance is None:
            provider = (Settings.llm_provider or "gemini").lower()
            if provider == "gemini":
                cls._instance = GeminiProvider()
            elif provider == "openai":
                cls._instance = OpenAIProvider()
            else:
                raise ValueError(f"Unknown LLM_PROVIDER='{provider}'. Use 'gemini' or 'openai'.")
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Force re-instantiation on next get(). Useful for tests."""
        cls._instance = None


# ── Backward-compatible wrapper ───────────────────────────────────────────────

def call_llm(text: str) -> dict:
    """Kept for backward compatibility. Prefer LLMFactory.get().extract(text)."""
    return LLMFactory.get().extract(text)