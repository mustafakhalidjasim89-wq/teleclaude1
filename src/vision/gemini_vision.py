"""
Claude Vision observation layer.

Analyzes site photographs (towers, antennas, DG systems, batteries,
grounding, cabinets, fire protection, housekeeping) and returns
structured findings for downstream reporting.

Originally built on Gemini; swapped to the Anthropic Claude API
(model: claude-sonnet-5) for the vision step. Module kept at its
original filename/path (src/vision/gemini_vision.py) so nothing else
in the app needs to change — only what's inside this file.
"""
import base64
import json
import mimetypes
import os
from typing import Any, Dict

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

ASSET_CATEGORIES = [
    "Telecom Tower",
    "Antenna / RRU",
    "Feeder & Fiber System",
    "Generator (DG) System",
    "Fuel Tank & Piping",
    "Battery Bank",
    "Rectifier & ATS Panel",
    "Commercial Power Infrastructure",
    "Outdoor Cabinet / Shelter",
    "Grounding System",
    "Fire Protection Equipment",
    "Site Housekeeping & Safety",
]

# Standardized findings taxonomy the model should map observations to
# wherever possible, instead of inventing free-text findings.
#
# Each entry includes the specific visual evidence that confirms the
# finding, and — critically — what commonly-confused, benign thing it
# is NOT. Naming defects alone lets the model over-trigger on
# superficial lookalikes (e.g. normal grass vs. fire-risk dry grass,
# a battery's normal rounded case vs. actual swelling). Spelling out
# the distinguishing cues up front is cheaper than discovering the
# false-positive pattern after the fact.
STANDARD_FINDINGS = [
    {
        "finding": "Dry grass near generator",
        "look_for": "brown/yellow, brittle-looking dead grass or vegetation within roughly 1-2 meters of the generator or fuel area",
        "not_to_confuse_with": "ordinary green or mixed green/brown grass elsewhere on site with no proximity to a fire-risk source",
    },
    {
        "finding": "Gas piping without cable trays",
        "look_for": "exposed gas/fuel piping running alongside or near electrical cabling with no enclosed tray or conduit protecting either",
        "not_to_confuse_with": "piping that is clearly separated from any cabling, or cabling that is already inside a tray",
    },
    {
        "finding": "Tray cover not closed properly",
        "look_for": "a visible gap, misalignment, or missing section in a cable tray's cover/lid",
        "not_to_confuse_with": "a tray with no cover by design, or a fully seated cover viewed at an angle that only looks open",
    },
    {
        "finding": "Battery swelling observed",
        "look_for": "a battery case that is visibly bulging, distorted, or cracked compared to its expected flat/rectangular shape",
        "not_to_confuse_with": "a battery's normal rounded or ribbed casing design, dust, or reflective glare that can look like distortion",
    },
    {
        "finding": "Generator fuel leakage observed",
        "look_for": "a visible wet patch, staining, or pooling of fuel/oil beneath or around the generator",
        "not_to_confuse_with": "water stains from rain, condensation, or a shadow that only resembles a stain",
    },
    {
        "finding": "Grounding cable disconnected",
        "look_for": "a grounding cable with a visibly detached terminal, dangling free end, or a connection point with no cable attached",
        "not_to_confuse_with": "a properly terminated ground cable that is simply routed out of the frame or partially obscured",
    },
    {
        "finding": "Fire extinguisher expired",
        "look_for": "a visible inspection tag/gauge showing an expired date or a gauge needle in the red/refill zone",
        "not_to_confuse_with": "a tag that is present but illegible in the photo — that is 'Tower equipment image unclear', not an expiry finding",
    },
    {
        "finding": "Disorganized feeder cables on tower",
        "look_for": "feeder cables that are loose, crossing haphazardly, or not secured/bundled to the tower structure",
        "not_to_confuse_with": "cables that are neatly bundled but simply numerous, or a normal cable routing pattern",
    },
    {
        "finding": "Required image not provided",
        "look_for": "use only when a specific mandatory angle/asset for this category is evidently missing from what was provided",
        "not_to_confuse_with": "n/a — this is a coverage gap, not a visual defect",
    },
    {
        "finding": "Tower equipment image unclear",
        "look_for": "the image is blurry, too dark, too far away, or obstructed such that a genuine inspection call cannot be made",
        "not_to_confuse_with": "an image that is clear but simply shows no defects — that should get zero findings, not this one",
    },
]

