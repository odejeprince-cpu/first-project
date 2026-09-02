import json


def save_expenses():
    with open("data.json", "w") as file:
        json.dump(expenses, file)


def load_expenses():
    try:
        with open("data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


expenses = load_expenses()

while True:
    print("\n--- Expense Tracker ---")
    print("1. Add an expense")
    print("2. View all expenses")
    print("3. View total spending")
    print("4. View spending by category")
    print("5. Quit")

    choice = input("Choose an option (1-5): ")

    if choice == "1":
        amount = input("Enter the amount spent: ")
        category = input("Enter the category: ")
        description = input("Enter a description: ")

        new_expense = {
            "amount": float(amount),
            "category": category,
            "description": description
        }

        expenses.append(new_expense)
        print("Expense added!")
        save_expenses()

    elif choice == "2":
        for expense in expenses:
            print("You spent", expense["amount"], "on", expense["category"], "-", expense["description"])

    elif choice == "3":
        total = 0
        for expense in expenses:
            total = total + expense["amount"]
        print("Total spending:", total)

    elif choice == "4":
        category_totals = {}
        for expense in expenses:
            category = expense["category"]
            amount = expense["amount"]

            if category in category_totals:
                category_totals[category] = category_totals[category] + amount
            else:
                category_totals[category] = amount
        print("Spending by category:", category_totals)

    elif choice == "5":
        print("Goodbye!")
        break

    else:
        print("Invalid option, try again.")