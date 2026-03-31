import json
import os
import re
from typing import Any, List, Tuple

from app.constants.marketplace import MARKETPLACE_TAGS, MARKETPLACE_TAGS_SET

# Keywords → canonical nav tag (first match wins per tag to avoid duplicates)
_HEURISTIC_RULES: List[Tuple[Tuple[str, ...], str]] = [
    (
        (
            "phone",
            "laptop",
            "computer",
            "tablet",
            "gpu",
            "cpu",
            "monitor",
            "headphone",
            "speaker",
            "camera",
            "console",
            "nintendo",
            "playstation",
            "xbox",
            "electronics",
            "usb",
            "hdmi",
            "charger",
            "iphone",
            "android",
            "tech",
        ),
        "Electronics",
    ),
    (
        (
            "shirt",
            "dress",
            "shoe",
            "sneaker",
            "jacket",
            "coat",
            "pants",
            "jeans",
            "watch",
            "handbag",
            "fashion",
            "apparel",
            "clothing",
        ),
        "Fashion",
    ),
    (
        ("coin", "card", "comic", "vintage", "antique", "memorabilia", "collectible", "figurine", "rare print"),
        "Collectibles",
    ),
    (
        (
            "furniture",
            "sofa",
            "chair",
            "table",
            "kitchen",
            "garden",
            "lawn",
            "plant",
            "decor",
            "bedding",
            "home",
            "appliance",
        ),
        "Home & Garden",
    ),
    (
        ("sport", "bicycle", "bike", "golf", "tennis", "hockey", "soccer", "football", "basketball", "fitness", "gym"),
        "Sports",
    ),
    (
        ("painting", "sculpture", "print", "canvas", "artist", "gallery", "artwork", "drawing", "photography"),
        "Art",
    ),
    (
        ("car", "truck", "suv", "motorcycle", "vehicle", "auto", "automotive", "boat", "tire", "engine"),
        "Vehicles",
    ),
    (
        ("jewelry", "jewellery", "ring", "necklace", "bracelet", "gold", "silver", "diamond", "gem", "earring"),
        "Jewelry",
    ),
]


def _normalize_blob(title: str, description: str) -> str:
    return f"{title}\n{description}".lower()


def suggest_tags_heuristic(title: str, description: str) -> List[str]:
    blob = _normalize_blob(title, description)
    out: List[str] = []
    seen: set[str] = set()
    for keywords, tag in _HEURISTIC_RULES:
        if tag in seen:
            continue
        if any(k in blob for k in keywords):
            out.append(tag)
            seen.add(tag)
        if len(out) >= 3:
            break
    return out


def _parse_tags_json_payload(parsed: Any) -> List[str] | None:
    if not isinstance(parsed, dict):
        return None
    raw_tags = parsed.get("tags")
    if not isinstance(raw_tags, list):
        return None
    out: List[str] = []
    seen: set[str] = set()
    for t in raw_tags:
        if not isinstance(t, str):
            continue
        s = t.strip()
        if s in MARKETPLACE_TAGS_SET and s not in seen:
            out.append(s)
            seen.add(s)
        if len(out) >= 5:
            break
    return out[:3] if len(out) > 3 else out


def _json_from_model_text(text: str) -> dict | None:
    t = text.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)```\s*$", t, re.IGNORECASE)
    if fence:
        t = fence.group(1).strip()
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(t[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def suggest_tags_gemini(title: str, description: str) -> List[str] | None:
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return None

    try:
        from google import genai
    except ImportError:
        return None

    allowed = ", ".join(f'"{x}"' for x in MARKETPLACE_TAGS)
    user_block = f"Title:\n{title.strip()}\n\nDescription:\n{description.strip()}"
    prompt = (
        "You assign marketplace categories. Pick 1 to 3 labels from this exact list only "
        f"(spelling and spacing must match exactly): {allowed}.\n"
        'Respond with JSON only, no markdown: {"tags":["Label1",...]} — use fewer if unsure. '
        "If nothing fits, use {\"tags\":[]}.\n\n"
        f"{user_block}"
    )

    model = (os.getenv("GEMINI_TAG_MODEL") or "gemini-2.0-flash").strip()

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        raw = (getattr(response, "text", None) or "").strip()
        if not raw:
            return None
        parsed = _json_from_model_text(raw)
        if parsed is None:
            return None
        tags = _parse_tags_json_payload(parsed)
        return tags
    except Exception:
        return None


def suggest_tags(title: str, description: str) -> Tuple[List[str], str]:
    """Returns (tags, source) where source is 'gemini' or 'heuristic'."""
    t, d = title.strip(), description.strip()
    if not t and not d:
        return [], "heuristic"

    gemini = suggest_tags_gemini(t, d)
    if gemini is not None and len(gemini) > 0:
        return gemini, "gemini"

    return suggest_tags_heuristic(t, d), "heuristic"
