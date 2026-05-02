import json
import logging
import os
import re
import threading
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from dataclasses import dataclass
from typing import Any, List, Optional

import httpx

from app.constants.marketplace import MARKETPLACE_TAGS, MARKETPLACE_TAGS_SET

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
# google-genai SDK http_options timeout is in MILLISECONDS.
# 60 000 ms = 60 s — enough to cover the SSL handshake (~25 s on Render)
# plus the model inference time.
GEMINI_TIMEOUT_MS = 60_000
# Hard wall-clock cap via Future.result(timeout=...) in SECONDS.
# Must be > GEMINI_TIMEOUT_MS/1000 so the SDK attempt can complete.
GEMINI_TOTAL_TIMEOUT_S = 65.0
MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGES = 4
IMAGE_FETCH_TIMEOUT_S = 6.0

# Module-level client singleton — reusing one client keeps the TLS connection
# warm and avoids the 20-30s handshake penalty on every request.
_gemini_client_lock = threading.Lock()
_gemini_client_cache: dict[str, Any] = {}

# Keywords → canonical nav tag (first match wins per tag to avoid duplicates)
_HEURISTIC_RULES: List[tuple[tuple[str, ...], str]] = [
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


@dataclass
class ListingSuggestion:
    tags: List[str]
    source: str
    title: Optional[str] = None
    description: Optional[str] = None


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


def _parse_tags_from_dict(parsed: dict) -> List[str]:
    raw_tags = parsed.get("tags")
    if not isinstance(raw_tags, list):
        return []
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


def _parse_listing_json(parsed: dict) -> tuple[Optional[str], Optional[str], List[str]]:
    title = parsed.get("title")
    desc = parsed.get("description")
    t_out: Optional[str] = None
    d_out: Optional[str] = None
    if isinstance(title, str):
        s = title.strip()
        if s:
            t_out = s[:200]
    if isinstance(desc, str):
        s = desc.strip()
        if s:
            d_out = s[:8000]
    tags = _parse_tags_from_dict(parsed)
    return t_out, d_out, tags


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


def _guess_mime_from_url(url: str) -> str:
    u = url.lower().split("?", 1)[0]
    if u.endswith(".png"):
        return "image/png"
    if u.endswith(".webp"):
        return "image/webp"
    if u.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def _fetch_image_part(url: str) -> Any:
    """Download an image and return a genai Part, or None on failure."""
    if not url.startswith("https://"):
        return None
    try:
        with httpx.Client(timeout=IMAGE_FETCH_TIMEOUT_S, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            body = r.content
            if len(body) > MAX_IMAGE_BYTES:
                logger.warning("Skipping image (%.1f MB > limit): %s", len(body) / 1024 / 1024, url)
                return None
            ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
            mime = ct if ct.startswith("image/") else _guess_mime_from_url(url)
            from google.genai import types as genai_types
            return genai_types.Part.from_bytes(data=body, mime_type=mime)
    except Exception as exc:
        logger.warning("Failed to fetch image for Gemini (%s): %s", url, exc)
        return None


def _get_gemini_client(api_key: str) -> Any:
    """Return a cached genai.Client for the given key.

    The client owns an httpx connection pool. Reusing it across requests avoids
    the expensive TLS handshake on every call (~20-30s on Render's network).
    Note: google-genai SDK http_options timeout is in MILLISECONDS.
    """
    if api_key in _gemini_client_cache:
        return _gemini_client_cache[api_key]
    with _gemini_client_lock:
        if api_key in _gemini_client_cache:
            return _gemini_client_cache[api_key]
        from google import genai
        client = genai.Client(
            api_key=api_key,
            http_options={"timeout": GEMINI_TIMEOUT_MS},
        )
        _gemini_client_cache[api_key] = client
        logger.info("Created new Gemini client (connection pool initialised)")
        return client


def suggest_listing_gemini(title: str, description: str, image_urls: List[str]) -> ListingSuggestion | None:
    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        logger.info("Gemini not configured (no GEMINI_API_KEY / GOOGLE_API_KEY) — using heuristics")
        return None

    try:
        from google.genai import types as genai_types
    except ImportError:
        logger.error("google-genai package not installed — pip install google-genai")
        return None

    allowed = ", ".join(f'"{x}"' for x in MARKETPLACE_TAGS)
    draft = (
        f"Current draft title (may be empty): {title.strip() or '[empty]'}\n"
        f"Current draft description (may be empty): {description.strip() or '[empty]'}\n"
    )
    instructions = (
        "You help sellers on an auction marketplace. After any listing photos (if provided), respond with JSON only, "
        "no markdown fences:\n"
        '{"title":"Short compelling auction title, max ~80 characters",'
        '"description":"2–5 sentences: what the item is, condition, what is included, shipping notes if obvious. '
        'Honest, neutral tone.",'
        '"tags":["Tag1",...]}\n\n'
        f"tags: pick 1–3 values from this exact list only (spelling and spacing must match): {allowed}. "
        "Use [] if none fit.\n"
        "If draft title/description are already good, keep or lightly polish them. If photos show the item, prioritize "
        "what you see in the images over weak drafts. If there are no photos, infer only from the drafts.\n\n"
        f"{draft}"
    )

    # Download images concurrently and send as inline bytes so Google's servers
    # don't need to fetch external URLs (which adds latency and can hang).
    parts: List[Any] = [genai_types.Part.from_text(text=instructions)]
    urls_to_fetch = image_urls[:MAX_IMAGES]
    if urls_to_fetch:
        with ThreadPoolExecutor(max_workers=len(urls_to_fetch)) as pool:
            futures = {pool.submit(_fetch_image_part, url): url for url in urls_to_fetch}
            ordered: dict[str, Any] = {}
            for future in as_completed(futures):
                ordered[futures[future]] = future.result()
        for url in urls_to_fetch:
            part = ordered.get(url)
            if part is not None:
                parts.append(part)
    logger.info("Sending %d image(s) inline to Gemini", len(parts) - 1)

    model = (os.getenv("GEMINI_TAG_MODEL") or DEFAULT_GEMINI_MODEL).strip()

    try:
        client = _get_gemini_client(api_key)
        # The SDK uses tenacity internally and may retry on timeouts, which
        # can multiply the wait time. Enforce an absolute wall-clock cap so
        # the endpoint always returns within a predictable window.
        with ThreadPoolExecutor(max_workers=1) as _gemini_pool:
            _future: Future = _gemini_pool.submit(
                lambda: client.models.generate_content(model=model, contents=parts)
            )
            try:
                response = _future.result(timeout=GEMINI_TOTAL_TIMEOUT_S)
            except FuturesTimeoutError:
                logger.error(
                    "Gemini total timeout (%.0fs) exceeded (model=%s) — falling back to heuristic",
                    GEMINI_TOTAL_TIMEOUT_S,
                    model,
                )
                return None
        raw = (getattr(response, "text", None) or "").strip()
        if not raw:
            logger.warning("Gemini returned empty text for model=%s", model)
            return None
        parsed = _json_from_model_text(raw)
        if parsed is None:
            logger.warning("Gemini response was not valid JSON: %.200s", raw)
            return None
        t_out, d_out, tags = _parse_listing_json(parsed)
        if not t_out and not d_out and not tags:
            return None
        return ListingSuggestion(tags=tags, source="gemini", title=t_out, description=d_out)
    except Exception as exc:
        logger.error("Gemini generate_content failed (model=%s): %s", model, exc, exc_info=True)
        return None


def suggest_listing(title: str, description: str, image_urls: List[str]) -> ListingSuggestion:
    """
    When the user clicks suggest on the create listing form:
    - With GEMINI_API_KEY: Gemini reads draft title/description plus up to 4 HTTPS listing image
      URLs (fetched by Google's servers directly) and returns suggested title, description, and tags.
    - Otherwise: keyword heuristics on title+description for tags only (no images).
    """
    t, d = title.strip(), description.strip()
    urls = [u.strip() for u in image_urls if isinstance(u, str) and u.startswith("https://")][:MAX_IMAGES]

    if not t and not d and not urls:
        return ListingSuggestion(tags=[], source="heuristic")

    gemini = suggest_listing_gemini(t, d, urls)
    if gemini is not None and (gemini.title or gemini.description or gemini.tags):
        return gemini

    if t or d:
        return ListingSuggestion(tags=suggest_tags_heuristic(t, d), source="heuristic")
    return ListingSuggestion(tags=[], source="heuristic")
