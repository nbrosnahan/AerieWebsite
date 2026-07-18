# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Hugo static site for [brosnahan.org](https://brosnahan.org) — a minimal, hand-built Hugo blog. No theme, no npm, no build tooling beyond Hugo itself.

## Commands

All common tasks go through the `Makefile`. Run `make` (or `make help`) with no
arguments to list targets.

```bash
# Serve locally with drafts enabled, open in Safari once ready
make run-site

# Create a new post from the archetype (content/posts/<slug>.md)
make new-post TITLE=my-first-post

# Production build (outputs to ./public/)
make build-site

# Remove build artifacts (public/, resources/_gen)
make clean

# Pre-merge gate: clean + build-site (skip with SKIP_PREFLIGHT=1)
make preflight
```

`run-site` runs `hugo server -D --navigateToChanged` — drafts are visible
locally, but `.github/workflows/deploy.yml` builds with plain `hugo --minify`,
so drafts stay unpublished on the live site.

**Authoring loop:** `make new-post TITLE=<slug>` creates the post with
`draft: true` (set in `archetypes/default.md`); `make run-site` previews it
locally since drafts are rendered; the post stays out of the production
build until `draft: true` is flipped to `false` in its frontmatter; deploying
is a push to `main`.

Hugo version in CI: **0.164.0 extended**.

## Architecture

This is a minimal, no-theme Hugo site. All structure is hand-built in `layouts/`:

| File | Purpose |
|------|---------|
| `Makefile` | Primary task interface: `run-site`, `build-site`, `new-post`, `clean`, `preflight`, `help` |
| `layouts/_default/baseof.html` | Shell: `<html>`, `<head>`, inlined CSS, header/footer partials, `main` block |
| `layouts/_default/list.html` | Section list pages (e.g. `/posts/`): renders post items with date, title, tags |
| `layouts/_default/single.html` | Single page/post template: title, date, tags, body content, prev/next nav |
| `layouts/_default/terms.html` | Taxonomy term listing (e.g. `/tags/`): alphabetical list of terms with counts |
| `layouts/index.html` | Homepage: lists all pages in the `posts` section, newest first |
| `layouts/partials/header.html` | Site header: title link and nav (Writing, About, Tags, RSS) |
| `layouts/partials/footer.html` | Site footer: copyright and RSS link |
| `assets/css/main.css` | All styles — inlined at build time via `resources.Get` + `minify` |
| `content/_index.md` | Homepage frontmatter (title only); content is driven by `layouts/index.html` |
| `archetypes/default.md` | Frontmatter template for `hugo new` (title, date, lastmod, description, tags, categories, draft) |
| `scripts/migrate-wordpress.py` | One-shot (but idempotent/re-runnable) WordPress→Hugo content migration. Stdlib-only, no third-party deps. Pulls from the live `brosnahan.org` WP REST API and writes `content/posts/<slug>.md`, `content/about.md` (body only), and `static/images/<basename>` |
| `static/images/` | Original (non-resized, non-`.avif`) images pulled from the WordPress media library, referenced site-absolutely as `/images/<file>` |

**CSS is inlined** — `baseof.html` uses `resources.Get "css/main.css" | minify` and emits it as a `<style>` block. There is no external stylesheet.

## Content Migration

The WordPress→Hugo content migration from the live brosnahan.org site is complete: 14 posts → `content/posts/<slug>.md`, the `who-am-i` page body → `content/about.md`, and 8 original images → `static/images/`. `content/photography.md` was migrated by hand, separately from the script. The migration is re-runnable via `scripts/migrate-wordpress.py` (see architecture table above) if content on the WordPress side changes before the DNS cutover — **re-running with no flags is safe and non-destructive**: any `content/posts/<slug>.md`, `content/about.md` body, or `static/images/<basename>` that already exists on disk is left untouched and reported as skipped. Pass `--force` to overwrite everything unconditionally; doing so **will discard any hand-written `description:` frontmatter** (see below), since those are regenerated fresh from the WordPress excerpt on every forced write.

**Every post's frontmatter carries an explicit `slug:` field pinned to the WordPress slug.** This is load-bearing, not incidental: Hugo's `:slug` permalink token falls back to a sanitized *title* when `slug:` is absent, and Hugo's title sanitizer — unlike WordPress's `sanitize_title()` — does not strip trailing punctuation. One migrated post's title ends in a literal period, which silently produced a divergent URL (`.../transportation-funding./` instead of the WordPress-matching slug) until `slug:` was added. **Do not remove or "clean up" a post's `slug:` field when editing its title** — doing so can silently break URL parity with the old WordPress URLs.

**URL parity** (already configured in `hugo.toml` — do not change without understanding why):

