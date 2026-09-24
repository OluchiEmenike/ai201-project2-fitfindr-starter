"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """
    session = _new_session(query, wardrobe)

    if not query or not str(query).strip():
        session["error"] = "Please enter a description of the item you want to find."
        return session

    cleaned = str(query).strip()
    description = cleaned
    size = None
    max_price = None

    match = __import__("re").search(r"(?:under|budget|up to)\s*\$?\s*(\d+(?:\.\d+)?)", cleaned, flags=__import__("re").IGNORECASE)
    if match:
        max_price = float(match.group(1))
        description = cleaned[:match.start()] + " " + cleaned[match.end():]

    size_match = __import__("re").search(r"(?:size|sz)\s*[:=-]?\s*([A-Za-z0-9/]+)", cleaned, flags=__import__("re").IGNORECASE)
    if size_match:
        size = size_match.group(1).strip()
        description = cleaned[:size_match.start()] + " " + cleaned[size_match.end():]

    description = " ".join(__import__("re").split(r"\s+", description.strip()))
    description = __import__("re").sub(r"\b(?:under|up to|budget|size|sz)\b", " ", description, flags=__import__("re").IGNORECASE)
    description = description.strip(" ,.-")

    if not description:
        description = cleaned

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    session["search_results"] = search_listings(description, size=size, max_price=max_price)
    if not session["search_results"]:
        session["error"] = "No listings matched your description. Would you like to search for something else?"
        return session

    session["selected_item"] = session["search_results"][0]
    session["outfit_suggestion"] = suggest_outfit(session["selected_item"], wardrobe)

    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    if not wardrobe_items:
        session["fit_card"] = "Unable to generate fit card because the outfit suggestion is missing or incomplete."
        return session

    session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
