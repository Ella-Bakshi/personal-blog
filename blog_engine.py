"""
blog_engine.py — shared engine for The Dispatch.

Used by both new_post.py (the interactive maker) and build.py (the
auto-detection builder). Contains:

  - a SAFE mini-Markdown renderer (all raw HTML is escaped first, so a
    post can never inject scripts into the site)
  - front-matter parsing for posts/*.md
  - template filling (templates/*.html use {{PLACEHOLDER}} tokens)

No third-party dependencies. Python 3.8+.
"""

import html
import json
import re
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
TEMPLATES_DIR = ROOT / "templates"
SITE_URL = "https://blog.anmolbakshi.com"
SITE_NAME = "The Dispatch"
AUTHOR = "Anmol Bakshi"

# ---------------------------------------------------------------- slugs

def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


# ---------------------------------------------------------------- front matter

def parse_front_matter(text: str) -> dict:
    """Parse a .md post: --- key: value --- block followed by markdown body."""
    meta = {"title": "Untitled", "date": "", "tags": [], "excerpt": ""}
    body = text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if m:
        raw, body = m.group(1), m.group(2)
        for line in raw.splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip().lower(), val.strip()
            if key == "tags":
                val = val.strip("[]")
                meta["tags"] = [t.strip() for t in val.split(",") if t.strip()]
            elif key in ("title", "date", "excerpt"):
                meta[key] = val.strip('"').strip("'")
    meta["body"] = body.strip("\n")
    return meta


# ---------------------------------------------------------------- markdown (safe)

def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def _safe_url(url: str) -> str:
    """Allow http(s), mailto and relative links only — kills javascript: etc."""
    url = url.strip()
    if re.match(r"^(https?://|mailto:|/|\./|\.\./|#)", url, re.I):
        return html.escape(url, quote=True)
    return "#"


def _inline(text: str) -> str:
    """Inline formatting on already-escaped text."""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", text)
    # images: ![alt](src)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)\)",
        lambda m: '<img src="%s" alt="%s" loading="lazy">' % (_safe_url(m.group(2)), m.group(1)),
        text,
    )
    # links: [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: '<a href="%s" rel="noopener noreferrer">%s</a>' % (_safe_url(m.group(2)), m.group(1)),
        text,
    )
    return text


def render_markdown(md: str) -> str:
    """Render the supported Markdown subset to safe HTML."""
    lines = md.replace("\r\n", "\n").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]

        # fenced code block
        if line.strip().startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf)))
            continue

        # blank
        if not line.strip():
            i += 1
            continue

        # headings
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, _inline(_esc(m.group(2).strip())), level))
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # blockquote (consecutive > lines)
        if line.strip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(_esc(" ".join(buf))))
            continue

        # pipe table (GitHub-style): header row, |---| separator, body rows
        if (line.strip().startswith("|") and i + 1 < len(lines)
                and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1])):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2  # skip header + separator
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = ("<thead><tr>" + "".join("<th>%s</th>" % _inline(_esc(c)) for c in header)
                     + "</tr></thead>")
            tbody = ("<tbody>" + "".join(
                "<tr>" + "".join("<td>%s</td>" % _inline(_esc(c)) for c in r) + "</tr>"
                for r in rows) + "</tbody>")
            out.append("<table>%s%s</table>" % (thead, tbody))
            continue

        # unordered list
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % _inline(_esc(x)) for x in items) + "</ul>")
            continue

        # ordered list
        if re.match(r"^\s*\d+[.)]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % _inline(_esc(x)) for x in items) + "</ol>")
            continue

        # paragraph (gather until blank line / block start)
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^\s*(#{2,3}\s|```|>|[-*]\s|\d+[.)]\s|(-{3,}|\*{3,})\s*$)", lines[i]
        ):
            buf.append(lines[i])
            i += 1
        out.append("<p>%s</p>" % _inline(_esc(" ".join(x.strip() for x in buf))))

    return "\n".join(out)


# ---------------------------------------------------------------- helpers

def human_date(iso: str) -> str:
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
    except ValueError:
        return iso
    return d.strftime("%d %b %Y").upper()


def fill(template: str, mapping: dict) -> str:
    for key, val in mapping.items():
        template = template.replace("{{%s}}" % key, str(val))
    return template


def load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def post_files():
    return sorted(POSTS_DIR.glob("*.md"))


def read_post(path: Path) -> dict:
    meta = parse_front_matter(path.read_text(encoding="utf-8"))
    meta["slug"] = path.stem
    if not meta["date"]:
        meta["date"] = date.today().isoformat()
    if not meta["excerpt"]:
        # fall back to first paragraph of the body
        first = meta["body"].strip().split("\n\n", 1)[0]
        meta["excerpt"] = re.sub(r"[#>*`\[\]]", "", first)[:180].strip()
    return meta
