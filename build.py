"""
build.py — auto-detect every post in posts/*.md and rebuild the site.

Regenerates:
  - posts/<slug>.html   (one styled page per .md file)
  - index.html          (archive with search + tags)
  - feed.xml            (RSS 2.0)
  - posts.json          (manifest used by client-side search)

Run it locally after adding a post:      python3 build.py
It also runs automatically on GitHub via .github/workflows/build.yml
every time you push — that is the "auto detect" part.

No third-party dependencies. Python 3.8+.
"""

import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from blog_engine import (
    ROOT, POSTS_DIR, SITE_URL, SITE_NAME, AUTHOR,
    read_post, post_files, render_markdown, human_date, fill, load_template,
)

ENTRY_HTML = """      <article class="entry" data-title="{title_attr}" data-tags="{tags_attr}" data-excerpt="{excerpt_attr}">
        <span class="entry-num">№ {num} / {total}</span>
        <div>
          <a href="posts/{slug}.html"><h2 class="entry-title">{title}</h2></a>
          <p class="entry-excerpt">{excerpt}</p>
          <div class="entry-tags">{tag_chips}</div>
        </div>
        <span class="entry-date">{date}</span>
      </article>"""

TAG_CHIP = '<button class="tag" type="button" data-tag-filter="{attr}">{label}</button>'


def esc_attr(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def render_post_page(post: dict, num: int, total: int, prev_p, next_p) -> str:
    import html as _html
    tags_plain = " · ".join(post["tags"]).upper() if post["tags"] else "GENERAL"
    tags_inline = " / ".join(post["tags"]) if post["tags"] else "general"
    meta_json = json.dumps({
        "title": post["title"], "slug": post["slug"], "date": post["date"],
        "tags": post["tags"], "excerpt": post["excerpt"],
    }, ensure_ascii=False).replace("--", "-​-")  # never break the HTML comment

    prev_link = ('<a href="%s.html">← %s</a>' % (prev_p["slug"], _html.escape(prev_p["title"]))) if prev_p else ""
    next_link = ('<a href="%s.html">%s →</a>' % (next_p["slug"], _html.escape(next_p["title"]))) if next_p else ""

    return fill(load_template("post.html"), {
        "POSTMETA": meta_json,
        "TITLE": _html.escape(post["title"]),
        "TITLE_ATTR": esc_attr(post["title"]),
        "SLUG": post["slug"],
        "DATE": human_date(post["date"]),
        "EXCERPT": _html.escape(post["excerpt"]),
        "EXCERPT_ATTR": esc_attr(post["excerpt"]),
        "CONTENT": render_markdown(post["body"]),
        "TAGS_PLAIN": _html.escape(tags_plain),
        "TAGS_INLINE": _html.escape(tags_inline),
        "POST_NUM": str(num).zfill(2),
        "TOTAL": str(total).zfill(2),
        "PREV_LINK": prev_link,
        "NEXT_LINK": next_link,
        "YEAR": datetime.now().year,
    })


def build() -> None:
    posts = [read_post(p) for p in post_files()]
    # newest first; ties broken by slug for stability
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    total = len(posts)

    # ---- individual post pages (with prev/next wired up)
    for i, post in enumerate(posts):
        num = i + 1
        prev_p = posts[i - 1] if i > 0 else None          # newer entry
        next_p = posts[i + 1] if i < total - 1 else None  # older entry
        html_out = render_post_page(post, num, total, prev_p, next_p)
        (POSTS_DIR / (post["slug"] + ".html")).write_text(html_out, encoding="utf-8")

    # ---- archive entries + tag buttons
    import html as _html
    all_tags = sorted({t for p in posts for t in p["tags"]}, key=str.lower)
    tag_buttons = "\n".join(
        "        " + TAG_CHIP.format(attr=esc_attr(t), label=_html.escape(t)) for t in all_tags
    ) or "        <span class=\"mono\">—</span>"

    entries = []
    for i, p in enumerate(posts):
        chips = " ".join(
            TAG_CHIP.format(attr=esc_attr(t), label=_html.escape(t)) for t in p["tags"]
        )
        entries.append(ENTRY_HTML.format(
            title_attr=esc_attr(p["title"]),
            tags_attr=esc_attr("|".join(p["tags"])),
            excerpt_attr=esc_attr(p["excerpt"]),
            num=str(i + 1).zfill(2), total=str(total).zfill(2),
            slug=p["slug"], title=_html.escape(p["title"]),
            excerpt=_html.escape(p["excerpt"]), tag_chips=chips,
            date=human_date(p["date"]),
        ))

    index = fill(load_template("index.html"), {
        "ENTRIES": "\n".join(entries) if entries else '        <p class="no-results" style="display:block">— Archive empty. Run <code>python3 new_post.py</code> —</p>',
        "TAG_BUTTONS": tag_buttons,
        "TOTAL": str(total).zfill(2),
        "UPDATED": human_date(datetime.now().date().isoformat()),
        "YEAR": datetime.now().year,
    })
    (ROOT / "index.html").write_text(index, encoding="utf-8")

    # ---- RSS feed
    items = []
    for p in posts:
        try:
            pub = datetime.strptime(p["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 08:00:00 +0000")
        except ValueError:
            pub = datetime.now().strftime("%a, %d %b %Y 08:00:00 +0000")
        items.append(
            "    <item>\n"
            "      <title>%s</title>\n"
            "      <link>%s/posts/%s.html</link>\n"
            "      <guid>%s/posts/%s.html</guid>\n"
            "      <pubDate>%s</pubDate>\n"
            "      <description>%s</description>\n"
            "    </item>" % (
                xml_escape(p["title"]), SITE_URL, p["slug"], SITE_URL, p["slug"],
                pub, xml_escape(p["excerpt"]),
            )
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n  <channel>\n'
        "    <title>%s — %s</title>\n"
        "    <link>%s</link>\n"
        "    <description>Security research, write-ups and field notes.</description>\n"
        "    <language>en</language>\n%s\n  </channel>\n</rss>\n"
        % (SITE_NAME, AUTHOR, SITE_URL, "\n".join(items))
    )
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")

    # ---- search manifest
    manifest = [{
        "title": p["title"], "slug": p["slug"], "date": p["date"],
        "tags": p["tags"], "excerpt": p["excerpt"],
    } for p in posts]
    (ROOT / "posts.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Built %d post(s): index.html, feed.xml, posts.json regenerated." % total)
    for p in posts:
        print("  - %s  (%s)" % (p["slug"], p["date"]))


if __name__ == "__main__":
    build()
