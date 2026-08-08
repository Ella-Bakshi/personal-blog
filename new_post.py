#!/usr/bin/env python3
"""
new_post.py — interactive post maker for The Dispatch.

Run:   python3 new_post.py

It asks a few questions, lets you type/paste the post in a safe
Markdown subset, writes posts/<slug>.md, then runs build.py so the
index, RSS feed and search manifest pick the new entry up right away.
When you push to GitHub, the Actions workflow rebuilds everything
automatically — new .md files are auto-detected.

No third-party dependencies. Python 3.8+.
"""

import sys
from datetime import date
from pathlib import Path

from blog_engine import POSTS_DIR, slugify
from build import build

BANNER = r"""
  +-------------------------------------------------------+
  |   T H E   D I S P A T C H  --  new entry typewriter   |
  +-------------------------------------------------------+
"""

SYNTAX_HELP = """\
  Supported formatting (safe Markdown subset — raw HTML is escaped):
    ## Heading            **bold**          *italic*
    ### Subheading        `inline code`     [link](https://example.com)
    > quote               ![alt](../assets/images/img.jpg)
    - bullet list         1. numbered list  ``` fenced code block ```
    | col | col |  pipe tables            ---  (horizontal rule)
  Images: put the file in assets/images/ first, then reference it as above.
"""

def ask(prompt: str, default: str = "") -> str:
    suffix = " [%s]" % default if default else ""
    try:
        val = input("%s%s: " % (prompt, suffix)).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted — nothing was written.")
        sys.exit(1)
    return val or default


def ask_multiline() -> str:
    print("\nType or paste the post below. Finish with a line containing only: EOF")
    print("(or press Ctrl+D)\n")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nAborted — nothing was written.")
            sys.exit(1)
        if line.strip() == "EOF":
            break
        lines.append(line)
    return "\n".join(lines).strip("\n")


def main() -> None:
    print(BANNER)
    title = ask("Title")
    if not title:
        print("A title is required. Aborted.")
        sys.exit(1)

    excerpt = ask("Standfirst (one italic line under the title)",
                  default="")
    tags_raw = ask("Tags (comma-separated)", default="notes")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    post_date = ask("Date (YYYY-MM-DD)", default=date.today().isoformat())

    slug = ask("URL slug", default=slugify(title))
    slug = slugify(slug)
    target = POSTS_DIR / (slug + ".md")
    if target.exists():
        overwrite = ask("'%s' already exists — overwrite? (y/N)" % slug, default="N")
        if overwrite.lower() != "y":
            print("Aborted — nothing was written.")
            sys.exit(1)

    print(SYNTAX_HELP)
    body = ask_multiline()
    if not body.strip():
        print("Empty post — nothing was written.")
        sys.exit(1)

    front = ["---", "title: %s" % title]
    if excerpt:
        front.append("excerpt: %s" % excerpt)
    front.append("date: %s" % post_date)
    front.append("tags: %s" % ", ".join(tags))
    front.append("---")
    front.append("")
    target.write_text("\n".join(front) + body + "\n", encoding="utf-8")
    print("\nSaved %s" % target.relative_to(POSTS_DIR.parent))

    print("Rebuilding the archive…")
    build()

    print("""
Done. Your entry is live at: posts/%s.html

To publish:
  git add .
  git commit -m "New entry: %s"
  git push
GitHub Actions will auto-detect the file and rebuild the site.
""" % (slug, title))


if __name__ == "__main__":
    main()
