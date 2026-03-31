"""Must match nav category pills (excluding "All") in the web app."""

MARKETPLACE_TAGS: tuple[str, ...] = (
    "Electronics",
    "Fashion",
    "Collectibles",
    "Home & Garden",
    "Sports",
    "Art",
    "Vehicles",
    "Jewelry",
)

MARKETPLACE_TAGS_SET = frozenset(MARKETPLACE_TAGS)
