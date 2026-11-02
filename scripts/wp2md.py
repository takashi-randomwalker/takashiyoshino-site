#!/usr/bin/env python3
"""Convert a WordPress post body (HTML) to Quarto Markdown.

The drafts were written with note-style math: inline $${...}$$ and display
$$<br>...<br>$$. Formulas are swapped for placeholder tokens while pandoc
converts the HTML, then put back as $...$ and $$...$$ so that pandoc does
not escape the TeX.

usage: wp2md.py post.html > index.qmd   (needs `quarto` on PATH)
"""
import html
import re
import subprocess
import sys


def main():
    src = open(sys.argv[1], encoding="utf-8").read()
    src = re.sub(r'\s(?:name|id)="[0-9a-f-]{36}"', "", src)
    formulas = []

    def stash(tex, display):
        tex = html.unescape(re.sub(r"<br\s*/?>", "\n", tex)).strip()
        formulas.append(f"\n\n$$\n{tex}\n$$\n\n" if display else f"${tex}$")
        return f"MATHTOKEN{len(formulas) - 1:04d}X"

    # Display first: $$ followed by a line break
    src = re.sub(r"\$\$\s*<br\s*/?>(.*?)<br\s*/?>\s*\$\$", lambda m: stash(m.group(1), True), src, flags=re.S)
    src = re.sub(r"\$\$\{(.*?)\}\$\$", lambda m: stash(m.group(1), False), src, flags=re.S)

    md = subprocess.run(
        ["quarto", "pandoc", "-f", "html", "-t", "markdown-raw_html-native_divs-native_spans",
         "--wrap=none"],
        input=src, capture_output=True, text=True, check=True).stdout
    md = re.sub(r"MATHTOKEN(\d{4})X", lambda m: formulas[int(m.group(1))], md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    sys.stdout.write(md.strip() + "\n")


if __name__ == "__main__":
    main()
