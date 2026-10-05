import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Review a Python file")
    parser.add_argument("filename", help="path to the Python file to review")
    args = parser.parse_args()

    if not os.path.exists(args.filename):
        print(f"Error: '{args.filename}' was not found.")
        return

    with open(args.filename, "r") as f:
        lines = f.readlines()

    function_count = sum(1 for line in lines if line.strip().startswith("def "))

    print(f"File: {args.filename}")
    print(f"Lines: {len(lines)}")
    print(f"Functions found: {function_count}")


if __name__ == "__main__":
    main()