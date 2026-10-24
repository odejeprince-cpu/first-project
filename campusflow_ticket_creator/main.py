import json
import os

FILE = "tickets.json"


def create_ticket():
    title = input("Enter ticket title: ").strip()
    description = input("Enter ticket description: ").strip()

    if not title or not description:
        print("Title and description cannot be empty.")
        return

    try:
        if os.path.exists(FILE):
            with open(FILE, "r") as f:
                tickets = json.load(f)
        else:
            tickets = []

        ticket = {
            "id": f"A{len(tickets) + 1:03d}",
            "title": title,
            "description": description
        }

        tickets.append(ticket)

        with open(FILE, "w") as f:
            json.dump(tickets, f, indent=4)

        print("Ticket created:", ticket["id"])

    except (OSError, json.JSONDecodeError) as e:
        print("Error:", e)


def menu():
    while True:
        print("\n===== CampusFlow Ticket Creator =====")
        print("1. Create a ticket")
        print("2. Exit")

        choice = input("Choose an option (1-2): ")

        if choice == "1":
            create_ticket()
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1 or 2.")


if __name__ == "__main__":
    menu()