"""
Telecom Findings Engine.

Flattens per-photo Claude Vision findings into a single findings table
for the app/Excel report, optionally cross-referencing the extracted
PDF report text for corroboration.

NOTE: The prototype's asset-classification + findings-matching happens
directly in the Claude Vision prompt (see src/vision/gemini_vision.py)
to keep the pipeline light. A dedicated ChromaDB retrieval step (to
match against a larger/evolving findings knowledge base, independent
of what one prompt can hold) is the natural next upgrade — see
get_collection() below as the integration point.
"""
from typing import Any, Dict, List

# Single source of truth for the findings taxonomy lives alongside the
# Claude Vision prompt that uses it (src/vision/gemini_vision.py — kept
# at its original filename so nothing else needs to change), so this
# stays in sync automatically rather than drifting as a second copy.
from src.vision.gemini_vision import STANDARD_FINDINGS  # noqa: F401


def get_collection():
    """Initialize/return a ChromaDB collection for findings retrieval.

    Not used yet in the prototype pipeline (see module docstring).
    """
    # import chromadb
    # client = chromadb.PersistentClient(path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
    # return client.get_or_create_collection("telecom_findings")
    raise NotImplementedError("ChromaDB collection not yet initialized.")


def match_findings(
    observations: List[Dict[str, Any]], pdf_text: str
) -> List[Dict[str, Any]]:
    """
    Flatten per-photo Claude Vision observations into a flat findings table.

    Args:
        observations: List of dicts from analyze_site_photo(), each with
            keys: filename, asset_category, findings (list of dicts with
            finding/priority/confidence/notes).
        pdf_text: Extracted PDF report text (currently informational only;
            not yet cross-matched — future enhancement).

    Returns:
        List of flat finding dicts: finding, asset_category, priority,
        confidence, notes, source_photo.
    """
    rows: List[Dict[str, Any]] = []

    for obs in observations:
        source_photo = obs.get("filename", "unknown")
        asset_category = obs.get("asset_category", "Unclassified")

        for f in obs.get("findings", []):
            rows.append(
                {
                    "source_photo": source_photo,
                    "asset_category": asset_category,
                    "finding": f.get("finding", ""),
                    "priority": f.get("priority", "Medium"),
                    "confidence": f.get("confidence", ""),
                    "notes": f.get("notes", ""),
                }
            )

    return rows
