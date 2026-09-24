# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

The project implements the following tool interfaces exactly as they appear in `tools.py`.

### 1) `search_listings`

Signature:
```python
search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]
```

- Purpose: Finds candidate thrift listings that match a user’s description, optional size requirement, and optional budget cap.
- Inputs:
  - `description` (`str`): item description, such as "vintage graphic tee" or "black denim jacket"
  - `size` (`str | None`): preferred size such as "M", "S/M", or "W30"
  - `max_price` (`float | None`): maximum accepted price
- Return value: `list[dict]` of matching listing dictionaries sorted by relevance, highest match first.
- Failure behavior: If no listings match, it returns an empty list rather than raising an exception.

### 2) `suggest_outfit`

Signature:
```python
suggest_outfit(new_item: dict, wardrobe: dict) -> str
```

- Purpose: Suggests 1–2 outfit ideas using the selected thrifted item and the user’s wardrobe.
- Inputs:
  - `new_item` (`dict`): the chosen listing item from `search_listings()`
  - `wardrobe` (`dict`): wardrobe dictionary with an `items` list
- Return value: a non-empty `str` containing outfit suggestions.
- Failure behavior: If the wardrobe is empty, the function still returns general styling advice instead of crashing.

`create_fit_card`

Signature:
```python
create_fit_card(outfit: str, new_item: dict) -> str
```

- Purpose: Turns an outfit suggestion into a short, calm caption about the new thrifted item.
- Inputs:
  - `outfit` (`str`): the outfit text returned by `suggest_outfit()`
  - `new_item` (`dict`): the selected listing dictionary
- Return value: a one-sentence `str` caption describing the item in a calm, social-media style.
- Failure behavior: If the outfit text is empty or missing, it returns an error string such as "Unable to generate fit card because the outfit suggestion is missing or incomplete."

---

## Planning Loop

**How does your agent decide which tool to call next?**
The planning loop first parses the user’s query to extract the item description, preferred size, and price budget. It then calls `search_listings` with those values to find matching listings. If no listings match, it stops early and asks the user to refine the search. If listings are found, it selects the most relevant item and stores it as `selected_item`. The agent then passes that item and the current wardrobe to `suggest_outfit` to create a styling suggestion. If the wardrobe is empty, it still returns general styling advice instead of crashing. Once an outfit is available, the agent passes both the outfit text and the selected item into `create_fit_card` to generate a short social caption. If the outfit is missing or empty, it returns the required fit-card error message instead of generating a caption.

---

## State Management

**How does information from one tool get passed to the next?**
The agent keeps a session dictionary that stores the original query, parsed values, search results, selected item, outfit suggestion, fit card, and any error message. After `search_listings` returns matches, the top result is stored in `selected_item`. That item is then passed into `suggest_outfit` along with the wardrobe, and the returned outfit string is saved as `outfit_suggestion`. Finally, the outfit text and selected item are passed into `create_fit_card` to produce the final caption. This state flow allows each tool to reuse the previous output without running earlier steps again.

---

## Interaction Walkthrough

**User query:**
"Could you find me a nice vintage hoodie under $50 dollars?"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `search_listings("vintage hoodie", size=None, max_price=50)`
- Why this tool: The agent must first find relevant hoodie listings under the user’s budget.
- Output: A ranked list of hoodie listings that match the request.

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `suggest_outfit(selected_item, wardrobe)`
- Why this tool: Once the best matching listing is identified, the agent styles it using the user’s wardrobe.
- Output: A short outfit suggestion that pairs the hoodie with wardrobe pieces or gives general styling advice.

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `create_fit_card(outfit_suggestion, selected_item)`
- Why this tool: The final step is to turn the outfit suggestion into a short, calm social-media caption.
- Output: A caption that mentions the item and its vibe without listing the full outfit or revealing the price/platform.

**Final output to user:**
The user sees the selected listing, a styling suggestion based on their wardrobe, and a short caption. For an empty wardrobe, the outfit still appears, but the fit card is explicitly returned as: "Unable to generate fit card because the outfit suggestion is missing or incomplete."

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response | Example |
|------|-------------|----------------|---------|
| `search_listings` | No results match the query | Returns an empty list and the agent reports: "No listings matched your description. Would you like to search for something else?" | A query like "cashmere sunglasses under $40" returned no listings. |
| `suggest_outfit` | Wardrobe is empty or no good matches are available | Falls back to general styling advice instead of crashing or returning an empty result | A search for a band tee with an empty wardrobe returns general styling advice about denim, sneakers, and layering. |
| `create_fit_card` | Outfit input is missing, blank, or incomplete | Returns: "Unable to generate fit card because the outfit suggestion is missing or incomplete." | An empty wardrobe or missing outfit input produces this exact response. |

---

## AI Usage

I used AI in two specific implementation steps:

1. Tool implementation help: I gave Copilot the `search_listings` tool spec from `planning.md`, including the inputs, return structure, and expected scoring logic. It produced the initial filtering and ranking function. I then worked with Copilot to adjust the scoring rules and stop-word filtering to better match the dataset and test expectations.

2. Outfit/caption refinement: I gave Copilot the `suggest_outfit` and `create_fit_card` specs, the wardrobe schema, and the planned flow from the architecture diagram in `planning.md`. It produced the initial outfit suggestion and caption wording. I then overrode some of the phrasing so the captions stayed short, calm, and focused on the item and vibe instead of listing the full outfit or exposing price and platform details.

---

## Spec Reflection

**One way planning.md helped during implementation:**
Reading through the planning.md clarified the requirements for each tool and the expected flow of the agent before coding began. It reduced ambiguity by setting the search → outfit → fit-card sequence and by defining the success and failure conditions for each stage.

**One divergence from your spec, and why:**

The implementation uses graceful fallback behavior in a few edge cases instead of strict failures. For example, when the wardrobe is empty or the Groq API is unavailable, the app still returns useful styling advice or a safe caption fallback rather than crashing, which makes the project more realistic in real use.

---

## Verification 

I validated the project by running the app and checking the full user flow. A happy-path query such as a vintage graphic tee under budget correctly populated the listing, outfit, and fit-card panels. I also tested a failure case, including an empty-wardrobe scenario, and confirmed the app responds with the required fit-card error message rather than crashing. 

---
## Youtube Link
https://youtu.be/uMPfLemYMKU

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
