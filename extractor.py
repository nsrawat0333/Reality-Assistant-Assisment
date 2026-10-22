import os
import json
import re
import time
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# 3.5 works right now, others as fallback when they come back online
MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]

ALL_FIELDS = [
    "project_name", "developer_name", "location_address",
    "price_range", "unit_types", "area", "amenities",
    "possession_date", "rera_number", "total_units",
]

EMPTY_RESULT = {f: {"value": "Not found", "confidence": "not_found"} for f in ALL_FIELDS}

EXTRACTION_PROMPT = """You are a real estate data extraction assistant. Analyze the property brochure text and extract key information.

Rules:
- Extract ONLY what is explicitly stated. Do NOT guess or infer.
- Missing fields → value: "Not found", confidence: "not_found"
- Return ONLY valid JSON, no extra text.

Fields to extract:
- project_name: Project/development name
- developer_name: Developer or builder company
- location_address: Full address, sector, city
- price_range: Price or price range with currency
- unit_types: e.g. 2BHK, 3BHK, Studio
- area: Unit size with unit (sqft/sqm)
- amenities: Comma-separated list
- possession_date: Expected handover/possession date
- rera_number: RERA registration number
- total_units: Total units/apartments in the project

JSON format:
{
  "project_name": {"value": "...", "confidence": "high|medium|low|not_found"},
  "developer_name": {"value": "...", "confidence": "..."},
  "location_address": {"value": "...", "confidence": "..."},
  "price_range": {"value": "...", "confidence": "..."},
  "unit_types": {"value": "...", "confidence": "..."},
  "area": {"value": "...", "confidence": "..."},
  "amenities": {"value": "...", "confidence": "..."},
  "possession_date": {"value": "...", "confidence": "..."},
  "rera_number": {"value": "...", "confidence": "..."},
  "total_units": {"value": "...", "confidence": "..."}
}

Brochure text:
\"\"\"
{brochure_text}
\"\"\"
"""

VISION_PROMPT = """You are a real estate data extraction assistant. Look at the property brochure image(s) and extract key information.

Rules:
- Extract ONLY what is clearly visible. Do NOT guess.
- Missing fields → value: "Not found", confidence: "not_found"
- Return ONLY valid JSON, no extra text.

Extract the same 10 fields as JSON:
project_name, developer_name, location_address, price_range, unit_types,
area, amenities, possession_date, rera_number, total_units

Each field: {"value": "...", "confidence": "high|medium|low|not_found"}
"""


_client = None

def _get_client():
    global _client
    if _client:
        return _client
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY not set in .env file. Get one at https://aistudio.google.com/apikey")
    _client = genai.Client(api_key=api_key)
    return _client


def _parse_json_response(text: str) -> dict:
    """Try multiple strategies to extract JSON from Gemini's response."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # handle markdown code blocks
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # last resort: grab first {...} block
    m = re.search(r'(\{.*\})', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("No valid JSON in response", text, 0)


def _validate_result(result: dict) -> dict:
    """Ensure all expected fields exist with correct structure."""
    valid_conf = {"high", "medium", "low", "not_found"}
    for field in ALL_FIELDS:
        if field not in result:
            result[field] = {"value": "Not found", "confidence": "not_found"}
        elif not isinstance(result[field], dict):
            result[field] = {"value": str(result[field]), "confidence": "medium"}
        else:
            result[field].setdefault("value", "Not found")
            result[field].setdefault("confidence", "medium")
            if result[field]["confidence"] not in valid_conf:
                result[field]["confidence"] = "medium"
    return result


def _call_gemini(client, contents, retries=2):
    """Call Gemini with automatic model fallback and retry on 503/429."""
    last_error = None
    for model in MODELS:
        for attempt in range(retries + 1):
            try:
                response = client.models.generate_content(model=model, contents=contents)
                return response
            except Exception as e:
                last_error = e
                err_str = str(e)
                # retry on 503 (overloaded) or 429 (rate limit)
                if "503" in err_str or "429" in err_str:
                    time.sleep(2 * (attempt + 1))  # backoff: 2s, 4s, 6s
                    continue
                # 404 means model doesn't exist, try next model
                if "404" in err_str:
                    break
                raise
    raise RuntimeError(f"All models failed. Last error: {last_error}")


def extract_property_info(raw_text: str) -> dict:
    """Extract property fields from brochure text using Gemini."""
    if not raw_text or not raw_text.strip():
        return EMPTY_RESULT.copy()

    client = _get_client()
    prompt = EXTRACTION_PROMPT.replace("{brochure_text}", raw_text)

    try:
        response = _call_gemini(client, prompt)
        return _validate_result(_parse_json_response(response.text))
    except json.JSONDecodeError:
        return {**EMPTY_RESULT, "_raw_ai_response": response.text.strip(),
                "_error": "Gemini returned non-JSON. See _raw_ai_response."}
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}")


def extract_property_info_from_images(images: list) -> dict:
    """Extract property fields directly from brochure images using Gemini Vision."""
    if not images:
        return EMPTY_RESULT.copy()

    client = _get_client()

    try:
        response = _call_gemini(client, [VISION_PROMPT] + list(images))
        return _validate_result(_parse_json_response(response.text))
    except json.JSONDecodeError:
        return {**EMPTY_RESULT, "_raw_ai_response": response.text.strip(),
                "_error": "Gemini Vision returned non-JSON."}
    except Exception as e:
        raise RuntimeError(f"Gemini Vision error: {e}")


def result_to_flat_json(result: dict) -> dict:
    """Flatten extraction result to simple key→value dict (no confidence info)."""
    return {
        k: v["value"] if isinstance(v, dict) and "value" in v else v
        for k, v in result.items()
        if not k.startswith("_")
    }
