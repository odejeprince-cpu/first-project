import argparse
import os
import sys
import time
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import history

MODEL = "gemini-3.5-flash"
MAX_ATTEMPTS = 4
RETRY_CODES = {429, 500, 503, 504}
MAX_FILES = 10  # safety limit so a big folder doesn't use up your free quota
SKIP_DIRS = {"venv", "__pycache__", "node_modules"}

SYSTEM_PROMPT = """You are a friendly senior Python developer reviewing code for a beginner.
Find bugs, bad practices, and improvements. Explain WHY each one matters in plain language
and give a short fix. Each line of the code starts with its line number; use those numbers.
Be encouraging, and finish with one thing the code does well."""

SEVERITY_COLORS = {"high": "red", "medium": "yellow", "low": "cyan"}

Severity = Literal["high", "medium", "low"]
Category = Literal[
    "correctness",
    "error-handling",
    "naming",
    "style",
    "structure",
    "readability",
    "performance",
    "security",
    "other",
]


class Issue(BaseModel):
    severity: Severity
    category: Category
    line: int = Field(description="Line number of the problem, or 0 if it affects the whole file")
    title: str = Field(description="Short name of the problem")
    why: str = Field(description="Plain-language explanation of why it matters")
    fix: str = Field(description="A short fix, with a code snippet if useful")


class Review(BaseModel):
    summary: str = Field(description="Two sentence overall summary")
    issues: list[Issue]
    praise: str = Field(description="One thing the code does well")


def read_file_with_line_numbers(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, start=1))


def find_python_files(folder):
    found = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in names:
            if name.endswith(".py"):
                found.append(os.path.join(root, name))
    return sorted(found)


def review_code(client, numbered_code, filename):
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=Review,
    )
    contents = f"Please review this file named {filename}:\n\n{numbered_code}"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            break
        except errors.APIError as e:
            if e.code not in RETRY_CODES or attempt == MAX_ATTEMPTS:
                raise RuntimeError(f"API error {e.code} after {attempt} attempt(s)") from e
            wait = 2 ** attempt  # 2, 4, 8 seconds
            print(f"Server busy (error {e.code}). Retrying in {wait}s...")
            time.sleep(wait)

    review = response.parsed
    if review is None:
        raise RuntimeError("The AI did not return a valid review.")
    return review


def print_review(console, review):
    console.print(Panel(review.summary, title="Summary", border_style="blue"))

    order = {"high": 0, "medium": 1, "low": 2}
    for issue in sorted(review.issues, key=lambda i: order[i.severity]):
        color = SEVERITY_COLORS[issue.severity]
        where = f"line {issue.line}" if issue.line else "whole file"
        body = f"[bold]Why:[/bold] {issue.why}\n\n[bold]Fix:[/bold] {issue.fix}"
        console.print(
            Panel(
                body,
                title=f"{issue.severity.upper()} | {where} | {issue.title}",
                border_style=color,
            )
        )

    console.print(Panel(review.praise, title="Done well", border_style="green"))


def save_report(review, filename):
    lines = [f"# Review of {filename}", "", review.summary, ""]
    for issue in review.issues:
        where = f"line {issue.line}" if issue.line else "whole file"
        lines += [
            f"## [{issue.severity.upper()}] {issue.title} ({where})",
            f"**Why:** {issue.why}",
            "",
            f"**Fix:** {issue.fix}",
            "",
        ]
    lines += ["## Done well", review.praise, ""]
    report_name = os.path.splitext(filename)[0] + "_review.md"
    with open(report_name, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_name


def review_file(console, client, path):
    """Review one file. Returns True on success, False if it was skipped."""
    console.print(f"Reviewing [bold]{path}[/bold]...")
    try:
        numbered_code = read_file_with_line_numbers(path)
        review = review_code(client, numbered_code, path)
    except (RuntimeError, OSError, UnicodeDecodeError) as e:
        console.print(f"[red]Skipped {path}: {e}[/red]")
        return False

    print_review(console, review)
    history.save_review(path, review.issues)
    report_name = save_report(review, path)
    console.print(f"Saved report to [green]{report_name}[/green]\n")
    return True


def print_stats(console):
    total_reviews, by_category, by_severity = history.get_stats()
    if total_reviews == 0:
        console.print("No reviews saved yet. Review a file first.")
        return

    table = Table(title=f"Your most common mistakes ({total_reviews} reviews)")
    table.add_column("Category")
    table.add_column("Count", justify="right")
    for category, count in by_category:
        table.add_row(category, str(count))
    console.print(table)

    severity_text = ", ".join(f"{s}: {n}" for s, n in by_severity)
    console.print(f"By severity: {severity_text}")


def main():
    parser = argparse.ArgumentParser(description="AI code reviewer for Python files")
    parser.add_argument("path", nargs="?", help="a Python file or a folder to review")
    parser.add_argument("--stats", action="store_true", help="show your most common mistakes")
    args = parser.parse_args()

    console = Console()

    if args.stats:
        print_stats(console)
        return

    if not args.path:
        parser.error("please give a file or folder, or use --stats")
    if not os.path.exists(args.path):
        sys.exit(f"Error: '{args.path}' was not found.")
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Error: GEMINI_API_KEY is not set.")

    client = genai.Client()  # created once, reused for every file

    if os.path.isdir(args.path):
        files = find_python_files(args.path)
        if not files:
            sys.exit(f"No .py files found in '{args.path}'.")
        if len(files) > MAX_FILES:
            console.print(
                f"[yellow]Found {len(files)} files. Reviewing the first {MAX_FILES} only.[/yellow]"
            )
            files = files[:MAX_FILES]
        results = [review_file(console, client, f) for f in files]
        console.print(f"Done: {sum(results)} of {len(files)} files reviewed.")
    else:
        if not review_file(console, client, args.path):
            sys.exit(1)


if __name__ == "__main__":
    main()