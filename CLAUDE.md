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

**CSS is inlined** — `baseof.html` uses `resources.Get "css/main.css" | minify` and emits it as a `<style>` block. There is no external stylesheet.

## Content Migration

The site is being migrated from a live WordPress 7.0.2 site at brosnahan.org: 15 published posts, 2 pages, 6 categories, 24 tags, 12 media items. WordPress's REST API (`/wp-json/wp/v2/`) is open and is the extraction path. Post bodies use only `<p>`, `<a>`, `<em>`, `<figure>`, `<figcaption>`, `<img>` — no galleries or embeds, so HTML→Markdown conversion is straightforward.

**URL parity** (already configured in `hugo.toml` — do not change without understanding why):

| Config | Effect |
|--------|--------|
| `[permalinks] posts = "/:year/:month/:day/:slug/"` | Matches WordPress's "Day and name" permalink structure |
| `[permalinks.term]` maps `tags` → `/tag/:slug/`, `categories` → `/category/:slug/` | WordPress uses singular URL segments; the `[taxonomies]` block stays plural so frontmatter keeps `tags:`/`categories:` keys |
| Alias on `content/about.md` | `/who-am-i/` → `/about/` |
| `content/photography.md` | Preserves `/photography/` |

**Decisions made:**
- **Images** migrate to Hugo-idiomatic paths (e.g. `static/images/` or page bundles), not a preserved `static/wp-content/uploads/` tree. `<img src>` attributes get rewritten during conversion. Pull the ORIGINAL media files from the WordPress media library, not the resized/`.avif` derivatives WordPress generates.
- **RSS** lands at Hugo's `/index.xml`, not WordPress's `/feed/` — that URL is not being preserved. Existing `/feed/` subscribers will stop receiving updates at the DNS cutover unless an alias is added later.
- **Date archives** (`/YYYY/MM/`) are NOT preserved. Hugo has no built-in date-archive generation; `GroupByDate`/`GroupByPublishDate` group posts inside a template but don't emit pages at those URLs. Reproducing them would require a generated stub page per month with a `url:` frontmatter override, plus a new stub every future month — rejected as ongoing maintenance for URLs with negligible inbound links. These URLs will 404 after cutover.
- **Excluded content:** the post at `/2025/04/01/__trashed/` is a WordPress deleted-post artifact and is NOT being migrated. 14 posts migrate, not 15.

## Deployment

Push to `main` → GitHub Actions builds with Hugo and deploys to GitHub Pages. Workflow at `.github/workflows/deploy.yml`.

The GitHub Pages custom domain is currently cleared, so the site publishes to `https://nbrosnahan.github.io/AerieWebsite/` rather than a custom domain. `deploy.yml` passes `--baseURL "${{ steps.pages.outputs.base_url }}/"`, which is what makes the project-subpath URLs resolve correctly without a custom domain. `hugo.toml` still declares `baseURL = "https://brosnahan.org/"` for the eventual cutover — the workflow override supersedes it at build time, so this is intentional, not a conflict. Restoring the custom domain later means re-adding `static/CNAME` containing `brosnahan.org` **and** setting the domain in repo Settings → Pages; doing only one of the two leaves the site unreachable.
