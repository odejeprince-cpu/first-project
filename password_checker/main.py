from checker import check_password_strength, get_strength_label

def main():
    password = input("Enter a password to check: ")
    score, feedback = check_password_strength(password)
    strength = get_strength_label(score)

    print(f"\nStrength: {strength} ({score}/5)")

    if feedback:
        print("Suggestions:")
        for tip in feedback:
            print(f" - {tip}")

if __name__ == "__main__":
    main()