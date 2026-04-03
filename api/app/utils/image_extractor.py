"""
image_extractor.py
------------------
Extracts medically relevant images from veterinary PDF reports.

Strategy (layered, fastest/cheapest first):
    1. Size filter      — discard images too small to be medical scans
    2. Aspect ratio     — discard very wide/tall strips (headers, separators)
    3. Color entropy    — discard near-monochromatic images (logos, signatures)
    4. Edge density     — discard images with very few edges (blank pages, solid backgrounds)
    5. AI classification — optional Gemini vision call for borderline cases

Dependencies:
    pip install pymupdf pillow numpy
    pip install google-genai   # only if USE_AI_FILTER=true
"""

import io
import logging
import math
import os
import base64
import fitz
import numpy as np
from PIL import Image

from api.app.utils.llm_service import LLMFactory
from api.app.utils.settings import Settings

# ── Tuneable thresholds ───────────────────────────────────────────────────────

# Minimum pixel dimensions to keep an image
MIN_WIDTH  = 150
MIN_HEIGHT = 150

# Aspect ratio limits (width/height). Logos/headers are very wide; signatures very tall
MAX_ASPECT_RATIO = 6.0   # wider than 6:1 → likely a banner/header
MIN_ASPECT_RATIO = 0.15  # taller than ~7:1 → likely a sidebar/signature strip

# Color entropy: near-zero means almost uniform color (white bg, solid logo)
MIN_ENTROPY = 3.5   # bits; real medical images typically > 5.0

# Edge density: fraction of pixels that are edges
MIN_EDGE_DENSITY = 0.02  # 2% of pixels must be edges

# If True, borderline images are sent to Gemini for classification
USE_AI_FILTER = Settings.use_ai_filter.lower() == "true"

# Entropy range considered "borderline" → goes to AI if enabled
BORDERLINE_ENTROPY_MIN = 3.5
BORDERLINE_ENTROPY_MAX = 5.0


# ── Heuristic helpers ─────────────────────────────────────────────────────────

def _image_entropy(img: Image.Image) -> float:
    """Shannon entropy of grayscale histogram. Low = uniform/simple image."""
    gray = img.convert("L")
    hist = gray.histogram()
    total = sum(hist)
    entropy = 0.0
    for count in hist:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def _edge_density(img: Image.Image) -> float:
    """Fraction of pixels with significant gradient (Sobel-like). Low = blank/flat."""
    gray = np.array(img.convert("L"), dtype=np.float32)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    # Pad to same shape
    gx = np.pad(gx, ((0, 0), (0, 1)))
    gy = np.pad(gy, ((0, 1), (0, 0)))
    magnitude = np.sqrt(gx**2 + gy**2)
    threshold = 15  # pixel gradient threshold
    edge_pixels = np.sum(magnitude > threshold)
    return edge_pixels / magnitude.size


def _is_medical_image_heuristic(img: Image.Image) -> tuple[bool, str]:
    """
    Returns (keep, reason).
    Applies size, aspect ratio, entropy and edge density filters.
    """
    w, h = img.size

    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return False, f"too small ({w}x{h})"

    ratio = w / h
    if ratio > MAX_ASPECT_RATIO:
        return False, f"too wide ({ratio:.1f}:1) — likely header/banner"
    if ratio < MIN_ASPECT_RATIO:
        return False, f"too tall ({ratio:.2f}:1) — likely sidebar/strip"

    entropy = _image_entropy(img)
    if entropy < MIN_ENTROPY:
        return False, f"low entropy ({entropy:.2f}) — likely logo/signature/blank"

    edge = _edge_density(img)
    if edge < MIN_EDGE_DENSITY:
        return False, f"low edge density ({edge:.3f}) — likely flat/blank"

    return True, f"passed heuristics (entropy={entropy:.2f}, edges={edge:.3f})"


# ── AI classification (optional) ──────────────────────────────────────────────

def _is_medical_image_ai(image_bytes: bytes) -> bool:
    """
    Ask Gemini whether an image is a medically relevant veterinary scan.
    Used only for borderline cases to reduce unnecessary API calls.
    Returns True if the image should be kept.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        b64 = base64.b64encode(image_bytes).decode()

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                (
                    "Is this image a medically relevant veterinary diagnostic image "
                    "(such as an ultrasound, echocardiogram, X-ray, CT scan, blood smear, "
                    "or similar clinical imaging)? "
                    "Answer ONLY 'yes' or 'no'."
                ),
            ],
            config=types.GenerateContentConfig(temperature=0),
        )
        answer = response.text.strip().lower()
        return answer.startswith("yes")

    except Exception as e:
        logging.warning(f"[image_extractor] AI filter failed: {e}. Keeping image by default.")
        return True  # fail open — better to keep than lose a real image


# ── Main extraction function ──────────────────────────────────────────────────

def extract_images_from_pdf(
    file_path: str,
    institution_id: int,
    patient_id: int,
    study_id: int,
) -> list[str]:
    """
    Extract medically relevant images from a PDF, skipping logos,
    signatures, headers and other non-clinical content.

    Returns a list of relative image paths (relative to Settings.upload_dir).
    """
    doc = fitz.open(file_path)
    images = []

    image_path = f"image/institution_{institution_id}/patient_{patient_id}/study_{study_id}"
    image_dir  = f"{Settings.upload_dir}/{image_path}"
    os.makedirs(image_dir, exist_ok=True)

    kept = 0
    discarded = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_images = page.get_images(full=True)

        for img_index, img in enumerate(page_images):
            xref = img[0]
            try:
                base_image  = doc.extract_image(xref)
                image_bytes = base_image["image"]
                pil_img     = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            except Exception as e:
                logging.warning(f"[image_extractor] Could not open image p{page_index}_{img_index}: {e}")
                continue

            # ── Layer 1-4: heuristic filters ──
            keep, reason = _is_medical_image_heuristic(pil_img)

            if not keep:
                logging.info(f"[image_extractor] SKIP p{page_index}_{img_index}: {reason}")
                discarded += 1
                continue

            # ── Layer 5: AI filter for borderline entropy ──
            if USE_AI_FILTER:
                entropy = _image_entropy(pil_img)
                if BORDERLINE_ENTROPY_MIN <= entropy <= BORDERLINE_ENTROPY_MAX:
                    logging.info(f"[image_extractor] Borderline image p{page_index}_{img_index} — asking AI")
                    if not LLMFactory.get().is_medical_image(image_bytes):
                        logging.info(f"[image_extractor] AI rejected p{page_index}_{img_index}")
                        discarded += 1
                        continue

            # ── Save ──
            filename = f"page_{page_index}_{img_index}.png"
            img_path = f"{image_dir}/{filename}"

            # Save as PNG for consistency (some PDFs embed JPEG)
            pil_img.save(img_path, format="PNG", optimize=True)

            relative_path = f"{image_path}/{filename}"
            images.append(relative_path)
            kept += 1
            logging.info(f"[image_extractor] KEEP p{page_index}_{img_index}: {reason}")

    logging.info(
        f"[image_extractor] Done — kept {kept}, discarded {discarded} "
        f"out of {kept + discarded} images from {os.path.basename(file_path)}"
    )
    return images