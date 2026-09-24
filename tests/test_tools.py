from tools import create_fit_card, search_listings, suggest_outfit


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert results


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)

    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe():
    result = suggest_outfit(
        {
            "title": "Vintage graphic tee",
            "category": "tops",
            "style_tags": ["vintage", "grunge"],
        },
        {"items": []},
    )

    assert isinstance(result, str)
    assert result


def test_suggest_outfit_uses_only_allowed_items(monkeypatch):
    prompts = []

    class FakeCompletions:
        def create(self, **kwargs):
            prompts.append(kwargs["messages"][0]["content"])
            return type("Response", (), {
                "choices": [type("Choice", (), {
                    "message": type("Message", (), {"content": "A simple outfit."})()
                })()]
            })()

    class FakeClient:
        chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("tools._get_groq_client", lambda: FakeClient())
    result = suggest_outfit(
        {
            "title": "Black combat boots",
            "category": "shoes",
            "style_tags": ["grunge"],
            "colors": ["black"],
        },
        {"items": [
            {"name": "White sneakers", "category": "shoes", "colors": ["white"]},
            {"name": "Black graphic tee", "category": "tops", "colors": ["black"]},
        ]},
    )

    assert result == "A simple outfit."
    assert prompts
    assert "White sneakers" not in prompts[0]
    assert "Black graphic tee" in prompts[0]


def test_create_fit_card_empty_outfit():
    result = create_fit_card("", {"title": "Vintage tee"})

    assert "Unable to generate fit card" in result


def test_create_fit_card_valid_input(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            return type("Response", (), {
                "choices": [type("Choice", (), {
                    "message": type("Message", (), {"content": "This vintage tee is such a good find."})()
                })()]
            })()

    class FakeClient:
        chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("tools._get_groq_client", lambda: FakeClient())
    result = create_fit_card(
        "Style it with jeans.",
        {"title": "Vintage tee", "price": 20, "platform": "depop"},
    )

    assert result == "This vintage tee is such a good find."
    assert result.count(".") == 1
    assert "20" not in result
    assert "depop" not in result


def test_create_fit_card_fallback_wording_varies(monkeypatch):
    captions = [
        "Vintage tee is such a good find.",
        "The Vintage tee looks effortlessly good.",
    ]
    monkeypatch.setattr("tools._get_groq_client", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr("tools.random.choice", lambda options: captions.pop(0))

    first = create_fit_card("Style it simply.", {"title": "Vintage tee"})
    second = create_fit_card("Style it simply.", {"title": "Vintage tee"})

    assert first != second
