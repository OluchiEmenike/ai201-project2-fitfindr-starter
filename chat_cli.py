from agent import run_agent
from tools import create_fit_card, suggest_outfit
from utils.data_loader import get_example_wardrobe


def main() -> None:
    print("FitFindr terminal chat")
    print("Type 'quit' or 'exit' to leave.")
    print("Start with a search, then ask for an outfit, then ask for a fit card.\n")

    wardrobe = get_example_wardrobe()
    session = None

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            print("\nSession ended.")
            break

        if not user_input:
            print("Agent: Please say what you want to look for.")
            continue

        command = user_input.lower()
        if command in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        outfit_keywords = ["outfit", "style me", "style it", "what should i wear", "what should i style", "look", "wardrobe"]
        fit_card_keywords = ["fit card", "fitcard", "caption", "social post", "make the fit card", "make a caption"]

        if any(keyword in command for keyword in fit_card_keywords):
            if session is None or not session.get("selected_item"):
                print("Agent: Search for an item and ask for an outfit before I make the fit card.")
                continue

            outfit = session.get("outfit_suggestion")
            if not outfit:
                print("Agent: I need an outfit suggestion first. Ask for an outfit before requesting the fit card.")
                continue

            fit_card = create_fit_card(outfit, session["selected_item"])
            session["fit_card"] = fit_card
            print(f"Fit card: {fit_card}")
            continue

        if any(keyword in command for keyword in outfit_keywords):
            if session is None or not session.get("selected_item"):
                print("Agent: Search for an item first, then I can suggest an outfit.")
                continue

            outfit = suggest_outfit(session["selected_item"], wardrobe)
            session["outfit_suggestion"] = outfit
            print(f"Outfit: {outfit}")
            continue

        session = run_agent(user_input, wardrobe)
        if session.get("error"):
            print(f"Agent: {session['error']}")
            continue

        item = session.get("selected_item")
        if not item:
            print("Agent: I couldn't find a matching listing.")
            continue

        print(f"Listing: {item.get('title')}")
        print("Agent: Ask for an outfit next, then a fit card.")
        print("---")


if __name__ == "__main__":
    main()
