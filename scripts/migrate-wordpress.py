#!/usr/bin/env python3
"""Migrate WordPress content from brosnahan.org into this Hugo site.

Stdlib only (urllib/html/re/json) -- no third-party dependencies.

Pulls posts, the "who-am-i" page, categories, tags, and media from the
WordPress REST API (https://brosnahan.org/wp-json/wp/v2/) and writes:

  - content/posts/<slug>.md  (one per published post, excluding __trashed)
  - content/about.md          (body only; existing frontmatter preserved)
  - static/images/<basename>  (ORIGINAL media files, not resized derivatives)

See CLAUDE.md for the URL-parity constraints this migration must preserve.

Usage:
    python3 scripts/migrate-wordpress.py

Re-running is safe by default: existing content/posts/<slug>.md files,
content/about.md (once it has a body), and static/images/<basename> files
are left untouched, and a "skip (exists)" line is printed for each. Pass
--force to overwrite everything unconditionally (this will discard any
hand-edited `description:` frontmatter values).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SITE = "https://brosnahan.org"
API = f"{SITE}/wp-json/wp/v2"
USER_AGENT = "AerieWebsite-migrate-wordpress/1.0 (+https://github.com/nbrosnahan/AerieWebsite)"

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "content" / "posts"
ABOUT_FILE = REPO_ROOT / "content" / "about.md"
IMAGES_DIR = REPO_ROOT / "static" / "images"

EXCLUDED_POST_SLUGS = {"__trashed"}

# Category slugs to exclude from category_names (and therefore from every
# migrated post's `categories:` frontmatter). Empty by default: the
# `uncategorized` category (WordPress's default placeholder, id 1) was
# temporarily RESTORED to preserve /category/uncategorized/ URL parity with
# the live WordPress site -- see CLAUDE.md "Decisions made". To re-drop it
# (accepting that /category/uncategorized/ will 404), set this back to
# `{"uncategorized"}` and remove `"Uncategorized"` from the two affected
# posts' `categories:` lists (content/posts/hello-sf.md,
# content/posts/what-topics.md).
DROP_CATEGORY_SLUGS: set[str] = set()  # was {"uncategorized"}


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def http_get_json(url: str):
    with urllib.request.urlopen(_request(url), timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"GET {url} returned HTTP {resp.status}")
        return json.loads(resp.read().decode("utf-8"))


def http_get_json_paginated(url: str) -> list:
    """Fetch every page of a WordPress REST API collection endpoint.

    `url` must already include `per_page` (and any other query params) but
    no `page` param -- this appends `&page=N` and follows the
    `X-WP-TotalPages` response header until exhausted. WordPress caps
    `per_page` at 100, so without this, collections with more than 100
    items would silently drop everything past the first page."""
    results: list = []
    page = 1
    total_pages = 1
    while page <= total_pages:
        paged_url = f"{url}&page={page}"
        with urllib.request.urlopen(_request(paged_url), timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"GET {paged_url} returned HTTP {resp.status}")
            body = resp.read()
            total_pages = int(resp.headers.get("X-WP-TotalPages", "1") or "1")
        results.extend(json.loads(body.decode("utf-8")))
        page += 1
    return results


def http_get_bytes(url: str) -> tuple[bytes, str]:
    """Returns (body, content_type). Raises on any non-2xx or empty body."""
    try:
        with urllib.request.urlopen(_request(url), timeout=60) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GET {url} failed: HTTP {e.code}") from e
    if status != 200:
        raise RuntimeError(f"GET {url} returned HTTP {status}")
    return body, content_type


# --------------------------------------------------------------------------
# Text / markdown helpers
# --------------------------------------------------------------------------

TAG_RE = re.compile(r"(<[^>]+>)")
MD_ESCAPE_RE = re.compile(r"([\\`*_\[\]])")


def yaml_dquote(s: str) -> str:
    """Escape a string for embedding in a YAML double-quoted scalar."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def escape_markdown(text: str) -> str:
    """Escape characters that are markdown-significant if they appear
    literally in prose, so they don't become accidental formatting."""
    return MD_ESCAPE_RE.sub(r"\\\1", text)


