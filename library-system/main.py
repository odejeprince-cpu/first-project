import json


class Book:
    def __init__(self, title, author, copies, available_copies=None):
        self.title = title
        self.author = author
        self.total_copies = copies
        if available_copies is None:
            self.available_copies = copies
        else:
            self.available_copies = available_copies

    def borrow(self):
        if self.available_copies > 0:
            self.available_copies = self.available_copies - 1
            return True
        else:
            return False

    def return_book(self):
        self.available_copies = self.available_copies + 1

    def __str__(self):
        return self.title + " by " + self.author

    def __repr__(self):
        return self.title + " by " + self.author

    def to_dict(self):
        return {
            "title": self.title,
            "author": self.author,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies
        }


class Member:
    def __init__(self, name):
        self.name = name
        self.borrowed_books = []

    def borrow_book(self, book):
        success = book.borrow()
        if success:
            self.borrowed_books.append(book)
            return True
        else:
            return False

    def return_book(self, book):
        if book in self.borrowed_books:
            book.return_book()
            self.borrowed_books.remove(book)
            return True
        else:
            return False

    def to_dict(self):
        borrowed_titles = []
        for book in self.borrowed_books:
            borrowed_titles.append(book.title)

        return {
            "name": self.name,
            "borrowed_books": borrowed_titles
        }


def save_data():
    books_data = []
    for book in books:
        books_data.append(book.to_dict())

    members_data = []
    for member in members:
        members_data.append(member.to_dict())

    data = {
        "books": books_data,
        "members": members_data
    }

    with open("library.json", "w") as file:
        json.dump(data, file)


def load_data():
    try:
        with open("library.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        return [], []

    loaded_books = []
    for book_dict in data["books"]:
        book = Book(
            book_dict["title"],
            book_dict["author"],
            book_dict["total_copies"],
            book_dict["available_copies"]
        )
        loaded_books.append(book)

    loaded_members = []
    for member_dict in data["members"]:
        member = Member(member_dict["name"])

        for title in member_dict["borrowed_books"]:
            for book in loaded_books:
                if book.title == title:
                    member.borrowed_books.append(book)

        loaded_members.append(member)

    return loaded_books, loaded_members


books, members = load_data()

while True:
    print("\n--- Library System ---")
    print("1. Add a book")
    print("2. Add a member")
    print("3. View all books")
    print("4. Borrow a book")
    print("5. Return a book")
    print("6. Quit")

    choice = input("Choose an option (1-6): ")

    if choice == "1":
        title = input("Enter book title: ")
        author = input("Enter author: ")
        copies = input("Enter number of copies: ")

        new_book = Book(title, author, int(copies))
        books.append(new_book)
        print("Book added!")
        save_data()

    elif choice == "2":
        name = input("Enter member name: ")
        new_member = Member(name)
        members.append(new_member)
        print("Member added!")
        save_data()

    elif choice == "3":
        for book in books:
            print(book, "-", book.available_copies, "available")

    elif choice == "4":
        member_name = input("Enter member name: ")
        book_title = input("Enter book title to borrow: ")

        found_member = None
        for member in members:
            if member.name.lower() == member_name.lower():
                found_member = member

        found_book = None
        for book in books:
            if book.title.lower() == book_title.lower():
                found_book = book

        if found_member is None:
            print("Member not found.")
        elif found_book is None:
            print("Book not found.")
        else:
            success = found_member.borrow_book(found_book)
            if success:
                print("Book borrowed successfully!")
                save_data()
            else:
                print("No copies available.")

    elif choice == "5":
        member_name = input("Enter member name: ")
        book_title = input("Enter book title to return: ")

        found_member = None
        for member in members:
            if member.name.lower() == member_name.lower():
                found_member = member

        found_book = None
        for book in books:
            if book.title.lower() == book_title.lower():
                found_book = book

        if found_member is None:
            print("Member not found.")
        elif found_book is None:
            print("Book not found.")
        else:
            success = found_member.return_book(found_book)
            if success:
                print("Book returned successfully!")
                save_data()
            else:
                print("This member didn't borrow that book.")

    elif choice == "6":
        print("Goodbye!")
        break

    else:
        print("Invalid option, try again.")