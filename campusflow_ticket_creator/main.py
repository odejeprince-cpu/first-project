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

# Models the user can choose from: menu number -> (model name, short note)
MODELS = {
    "1": ("gemini-3.1-flash-lite", "fast and lightweight (recommended)"),
    "2": ("gemini-3.5-flash-lite", "newer lightweight model"),
    "3": ("gemini-3.8-flash", "smarter, but can be slower"),
    "4": ("gemma-4-26b-a4b-it", "open model from Google"),
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
def get_ai_suggestions(ticket, model):
    """Send the ticket to the chosen Gemini model.
    Returns (suggestions, None) on success or (None, error_message) on failure."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY is not set. Add it to ~/.zshrc and try again."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    prompt = (
        "You are an IT support assistant for a university campus helpdesk.\n"
        "A user submitted this support ticket:\n\n"
        f"Title: {ticket['title']}\n"
        f"Description: {ticket['description']}\n\n"
        "Suggest 3 to 5 practical ways to fix or investigate this problem. "
        "Reply as a short numbered list, one step per line, with no extra introduction."
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text, None

    except requests.exceptions.ConnectionError:
        return None, "Could not connect. Please check your internet connection."
    except requests.exceptions.Timeout:
        return None, f"The request to {model} timed out. Try again or choose another model."
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status in (400, 403):
            return None, "The API key was rejected. Please check your GEMINI_API_KEY."
        if status == 404:
            return None, f"Model '{model}' was not found. Try a different model."
        if status == 429:
            return None, "Too many requests (free tier limit). Wait a moment and try again."
        if status in (500, 503):
            return None, f"{model} is unavailable or overloaded. Try another model."
        return None, f"The API request failed (status {status})."
    except (KeyError, IndexError, ValueError):
        return None, "The AI returned a response in an unexpected format."
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"


def choose_model():
    """Ask the user which AI model to use. Returns the model name, or None to skip."""
    print(paint("\nChoose an AI model:", BLUE))
    for key, (name, note) in MODELS.items():
        print(f"{key}. {name} - {paint(note, GRAY)}")
    print("0. Skip AI suggestions")

    while True:
        choice = input(paint("Choose a model (0-4, press Enter for 1): ", GREEN)).strip() or "1"
        if choice == "0":
            return None
        if choice in MODELS:
            return MODELS[choice][0]
        print(paint("Invalid choice. Please enter a number from 0 to 4.", RED))


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

    model = choose_model()
    if model is None:
        print(paint("\nSkipped AI suggestions. Your ticket is saved.", GRAY))
        return

    print()
    spinner = Spinner(f"Getting AI suggestions from {model}...")
    spinner.start()
    suggestions, error = get_ai_suggestions(ticket, model)

    if error:
        spinner.stop(False, error)
        print(paint("The ticket was saved, but no AI suggestions are available right now.", GRAY))
    else:
        spinner.stop(True, "Got AI suggestions")
        print(paint("\nSuggestions:", PURPLE))
        print_yellow_box(suggestions)


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