def strip_tags(html_str: str) -> str:
    return re.sub(r"<[^>]+>", "", html_str)


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


EM_RE = re.compile(r"<em([^>]*)>(.*?)</em>", re.DOTALL)


def normalize_em(fragment: str) -> str:
    """WordPress sometimes splits what's conceptually one italic run into
    multiple adjacent <em> tags (e.g. an empty "<em> </em>" immediately
    followed by "<em class=...>Voila!</em>"). Emitting each independently
    as "*...*" produces broken/mismatched markdown delimiters (interior
    whitespace right after an opening "*", or "**" from two spans butting
    up against each other). Merge directly-adjacent <em> runs and pull any
    leading/trailing whitespace out of each remaining <em> so emphasis
    delimiters always sit next to non-whitespace, dropping any <em> that
    turns out to be whitespace-only."""
    fragment = re.sub(r"</em><em[^>]*>", "", fragment)

    def repl(m: re.Match) -> str:
        attrs, inner = m.group(1), m.group(2)
        if not inner.strip():
            return inner  # whitespace-only <em>: drop the tags, keep the space
        leading = inner[: len(inner) - len(inner.lstrip())]
        trailing = inner[len(inner.rstrip()):]
        core = inner.strip()
        return f"{leading}<em{attrs}>{core}</em>{trailing}"

    return EM_RE.sub(repl, fragment)


def convert_inline(fragment: str) -> str:
    """Convert an inline HTML fragment (the contents of a <p> or
    <figcaption>) containing only <a>, <em>, and <br> into markdown,
    entity-decoding and markdown-escaping literal text along the way."""
    fragment = normalize_em(fragment)
    tokens = TAG_RE.split(fragment)
    out: list[str] = []
    link_href: str | None = None
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("<"):
            tag_lower = tok.lower()
            if tag_lower.startswith("<a "):
                m = re.search(r'href="([^"]*)"', tok)
                if not m:
                    raise ValueError(f"<a> tag with no href: {tok!r}")
                href = html.unescape(m.group(1))
                if " " in href:
                    raise ValueError(f"href contains a space, would break markdown link syntax: {href!r}")
                link_href = href
                out.append("[")
            elif tag_lower == "</a>":
                if link_href is None:
                    raise ValueError("</a> with no matching <a>")
                out.append(f"]({link_href})")
                link_href = None
            elif tag_lower.startswith("<em"):
                out.append("*")
            elif tag_lower == "</em>":
                out.append("*")
            elif tag_lower.startswith("<br"):
                out.append("\\\n")
            else:
                raise ValueError(f"Unhandled inline tag {tok!r} in fragment: {fragment!r}")
        else:
            out.append(escape_markdown(html.unescape(tok)))
    return "".join(out)


