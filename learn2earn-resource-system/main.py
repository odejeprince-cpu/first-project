resources = [
  {"id": "R001", "name": "Laptop", "category": "Electronics", "total": 10, "available": 10},
  {"id": "R002", "name": "Keyboard", "category": "Accessories", "total": 5, "available": 5},
  {"id": "R003", "name": "Headset", "category": "Accessories", "total": 3, "available": 3}
]
fellows = {"F001": "Ada", "F002": "John", "F003": "Grace"}
borrow_records = []

def list_resources():
    for resource in resources:
        print("ID:", resource["id"])
        print("NAME:", resource["name"])
        print("CATEGORY:", resource["category"])
        print("TOTAL:", resource["total"])
        print("AVAILABLE:", resource["available"])
        print()

def check_resource(resource_id):
    for resource in resources:
        if resource["id"] == resource_id:
            return resource

    return None

def add_resource():
    resource_id = input("Enter resource ID: ")
    if check_resource(resource_id) is not None:
        print("ID already exists")
        return
    name = input("Enter resource name: ")
    category = input("Enter resource category: ")
    total = int(input("Enter total amount of the resource: "))

    resource = {"Id": resource_id, "name": name, "category": category, "total": total, "available": total
    }
    resources.append(resource)
    print("resource added successfully")

def borrow_resource():
    fellow_id = input("Enter fellow id: ")
    if fellow_id not in fellows:
        print("Fellow does not exist")
        return

    resource_id = input("Enter resource id: ")
    resource = check_resource(resource_id)
    if resource is None:
        print("Resource does not exist")
        return
    
    resource_quantity = int(input("Enter the required quantity: "))
    if resource_quantity > resource["available"]:
        print("available units is not enough")
        return
    if resource_quantity <= 0:
        print("quantity must be greater than 0")
        return
    resource["available"] -= resource_quantity
    borrow_record = {
        "fellow_id": fellow_id,
        "resource_quantity": resource_quantity,
        "resource_id": resource_id
    }
    borrow_records.append(borrow_record)
    print("resource borrowed successfully")

def return_resource():
    fellow_id = input("Enter fellow ID: ")

    if fellow_id not in fellows:
        print("Error: Fellow does not exist.")
        return

    resource_id = input("Enter resource ID: ")

    resource = check_resource(resource_id)

    if resource is None:
        print("Error: Resource does not exist.")
        return

    quantity = int(input("Enter quantity to return: "))

    if quantity <= 0:
        print("Error: Quantity must be greater than zero.")
        return

    for record in borrow_records:
        if record["fellow_id"] == fellow_id and record["resource_id"] == resource_id:

            if quantity > record["resource_quantity"]:
                print("Error: You cannot return more than you borrowed.")
                return

            resource["available"] += quantity
            record["resource_quantity"] -= quantity

            if record["resource_quantity"] == 0:
                borrow_records.remove(record)

            print("Resource returned successfully.")
            return

    print("Error: This fellow has not borrowed this resource.")

def main():
    while True:
        print("\n===== Learn2Earn Resource System =====")
        print("1. Add Resource")
        print("2. List Resources")
        print("3. Borrow Resource")
        print("4. Return Resource")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_resource()

        elif choice == "2":
            list_resources()

        elif choice == "3":
            borrow_resource()

        elif choice == "4":
            return_resource()

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please choose 1, 2, 3, 4, or 5.")


main()