import json
import os

import requests

FILE = "tickets.json"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def get_ai_suggestions(ticket):
    """Send the ticket description to Gemini and return the suggestions as text.
    Returns None if anything goes wrong (an error message is printed)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set. See the setup steps to add your key.")
        return None

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
        response = requests.post(API_URL, headers=headers, json=body, timeout=90)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect. Please check your internet connection.")
    except requests.exceptions.Timeout:
        print("Error: The request timed out. Please try again.")
    except requests.exceptions.HTTPError:
        status = response.status_code
        if status in (400, 403):
            print("Error: The API key was rejected. Please check your GEMINI_API_KEY.")
        elif status == 404:
            print(f"Error: Model '{MODEL}' was not found. Pick an available model in Google AI Studio.")
        elif status == 429:
            print("Error: Too many requests (free tier limit). Wait a moment and try again.")
        elif status in (500, 503):
            print("Error: The AI model is unavailable or overloaded right now. Try again later.")
        else:
            print(f"Error: The API request failed (status {status}).")
    except (KeyError, IndexError, ValueError):
        print("Error: The AI returned a response in an unexpected format.")
    except requests.exceptions.RequestException as e:
        print("Error: Request failed:", e)

    return None


def create_ticket():
    title = input("Enter ticket title: ").strip()
    description = input("Enter ticket description: ").strip()

    if not title or not description:
        print("Title and description cannot be empty.")
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

        print("\nTicket created successfully.")
        print("ID:", ticket["id"])
        print("Description:", ticket["description"])
        return ticket

    except (OSError, json.JSONDecodeError) as e:
        print("Error:", e)
        return None


def create_ticket_with_suggestions():
    ticket = create_ticket()
    if ticket is None:
        return

    print("\nGetting AI suggestions...")
    suggestions = get_ai_suggestions(ticket)

    if suggestions:
        print("\nSuggestions:\n")
        print(suggestions)
    else:
        print("\nThe ticket was saved, but no AI suggestions are available right now.")


def menu():
    while True:
        print("\n===== CampusFlow Ticket Creator =====")
        print("1. Create a ticket")
        print("2. Exit")

        choice = input("Choose an option (1-2): ")

        if choice == "1":
            create_ticket_with_suggestions()
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1 or 2.")


if __name__ == "__main__":
    menu()