def to_iso_with_offset(local: str, gmt: str) -> str:
    """WP returns `date`/`date_gmt` (and `modified`/`modified_gmt`) as
    naive local/UTC timestamps with no offset. Derive the offset from the
    two and emit a full ISO-8601 timestamp, so we use the WP *local* time
    (not `_gmt`) without silently shifting the published URL's date."""
    d = datetime.fromisoformat(local)
    g = datetime.fromisoformat(gmt)
    delta = d - g
    total_minutes = int(delta.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hh, mm = divmod(total_minutes, 60)
    return d.strftime("%Y-%m-%dT%H:%M:%S") + f"{sign}{hh:02d}:{mm:02d}"


def clean_description(excerpt_html: str) -> str:
    text = strip_tags(excerpt_html)
    text = html.unescape(text)
    text = collapse_whitespace(text)
    # Strip WordPress's "… Continue reading →" boilerplate appended to
    # truncated excerpts (post-decode: "&hellip;" -> "…", "&rarr;" -> "→").
    text = re.sub(r"\s*…\s*Continue reading\s*→\s*$", "", text).strip()
    return text


# --------------------------------------------------------------------------
# Media handling
# --------------------------------------------------------------------------


class MediaLibrary:
    def __init__(self, force: bool = False):
        self.force = force
        self._detail_cache: dict[int, dict] = {}
        self._all_media: list[dict] | None = None
        self._downloaded: dict[str, str] = {}  # local basename -> original url (for reporting)
        self.skipped_report: list[str] = []
        self.images_written = 0
        self.images_skipped = 0

    def _all(self) -> list[dict]:
        if self._all_media is None:
            self._all_media = http_get_json_paginated(f"{API}/media?per_page=100")
        return self._all_media

    def _detail(self, media_id: int) -> dict:
        if media_id not in self._detail_cache:
            self._detail_cache[media_id] = http_get_json(f"{API}/media/{media_id}")
        return self._detail_cache[media_id]

    def _find_id_by_src_basename(self, src: str) -> int | None:
        """Fallback path: match a resized derivative's basename (after
        stripping a trailing -WxH size suffix) against media source_url
        basenames."""
        basename = os.path.basename(urlparse(src).path)
        stem, ext = os.path.splitext(basename)
        stem_no_size = re.sub(r"-\d+x\d+$", "", stem)
        for m in self._all():
            m_basename = os.path.basename(urlparse(m["source_url"]).path)
            m_stem, m_ext = os.path.splitext(m_basename)
            if m_stem == stem_no_size and m_ext == ext:
                return m["id"]
        return None

    def resolve_and_download(self, wp_image_id: int | None, src: str) -> str:
        """Resolve an <img> (by wp-image-<ID> class, falling back to
        matching src's basename) to a locally-downloaded original image,
        returning the site-absolute path to reference in markdown."""
        media_id = wp_image_id
        if media_id is None:
            media_id = self._find_id_by_src_basename(src)
        if media_id is None:
            raise RuntimeError(f"Could not resolve media for <img src=\"{src}\"> (no wp-image-N class and no basename match)")

        detail = self._detail(media_id)
        media_details = detail.get("media_details") or {}
        source_url = detail["source_url"]
        file_path = media_details.get("file")
        original_image = media_details.get("original_image")

        if original_image and file_path:
            uploads_base = source_url[: -len(file_path)]
            file_dir = os.path.dirname(file_path)
            original_url = f"{uploads_base}{file_dir}/{original_image}" if file_dir else f"{uploads_base}{original_image}"
        else:
            original_url = source_url

        local_basename = os.path.basename(urlparse(original_url).path).lower()
        dest = IMAGES_DIR / local_basename

        if local_basename in self._downloaded:
            return f"/images/{local_basename}"

        if dest.exists() and not self.force:
            print(f"  skip (exists): static/images/{local_basename}")
            self._downloaded[local_basename] = original_url
            self.images_skipped += 1
            return f"/images/{local_basename}"

        body, content_type = http_get_bytes(original_url)
        if not content_type.startswith("image/"):
            raise RuntimeError(
                f"Refusing to write non-image content for {original_url}: Content-Type={content_type!r}"
            )
        if len(body) < 100:
            raise RuntimeError(f"Refusing to write suspiciously tiny download ({len(body)} bytes) for {original_url}")

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        self._downloaded[local_basename] = original_url
        self.images_written += 1
        print(f"  downloaded {original_url} -> static/images/{local_basename} ({len(body)} bytes)")
        return f"/images/{local_basename}"

    def report_skipped(self, referenced_ids: set[int]) -> None:
        for m in self._all():
            if m["id"] not in referenced_ids:
                print(f"  skipped media id={m['id']} slug={m['slug']!r} ({m['source_url']}) -- not referenced by any migrated post")


# --------------------------------------------------------------------------
# Content-block conversion
# --------------------------------------------------------------------------

BLOCK_RE = re.compile(r"<(p|figure)\b([^>]*)>(.*?)</\1>", re.DOTALL)


def convert_content(content_html: str, media: MediaLibrary, post_slug: str) -> str:
    blocks: list[str] = []
    for tag, attrs, inner in BLOCK_RE.findall(content_html):
        inner = inner.strip()
        if tag == "p":
            if not inner:
                continue  # drop empty paragraphs
            blocks.append(convert_inline(inner))
        elif tag == "figure":
            if "wp-block-embed" in attrs and "youtube" in attrs:
                m = re.search(r'<iframe\b[^>]*\bsrc="([^"]+)"', inner)
                if not m:
                    raise ValueError(f"[{post_slug}] youtube embed figure with no iframe src: {inner!r}")
                iframe_src = html.unescape(m.group(1))
                vid_m = re.search(r"/embed/([^?&\"]+)", iframe_src)
                if not vid_m:
                    raise ValueError(f"[{post_slug}] could not parse video id from iframe src: {iframe_src!r}")
                blocks.append(f"{{{{< youtube {vid_m.group(1)} >}}}}")
            else:
                img_m = re.search(r"<img\b([^>]*)/?>", inner)
                if not img_m:
                    raise ValueError(f"[{post_slug}] <figure> with no <img>: {inner!r}")
                img_attrs = img_m.group(1)

                src_m = re.search(r'src="([^"]*)"', img_attrs)
                if not src_m:
                    raise ValueError(f"[{post_slug}] <img> with no src: {img_attrs!r}")
                src = html.unescape(src_m.group(1))

                class_m = re.search(r'class="([^"]*)"', img_attrs)
                wp_image_id = None
                if class_m:
                    id_m = re.search(r"wp-image-(\d+)", class_m.group(1))
                    if id_m:
                        wp_image_id = int(id_m.group(1))

                alt_m = re.search(r'alt="([^"]*)"', img_attrs)
                alt = html.unescape(alt_m.group(1)).strip() if alt_m else ""

                local_src = media.resolve_and_download(wp_image_id, src)

                cap_m = re.search(r"<figcaption\b[^>]*>(.*?)</figcaption>", inner, re.DOTALL)
                caption = ""
                if cap_m:
                    caption = collapse_whitespace(html.unescape(strip_tags(cap_m.group(1))))

                parts = [f'src="{local_src}"']
                if alt:
                    parts.append(f'alt="{alt.replace(chr(34), chr(92) + chr(34))}"')
                if caption:
                    parts.append(f'caption="{caption.replace(chr(34), chr(92) + chr(34))}"')
                blocks.append("{{< figure " + " ".join(parts) + " >}}")
    return "\n\n".join(blocks)


# --------------------------------------------------------------------------
# Frontmatter / file writers
# --------------------------------------------------------------------------


def write_post(
    post: dict,
    tag_names: dict[int, str],
    category_names: dict[int, str],
    media: MediaLibrary,
    force: bool = False,
) -> tuple[Path, bool]:
    """Returns (dest, skipped)."""
    slug = post["slug"]
    dest = POSTS_DIR / f"{slug}.md"
    if dest.exists() and not force:
        print(f"  skip (exists): {dest.relative_to(REPO_ROOT)}")
        return dest, True

    title = html.unescape(post["title"]["rendered"])
    date = to_iso_with_offset(post["date"], post["date_gmt"])
    lastmod = to_iso_with_offset(post["modified"], post["modified_gmt"])
    description = clean_description(post["excerpt"]["rendered"])

    tags = [tag_names[t] for t in post["tags"] if t in tag_names]
    categories = [category_names[c] for c in post["categories"] if c in category_names]

    body = convert_content(post["content"]["rendered"], media, slug)
    if not body.strip():
        raise RuntimeError(f"[{slug}] converted body is empty")

    fm_lines = [
        "---",
        f'title: "{yaml_dquote(title)}"',
        f"date: {date}",
        f"lastmod: {lastmod}",
        f'description: "{yaml_dquote(description)}"',
        f"tags: [{', '.join(json.dumps(t) for t in tags)}]",
        f"categories: [{', '.join(json.dumps(c) for c in categories)}]",
        "draft: false",
        # Explicit slug, not left to Hugo's default: when unset, Hugo's
        # `:slug` permalink token falls back to a sanitized *title*, and
        # Hugo's sanitizer doesn't strip trailing punctuation the way
        # WordPress's sanitize_title() does (e.g. a title ending in "."
        # would otherwise leak a trailing dot into the URL). Pinning this
        # to the WP slug is what actually guarantees URL parity.
        f'slug: "{yaml_dquote(slug)}"',
        "---",
        "",
    ]
    content = "\n".join(fm_lines) + body + "\n"

    dest.write_text(content, encoding="utf-8")
    return dest, False


def write_about(page: dict, media: MediaLibrary, force: bool = False) -> tuple[Path, bool]:
    """Returns (dest, skipped). Frontmatter is always preserved; the body
    is left untouched (skipped) if it's already non-empty, unless force."""
    existing = ABOUT_FILE.read_text(encoding="utf-8")
    m = re.match(r"^(---\n.*?\n---\n)", existing, re.DOTALL)
    if not m:
        raise RuntimeError(f"{ABOUT_FILE} does not start with a --- frontmatter block; refusing to overwrite blindly")
    frontmatter = m.group(1)
    existing_body = existing[len(frontmatter):]

    if existing_body.strip() and not force:
        print(f"  skip (exists): {ABOUT_FILE.relative_to(REPO_ROOT)}")
        return ABOUT_FILE, True

    body = convert_content(page["content"]["rendered"], media, page["slug"])
    if not body.strip():
        raise RuntimeError(f"[{page['slug']}] converted about-page body is empty")

    content = frontmatter + "\n" + body + "\n"
    ABOUT_FILE.write_text(content, encoding="utf-8")
    return ABOUT_FILE, False


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate WordPress content from brosnahan.org into this Hugo site."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite content/posts/<slug>.md, content/about.md's body, and "
            "static/images/<basename> even if already present. Without this "
            "flag, existing files are left untouched (safe to re-run). "
            "WARNING: discards any hand-edited `description:` frontmatter."
        ),
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    print(f"Fetching taxonomies from {API} ...")
    categories = http_get_json_paginated(f"{API}/categories?per_page=100")
    tags = http_get_json_paginated(f"{API}/tags?per_page=100")

    category_names = {
        c["id"]: html.unescape(c["name"]) for c in categories if c["slug"] not in DROP_CATEGORY_SLUGS
    }
    tag_names = {t["id"]: html.unescape(t["name"]) for t in tags}

    print("Fetching posts ...")
    posts = http_get_json_paginated(f"{API}/posts?per_page=100&status=publish")
    posts = [p for p in posts if p["slug"] not in EXCLUDED_POST_SLUGS]
    print(f"  {len(posts)} posts to migrate (excluded: {sorted(EXCLUDED_POST_SLUGS)})")

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    media = MediaLibrary(force=args.force)

    written: list[Path] = []
    skipped: list[Path] = []
    referenced_media_ids: set[int] = set()
    for post in sorted(posts, key=lambda p: p["date"]):
        print(f"Migrating post: {post['slug']}")
        dest, was_skipped = write_post(post, tag_names, category_names, media, force=args.force)
        (skipped if was_skipped else written).append(dest)
        for m in re.finditer(r"wp-image-(\d+)", post["content"]["rendered"]):
            referenced_media_ids.add(int(m.group(1)))

    print("Fetching 'who-am-i' page ...")
    pages = http_get_json_paginated(f"{API}/pages?per_page=100")
    about_page = next((p for p in pages if p["slug"] == "who-am-i"), None)
    if about_page is None:
        raise RuntimeError("Could not find WordPress page with slug 'who-am-i'")
    about_dest, about_skipped = write_about(about_page, media, force=args.force)
    (skipped if about_skipped else written).append(about_dest)

    print("\nMedia report:")
    media.report_skipped(referenced_media_ids)

    print(
        f"\nFiles: {len(written)} written, {len(skipped)} skipped (already present)"
    )
    print(
        f"Images: {media.images_written} downloaded, {media.images_skipped} skipped (already present)"
    )
    if written:
        print("Written:")
        for f in written:
            print(f"  {f.relative_to(REPO_ROOT)}")
    if skipped:
        suffix = "" if args.force else " (use --force to overwrite)"
        print(f"Skipped{suffix}:")
        for f in skipped:
            print(f"  {f.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
