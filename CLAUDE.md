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

**Description convention:** every post's `description:` frontmatter is a
single short fragment naming what the post is about — not a full sentence,
no terminal period. Roughly 25–110 characters is the observed range across
the site. No bare URLs, no markdown links, and no editorializing or verdict
(state the topic, not what to think of it). For posts that are primarily a
link plus commentary, describe *what's being linked* in words; the link
itself belongs in the post body, where it's clickable and has context.

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
| `scripts/migrate-wordpress.py` | **HISTORICAL — do not re-run.** The one-time WordPress→Hugo migration, completed 2026-07-18. It emits WordPress-era conventions (explicit `slug:` fields, flat `static/images/` paths, excerpt-derived descriptions) that the site has since abandoned; re-running it would reintroduce them and overwrite hand-written descriptions. Kept for the record only |
| `content/posts/<slug>/` | **Page bundles.** Posts that carry images are directories: `index.md` plus the image files alongside it, referenced bundle-relatively as `{{< figure src="<file>" >}}`. Posts without images stay as flat `content/posts/<slug>.md`. There is no `static/` directory |

**CSS is inlined** — `baseof.html` uses `resources.Get "css/main.css" | minify` and emits it as a `<style>` block. There is no external stylesheet.

## Content Migration

The WordPress→Hugo content migration from the live brosnahan.org site is complete: 14 posts, the `who-am-i` page body → `content/about.md`, and 8 original images. `content/photography.md` was migrated by hand, separately from the script. **`scripts/migrate-wordpress.py` is historical and must not be re-run** — see the architecture table above.

### URL scheme: Hugo defaults (WordPress parity abandoned 2026-07-18)

The site uses **Hugo's default permalinks**. `hugo.toml` carries no `[permalinks]` block, no `[permalinks.term]` block, and no `capitalizeListTitles` override:

| Content | URL |
|---------|-----|
| Posts | `/posts/<slug>/` |
| Tags | `/tags/<slug>/` |
| Categories | `/categories/<slug>/` |
| Pages | `/about/`, `/photography/` |

The owner **deliberately abandoned WordPress URL parity on 2026-07-18** and accepted the breakage. These old WordPress URLs now 404: dated post permalinks (`/YYYY/MM/DD/<slug>/`), singular term paths (`/tag/<slug>/`, `/category/<slug>/`), `/who-am-i/`, date archives (`/YYYY/MM/`), and `/feed/`.

**Post slugs derive from the filename**, not the title — posts carry no `slug:` frontmatter field, and none should be added. Because the slug comes from the filename, the old trailing-punctuation hazard no longer applies: a title ending in a period (e.g. the SB 63 post) cannot leak a trailing dot into its URL. **To change a post's URL, rename its file** (`content/posts/<slug>.md`, or the bundle directory `content/posts/<slug>/`).

**Taxonomy names are authored in their proper display form** (`SVBC`, `ECRR2025`, `Door Lock`, `AI`, `UPS`, `Public Transit`), and Hugo urlizes them down to unchanged slugs (`svbc`, `ecrr2025`, `door-lock`, …). This is what lets `capitalizeListTitles` stay at its default: Hugo's title caser only uppercases each word's first rune and leaves the rest alone, so acronyms survive intact rather than becoming "Svbc". **Author new tags in display form** — a lowercase tag would render lowercase in headings.

**Decisions made:**
- **Images** live in **page bundles**: a post with images is a directory (`content/posts/<slug>/index.md`) with its images beside it, referenced bundle-relatively (`{{< figure src="<file>" >}}`). Two posts carry images (`cities-moving`, 3; `i-got-tired-of-changing-batteries`, 5). There is no `static/` directory. Media pulled from WordPress was the ORIGINAL files, not the resized/`.avif` derivatives.
- **Embeds:** one post (`superman-sneak-peek`) contained a YouTube iframe, converted to Hugo's built-in `{{< youtube >}}` shortcode. Figures use the built-in `{{< figure >}}` shortcode. Both avoid needing `markup.goldmark.renderer.unsafe`.
- **RSS** lands at Hugo's `/index.xml`, not WordPress's `/feed/` — that URL was not preserved. The owner has decided not to add a `/feed/` alias: existing subscribers at that URL will 404, accepted.
- **Favicon** is sourced from WordPress's site-icon crop, `cropped-aerie_icon.webp` (512x512), not the uncropped 1024x1024 `aerie_icon.webp` upload, whose framing (more padding around the circle) differs. The 512 master is stored as `assets/images/aerie-icon.webp`; `layouts/_default/baseof.html` generates 32x32, 180x180 (apple-touch-icon), and 192x192 PNGs from it at build time via Hugo image processing (`resources.Get` + `.Resize`).
- **Date archives** (`/YYYY/MM/`) are NOT generated. Hugo has no built-in date-archive generation; `GroupByDate`/`GroupByPublishDate` group posts inside a template but don't emit pages at those URLs. Reproducing them would require a generated stub page per month with a `url:` frontmatter override, plus a new stub every future month — rejected as ongoing maintenance for URLs with negligible inbound links.
- **Excluded content:** the post at `/2025/04/01/__trashed/` was a WordPress deleted-post artifact and was NOT migrated. 14 posts migrated, not 15.
- **`Uncategorized` category retained.** It was originally dropped as a WordPress default placeholder, then restored to preserve `/category/uncategorized/`. That parity rationale is now moot — the URL is `/categories/uncategorized/` and the old one 404s — but the category is kept as-is; its two posts (`hello-sf`, `what-topics`) carry `categories: ["Uncategorized"]`. Dropping it is now a plain content edit to those two files, not a script setting.
- **All 14 posts' `description:` values are hand-written**, not derived from WordPress's auto-excerpts, and follow the description convention documented under Commands → Authoring loop above. **Durable warning:** `scripts/migrate-wordpress.py` regenerates descriptions from the WordPress excerpt and would **destroy** this hand-written text. This is one of the reasons that script must never be re-run.

## Deployment

Push to `main` → GitHub Actions builds with Hugo and deploys to GitHub Pages. Workflow at `.github/workflows/deploy.yml`.

The GitHub Pages custom domain is currently cleared, so the site publishes to `https://nbrosnahan.github.io/AerieWebsite/` rather than a custom domain. `deploy.yml` passes `--baseURL "${{ steps.pages.outputs.base_url }}/"`, which is what makes the project-subpath URLs resolve correctly without a custom domain. `hugo.toml` itself currently declares `baseURL = "https://nbrosnahan.github.io/AerieWebsite/"`, with a comment noting to revert it to `https://brosnahan.org/` at the eventual DNS cutover — but the workflow's `--baseURL` override supersedes whatever `hugo.toml` says at build time regardless, so drift between the two isn't a live conflict. Restoring the custom domain later means re-adding `static/CNAME` containing `brosnahan.org` **and** setting the domain in repo Settings → Pages; doing only one of the two leaves the site unreachable. Note that the `static/` directory no longer exists (images moved into page bundles), so restoring the custom domain means recreating `static/` for that one file.
