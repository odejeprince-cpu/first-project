import itertools
import json
import os
import shutil
import sys
import textwrap
import threading
import time

import requests

FILE = "tickets.json"

# Each provider has its own key (read from an environment variable),
# its own request style, and its own list of models.
PROVIDERS = {
    "1": {
        "name": "Gemini (Google)",
        "key_env": "GEMINI_API_KEY",
        "style": "gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "models": [
            ("gemini-3.1-flash-lite", "fast and lightweight (recommended)"),
            ("gemini-3.5-flash-lite", "newer lightweight model"),
            ("gemini-3.8-flash", "smarter, but can be slower"),
            ("gemma-4-26b-a4b-it", "open model from Google"),
        ],
    },
    "2": {
        "name": "Groq",
        "key_env": "GROQ_API_KEY",
        "style": "openai",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "models": [
            ("openai/gpt-oss-20b", "small open model, very fast (recommended)"),
            ("openai/gpt-oss-120b", "larger open model, more capable"),
            ("qwen/qwen3.8-27b", "Qwen model, balanced"),
        ],
    },
    "3": {
        "name": "OpenRouter",
        "key_env": "OPENROUTER_API_KEY",
        "style": "openai",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "models": [
            ("openrouter/free", "automatically picks a free model (recommended)"),
            ("nvidia/nemotron-3-ultra-550b-a55b:free", "large free model"),
        ],
    },
}

# ---------- Colours ----------
USE_COLOR = sys.stdout.isatty()

BLUE = "1;94"
GREEN = "92"
BRIGHT_GREEN = "1;92"
YELLOW = "93"
PURPLE = "1;95"
RED = "91"
GRAY = "90"
WHITE = "97"

BOX_COLOR = YELLOW   # colour of the box outline
BOX_TEXT = WHITE     # colour of the text inside the box


def paint(text, code):
    """Wrap text in a colour code (plain text if the terminal has no colour)."""
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def print_yellow_box(text):
    """Print text inside a yellow outlined rectangle."""
    max_width = min(70, shutil.get_terminal_size().columns - 8)

    lines = []
    for raw in text.splitlines():
        lines.extend(textwrap.wrap(raw, max_width, subsequent_indent="   ") or [""])

    inner = max(len(line) for line in lines)

    print(paint("┌" + "─" * (inner + 2) + "┐", BOX_COLOR))
    for line in lines:
        print(
            paint("│ ", BOX_COLOR)
            + paint(line.ljust(inner), BOX_TEXT)
            + paint(" │", BOX_COLOR)
        )
    print(paint("└" + "─" * (inner + 2) + "┘", BOX_COLOR))


# ---------- Loading spinner ----------
class Spinner:
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, message):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop_event.is_set():
                break
            print(f"\r{paint(frame + ' ' + self.message, YELLOW)}", end="", flush=True)
            time.sleep(0.1)

    def start(self):
        self._thread.start()

    def stop(self, success, final_message):
        self._stop_event.set()
        self._thread.join()
        if success:
            line = paint("✔ " + final_message, BRIGHT_GREEN)
        else:
            line = paint("✖ " + final_message, RED)
        print("\r\033[K" + line)


# ---------- AI ----------
def build_prompt(ticket):
    return (
        "You are an IT support assistant for a university campus helpdesk.\n"
        "A user submitted this support ticket:\n\n"
        f"Title: {ticket['title']}\n"
        f"Description: {ticket['description']}\n\n"
        "Suggest 3 to 5 practical ways to fix or investigate this problem. "
        "Reply as a short numbered list, one step per line, with no extra introduction."
    )


