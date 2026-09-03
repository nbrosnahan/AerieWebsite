---
name: aerie-website
title: AerieWebsite
status: maintenance
created: 2026-06-17
color: "#01786f"   # Pine Green
tags: [hugo, website, static-site, blog]
---
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Hugo static site for [brosnahan.org](https://brosnahan.org), built on the [Congo](https://github.com/jpanther/congo)
theme, consumed as a Hugo Module. No npm; the only build tooling beyond Hugo itself is Go, which Hugo needs on `PATH` to
resolve the theme module (see Theme Management below). The site is branded "The Aerie", with the tagline "The stairs are
a FEATURE" as the homepage headline (see Social Links / Configuration layout above for where that string lives).

## Commands

All common tasks go through the `Makefile`. Run `make` (or `make help`) with no arguments to list targets.

```bash
# Serve locally with drafts enabled, open in Safari once ready
make run-site

# Create a new post from the archetype (content/posts/YYYY-MM-DD-<slug>.md)
make new-post TITLE=my-first-post

# Production build (outputs to ./public/)
make build-site

# Remove build artifacts (public/, resources/_gen)
make clean

# Verify every post filename is YYYY-MM-DD-<slug> (runs inside preflight)
make check-post-names

# Pre-merge gate: clean + check-post-names + build-site (skip with SKIP_PREFLIGHT=1)
make preflight
```

`run-site` runs `hugo server -D --navigateToChanged` — drafts are visible locally, but `.github/workflows/deploy.yml`
builds with `hugo --gc --minify`, so drafts stay unpublished on the live site.

**Authoring loop:** `make new-post TITLE=<slug>` creates the post with `draft: true` (set in `archetypes/default.md`);
`make run-site` previews it locally since drafts are rendered; the post stays out of the production build until
`draft: true` is flipped to `false` in its frontmatter; deploying is a push to `main`.

**Post filenames and URLs.** Posts are named `content/posts/YYYY-MM-DD-<slug>.md` (or the bundle directory
`content/posts/YYYY-MM-DD-<slug>/`), matching the convention already used in `content/ideas/`. The date prefix is
**filing only — it never reaches the URL**: each post carries an explicit `slug:` field, and that is what Hugo publishes
at. `2025-04-23-ai-2027.md` serves `/posts/ai-2027/`.

This split is deliberate and both halves are load-bearing:

- **Renaming a file changes nothing about the URL** — it only changes disk order. To change a URL, edit `slug:`.
- **Do not try to make Hugo derive the URL from a dated filename.** Setting `[frontmatter] date = [":filename", ...]`
  does strip the prefix, but only by making the filename the authoritative date, which discards the time of day from
  `date:`. Four dates on this site carry multiple posts (four on 2025-04-05 alone), and without times they fall back to
  alphabetical order — verified to reorder 11 of the 14 posts. The `slug:` field avoids this entirely. Do not
  re-litigate it.

`make new-post TITLE=<slug>` handles the prefix for you: pass an undated slug and it creates
`posts/$(date +%F)-<slug>.md`, with `archetypes/default.md` stripping the date back off into both `title:` and `slug:`.

**`make new-post` is the only command that applies the prefix**, and `make check-post-names` (folded into `preflight`)
is what enforces it everywhere else. The guard is not decoration — nothing else catches a violation:

- **Hugo cannot add the prefix itself.** `hugo new posts/<name>.md` writes exactly the path it is given; no Hugo setting
  rewrites that path, and an archetype controls only a file's *contents*, never its name. An archetype can strip a date
  prefix, as this one does, but can never add one.
- **A build will not flag it.** New posts are `draft: true`, so a production build never renders them; and once
  published, `slug:` means the URL is correct regardless of the filename. An undated post is invisibly valid.

The check covers page-bundle directories as well as flat files, and exempts `_index.md`.

Post *ideas* arrive on their own schedule: a weekly Cowork job drops five researched topic prompts into `content/ideas/`
every Monday morning, and promoting one is a different starting point than `make new-post` — see Idea Pipeline below.

**Description convention:** every post's `description:` frontmatter is a single short fragment naming what the post is
about — not a full sentence, no terminal period. Roughly 25–110 characters is the observed range across the site. No
bare URLs, no markdown links, and no editorializing or verdict (state the topic, not what to think of it). For posts
that are primarily a link plus commentary, describe *what's being linked* in words; the link itself belongs in the post
body, where it's clickable and has context.

**Hugo version: 0.165.0 extended.** CI pins it as `HUGO_VERSION` in `.github/workflows/deploy.yml`, installed as a
checksum-verified `.deb`; this machine runs Homebrew's **0.165.0+extended+withdeploy**, so `make preflight` and the
deploy exercise the same Hugo. Keep them matched when bumping either — the local gate is only meaningful as a pre-merge
check while it runs the same build that produces the published site. (The `withdeploy` suffix Homebrew adds is not a
discrepancy worth chasing: it only adds the `hugo deploy` command for S3/GCS targets, which this site never uses — it
deploys through Actions to Pages.)

**Nothing watches the pin for you.** Dependabot's `github-actions` ecosystem tracks `uses:` refs, not arbitrary env
vars, so it cannot see `HUGO_VERSION` and will never open a bump PR for it — noticing a Hugo release is manual, and that
is not fixable by switching to a setup action (Dependabot would bump the action, not the `hugo-version` input passed to
it). The pin drifted a release behind this way once already, caught only by eye in September 2026.

Bumping it is a one-line edit **provided the release keeps Hugo's asset naming** — the install step interpolates
`HUGO_VERSION` into both `hugo_extended_${HUGO_VERSION}_linux-amd64.deb` and `hugo_${HUGO_VERSION}_checksums.txt`, so
check those two assets exist on the target release before bumping. A rename fails loudly at the `grep`, by design.

## Architecture

The site renders via the **Congo theme module** — there is no hand-built
`baseof.html`/`list.html`/`single.html`/`header.html`/`footer.html` or inlined `assets/css/main.css` in this repo
anymore; those were deleted when the site moved off the original hand-built layout. Congo's own templates, partials, and
CSS (pulled in as a Hugo Module) drive the shell, list pages, single pages, taxonomy terms, and homepage. What remains
locally is configuration and the one supported theme-extension point:

| File | Purpose |
|------|---------|
| `Makefile` | Primary task interface: `run-site`, `build-site`, `new-post` (prepends today's date to `TITLE`), `check-post-names`, `clean`, `preflight`, `help` |
| `go.mod` / `go.sum` | Pin the Congo theme as a Hugo Module at the upstream release tag `v2.14.0` — see Theme Management below |
| `LICENSE` | Proprietary, all-rights-reserved — not Apache 2.0. The written content is the asset here, not open-source code, so this repo deliberately departs from this org's usual public-repo licensing default |
| `config/_default/` | **All site configuration.** Congo expects its config split across this directory rather than a single root `hugo.toml`; there is no root `hugo.toml` in this repo — see the file-by-file breakdown below |
| `layouts/_partials/favicons.html` | Congo's supported icon override point. Generates the favicon / apple-touch-icon / android-chrome PNG derivatives from `assets/images/aerie-icon.webp` **and emits three `<link>` tags** (16x16, 32x32, apple-touch-icon) — defining this partial *replaces* Congo's default icon tags rather than adding to them, which is what keeps the hrefs from duplicating |
| `static/favicon.ico` | A real multi-size ICO overriding Congo's blank placeholder at the same path — see Icon Overrides below |
| `content/_index.md` | Homepage frontmatter (title only). The homepage body comes from Congo's `profile` home layout: the site title plus `params.author.headline` (the tagline), then the recent-articles list |
| `archetypes/default.md` | Frontmatter template for `hugo new`. Strips the `YYYY-MM-DD-` prefix off the filename into both `title:` and `slug:`, so a dated filename yields an undated title and URL |
| `layouts/robots.txt` | Congo's supported robots.txt override point (module ships its own template at the same relative path). Emits the site's AI-crawler policy — see Robots.txt / AI-Crawler Policy below. Requires `enableRobotsTXT = true` in `hugo.toml` or Hugo never renders it |
| `scripts/migrate-wordpress.py` | **HISTORICAL — do not re-run.** The one-time WordPress→Hugo migration, completed 2026-07-18. It emits WordPress-era conventions (explicit `slug:` fields, flat `static/images/` paths, excerpt-derived descriptions) that the site has since abandoned; re-running it would reintroduce them and overwrite hand-written descriptions. Kept for the record only |
| `content/posts/YYYY-MM-DD-<slug>/` | **Page bundles.** Posts that carry images are directories: `index.md` plus the image files alongside it, referenced bundle-relatively as `{{< figure src="<file>" >}}`. Posts without images stay as flat `content/posts/YYYY-MM-DD-<slug>.md`. The date prefix is filing only — the URL comes from `slug:` (see Post filenames and URLs above). Post/page images live in bundles, not `static/` — the only thing in `static/` is `favicon.ico` (see Icon Overrides below) |
| `BEATS.md` | The list of topics the weekly Cowork idea generator researches — one `## ` heading per beat, `(paused)` in a heading skips it, bullets under it are hints. This is the whole hand-editable configuration surface for that job; see Idea Pipeline below |
| `content/ideas/` | The idea queue that job writes into — never published. `_index.md` sets `cascade: draft: true` over the whole section; see Idea Pipeline below |
| `.github/dependabot.yml` | Weekly `gomod` + `github-actions` update checks. The `gomod` entry is what bumps the Congo theme pin (`go.mod`), since the theme is consumed as a Hugo Module; the `github-actions` entry bumps the SHA-pinned actions in `deploy.yml` — see Deployment below |

### Configuration layout

Congo reads its configuration from `config/_default/*.toml`, and **which file a key lives in matters** — Congo ships its
own `config/_default/` inside the module, merged in at lower priority, so a key placed in the wrong file can be silently
overridden by the theme's default.

| File | Holds |
|------|-------|
| `config/_default/hugo.toml` | Core Hugo settings: `baseURL`, `defaultContentLanguage`, `[taxonomies]` (`tag`/`category` — the URLs depend on these), `[pagination]` `pagerSize = 20`, `[outputs] home = ["HTML", "RSS", "JSON"]` (the search index, see Search below), `[privacy] [privacy.youtube] privacyEnhanced = true` (makes the built-in `{{< youtube >}}` shortcode, used only by `content/posts/2025-04-05-superman-sneak-peek.md`, emit `youtube-nocookie.com` instead of `www.youtube.com`), and the `[module]` block importing Congo. No explicit `mounts` — Congo's default mounts are used as-is (see Icon Overrides below for why) |
| `config/_default/languages.en.toml` | `title = "The Aerie"`, `locale`/`label`/`direction`, `params.description`, `params.mainSections`, `params.author.headline` (the tagline), and `params.author.links` (the profile block's social icons — Instagram, Flickr, GitHub, RSS, see Social Links below) |
| `config/_default/params.toml` | Congo's theme parameters: appearance, `enableSearch`, `[header]`, `[footer]`, `[homepage]`, `[article]`, `[list]`, `[taxonomy]` |
| `config/_default/menus.en.toml` | The main menu. In a `menus.<lang>.toml` file the menu name is the **top-level** key, so entries are `[[main]]`, not `[[menu.main]]` as they would be in `hugo.toml` |

Three traps worth knowing:

- **The site title must be set in `languages.en.toml`, not `hugo.toml`.** Congo's bundled `languages.en.toml` sets
  `title = "Congo"`. A language-level title outranks a site-level one, so putting the title in `hugo.toml` leaves the
  site rendering as "Congo".
- **Congo has no `tagline` parameter.** The tagline reaches the page through the `profile` homepage layout, which
  renders `params.author.headline` as an `<h2>` under the site title. `params.author.name` is deliberately left unset so
  that `<h1>` falls back to the site title; `article.showAuthor` is `false` to avoid an empty byline as a result.
- **Congo's `static/` is mounted normally — its placeholder icons are overridden at the file level, not excluded.**
  Congo ships seven placeholder files at root-level paths (`favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`,
  `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`, `site.webmanifest`) meant to be
  overridden by a site's own `static/`. **A project-level `static/` file wins over a module's file at the same path** —
  this site relies on that instead of excluding Congo's `static/` mount outright, which is what an earlier version of
  this config did via an explicit `[[module.imports.mounts]]` list naming every *other* Congo directory. That approach
  was fragile: declaring any mounts for a module replaces *all* of its defaults, so the list had to be re-checked
  against Congo's tree on every pin bump, and any directory Congo added later would silently go unmounted. See **Icon
  Overrides** below for how the six icon files are covered; `site.webmanifest` is the one placeholder left as Congo's
  own, since nothing links to it (see below).

**Customizing the theme is done through Congo's extension points** — `layouts/_partials/favicons.html` (icons),
`extend-head.html`, `extend-footer.html`, `extend-article-link.html`, `comments.html`, and the `home/<layout>.html` /
`header/<layout>.html` hooks. Note the hyphens: Congo uses `extend-head.html`, *not* PaperMod's `extend_head.html`, and
a file under the wrong name is simply never called. See the theme's own `layouts/_partials/` for the full list. Do
**not** customize by copying/forking theme files into `layouts/` — forking a theme template shadows it permanently and
stops receiving upstream fixes to that file.

### Icon Overrides

Every icon path Congo's `static/` ships is overridden by an Aerie-branded file at the same path, so nothing published
under those six paths is Congo's placeholder:

| Path | Source |
|------|--------|
| `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png` | Generated at build time in `layouts/_partials/favicons.html` from `assets/images/aerie-icon.webp` via `resources.Get` + `.Resize` + `resources.Copy` |
| `favicon.ico` | Committed as a static file, `static/favicon.ico` — Hugo resource pipelines can't emit multi-size `.ico`, so it's pre-generated and checked in rather than built |

Only the first three of the five generated PNGs get a `<link>` tag (16x16, 32x32, apple-touch-icon) — the two
`android-chrome-*` sizes are published purely to occupy those paths with the Aerie icon instead of Congo's placeholder;
nothing references them, since Android home-screen icons are normally declared via a web manifest this site doesn't
ship. Note: `resources.Copy` alone does not publish a resource to `public/` — only accessing
`.Permalink`/`.RelPermalink` on the result does, so the android-chrome lines in `favicons.html` force that access via a
discarded `$`-assignment rather than piping straight into an unwrapped action (which would print the value into the page
as stray text).

`site.webmanifest` is the one Congo placeholder left un-overridden — nothing emits a `<link rel="manifest">`, so it's an
inert orphan file (still bearing Congo's name/colors) rather than a rendered branding leak.

To regenerate `static/favicon.ico` after the master image changes:

```bash
magick assets/images/aerie-icon.webp -define icon:auto-resize=48,32,16 static/favicon.ico
```

(ImageMagick, `/opt/homebrew/bin/magick` on this machine, is a one-time authoring-time dependency only — the committed
`.ico` is what ships, and CI never runs ImageMagick.)

This works because **a project-level `static/` file overrides a module's file at the same path** — Congo's `static/`
mount stays enabled (`hugo.toml` declares no explicit `[[module.imports.mounts]]`, so all of Congo's default mounts,
including `static`, apply), and per-path overrides replace only the conflicting files rather than needing every other
Congo directory re-declared to exclude `static` wholesale.

### Search

Search is enabled via `enableSearch = true` in `params.toml`. That alone wires up the header search button and the
search modal (`header/basic.html` auto-adds a search button when no menu entry declares `action = "search"`, so
`menus.en.toml` needs no change) — but the search index itself requires `[outputs] home = ["HTML", "RSS", "JSON"]` in
`hugo.toml`. Congo's own module config declares that same `[outputs]` block, but it is **not** inherited: structured
(non-map) keys like `[outputs]` don't merge from the theme module into a site's own `hugo.toml` once that file exists,
so the block must be restated here or `public/index.json` (the search index the modal fetches client-side) never gets
built.

### Robots.txt / AI-Crawler Policy

`layouts/robots.txt` renders the site's `robots.txt`, enabled by `enableRobotsTXT = true` in `hugo.toml` — without that
setting Hugo emits no robots.txt at all, regardless of the template's presence. The file lives at the top-level
`layouts/robots.txt`, not `static/robots.txt` and not `layouts/_default/`: that's the exact relative path Congo's own
module uses for its default robots.txt, so a site-level file at that same path overrides it, the same override mechanism
used elsewhere in this repo (see Icon Overrides). The sitemap line is templated as `{{ "sitemap.xml" | absURL }}` rather
than hardcoded.

**The policy blocks AI/LLM training crawlers but deliberately allows retrieval and AI-search crawlers** (`ChatGPT-User`,
`Claude-User`, `Perplexity-User`, `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, and similar). Retrieval/search
bots fetch a page on behalf of a human asking a question and the resulting answer cites and links back — the same value
exchange as a conventional search engine — whereas training crawlers ingest content into model weights with no
attribution or referral traffic back to the site. **This asymmetry is the whole point of the file — do not "tighten" it
by moving the retrieval/search bots into the training-crawler `Disallow` group**; doing so would just remove this blog
from AI answers where it would otherwise be credited, without stopping any training.

A few details worth not re-litigating:

- Blocking `Google-Extended` / `Applebot-Extended` does **not** affect Google Search or Apple's search products — per
  both vendors' own documentation, these are training-use-control tokens layered on the existing Googlebot/Applebot
  crawl, not separate crawlers, so disallowing them has no effect on search inclusion or ranking.
- The deprecated tokens `anthropic-ai`, `Claude-Web`, and `cohere-ai` are deliberately excluded, not overlooked —
  they're superseded (by `ClaudeBot`/`Claude-User`/`Claude-SearchBot` and `cohere-training-data-crawler` respectively)
  and the file documents this inline so a future audit doesn't "helpfully" re-add them.
- robots.txt is voluntary, and GitHub Pages serves static files with no way to add custom response headers (no
  `X-Robots-Tag`), so there's no server-side enforcement behind it. Bytespider, Perplexity's undeclared crawlers, and
  xAI's crawlers are documented as ignoring robots.txt regardless of what it says. Treat this file as a statement of
  intent, not a fence.

The template's own comments carry the full bot list and reasoning inline — this section only records the parts that
would otherwise get silently reverted.

### Social Links

The homepage profile block's row of social icons comes from `params.author.links` in `languages.en.toml` — an array of
single-key tables keyed by icon name (`{ instagram = "..." }`, etc.), rendered by Congo's `author-links.html` partial.
The icon key must match a filename under Congo's `assets/icons/` exactly, or the link silently renders nothing (no build
error). That partial emits the URL verbatim (`{{ $url | safeURL }}`, no `relURL`/`absURL`), so a config value can't be
made baseURL-subpath-aware the way template-authored hrefs elsewhere in this repo are — the RSS entry is therefore a
hardcoded absolute URL matching the current `baseURL` (`https://brosnahan.org/index.xml`), not a bare `/index.xml`
(which would 404). Update it if `baseURL` ever changes again.

## Theme Management

Congo is consumed as a **Hugo Module**, not a git submodule or vendored theme — `go.mod` requires
`github.com/jpanther/congo/v2`, and `config/_default/hugo.toml`'s `[[module.imports]]` pulls it into the build.

Update the pin with:

```bash
hugo mod get -u github.com/jpanther/congo/v2
```

**The pin is a real release tag: `v2.14.0`.** `go.mod` should read `github.com/jpanther/congo/v2 v2.14.0` — a semver
tag, not a `v0.0.0-<date>-<hash>` pseudo-version. If a `hugo mod get -u` ever leaves a pseudo-version there, that's a
regression to fix, not the intended state.

**PaperMod was evaluated first and rejected — do not re-litigate this.** The site briefly ran on
[PaperMod](https://github.com/adityatelange/hugo-PaperMod) and was moved off it on 2026-07-18 for one reason: **PaperMod
cannot be pinned to a release tag.** Its newest release, v8.0 (Nov 2024), predates Hugo v0.146's template-system rewrite
and fails to build on Hugo 0.164 (`partial ... _funcs/get-page-images not found`); the fix landed on `master` but has
never been tagged, and PaperMod's tags are not valid semver besides. Running it therefore required pinning a bare
upstream commit indefinitely. Congo has proper semver tags, builds clean on Hugo 0.164, and has an active upstream, so
the pin is a supported release rather than an arbitrary commit. Switching back to PaperMod would reintroduce the
unpinnable-theme problem.

**CI requires Go.** Because Hugo Modules resolve at build time via `go`, `.github/workflows/deploy.yml` runs
`actions/setup-go` before the Hugo build step. Removing that step breaks the deploy — the themed build succeeds locally
only because Go is already on this machine's `PATH`.

## Idea Pipeline (weekly Cowork job)

Blog topic prompts are generated weekly by a **Claude Cowork scheduled task named "Weekly blog ideas — AerieWebsite"**,
which runs **every Monday at 7:00 AM Pacific**. It is a *device* task: it requires this Mac (Claude Desktop, macOS) and
works through `device_bash`, with the repo mounted at `$HOME/mnt/AerieWebsite` rather than at its real path. It is set
to auto-approve.

**It also gets run by hand**, so new files can appear in `content/ideas/` on any day of the week. Ideas arriving
off-schedule are normal and are not a sign the trigger is misconfigured.

**The task itself lives in Cowork, not in this repo.** It cannot be grepped, diffed, reviewed, or version-controlled
from a checkout, and nothing here will fail if its instructions drift — so a change to how ideas are generated is an
edit in the Cowork UI, not a commit. What *is* in the repo is its input (`BEATS.md`) and its output (`content/ideas/`).

Each run:

1. Re-reads `BEATS.md` — every `## ` heading is one beat, headings containing `(paused)` are skipped, bullets under a
   beat are hints rather than requirements. It never assumes last week's beats and it never edits this file, so
   `BEATS.md` is safe to hand-edit at any time and is the intended way to steer the job.
2. Reads the filenames in `content/posts/` and `content/ideas/` so it doesn't hand over an idea that already exists or
   was already suggested.
3. Web-searches each beat for items from roughly the past one to two weeks. Every idea must be grounded in a real,
   current, linkable item — no evergreen filler. A beat with nothing fresh is skipped, and the slot goes to a beat that
   does have something.
4. Writes **exactly 5** files into `content/ideas/`, named `YYYY-MM-DD-short-slug.md`.
5. Ends with a one-line-per-idea summary plus a note on any beat it skipped and why.

### What the job will not do

These are constraints in its instructions, and code or docs here shouldn't assume otherwise:

- **It runs no git commands.** New ideas land as untracked files in the working tree; committing them (or not) is a
  manual decision. Nothing in `content/ideas/` is precious — they are disposable prompts, regenerated weekly, and
  deleting or ignoring a batch costs nothing. Only `_index.md` is structural.
- **It writes nothing outside `content/ideas/`** — in particular it does not touch `BEATS.md`, config, or
  `content/posts/`.
- **It does not delete.** Superseded batches are moved into `content/ideas/_previous/` instead, because the task cannot
  reliably get deletions authorized — see below.
- **It does not build.** `hugo` and `go` are not installed in the device shell, so the job can't validate its own output
  by rendering the site.

### Idea file format

Idea frontmatter matches a post's, plus one extra key:

```yaml
---
title: "..."
date: <RFC3339, Pacific offset>
lastmod: <same>
description: "short fragment, no period, no URLs"
tags: [...]
categories: ["..."]
draft: true
beat: "<the beat heading it came from>"
---
```

`beat:` is **provenance only** — it is not a Hugo or Congo parameter and nothing renders it. The body is `## Prompt` /
`## Why now` / `## Angles` / `## Links`, plus a `## Prior art on this site` section listing repo-relative paths when the
idea is a genuine follow-up to an existing post.

Note that the description convention documented under Commands above is **restated inside the Cowork task's own
instructions**, since the task can't read this file's rules by reference. If that convention ever changes here, it has
to be changed there too or the generated ideas will quietly drift from house style.

### `content/ideas/_previous/` — the job archives, it does not delete

Old idea batches are **moved into `content/ideas/_previous/` rather than deleted**. This is a workaround, not a design
choice: the Cowork task has trouble getting deletions authorized, so it moves files instead. Do not "fix" the
accumulation by wiring deletion back into the task — the authorization problem is what put the directory there in the
first place. Pruning it by hand, whenever it gets noisy, is fine and expected.

**The underscore does nothing on its own.** Hugo has no convention of ignoring `_`-prefixed directories — that is
Jekyll. Hugo treats `_previous/` as an ordinary part of the `ideas` section: its files are real pages with real
permalinks (`/ideas/_previous/<slug>/`), and `hugo list drafts` shows them. They stay unpublished for exactly one reason
— the section's `cascade: draft: true` reaches them like any other descendant. If that cascade were ever removed, this
directory would publish along with everything else.

### Why nothing in `content/ideas/` can publish

Two independent mechanisms, and both are load-bearing enough to leave alone:

- `content/ideas/_index.md` sets `cascade: draft: true`, so every page in the section is a draft regardless of its own
  frontmatter — and the production build (`hugo --gc --minify`, no `-D`) drops drafts.
- `params.mainSections = ["posts"]` in `config/_default/languages.en.toml` keeps the section out of the homepage list,
  the RSS feed, and Congo's article listings.

`make run-site` uses `-D`, so ideas *are* visible in local preview — that's the point.

### Promoting an idea to a post

Move the file to `content/posts/` (or a bundle directory if it will carry images). The idea's `YYYY-MM-DD-<slug>.md`
name is already the right shape, but **re-date it to the post's publication date** — the generated name carries the date
the *idea* was produced, which is rarely when the post ships.

Then: add a `slug:` field (this is what sets the URL — the date prefix never reaches it, see *Post filenames and URLs*
above), flip `draft` to `false`, drop the `beat:` key, and delete the `## Prompt` / `## Why now` / `## Angles` /
`## Links` / `## Prior art` scaffolding. Rewrite `description:` for the finished post — the generated one describes the
*idea*, not the piece.

## Content Migration

The WordPress→Hugo content migration from the live brosnahan.org site is complete: 14 posts, the `who-am-i` page body →
`content/about.md`, and 8 original images. `content/photography.md` was migrated by hand, separately from the script.
**`scripts/migrate-wordpress.py` is historical and must not be re-run** — see the architecture table above.

### URL scheme: Hugo defaults (WordPress parity abandoned 2026-07-18)

The site uses **Hugo's default permalinks**. The config carries no `[permalinks]` block, no `[permalinks.term]` block,
and no `capitalizeListTitles` override:

| Content | URL |
|---------|-----|
| Posts | `/posts/<slug>/` |
| Tags | `/tags/<slug>/` |
| Categories | `/categories/<slug>/` |
| Pages | `/about/`, `/photography/` |

The owner **deliberately abandoned WordPress URL parity on 2026-07-18** and accepted the breakage. These old WordPress
URLs now 404: dated post permalinks (`/YYYY/MM/DD/<slug>/`), singular term paths (`/tag/<slug>/`, `/category/<slug>/`),
`/who-am-i/`, date archives (`/YYYY/MM/`), and `/feed/`.

**Post filenames are `YYYY-MM-DD-<slug>.md`, and every post carries an explicit `slug:` field** — see *Post filenames
and URLs* under Commands above. The date is a filing prefix only; `slug:` is what sets the URL, so
`content/posts/2025-04-23-ai-2027.md` publishes at `/posts/ai-2027/`. **To change a post's URL, edit its `slug:`** —
renaming the file changes only how it sorts on disk.

This reverses an earlier rule that posts should carry no `slug:` field. That rule was written against
`scripts/migrate-wordpress.py`, which emitted `slug:` values that merely restated the filename and were therefore pure
redundancy. Under dated filenames the field does real work: it is the only thing keeping the date out of the URL. A
`slug:` that restates the *undated* part of the filename is expected and correct now, not the redundancy the old rule
warned about. The trailing-punctuation hazard the old rule also guarded against is still handled, since the slug is
still authored rather than derived from the title: the SB 63 post's trailing period cannot leak into its URL.

**Taxonomy names are authored in their proper display form** (`SVBC`, `ECRR2025`, `Door Lock`, `AI`, `UPS`,
`Public Transit`), and Hugo urlizes them down to unchanged slugs (`svbc`, `ecrr2025`, `door-lock`, …). This is what lets
`capitalizeListTitles` stay at its default: Hugo's title caser only uppercases each word's first rune and leaves the
rest alone, so acronyms survive intact rather than becoming "Svbc". **Author new tags in display form** — a lowercase
tag would render lowercase in headings.

**Decisions made:**

- **Images** live in **page bundles**: a post with images is a directory (`content/posts/YYYY-MM-DD-<slug>/index.md`)
  with its images beside it, referenced bundle-relatively (`{{< figure src="<file>" >}}`). Two posts carry images
  (`2025-05-31-cities-moving`, 3; `2026-04-13-i-got-tired-of-changing-batteries`, 5). Post/page media does not use
  `static/`. Media pulled from WordPress was the ORIGINAL files, not the resized/`.avif` derivatives.
- **Embeds:** one post (`2025-04-05-superman-sneak-peek`) contained a YouTube iframe, converted to Hugo's built-in
  `{{< youtube >}}` shortcode. Figures use the built-in `{{< figure >}}` shortcode. Both avoid needing
  `markup.goldmark.renderer.unsafe`.
- **RSS** lands at Hugo's `/index.xml`, not WordPress's `/feed/` — that URL was not preserved. The owner has decided not
  to add a `/feed/` alias: existing subscribers at that URL will 404, accepted.
- **Favicon** is sourced from WordPress's site-icon crop, `cropped-aerie_icon.webp` (512x512), not the uncropped
  1024x1024 `aerie_icon.webp` upload, whose framing (more padding around the circle) differs. The 512 master is stored
  as `assets/images/aerie-icon.webp` and **remains the single source for every icon on the site** — see Icon Overrides
  above for how it drives every published icon path, including the committed `static/favicon.ico`.
- **Date archives** (`/YYYY/MM/`) are NOT generated. Hugo has no built-in date-archive generation;
  `GroupByDate`/`GroupByPublishDate` group posts inside a template but don't emit pages at those URLs. Reproducing them
  would require a generated stub page per month with a `url:` frontmatter override, plus a new stub every future month —
  rejected as ongoing maintenance for URLs with negligible inbound links.
- **Excluded content:** the post at `/2025/04/01/__trashed/` was a WordPress deleted-post artifact and was NOT migrated.
  14 posts migrated, not 15.
- **`Uncategorized` category retained.** It was originally dropped as a WordPress default placeholder, then restored to
  preserve `/category/uncategorized/`. That parity rationale is now moot — the URL is `/categories/uncategorized/` and
  the old one 404s — but the category is kept as-is; its two posts (`hello-sf`, `what-topics`) carry
  `categories: ["Uncategorized"]`. Dropping it is now a plain content edit to those two files, not a script setting.
- **All 14 posts' `description:` values are hand-written**, not derived from WordPress's auto-excerpts, and follow the
  description convention documented under Commands → Authoring loop above. **Durable warning:**
  `scripts/migrate-wordpress.py` regenerates descriptions from the WordPress excerpt and would **destroy** this
  hand-written text. This is one of the reasons that script must never be re-run.

## Deployment

Push to `main` → GitHub Actions builds with Hugo and deploys to GitHub Pages. A pull request against `main` also
triggers the same workflow, but builds only — `Setup Pages`, `Upload artifact`, and the `deploy` job itself are all
`if: github.event_name != 'pull_request'`, so a PR run never publishes anything and runs with narrower permissions
(`contents: read` only; `pages: write`/`id-token: write` are scoped to the `deploy` job, which PR runs never reach). One
behavioral difference worth knowing: a PR build validates against `config/_default/hugo.toml`'s own `baseURL`, not the
Pages-provided one — `Setup Pages` is skipped on PRs (there's nothing to configure Pages access for), so its `base_url`
output would be empty, and the PR build step omits `--baseURL` entirely rather than pass that empty value through.
Workflow at `.github/workflows/deploy.yml`.

The GitHub Pages custom domain is `brosnahan.org`, set via `static/CNAME` (containing `brosnahan.org`) plus the domain
configured in repo Settings → Pages — both are required; doing only one of the two leaves the site unreachable.
`config/_default/hugo.toml` declares `baseURL = "https://brosnahan.org/"`. `deploy.yml` still passes
`--baseURL "${{ steps.pages.outputs.base_url }}/"`, which supersedes whatever the config says at build time regardless,
and now resolves to the custom domain since it's set in Settings → Pages.

### Supply-Chain Posture (`deploy.yml`)

- **The Hugo `.deb` download is checksum-verified** against Hugo's own published `hugo_${HUGO_VERSION}_checksums.txt`
  before `dpkg -i` runs — `wget` alone gives no integrity check. **`set -euo pipefail` in that step is kept for
  portability, not because a live bypass was found on CI:** GitHub Actions runs `run:` blocks as `bash -e` without
  `pipefail`, so a pipeline's exit status is only the last command's, and a bare `grep ... | sha256sum -c -` with no
  match depends on which `sha256sum` is running — GNU coreutils 9.4 (what `ubuntu-latest` ships) exits 1 on empty stdin,
  so the runner actually used by this workflow fails correctly without the fix; macOS's Darwin `sha256sum` exits 0 on
  empty stdin, which is a real bypass, just not on this platform. The fix extracts the matched checksum line to a file
  first, removing the implementation dependency and making a no-match fail at `grep` with a clear locus rather than
  depending on `sha256sum`'s empty-input behavior. One known rough edge: `grep` prints nothing on no-match, so that
  failure mode is silent (fails closed, no diagnostic message) — accepted rather than fixed.
- **All five actions are pinned to a commit SHA**, each with a trailing `# vN` comment so Dependabot can still parse and
  bump the version despite the pin.
- **`persist-credentials: false` on the checkout step** — nothing in the job pushes, so the `GITHUB_TOKEN` doesn't need
  to stay in `.git/config` for the rest of the job.

## DNS and Email

`brosnahan.org` is registered at **Namecheap**, and DNS is hosted there too, via Namecheap's free **BasicDNS** service
(nameservers `dns1.registrar-servers.com` / `dns2.registrar-servers.com`) — registrar and DNS host are the same account,
so there is no separate provider to keep in sync when records change. Registry expiry is **2027-07-24**; the domain
carries `clientTransferProhibited` (transfer-locked), which is Namecheap's default anti-hijacking posture rather than
something turned on deliberately for this project.

There is no DNSSEC and no CAA record on the zone, both left off on purpose. A CAA record would restrict certificate
issuance to a single named CA, but the marginal security benefit for a personal blog is small, and a misconfigured CAA
record is a well-documented way to silently break a host's *automatic* certificate renewal — a real risk given how this
site's own certificate provisioning has already behaved once (see below), so the tradeoff wasn't judged worth it.

### Web Records

DNS points the domain at GitHub Pages using GitHub's documented apex-plus-`www` pattern:

| Record | Value |
|--------|-------|
| `brosnahan.org` A | 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 |
| `brosnahan.org` AAAA | 2606:50c0:8000::153, 2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153 |
| `www` CNAME | `nbrosnahan.github.io` |

`www` is not a second copy of the site — it resolves through GitHub's own redirect to whichever domain is configured as
canonical in Settings → Pages, which here is the apex. Live behavior is two redirects, both expected: `http://` → 301 →
`https://`, and `www.brosnahan.org` → 301 → `brosnahan.org`. HTTPS enforcement is a checkbox in repo Settings → Pages;
the certificate itself is issued by Let's Encrypt and renews automatically once provisioned — see the next section for
what reaching "provisioned" actually took.

### Certificate Provisioning: GitHub Gives No Retry Button

**GitHub only begins Let's Encrypt provisioning once the custom domain is set in Settings → Pages *and* DNS already
resolves to GitHub** — there is no API call or UI control to request or retry issuance on demand; the domain field
itself is the only lever. That matters because provisioning can stall with no diagnosable cause: on this domain the
certificate sat in state `authorization_created` for **over three hours** with DNS fully correct, no CAA record blocking
anything, and the domain already showing as verified. Nothing about that state changed on its own, and there was nothing
to poll or nudge to move it along.

**The only remedy that worked was removing and re-adding the custom domain**, which restarts provisioning from scratch:

```bash
gh api repos/nbrosnahan/AerieWebsite/pages -X PUT -f cname=""
gh api repos/nbrosnahan/AerieWebsite/pages -X PUT -f cname="brosnahan.org"
```

(equivalently, clearing and retyping the domain in Settings → Pages). That produced an issued certificate within
minutes, after three hours of the previous attempt going nowhere. Check current state with:

```bash
gh api repos/nbrosnahan/AerieWebsite/pages
```

and read `https_certificate.state` — `authorization_created` means still pending; wait for `approved`, the terminal
success state and the only one `https_enforced` can be set from. An absent/null `https_certificate` is a different
problem, not a stall: it means provisioning hasn't started at all, usually because DNS isn't resolving to GitHub yet or
the domain isn't actually set.

`https_enforced` cannot be set until the certificate actually exists: requesting enforcement too early gets a 404
(`The certificate does not exist yet`) from the API. Once the certificate is issued, set it with:

```bash
gh api repos/nbrosnahan/AerieWebsite/pages -X PUT -F https_enforced=true
```

**Note the `-F`, not `-f`.** `-F` sends a real JSON boolean; `-f` sends the literal string `"true"`, which the API
rejects with a 422.

**Enabling HTTPS enforcement is not the last step — one more deploy is required afterward.** `deploy.yml` passes
`--baseURL "${{ steps.pages.outputs.base_url }}/"` to `hugo`, and that Pages API value only flips from `http://` to
`https://` once enforcement is turned on. Every URL a build generated before that point — canonical links, RSS entries,
the sitemap — still says `http://` until a *subsequent* workflow run picks up the now-`https://` value. Trigger a
rebuild (any push to `main`) after flipping enforcement rather than assuming the already-deployed site updates itself.

### Email — Receive-only Forwarding

The domain receives mail but sends none — there is no mailbox, no SMTP submission, nothing capable of originating mail
*as* `brosnahan.org`. MX records point at Namecheap's free email-forwarding service:

| Priority | Host |
|----------|------|
| 10 | eforward1.registrar-servers.com |
| 10 | eforward2.registrar-servers.com |
| 10 | eforward3.registrar-servers.com |
| 15 | eforward4.registrar-servers.com |
| 20 | eforward5.registrar-servers.com |

Two aliases are configured: `hello@brosnahan.org`, the published contact address linked from the homepage profile block
(the `email` entry in `params.author.links`, see Social Links above), and `dmarc-reports@brosnahan.org`, which exists
solely to receive DMARC aggregate reports (see Mail Authentication below). Both forward to a personal inbox; neither is
a real mailbox anyone logs into.

**The catch-all is deliberately left off — only these two explicit aliases exist.** A catch-all accepts mail for every
guessed local part (`info@`, `admin@`, `sales@`, …), so dictionary-attack spam forwards through at no cost to the
sender; with the catch-all off, mail to an unconfigured address simply bounces at the MX. This is also what makes
`hello@` genuinely disposable: if it starts attracting spam it can be deleted and replaced with a freshly named alias,
which is the entire reason a personal address isn't published directly in the first place.

### Mail Authentication (SPF / DKIM / DMARC)

SPF is a single TXT record: `v=spf1 include:spf.efwd.registrar-servers.com ~all`, authorizing Namecheap's forwarding
infrastructure and costing 1 of SPF's 10 permitted DNS lookups.

**Never publish two SPF records on this zone.** It briefly carried both this record and a stale
`include:spf.web-hosting.com` entry left behind by the retired WordPress cPanel host. Two SPF TXT records for one domain
is a `permerror` under RFC 7208, not "the stricter of the two wins" — the practical effect is that SPF can never pass
for the domain at all until the duplicate is removed.

There is no DKIM signing key. An orphaned `default._domainkey` record, another leftover from the old cPanel host, was
removed; nothing on this domain signs outbound mail, which is consistent with the domain not sending any.

DMARC is a `_dmarc` TXT record:
`v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s; rua=mailto:dmarc-reports@brosnahan.org`. `p=reject` is safe
specifically *because* the domain sends no mail of its own — there is no legitimate outbound traffic for a strict policy
to accidentally catch, so the policy only serves to make the domain unattractive to spoof. `ruf` (per-message failure
reports) is deliberately omitted, since major receivers stopped honoring it years ago over the privacy implications of
forwarding full message samples to a third party; the `fo` and `rf` tags were dropped along with it, since both only
configure failure-report behavior. `pct` and `ri` were left out as restatements of their own defaults (100% and 86400s),
not because they're unsupported.

As an inbound caveat rather than a misconfiguration: because the MX is a forwarder, other senders' own SPF technically
breaks in transit — the envelope sender Namecheap re-emits to the personal inbox isn't the original sender's domain.
Namecheap compensates with SRS (Sender Rewriting Scheme), and DKIM signatures usually survive forwarding intact, so most
mail is unaffected — but mail from a handful of unusually strict senders may occasionally get filtered on the receiving
end. That's a property of forwarding generally, not something wrong with this domain's setup.

### If This Domain Ever Needs to Send Mail

**Gmail's "send as" feature will not work with this configuration, and it will look like it should work.** Consumer
Gmail sets the envelope sender to the underlying `@gmail.com` address and DKIM-signs outgoing mail with `d=gmail.com` —
neither SPF nor DKIM ends up aligned to `brosnahan.org`, which is exactly what `adkim=s`/`aspf=s` (strict alignment)
plus `p=reject` exist to catch. Mail sent that way gets refused, not quarantined.

Adding `include:_spf.google.com` to the SPF record is necessary if Gmail is ever used to send as this domain, but **it
is not sufficient by itself** — it authorizes Google's sending IPs, but authorization isn't alignment, and DMARC under
strict alignment checks alignment, not mere authorization.

Actually sending as `hello@brosnahan.org` requires a mail host that DKIM-signs outbound mail with `d=brosnahan.org` —
Fastmail, Migadu, Zoho, and Google Workspace (the paid product, not consumer Gmail) all qualify; consumer Gmail's free
"send mail as" does not, regardless of any SPF change. The safe sequence, if this is ever done: drop DMARC to `p=none`
first, stand up the new mail host, confirm SPF/DKIM alignment is actually passing in the aggregate reports arriving at
`dmarc-reports@brosnahan.org`, and only then move the policy back to `p=reject`. Going straight to send-as while
`p=reject` is still published means the very first message bounces.
