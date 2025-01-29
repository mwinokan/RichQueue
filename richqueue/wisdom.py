from random import sample
from .console import console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.padding import Padding
from typer import Typer

import textwrap

app = Typer()


def get_quotes():
    import json
    from pathlib import Path

    root = Path(__file__).parent
    if not (root / "quotes_decrypted.json").exists():
        from cryptography.fernet import Fernet

        key = console.input("[bold]Enter passkey:\n")

        with open(root / "quotes_encrypted.py", "rb") as f:
            encrypted = f.read()

        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)

        with open(root / "quotes_decrypted.json", "wt") as f:
            encrypted = f.write(decrypted.decode())

        payload = json.loads(decrypted.decode())
        return payload

    else:
        return json.load(open(root / "quotes_decrypted.json", "rt"))


@app.callback(invoke_without_command=True)
def print_random_quote():

    width = console.size.width

    if width < 12 + PADDING * 2:
        return

    quote = sample(QUOTES, 1)[0]
    index = QUOTES.index(quote)

    lines = [""]

    paragraphs = [""]
    for c in quote:
        if c == "\n":
            paragraphs.append("")
        else:
            paragraphs[-1] += c

    for i, paragraph in enumerate(paragraphs):

        if len(paragraph) == 0:
            lines.append("")
            continue

        if i == 0:
            first_padding = " " * PADDING
        else:
            first_padding = " " * (PADDING + 1)

        subsequent_padding = " " * (PADDING + 1)

        if i == 0:
            paragraph = f'"{paragraph}'

        if i + 1 == len(paragraphs):
            paragraph = f'{paragraph}"'

        lines += textwrap.wrap(
            paragraph,
            width=width - PADDING,
            replace_whitespace=False,
            initial_indent=first_padding,
            subsequent_indent=subsequent_padding,
        )

    lines.append("")

    longest = max(len(l) for l in lines)
    signoff = f"-CONFUCIUS #{index+1}"
    lines.append(" " * (longest - len(signoff)) + f"[italic]{signoff}[reset]")

    lines.append("")

    for line in lines:
        console.print(line, highlight=False)


PADDING = 6


def main():
    global QUOTES
    QUOTES = get_quotes()
    app()


if __name__ == "__main__":
    global QUOTES
    QUOTES = get_quotes()
    app()