def get_ai_suggestions(ticket, provider, model):
    """Send the ticket to the chosen provider and model.
    Returns (suggestions, None) on success or (None, error_message) on failure."""
    key_env = provider["key_env"]
    api_key = os.environ.get(key_env)
    if not api_key:
        return None, f"{key_env} is not set. Add it to ~/.zshrc, or choose another provider."

    prompt = build_prompt(ticket)

    if provider["style"] == "gemini":
        url = provider["url"].format(model=model)
        headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
        body = {"contents": [{"parts": [{"text": prompt}]}]}
    else:  # "openai" style, used by Groq and OpenRouter
        url = provider["url"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        body = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        data = response.json()

        if provider["style"] == "gemini":
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            text = data["choices"][0]["message"]["content"]

        if not text or not text.strip():
            raise ValueError("empty answer")
        return text.strip(), None

    except requests.exceptions.ConnectionError:
        return None, "Could not connect. Please check your internet connection."
    except requests.exceptions.Timeout:
        return None, f"The request to {model} timed out. Try again or choose another model."
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status in (400, 401, 403):
            return None, f"The request was rejected. Check your {key_env} and the model name."
        if status == 402:
            return None, f"{provider['name']} needs credits or a payment method for this model."
        if status == 404:
            return None, f"Model '{model}' was not found. Try a different model."
        if status == 429:
            return None, "Too many requests (free limit reached). Wait a moment and try again."
        if status in (500, 502, 503):
            return None, f"{model} is unavailable or overloaded. Try another model or provider."
        return None, f"The API request failed (status {status})."
    except (KeyError, IndexError, TypeError, ValueError):
        return None, "The AI returned a response in an unexpected format."
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"


def choose_ai():
    """Ask the user for a provider, then a model. Returns (provider, model) or None to skip."""
    print(paint("\nChoose an AI provider:", BLUE))
    for key, p in PROVIDERS.items():
        print(f"{key}. {p['name']}")
    print("0. Skip AI suggestions")

    while True:
        choice = input(paint("Choose a provider (0-3, press Enter for 1): ", GREEN)).strip() or "1"
        if choice == "0":
            return None
        if choice in PROVIDERS:
            provider = PROVIDERS[choice]
            break
        print(paint("Invalid choice. Please enter a number from 0 to 3.", RED))

    models = provider["models"]
    print(paint(f"\nChoose a {provider['name']} model:", BLUE))
    for number, (name, note) in enumerate(models, start=1):
        print(f"{number}. {name} - {paint(note, GRAY)}")

    while True:
        choice = input(
            paint(f"Choose a model (1-{len(models)}, press Enter for 1): ", GREEN)
        ).strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            return provider, models[int(choice) - 1][0]
        print(paint(f"Invalid choice. Please enter a number from 1 to {len(models)}.", RED))


# ---------- Tickets ----------
def create_ticket():
    title = input(paint("Enter ticket title: ", GREEN)).strip()
    description = input(paint("Enter ticket description: ", GREEN)).strip()

    if not title or not description:
        print(paint("Title and description cannot be empty.", RED))
        return None

    try:
        if os.path.exists(FILE):
            with open(FILE, "r") as f:
                tickets = json.load(f)
        else:
            tickets = []

        ticket = {
            "id": f"A{len(tickets) + 1:03d}",
            "title": title,
            "description": description,
        }

        tickets.append(ticket)

        with open(FILE, "w") as f:
            json.dump(tickets, f, indent=4)

        print(paint("\n✔ Ticket created successfully.", BRIGHT_GREEN))
        print(paint("ID:", GRAY), paint(ticket["id"], WHITE))
        print(paint("Description:", GRAY), paint(ticket["description"], WHITE))
        return ticket

    except (OSError, json.JSONDecodeError) as e:
        print(paint(f"Error: {e}", RED))
        return None


def create_ticket_with_suggestions():
    ticket = create_ticket()
    if ticket is None:
        return

    while True:
        choice = choose_ai()
        if choice is None:
            print(paint("\nSkipped AI suggestions. Your ticket is saved.", GRAY))
            return

        provider, model = choice

        print()
        spinner = Spinner(f"Getting AI suggestions from {provider['name']} ({model})...")
        spinner.start()
        suggestions, error = get_ai_suggestions(ticket, provider, model)

        if error:
            spinner.stop(False, error)
            again = input(paint("Try a different AI? (y/n): ", GREEN)).strip().lower()
            if again == "y":
                continue
            print(paint("The ticket was saved, but no AI suggestions were shown.", GRAY))
            return

        spinner.stop(True, "Got AI suggestions")
        print(paint("\nSuggestions:", PURPLE))
        print_yellow_box(suggestions)
        return


# ---------- Menu ----------
def menu():
    while True:
        print(paint("\n===== CampusFlow Ticket Creator =====", BLUE))
        print("1. Create a ticket")
        print("2. Exit")

        choice = input(paint("Choose an option (1-2): ", GREEN))

        if choice == "1":
            create_ticket_with_suggestions()
        elif choice == "2":
            print(paint("Goodbye!", GRAY))
            break
        else:
            print(paint("Invalid choice. Please select 1 or 2.", RED))


if __name__ == "__main__":
    menu()