| Config | Effect |
|--------|--------|
| `[permalinks] posts = "/:year/:month/:day/:slug/"` | Matches WordPress's "Day and name" permalink structure |
| `[permalinks.term]` maps `tags` → `/tag/:slug/`, `categories` → `/category/:slug/` | WordPress uses singular URL segments; the `[taxonomies]` block stays plural so frontmatter keeps `tags:`/`categories:` keys |
| Alias on `content/about.md` | `/who-am-i/` → `/about/` |
| `content/photography.md` | Preserves `/photography/` |

**Decisions made:**
- **Images** migrated to `static/images/` (flat), not page bundles or a preserved `static/wp-content/uploads/` tree: only 3 posts carry images (8 total), so a flat tree was cheap and keeps `content/posts/` as uniform flat `.md` files. `<img src>` attributes were rewritten to `/images/<file>` during conversion. Media pulled is the ORIGINAL files from the WordPress media library, not the resized/`.avif` derivatives WordPress generates.
- **Embeds:** one post (`superman-sneak-peek`) contained a YouTube iframe, converted to Hugo's built-in `{{< youtube >}}` shortcode. Figures use the built-in `{{< figure >}}` shortcode. Both avoid needing `markup.goldmark.renderer.unsafe`.
- **RSS** lands at Hugo's `/index.xml`, not WordPress's `/feed/` — that URL was not preserved. The owner has decided not to add a `/feed/` alias: existing subscribers at that URL will 404 after the DNS cutover, accepted.
- **Favicon** is sourced from WordPress's site-icon crop, `cropped-aerie_icon.webp` (512x512), not the uncropped 1024x1024 `aerie_icon.webp` upload, whose framing (more padding around the circle) differs. The 512 master is stored as `assets/images/aerie-icon.webp`; `layouts/_default/baseof.html` generates 32x32, 180x180 (apple-touch-icon), and 192x192 PNGs from it at build time via Hugo image processing (`resources.Get` + `.Resize`).
- **Date archives** (`/YYYY/MM/`) are NOT preserved. Hugo has no built-in date-archive generation; `GroupByDate`/`GroupByPublishDate` group posts inside a template but don't emit pages at those URLs. Reproducing them would require a generated stub page per month with a `url:` frontmatter override, plus a new stub every future month — rejected as ongoing maintenance for URLs with negligible inbound links. These URLs will 404 after cutover.
- **Excluded content:** the post at `/2025/04/01/__trashed/` was a WordPress deleted-post artifact and was NOT migrated. 14 posts migrated, not 15.
- **`uncategorized` category retained (reversing an earlier decision)** — it was originally dropped as a WordPress default placeholder, not a real category, but the owner asked for it back: `/category/uncategorized/` returns HTTP 200 on the live WordPress site, and keeping the category preserves that URL's parity after the DNS cutover. Its two posts (`hello-sf`, `what-topics`) carry `categories: ["Uncategorized"]`. **This is considered temporary** — a future cleanup may drop it again, which would 404 that URL. The single lever for this is `DROP_CATEGORY_SLUGS` in `scripts/migrate-wordpress.py` (currently empty; the comment there documents exactly how to re-drop it and which files to touch).
- **All 14 posts' `description:` values are hand-written**, not derived from WordPress's auto-excerpts. Each is kept under 160 characters (so search engines render it without truncation), ends on a complete sentence, and contains no bare URLs. These feed `<meta name="description">` via `layouts/_default/baseof.html`, so they're what search engines show today. **Durable warning:** re-running `scripts/migrate-wordpress.py` with `--force` regenerates descriptions from the WordPress excerpt and would **destroy** this hand-written text — the default no-flag run is safe (it skips files that already exist). This is the concrete reason the `--force` guard exists.

## Deployment

Push to `main` → GitHub Actions builds with Hugo and deploys to GitHub Pages. Workflow at `.github/workflows/deploy.yml`.

The GitHub Pages custom domain is currently cleared, so the site publishes to `https://nbrosnahan.github.io/AerieWebsite/` rather than a custom domain. `deploy.yml` passes `--baseURL "${{ steps.pages.outputs.base_url }}/"`, which is what makes the project-subpath URLs resolve correctly without a custom domain. `hugo.toml` itself currently declares `baseURL = "https://nbrosnahan.github.io/AerieWebsite/"`, with a comment noting to revert it to `https://brosnahan.org/` at the eventual DNS cutover — but the workflow's `--baseURL` override supersedes whatever `hugo.toml` says at build time regardless, so drift between the two isn't a live conflict. Restoring the custom domain later means re-adding `static/CNAME` containing `brosnahan.org` **and** setting the domain in repo Settings → Pages; doing only one of the two leaves the site unreachable.