PROMPT_TEMPLATE = """You are an experienced telecom infrastructure site inspector.
Analyze this site photo and identify the asset category shown and any
genuine audit findings (defects, safety issues, non-compliance, or anomalies).

Known asset categories: {categories}

Known standardized findings. For each, "look_for" is the specific visual
evidence required to report it, and "not_to_confuse_with" names the
benign lookalike that should NOT trigger it. Only report a finding when
the "look_for" evidence is actually present in the image — do not report
it just because the general topic (e.g. grass, cables, a battery) is
visible:
{standard_findings}

Rules:
- Prefer these standardized finding phrases exactly when they apply.
  Only propose a new, concise finding phrase if none of the above fit.
- Do not report a finding on the strength of the asset's mere presence
  (e.g. a battery photo alone is not "Battery swelling observed" unless
  swelling is actually visible).
- If you are genuinely unsure whether something qualifies, prefer NOT
  reporting it over guessing, and lower "confidence" accordingly.
- An image with no visible issues should return an empty "findings" list
  — that is a valid and expected outcome, not a failure to find something.

Respond with ONLY valid JSON, no markdown fences, no commentary before or
after, in this exact shape:
{{
  "asset_category": "<one of the known asset categories, or \\"Unclassified\\">",
  "findings": [
    {{
      "finding": "<standardized finding phrase, or a concise new one>",
      "priority": "<High|Medium|Low>",
      "confidence": <0.0-1.0>,
      "notes": "<one short sentence citing the specific visual evidence observed>"
    }}
  ]
}}
"""


def _format_standard_findings() -> str:
    lines = []
    for f in STANDARD_FINDINGS:
        lines.append(
            f"- {f['finding']}\n"
            f"    look_for: {f['look_for']}\n"
            f"    not_to_confuse_with: {f['not_to_confuse_with']}"
        )
    return "\n".join(lines)


def _build_prompt() -> str:
    return PROMPT_TEMPLATE.format(
        categories=", ".join(ASSET_CATEGORIES),
        standard_findings=_format_standard_findings(),
    )


def _parse_model_json(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"asset_category": "Unclassified", "findings": [], "raw_response": text}


def _guess_media_type(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    if guessed in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        return guessed
    return "image/jpeg"


def analyze_site_photo(photo_file) -> Dict[str, Any]:
    """
    Send a single site photo to Claude Vision and return structured
    findings (asset category, matched findings, priority, confidence).

    Args:
        photo_file: A file-like object (e.g. Streamlit UploadedFile).

    Returns:
        Dict with keys: filename, asset_category, findings (list of dicts).
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file locally, "
            "or to your app's Secrets if deployed on Streamlit Cloud."
        )

    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    filename = getattr(photo_file, "name", "unknown.jpg")

    if hasattr(photo_file, "seek"):
        photo_file.seek(0)
    raw_bytes = photo_file.read()
    if hasattr(photo_file, "seek"):
        photo_file.seek(0)

    media_type = _guess_media_type(filename)
    image_b64 = base64.standard_b64encode(raw_bytes).decode("utf-8")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": _build_prompt()},
                ],
            }
        ],
    )

    response_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    parsed = _parse_model_json(response_text)

    return {
        "filename": filename,
        "asset_category": parsed.get("asset_category", "Unclassified"),
        "findings": parsed.get("findings", []),
    }
