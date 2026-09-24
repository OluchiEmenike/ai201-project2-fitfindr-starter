from tools import create_fit_card, search_listings
from agent import run_agent
from utils.data_loader import get_example_wardrobe


def test_create_fit_card_valid_input():
    outfit = "Vintage tee with baggy jeans and chunky sneakers for a worn-in street look."
    item = {
        "title": "Vintage Levi's 501 Jeans",
        "price": 38.0,
        "platform": "depop",
    }

    caption = create_fit_card(outfit, item)

    assert isinstance(caption, str)
    assert len(caption) > 20
    assert "Vintage Levi's 501 Jeans" in caption or "Levi's 501" in caption
    assert caption.count(".") <= 1
    assert "depop" not in caption.lower()
    assert "38" not in caption


def test_create_fit_card_missing_outfit():
    item = {"title": "Vintage tee", "price": 20.0, "platform": "thredUp"}

    caption = create_fit_card("   ", item)

    assert "Unable to generate fit card" in caption


def test_run_agent_success_path():
    session = run_agent("looking for a vintage graphic tee under $30", get_example_wardrobe())

    assert session["error"] is None
    assert session["selected_item"] is not None
    assert session["outfit_suggestion"]
    assert session["fit_card"]


def test_run_agent_no_results():
    session = run_agent("designer ballgown size XXS under $5", get_example_wardrobe())

    assert session["error"] is not None
    assert session["selected_item"] is None


def test_run_agent_empty_wardrobe_has_no_fit_card():
    session = run_agent("vintage graphic tee under $30", {"items": []})

    assert session["error"] is None
    assert session["selected_item"] is not None
    assert session["outfit_suggestion"]
    assert session["fit_card"] is None


def test_search_listings_filters_and_ranks():
    results = search_listings("vintage graphic tee", size="M", max_price=30)

    assert isinstance(results, list)
    assert results
    assert all(item.get("price", 0) <= 30 for item in results)


def test_search_listings_prefers_category_matches():
    results = search_listings("vintage accessory")

    assert results
    assert all(item.get("category") == "accessories" for item in results[:3])


def test_suggest_outfit_excludes_same_category():
    from utils.data_loader import get_example_wardrobe
    from tools import suggest_outfit

    item = {
        "title": "Vintage Levi's 501 Jeans",
        "category": "bottoms",
        "style_tags": ["vintage", "denim"],
        "colors": ["blue"],
    }

    outfit = suggest_outfit(item, get_example_wardrobe())

    assert "Baggy straight-leg jeans" not in outfit
    assert "Wide-leg khaki trousers" not in outfit


def test_suggest_outfit_prefers_matching_colors():
    from tools import suggest_outfit

    wardrobe = {
        "items": [
            {"name": "Black combat boots", "category": "shoes", "colors": ["black"], "style_tags": ["boots", "grunge"]},
            {"name": "Suede Chelsea Boots", "category": "shoes", "colors": ["tan", "camel"], "style_tags": ["vintage", "classic"]},
            {"name": "White ribbed tank top", "category": "tops", "colors": ["white"], "style_tags": ["basics", "minimal"]},
            {"name": "Black crossbody bag", "category": "accessories", "colors": ["black"], "style_tags": ["minimal", "accessories"]},
        ]
    }

    outfit = suggest_outfit({
        "title": "Black combat boots",
        "category": "shoes",
        "style_tags": ["boots", "grunge"],
        "colors": ["black"],
    }, wardrobe)

    assert "Suede Chelsea Boots" not in outfit
    assert "White ribbed tank top" in outfit or "Black crossbody bag" in outfit


def test_suggest_outfit_prompt_excludes_other_shoes(monkeypatch):
    from tools import suggest_outfit

    prompts = []

    class FakeCompletions:
        def create(self, **kwargs):
            prompts.append(kwargs["messages"][0]["content"])
            return type("Response", (), {
                "choices": [type("Choice", (), {
                    "message": type("Message", (), {"content": "Black boots with a graphic tee."})()
                })()]
            })()

    class FakeClient:
        chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("tools._get_groq_client", lambda: FakeClient())
    suggest_outfit(
        {"title": "Black combat boots", "category": "shoes", "style_tags": ["grunge"], "colors": ["black"]},
        {"items": [
            {"name": "White sneakers", "category": "shoes", "colors": ["white"], "style_tags": ["classic"]},
            {"name": "Black graphic tee", "category": "tops", "colors": ["black"], "style_tags": ["grunge"]},
        ]},
    )

    assert prompts
    assert "White sneakers" not in prompts[0]
    assert "Never recommend another item from the new item's category" in prompts[0]


def test_suggest_outfit_avoids_duplicate_bottoms_for_shoes():
    from tools import suggest_outfit

    wardrobe = {
        "items": [
            {"name": "Black straight-leg trousers", "category": "bottoms", "colors": ["black"], "style_tags": ["classic", "minimal"]},
            {"name": "Wide-leg khaki trousers", "category": "bottoms", "colors": ["khaki"], "style_tags": ["vintage", "relaxed"]},
            {"name": "Black graphic tee", "category": "tops", "colors": ["black"], "style_tags": ["grunge", "graphic"]},
            {"name": "White leather sneakers", "category": "shoes", "colors": ["white"], "style_tags": ["minimal", "classic"]},
            {"name": "Black crossbody bag", "category": "accessories", "colors": ["black"], "style_tags": ["minimal", "accessories"]},
        ]
    }

    outfit = suggest_outfit({
        "title": "Black combat boots",
        "category": "shoes",
        "style_tags": ["boots", "grunge"],
        "colors": ["black"],
    }, wardrobe)

    bottom_names = [
        "Black straight-leg trousers",
        "Wide-leg khaki trousers",
    ]
    assert sum(name in outfit for name in bottom_names) <= 1
    assert "Black graphic tee" in outfit or "Black crossbody bag" in outfit
