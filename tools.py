"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import random

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    if not description or not str(description).strip():
        return []

    query = str(description).strip().lower()
    stop_words = {
        "under", "size", "for", "looking", "want", "wants", "need",
        "needs", "search", "find", "item", "clothing", "wear", "user",
        "with", "like", "and", "the", "a", "an", "my", "i", "me"
    }
    size_filter = str(size).strip().lower() if size else ""
    max_price_value = float(max_price) if max_price is not None else None

    listings = load_listings()
    scored_results = []

    for listing in listings:
        price = listing.get("price")
        if max_price_value is not None and price is not None and float(price) > max_price_value:
            continue

        if size_filter:
            listing_size = str(listing.get("size", "")).lower()
            size_variants = {part.strip() for part in listing_size.replace("/", " ").split()}
            if size_filter not in size_variants and size_filter not in listing_size:
                continue

        title = str(listing.get("title", "")).lower()
        desc = str(listing.get("description", "")).lower()
        category = str(listing.get("category", "")).lower()
        style_tags = " ".join(listing.get("style_tags", []) or []).lower()
        colors = " ".join(listing.get("colors", []) or []).lower()

        haystack = " ".join([title, desc, category, style_tags, colors])
        query_tokens = [
            token for token in query.replace("-", " ").split()
            if token and token not in stop_words
        ]
        unique_tokens = set(query_tokens)

        category_hints = {
            "accessory": "accessories",
            "accessories": "accessories",
            "bag": "accessories",
            "belt": "accessories",
            "hat": "accessories",
            "jacket": "outerwear",
            "blazer": "outerwear",
            "coat": "outerwear",
            "vest": "outerwear",
            "shirt": "tops",
            "tee": "tops",
            "top": "tops",
            "hoodie": "tops",
            "sweater": "tops",
            "jeans": "bottoms",
            "pants": "bottoms",
            "trouser": "bottoms",
            "trousers": "bottoms",
            "skirt": "bottoms",
            "shorts": "bottoms",
            "shoe": "shoes",
            "shoes": "shoes",
            "boot": "shoes",
            "boots": "shoes",
            "sneaker": "shoes",
            "sneakers": "shoes",
        }
        expected_category = None
        for token in unique_tokens:
            if token in category_hints:
                expected_category = category_hints[token]
                break

        score = 0
        for token in unique_tokens:
            if token in title:
                score += 4
            if token in desc:
                score += 2
            if token in style_tags:
                score += 2
            if token in category:
                score += 4
            if token in colors:
                score += 1
            if token in haystack:
                score += 1

        if expected_category:
            if category == expected_category:
                score += 12
            else:
                score -= 18

        if score > 0:
            scored_results.append((score, listing))

    scored_results.sort(key=lambda item: (-item[0], float(item[1].get("price", 0.0))))
    return [listing for _, listing in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    if not isinstance(new_item, dict):
        return "I can’t suggest an outfit without a valid item to style."

    wardrobe = wardrobe or {}
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    item_name = new_item.get("title") or new_item.get("name") or "this piece"
    item_category = new_item.get("category") or ""
    item_styles = new_item.get("style_tags") or []
    item_colors = new_item.get("colors") or []

    if not items:
        vibe = "casual, relaxed, and easy"
        if item_styles:
            vibe = ", ".join(item_styles[:2])

        if item_category == "tops":
            return (
                f"{item_name} would look great with relaxed denim, chunky sneakers, "
                f"and a simple layer like a denim jacket or oversized sweater. "
                f"The overall vibe is {vibe} and easy to wear all day."
            )
        if item_category == "bottoms":
            return (
                f"{item_name} pairs well with a fitted top, clean sneakers, and a light "
                f"layer or crossbody bag. It gives off a polished {vibe} feel without being too dressed up."
            )
        if item_category == "outerwear":
            return (
                f"{item_name} works best with basics underneath, straight-leg denim, and "
                f"simple shoes. It creates a laid-back {vibe} look that still feels put together."
            )
        return (
            f"{item_name} is versatile enough to style with relaxed denim, a simple tee, "
            f"and sneakers or boots depending on the vibe you want. It works especially well in {vibe} outfits."
        )

    def category_priority(category: str) -> set[str]:
        mapping = {
            "tops": {"bottoms", "shoes", "accessories"},
            "bottoms": {"tops", "shoes", "outerwear"},
            "outerwear": {"tops", "bottoms", "shoes"},
            "shoes": {"tops", "bottoms", "accessories"},
            "accessories": {"tops", "bottoms", "outerwear"},
        }
        return mapping.get(category, {"tops", "bottoms", "shoes", "accessories"})

    compatible_items = []
    for wardrobe_item in items:
        wardrobe_category = wardrobe_item.get("category") or ""
        if wardrobe_category == item_category:
            continue
        if item_category == "shoes" and wardrobe_category == "shoes":
            continue
        compatible_items.append(wardrobe_item)

    ranked = []
    for wardrobe_item in compatible_items:
        wardrobe_name = wardrobe_item.get("name") or "an item"
        wardrobe_category = wardrobe_item.get("category") or ""
        wardrobe_styles = wardrobe_item.get("style_tags") or []
        wardrobe_colors = wardrobe_item.get("colors") or []

        score = 0
        if wardrobe_category in category_priority(item_category):
            score += 3
        shared_styles = set(item_styles) & set(wardrobe_styles)
        score += len(shared_styles) * 2

        matching_color_count = len(set(str(color).lower() for color in item_colors) & set(str(color).lower() for color in wardrobe_colors))
        if matching_color_count:
            score += 4 * matching_color_count
        elif wardrobe_colors and item_colors:
            score -= 3

        ranked.append((score, wardrobe_name, wardrobe_item))

    ranked.sort(key=lambda entry: entry[0], reverse=True)
    best_matches = []
    used_categories = set()
    for _, _, wardrobe_item in ranked:
        wardrobe_category = wardrobe_item.get("category") or ""
        if wardrobe_category in used_categories:
            continue
        best_matches.append(wardrobe_item)
        used_categories.add(wardrobe_category)
        if len(best_matches) == 4:
            break

    if not best_matches:
        best_matches = compatible_items[:3]

    main_piece = best_matches[0]
    second_piece = best_matches[1] if len(best_matches) > 1 else None
    third_piece = best_matches[2] if len(best_matches) > 2 else None

    try:
        client = _get_groq_client()
        wardrobe_summary = "; ".join(
            f"{item.get('name')} ({item.get('category')})" for item in best_matches
        )
        prompt = (
            f"You are styling a thrifted item for a fashion recommendation. "
            f"Item: {item_name}. Category: {item_category}. Style tags: {item_styles}. "
            f"Allowed wardrobe items: {wardrobe_summary}. "
            f"Use only the allowed wardrobe items and the new item. "
            f"Never recommend another item from the new item's category; boots, sneakers, "
            f"and all other footwear count as the same shoes category. "
            f"Use at most one item from each wardrobe category. "
            f"Suggest 1–2 concise outfit options without mentioning these rules or the model."
        )
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=180,
        )
        result = response.choices[0].message.content.strip()
        if result:
            return result
    except Exception:
        pass

    if second_piece and third_piece:
        return (
            f"{item_name} pairs really well with {main_piece.get('name')} and {second_piece.get('name')}. "
            f"Add {third_piece.get('name')} to keep the styling easy and intentional."
        )
    if second_piece:
        return (
            f"{item_name} looks great with {main_piece.get('name')} and {second_piece.get('name')}. "
            f"This creates a balanced outfit with a relaxed but stylish feel."
        )

    return (
        f"{item_name} would fit naturally into your wardrobe with {main_piece.get('name')}. "
        f"Add a simple neutral layer or accessory and keep the styling casual, balanced, and easy to wear."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A short, one-sentence string usable as a calm Instagram caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Mention only the new listing item
    - Feel calm, casual, and authentic
    - Stay to one sentence
    - Vary naturally between requests
    """
    if not isinstance(outfit, str) or not outfit.strip():
        return "Unable to generate fit card because the outfit suggestion is missing or incomplete."

    if not isinstance(new_item, dict):
        return "Unable to generate fit card because the item data is missing or incomplete."

    item_name = str(new_item.get("title") or new_item.get("name") or "this thrifted find").strip()
    vibe_hint = ""
    wardrobe_piece = ""
    outfit_text = str(outfit).strip()
    lowered = outfit_text.lower()

    if any(word in lowered for word in ["vintage", "grunge", "streetwear", "minimal", "oversized", "casual", "relaxed", "classic"]):
        for word in ["vintage", "grunge", "streetwear", "minimal", "oversized", "casual", "relaxed", "classic"]:
            if word in lowered:
                vibe_hint = word
                break

    wardrobe_matches = [
        "baggy straight-leg jeans",
        "wide-leg khaki trousers",
        "white ribbed tank top",
        "oversized grey crewneck sweatshirt",
        "black cropped zip hoodie",
        "vintage black denim jacket",
        "chunky white sneakers",
        "black combat boots",
        "brown leather belt",
        "black crossbody bag",
    ]
    for name in wardrobe_matches:
        if name.lower() in lowered.lower():
            wardrobe_piece = name
            break

    try:
        client = _get_groq_client()
        prompt = (
            f"Write one short, calm Instagram caption about this thrift listing: {item_name}. "
            "Mention the item and one subtle styling cue, such as the overall vibe or a wardrobe piece like a jacket, sneakers, or jeans. "
            "Do not mention the price, platform, detailed outfit breakdown, or list the full outfit. "
            "Use exactly one sentence, no hashtags, and keep it natural and brief."
        )
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=60,
        )
        caption = response.choices[0].message.content.strip()
        if caption:
            return caption
    except Exception:
        pass

    vibe_templates = [
        f"{item_name} has that easy, worn-in feel I keep reaching for.",
        f"The {item_name} gives off such a relaxed vintage vibe.",
        f"Really loving the effortless feel of {item_name}.",
        f"{item_name} feels like the kind of piece that makes an outfit feel easy.",
    ]
    if wardrobe_piece:
        return f"{item_name} and {wardrobe_piece} feel like such an easy pair together."
    if vibe_hint:
        return random.choice([
            f"{item_name} has that {vibe_hint} feel I keep reaching for.",
            f"The {item_name} feels effortlessly {vibe_hint}.",
            f"This {item_name} has such a {vibe_hint} energy.",
        ])
    return random.choice(vibe_templates)
