#!/usr/bin/env python3
"""Add a "backlinks" section to every page of a built Zensical site.

Run after `zensical build`:
    python backlinks.py site
    python backlinks.py site --title "Verlinkt von" --base-path /wiki/

Only links inside the page content (<article class="md-content__inner">)
count, so navigation, header and footer links are ignored. Running the
script twice is safe: an existing backlinks section is replaced.

Obsidian wikilinks ([[Page]], [[Page|Alias]], [[Page#Heading]]) are left
as plain text by Zensical; they are turned into real links here, so they
are clickable and count as backlinks. Embeds (![[...]]) are left alone.

Requires: pip install beautifulsoup4
"""
import argparse
import posixpath
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from bs4 import BeautifulSoup, NavigableString

ARTICLE = "article.md-content__inner"
SECTION_CLASS = "backlinks"
SKIP_LINK_CLASSES = {"headerlink", "md-content__button", "footnote-ref", "footnote-backref"}
SKIP_PAGES = {"404.html"}
SKIP_TEXT_PARENTS = {"a", "code", "pre", "script", "style", "kbd"}
WIKILINK = re.compile(r"(?<!!)\[\[([^\[\]|#]*)(?:#([^\[\]|]*))?(?:\|([^\[\]]*))?\]\]")


def resolve(src: str, href: str, pages: dict, base_path: str):
    """Map an href found on page `src` to a page key like 'foo/index.html'."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path:
        return None  # external, mailto:, or pure #anchor
    path = unquote(parts.path)
    if path.startswith("/"):
        if not path.startswith(base_path):
            return None
        target = path[len(base_path):]
    else:
        target = posixpath.join(posixpath.dirname(src), path)
    target = posixpath.normpath(target) if target else "."
    if target.startswith(".."):
        return None
    for cand in (target, posixpath.join(target, "index.html")):
        cand = posixpath.normpath(cand)
        if cand in pages:
            return cand
    return None


def rel_url(from_page: str, to_page: str) -> str:
    """Relative URL from one page to another, using directory URLs where possible."""
    rel = posixpath.relpath(to_page, posixpath.dirname(from_page) or ".")
    if rel == "index.html":
        return "./"
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return quote(rel)


def page_names(pages: dict) -> dict:
    """Map lowercased note names ('git howto', 'sub/page') to page keys, like Obsidian resolves them."""
    names = {}
    for key in pages:
        path = key[: -len("/index.html")] if key.endswith("/index.html") else key.removesuffix(".html")
        if path == "index.html":
            path = "index"
        names.setdefault(posixpath.basename(path).lower(), key)
        names[path.lower()] = key
    return names


def heading_id(soup, heading: str):
    """Find the id of the heading in `soup` whose text matches `heading`."""
    wanted = heading.strip().lower()
    for h in soup.select_one(ARTICLE).select("h1, h2, h3, h4, h5, h6"):
        text = "".join(s for s in h.find_all(string=True) if s.parent.name != "a" or "headerlink" not in s.parent.get("class", []))
        if text.strip().lower() == wanted and h.get("id"):
            return h["id"]
    return None


def convert_wikilinks(key: str, soup, pages: dict, names: dict) -> int:
    """Replace [[wikilinks]] in text nodes of the article with <a> tags. Returns count."""
    count = 0
    for text in soup.select_one(ARTICLE).find_all(string=WIKILINK):
        if any(p.name in SKIP_TEXT_PARENTS for p in text.parents):
            continue
        pieces, pos = [], 0
        for m in WIKILINK.finditer(text):
            name, heading, alias = (g.strip() if g else g for g in m.groups())
            target = names.get(name.removesuffix(".md").lower()) if name else key
            if target is None:
                continue  # unknown page: keep the text as it is
            href = rel_url(key, target) if target != key else ""
            if heading:
                anchor = heading_id(pages[target], heading)
                href += "#" + (anchor or quote(heading))
            link = soup.new_tag("a", href=href or "./")
            link.string = alias or (f"{name} › {heading}" if name and heading else name or heading)
            pieces += [text[pos : m.start()], link]
            pos = m.end()
            count += 1
        if not pieces:
            continue
        pieces.append(text[pos:])
        for piece in pieces:
            text.insert_before(NavigableString(piece) if isinstance(piece, str) else piece)
        text.extract()
    return count


def page_title(soup, article) -> str:
    h1 = article.find("h1")
    if h1:
        for a in h1.select("a.headerlink"):
            a.decompose()
        return h1.get_text(strip=True)
    return soup.title.get_text(strip=True) if soup.title else "Untitled"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", nargs="?", default="site", help="build output folder (default: site)")
    ap.add_argument("--title", default="Backlinks", help="heading of the backlinks section")
    ap.add_argument("--base-path", default="/", help="URL path the site is served under, e.g. /wiki/")
    args = ap.parse_args()

    site = Path(args.site)
    base_path = args.base_path if args.base_path.endswith("/") else args.base_path + "/"

    # 1. Load every content page.
    pages, files = {}, {}
    for f in sorted(site.rglob("*.html")):
        key = f.relative_to(site).as_posix()
        if key in SKIP_PAGES:
            continue
        soup = BeautifulSoup(f.read_text(encoding="utf-8"), "html.parser")
        article = soup.select_one(ARTICLE)
        if article is None:
            continue
        pages[key] = soup
        files[key] = f

    # 2. Remove old sections (idempotency) and collect titles.
    titles, changed = {}, set()
    for key, soup in pages.items():
        article = soup.select_one(ARTICLE)
        for old in article.select(f"aside.{SECTION_CLASS}"):
            old.decompose()
            changed.add(key)
        copy = BeautifulSoup(str(soup), "html.parser")  # title extraction mutates
        titles[key] = page_title(copy, copy.select_one(ARTICLE))

    # 2b. Turn Obsidian [[wikilinks]] into real links.
    names = page_names(pages)
    wikilinks = 0
    for key, soup in pages.items():
        n = convert_wikilinks(key, soup, pages, names)
        if n:
            wikilinks += n
            changed.add(key)

    # 3. Collect links: target -> set of source pages.
    backlinks = defaultdict(set)
    for src, soup in pages.items():
        for a in soup.select_one(ARTICLE).select("a[href]"):
            if SKIP_LINK_CLASSES & set(a.get("class", [])):
                continue
            target = resolve(src, a["href"], pages, base_path)
            if target and target != src:
                backlinks[target].add(src)

    # 4. Write sections.
    written = 0
    for key, soup in pages.items():
        sources = backlinks.get(key)
        if not sources and key not in changed:
            continue
        if sources:
            aside = soup.new_tag("aside", attrs={"class": SECTION_CLASS})
            h = soup.new_tag("h2")
            h.string = args.title
            ul = soup.new_tag("ul")
            for src in sorted(sources, key=lambda s: titles[s].lower()):
                li = soup.new_tag("li")
                link = soup.new_tag("a", href=rel_url(key, src))
                link.string = titles[src]
                li.append("🔗" + link)
                ul.append(li)
            aside.extend([h, ul])
            soup.select_one(ARTICLE).append(aside)
        files[key].write_text(str(soup), encoding="utf-8")
        written += 1

    total = sum(len(v) for v in backlinks.values())
    print(
        f"backlinks: {len(pages)} pages scanned, {wikilinks} wikilinks converted, "
        f"{total} links found, {written} pages updated"
    )


if __name__ == "__main__":
    main()