import json


def save_contacts():
    with open("contacts.json", "w") as file:
        json.dump(contacts, file)


def load_contacts():
    try:
        with open("contacts.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


contacts = load_contacts()

while True:
    print("\n--- Contact Book ---")
    print("1. Add a contact")
    print("2. View all contacts")
    print("3. Search for a contact")
    print("4. Delete a contact")
    print("5. Quit")

    choice = input("Choose an option (1-5): ")

    if choice == "1":
        name = input("Enter name: ")
        phone = input("Enter phone: ")
        email = input("Enter email: ")

        new_contact = {
            "name": name,
            "phone": phone,
            "email": email
        }

        contacts.append(new_contact)
        print("Contact added!")
        save_contacts()

    elif choice == "2":
        for contact in contacts:
            print(contact["name"], "-", contact["phone"], "-", contact["email"])

    elif choice == "3":
        search_name = input("Enter name to search: ")
        found = False

        for contact in contacts:
            if contact["name"].lower() == search_name.lower():
                print(contact["name"], "-", contact["phone"], "-", contact["email"])
                found = True

        if not found:
            print("No contact found with that name.")

    elif choice == "4":
        delete_name = input("Enter name to delete: ")
        contact_to_delete = None

        for contact in contacts:
            if contact["name"].lower() == delete_name.lower():
                contact_to_delete = contact

        if contact_to_delete is not None:
            contacts.remove(contact_to_delete)
            print("Contact deleted!")
            save_contacts()
        else:
            print("No contact found with that name.")

    elif choice == "5":
        print("Goodbye!")
        break

    else:
        print("Invalid option, try again.")