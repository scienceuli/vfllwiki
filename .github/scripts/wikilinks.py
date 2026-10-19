#!/usr/bin/env python3
"""Convert Obsidian wikilinks to Markdown links before a Zensical build.

The Obsidian vault (source) is never modified: it is copied to a build
folder and the wikilinks are converted in the copy. Point `docs_dir` in
zensical.toml at the build folder.

    python wikilinks.py docs build_docs
    zensical build --clean

Supported:
    [[Note]]                    -> [Note](rel/path/Note.md)
    [[Note|Text]]               -> [Text](rel/path/Note.md)
    [[Note#Heading]]            -> [Note > Heading](rel/path/Note.md#heading)
    [[#Heading]]                -> link to a heading on the same page
    [[folder/Note]]             -> explicit path when names are ambiguous
    [[Note#^block]]             -> link to the note (block ids are dropped)
    ![[image.png]]              -> ![image](rel/path/image.png)
    ![[image.png|300]]          -> ![image](...){ width="300" }  (needs attr_list)
    ![[Note]]                   -> plain link (note embeds can't be transcluded)

Notes are found by file name anywhere in the vault, like Obsidian does.
Links inside code blocks and inline code are left alone. Unresolved links
become plain text and are reported; --strict makes them fail the build.
"""
import argparse
import posixpath
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

WIKILINK = re.compile(r"(!?)\[\[([^\[\]\n]+?)\]\]")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+).+?\1")
IGNORE = shutil.ignore_patterns(".obsidian", ".trash", ".git", ".DS_Store")


def slugify(text: str, unicode: bool) -> str:
    """Python-Markdown's default heading ids (toc extension)."""
    if not unicode:
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


class Vault:
    def __init__(self, root: Path):
        self.root = root
        self.notes = defaultdict(list)   # lowercase stem -> [rel paths]
        self.files = defaultdict(list)   # lowercase file name -> [rel paths]
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(root).as_posix()
            if f.suffix.lower() == ".md":
                self.notes[f.stem.lower()].append(rel)
            self.files[f.name.lower()].append(rel)

    def resolve(self, target: str, src: str, embed: bool):
        """Return the vault-relative path for a link target, or None."""
        t = target.strip().lstrip("/")
        is_note = not Path(t).suffix or t.lower().endswith(".md")
        if is_note and t.lower().endswith(".md"):
            t = t[:-3]
        name = posixpath.basename(t).lower()
        cands = self.notes.get(name, []) if is_note else self.files.get(name, [])
        if "/" in t:  # explicit path: match the end of the path
            suffix = (t + ".md" if is_note else t).lower()
            cands = [c for c in cands if ("/" + c.lower()).endswith("/" + suffix)]
        if not cands:
            return None, False
        src_dir = posixpath.dirname(src)
        # Prefer the same folder, then the shortest path (Obsidian-like).
        best = sorted(cands, key=lambda c: (posixpath.dirname(c) != src_dir, c.count("/"), c))
        return best[0], len(cands) > 1


def rel_link(src: str, dst: str) -> str:
    rel = posixpath.relpath(dst, posixpath.dirname(src) or ".")
    return quote(rel, safe="/")


def convert(text: str, src: str, vault: Vault, unicode_slugs: bool, problems: list) -> tuple[str, int]:
    count = 0

    def repl(m):
        nonlocal count
        embed, inner = m.group(1) == "!", m.group(2)
        target, _, label = inner.partition("|")
        target, _, anchor = target.partition("#")
        target, label, anchor = target.strip(), label.strip(), anchor.strip()

        # Same-page heading: [[#Heading]]
        if not target:
            count += 1
            return f"[{label or anchor}](#{slugify(anchor, unicode_slugs)})"

        path, ambiguous = vault.resolve(target, src, embed)
        if path is None:
            problems.append(f"{src}: unresolved [[{inner}]]")
            return label or target
        if ambiguous:
            problems.append(f"{src}: [[{target}]] is ambiguous, using {path}")
        count += 1
        url = rel_link(src, path)

        if embed and not path.lower().endswith(".md"):
            alt = Path(target).stem
            if label and re.fullmatch(r"\d+(x\d+)?", label):  # ![[img.png|300]] or |300x200
                w, _, h = label.partition("x")
                attrs = f'width="{w}"' + (f' height="{h}"' if h else "")
                return f"![{alt}]({url}){{ {attrs} }}"
            return f"![{label or alt}]({url})"
        if embed:
            problems.append(f"{src}: note embed ![[{inner}]] converted to a link")

        if anchor.startswith("^"):  # block reference: no equivalent, link the note
            anchor = ""
        if anchor:
            url += "#" + slugify(anchor, unicode_slugs)
        name = posixpath.basename(target)
        if name.lower().endswith(".md"):
            name = name[:-3]
        text_ = label or (f"{name} > {anchor}" if anchor else name)
        return f"[{text_}]({url})"

    out, in_fence, fence = [], False, ""
    for line in text.splitlines(keepends=True):
        m = FENCE.match(line)
        if m:
            if not in_fence:
                in_fence, fence = True, m.group(1)[0]
            elif m.group(1)[0] == fence:
                in_fence = False
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # Convert only outside inline code spans.
        parts, pos = [], 0
        for c in INLINE_CODE.finditer(line):
            parts.append(WIKILINK.sub(repl, line[pos:c.start()]))
            parts.append(c.group(0))
            pos = c.end()
        parts.append(WIKILINK.sub(repl, line[pos:]))
        out.append("".join(parts))
    return "".join(out), count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="Obsidian vault / docs folder (not modified)")
    ap.add_argument("dst", help="build folder to create (deleted and recreated)")
    ap.add_argument("--strict", action="store_true", help="exit with an error on unresolved links")
    ap.add_argument("--unicode-slugs", action="store_true",
                    help="keep umlauts in heading anchors (use if your toc slugify keeps unicode)")
    args = ap.parse_args()

    src, dst = Path(args.src).resolve(), Path(args.dst).resolve()
    if dst == src or src in dst.parents:
        sys.exit("dst must be outside src")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE)

    vault = Vault(dst)
    problems, total, files = [], 0, 0
    for f in sorted(dst.rglob("*.md")):
        rel = f.relative_to(dst).as_posix()
        text = f.read_text(encoding="utf-8")
        new, n = convert(text, rel, vault, args.unicode_slugs, problems)
        if n or new != text:
            f.write_text(new, encoding="utf-8")
            files += 1
            total += n

    for p in problems:
        print("warning:", p, file=sys.stderr)
    print(f"wikilinks: {total} links converted in {files} files, {len(problems)} warnings")
    if args.strict and any("unresolved" in p for p in problems):
        sys.exit(1)


if __name__ == "__main__":
    main()