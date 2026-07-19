# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Hugo static site for [brosnahan.org](https://brosnahan.org), built on the [Congo](https://github.com/jpanther/congo) theme, consumed as a Hugo Module. No npm; the only build tooling beyond Hugo itself is Go, which Hugo needs on `PATH` to resolve the theme module (see Theme Management below).

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

The site renders via the **Congo theme module** — there is no hand-built `baseof.html`/`list.html`/`single.html`/`header.html`/`footer.html` or inlined `assets/css/main.css` in this repo anymore; those were deleted when the site moved off the original hand-built layout. Congo's own templates, partials, and CSS (pulled in as a Hugo Module) drive the shell, list pages, single pages, taxonomy terms, and homepage. What remains locally is configuration and the one supported theme-extension point:

| File | Purpose |
|------|---------|
| `Makefile` | Primary task interface: `run-site`, `build-site`, `new-post`, `clean`, `preflight`, `help` |
| `go.mod` / `go.sum` | Pin the Congo theme as a Hugo Module at the upstream release tag `v2.14.0` — see Theme Management below |
| `config/_default/` | **All site configuration.** Congo expects its config split across this directory rather than a single root `hugo.toml`; there is no root `hugo.toml` in this repo — see the file-by-file breakdown below |
| `layouts/_partials/favicons.html` | Congo's supported icon override point. Generates the favicon / apple-touch-icon / android-chrome PNG derivatives from `assets/images/aerie-icon.webp` **and emits three `<link>` tags** (16x16, 32x32, apple-touch-icon) — defining this partial *replaces* Congo's default icon tags rather than adding to them, which is what keeps the hrefs from duplicating |
| `static/favicon.ico` | A real multi-size ICO overriding Congo's blank placeholder at the same path — see Icon Overrides below |
| `content/_index.md` | Homepage frontmatter (title only). The homepage body comes from Congo's `profile` home layout: the site title plus `params.author.headline` (the tagline), then the recent-articles list |
| `archetypes/default.md` | Frontmatter template for `hugo new` (title, date, lastmod, description, tags, categories, draft) |
| `layouts/robots.txt` | Congo's supported robots.txt override point (module ships its own template at the same relative path). Emits the site's AI-crawler policy — see Robots.txt / AI-Crawler Policy below. Requires `enableRobotsTXT = true` in `hugo.toml` or Hugo never renders it |
| `scripts/migrate-wordpress.py` | **HISTORICAL — do not re-run.** The one-time WordPress→Hugo migration, completed 2026-07-18. It emits WordPress-era conventions (explicit `slug:` fields, flat `static/images/` paths, excerpt-derived descriptions) that the site has since abandoned; re-running it would reintroduce them and overwrite hand-written descriptions. Kept for the record only |
| `content/posts/<slug>/` | **Page bundles.** Posts that carry images are directories: `index.md` plus the image files alongside it, referenced bundle-relatively as `{{< figure src="<file>" >}}`. Posts without images stay as flat `content/posts/<slug>.md`. Post/page images live in bundles, not `static/` — the only thing in `static/` is `favicon.ico` (see Icon Overrides below) |

### Configuration layout

Congo reads its configuration from `config/_default/*.toml`, and **which file a key lives in matters** — Congo ships its own `config/_default/` inside the module, merged in at lower priority, so a key placed in the wrong file can be silently overridden by the theme's default.

| File | Holds |
|------|-------|
| `config/_default/hugo.toml` | Core Hugo settings: `baseURL`, `defaultContentLanguage`, `[taxonomies]` (`tag`/`category` — the URLs depend on these), `[pagination]` `pagerSize = 20`, `[outputs] home = ["HTML", "RSS", "JSON"]` (the search index, see Search below), and the `[module]` block importing Congo. No explicit `mounts` — Congo's default mounts are used as-is (see Icon Overrides below for why) |
| `config/_default/languages.en.toml` | `title = "The Aerie"`, `locale`/`label`/`direction`, `params.description`, `params.mainSections`, `params.author.headline` (the tagline), and `params.author.links` (the profile block's social icons — Instagram, Flickr, GitHub, RSS, see Social Links below) |
| `config/_default/params.toml` | Congo's theme parameters: appearance, `enableSearch`, `[header]`, `[footer]`, `[homepage]`, `[article]`, `[list]`, `[taxonomy]` |
| `config/_default/menus.en.toml` | The main menu. In a `menus.<lang>.toml` file the menu name is the **top-level** key, so entries are `[[main]]`, not `[[menu.main]]` as they would be in `hugo.toml` |

Three traps worth knowing:

- **The site title must be set in `languages.en.toml`, not `hugo.toml`.** Congo's bundled `languages.en.toml` sets `title = "Congo"`. A language-level title outranks a site-level one, so putting the title in `hugo.toml` leaves the site rendering as "Congo".
- **Congo has no `tagline` parameter.** The tagline reaches the page through the `profile` homepage layout, which renders `params.author.headline` as an `<h2>` under the site title. `params.author.name` is deliberately left unset so that `<h1>` falls back to the site title; `article.showAuthor` is `false` to avoid an empty byline as a result.
- **Congo's `static/` is mounted normally — its placeholder icons are overridden at the file level, not excluded.** Congo ships seven placeholder files at root-level paths (`favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`, `site.webmanifest`) meant to be overridden by a site's own `static/`. **A project-level `static/` file wins over a module's file at the same path** — this site relies on that instead of excluding Congo's `static/` mount outright, which is what an earlier version of this config did via an explicit `[[module.imports.mounts]]` list naming every *other* Congo directory. That approach was fragile: declaring any mounts for a module replaces *all* of its defaults, so the list had to be re-checked against Congo's tree on every pin bump, and any directory Congo added later would silently go unmounted. See **Icon Overrides** below for how the six icon files are covered; `site.webmanifest` is the one placeholder left as Congo's own, since nothing links to it (see below).

**Customizing the theme is done through Congo's extension points** — `layouts/_partials/favicons.html` (icons), `extend-head.html`, `extend-footer.html`, `extend-article-link.html`, `comments.html`, and the `home/<layout>.html` / `header/<layout>.html` hooks. Note the hyphens: Congo uses `extend-head.html`, *not* PaperMod's `extend_head.html`, and a file under the wrong name is simply never called. See the theme's own `layouts/_partials/` for the full list. Do **not** customize by copying/forking theme files into `layouts/` — forking a theme template shadows it permanently and stops receiving upstream fixes to that file.

### Icon Overrides

Every icon path Congo's `static/` ships is overridden by an Aerie-branded file at the same path, so nothing published under those six paths is Congo's placeholder:

| Path | Source |
|------|--------|
| `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png` | Generated at build time in `layouts/_partials/favicons.html` from `assets/images/aerie-icon.webp` via `resources.Get` + `.Resize` + `resources.Copy` |
| `favicon.ico` | Committed as a static file, `static/favicon.ico` — Hugo resource pipelines can't emit multi-size `.ico`, so it's pre-generated and checked in rather than built |

Only the first three of the five generated PNGs get a `<link>` tag (16x16, 32x32, apple-touch-icon) — the two `android-chrome-*` sizes are published purely to occupy those paths with the Aerie icon instead of Congo's placeholder; nothing references them, since Android home-screen icons are normally declared via a web manifest this site doesn't ship. Note: `resources.Copy` alone does not publish a resource to `public/` — only accessing `.Permalink`/`.RelPermalink` on the result does, so the android-chrome lines in `favicons.html` force that access via a discarded `$`-assignment rather than piping straight into an unwrapped action (which would print the value into the page as stray text).

`site.webmanifest` is the one Congo placeholder left un-overridden — nothing emits a `<link rel="manifest">`, so it's an inert orphan file (still bearing Congo's name/colors) rather than a rendered branding leak.

To regenerate `static/favicon.ico` after the master image changes:

```bash
magick assets/images/aerie-icon.webp -define icon:auto-resize=48,32,16 static/favicon.ico
```

(ImageMagick, `/opt/homebrew/bin/magick` on this machine, is a one-time authoring-time dependency only — the committed `.ico` is what ships, and CI never runs ImageMagick.)

This works because **a project-level `static/` file overrides a module's file at the same path** — Congo's `static/` mount stays enabled (`hugo.toml` declares no explicit `[[module.imports.mounts]]`, so all of Congo's default mounts, including `static`, apply), and per-path overrides replace only the conflicting files rather than needing every other Congo directory re-declared to exclude `static` wholesale.

### Search

Search is enabled via `enableSearch = true` in `params.toml`. That alone wires up the header search button and the search modal (`header/basic.html` auto-adds a search button when no menu entry declares `action = "search"`, so `menus.en.toml` needs no change) — but the search index itself requires `[outputs] home = ["HTML", "RSS", "JSON"]` in `hugo.toml`. Congo's own module config declares that same `[outputs]` block, but it is **not** inherited: structured (non-map) keys like `[outputs]` don't merge from the theme module into a site's own `hugo.toml` once that file exists, so the block must be restated here or `public/index.json` (the search index the modal fetches client-side) never gets built.

### Robots.txt / AI-Crawler Policy

`layouts/robots.txt` renders the site's `robots.txt`, enabled by `enableRobotsTXT = true` in `hugo.toml` — without that setting Hugo emits no robots.txt at all, regardless of the template's presence. The file lives at the top-level `layouts/robots.txt`, not `static/robots.txt` and not `layouts/_default/`: that's the exact relative path Congo's own module uses for its default robots.txt, so a site-level file at that same path overrides it, the same override mechanism used elsewhere in this repo (see Icon Overrides). The sitemap line is templated as `{{ "sitemap.xml" | absURL }}` rather than hardcoded.

**The policy blocks AI/LLM training crawlers but deliberately allows retrieval and AI-search crawlers** (`ChatGPT-User`, `Claude-User`, `Perplexity-User`, `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, and similar). Retrieval/search bots fetch a page on behalf of a human asking a question and the resulting answer cites and links back — the same value exchange as a conventional search engine — whereas training crawlers ingest content into model weights with no attribution or referral traffic back to the site. **This asymmetry is the whole point of the file — do not "tighten" it by moving the retrieval/search bots into the training-crawler `Disallow` group**; doing so would just remove this blog from AI answers where it would otherwise be credited, without stopping any training.

A few details worth not re-litigating:
- Blocking `Google-Extended` / `Applebot-Extended` does **not** affect Google Search or Apple's search products — per both vendors' own documentation, these are training-use-control tokens layered on the existing Googlebot/Applebot crawl, not separate crawlers, so disallowing them has no effect on search inclusion or ranking.
- The deprecated tokens `anthropic-ai`, `Claude-Web`, and `cohere-ai` are deliberately excluded, not overlooked — they're superseded (by `ClaudeBot`/`Claude-User`/`Claude-SearchBot` and `cohere-training-data-crawler` respectively) and the file documents this inline so a future audit doesn't "helpfully" re-add them.
- robots.txt is voluntary, and GitHub Pages serves static files with no way to add custom response headers (no `X-Robots-Tag`), so there's no server-side enforcement behind it. Bytespider, Perplexity's undeclared crawlers, and xAI's crawlers are documented as ignoring robots.txt regardless of what it says. Treat this file as a statement of intent, not a fence.

The template's own comments carry the full bot list and reasoning inline — this section only records the parts that would otherwise get silently reverted.

### Social Links

The homepage profile block's row of social icons comes from `params.author.links` in `languages.en.toml` — an array of single-key tables keyed by icon name (`{ instagram = "..." }`, etc.), rendered by Congo's `author-links.html` partial. The icon key must match a filename under Congo's `assets/icons/` exactly, or the link silently renders nothing (no build error). That partial emits the URL verbatim (`{{ $url | safeURL }}`, no `relURL`/`absURL`), so a config value can't be made baseURL-subpath-aware the way template-authored hrefs elsewhere in this repo are — the RSS entry is therefore a hardcoded absolute URL matching the current `baseURL` (`https://brosnahan.org/index.xml`), not a bare `/index.xml` (which would 404). Update it if `baseURL` ever changes again.

## Theme Management

Congo is consumed as a **Hugo Module**, not a git submodule or vendored theme — `go.mod` requires `github.com/jpanther/congo/v2`, and `config/_default/hugo.toml`'s `[[module.imports]]` pulls it into the build.

Update the pin with:

```bash
hugo mod get -u github.com/jpanther/congo/v2
```

**The pin is a real release tag: `v2.14.0`.** `go.mod` should read `github.com/jpanther/congo/v2 v2.14.0` — a semver tag, not a `v0.0.0-<date>-<hash>` pseudo-version. If a `hugo mod get -u` ever leaves a pseudo-version there, that's a regression to fix, not the intended state.

**PaperMod was evaluated first and rejected — do not re-litigate this.** The site briefly ran on [PaperMod](https://github.com/adityatelange/hugo-PaperMod) and was moved off it on 2026-07-18 for one reason: **PaperMod cannot be pinned to a release tag.** Its newest release, v8.0 (Nov 2024), predates Hugo v0.146's template-system rewrite and fails to build on Hugo 0.164 (`partial ... _funcs/get-page-images not found`); the fix landed on `master` but has never been tagged, and PaperMod's tags are not valid semver besides. Running it therefore required pinning a bare upstream commit indefinitely. Congo has proper semver tags, builds clean on Hugo 0.164, and has an active upstream, so the pin is a supported release rather than an arbitrary commit. Switching back to PaperMod would reintroduce the unpinnable-theme problem.

**CI requires Go.** Because Hugo Modules resolve at build time via `go`, `.github/workflows/deploy.yml` runs `actions/setup-go` before the Hugo build step. Removing that step breaks the deploy — the themed build succeeds locally only because Go is already on this machine's `PATH`.

## Content Migration

The WordPress→Hugo content migration from the live brosnahan.org site is complete: 14 posts, the `who-am-i` page body → `content/about.md`, and 8 original images. `content/photography.md` was migrated by hand, separately from the script. **`scripts/migrate-wordpress.py` is historical and must not be re-run** — see the architecture table above.

### URL scheme: Hugo defaults (WordPress parity abandoned 2026-07-18)

The site uses **Hugo's default permalinks**. The config carries no `[permalinks]` block, no `[permalinks.term]` block, and no `capitalizeListTitles` override:

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
- **Images** live in **page bundles**: a post with images is a directory (`content/posts/<slug>/index.md`) with its images beside it, referenced bundle-relatively (`{{< figure src="<file>" >}}`). Two posts carry images (`cities-moving`, 3; `i-got-tired-of-changing-batteries`, 5). Post/page media does not use `static/`. Media pulled from WordPress was the ORIGINAL files, not the resized/`.avif` derivatives.
- **Embeds:** one post (`superman-sneak-peek`) contained a YouTube iframe, converted to Hugo's built-in `{{< youtube >}}` shortcode. Figures use the built-in `{{< figure >}}` shortcode. Both avoid needing `markup.goldmark.renderer.unsafe`.
- **RSS** lands at Hugo's `/index.xml`, not WordPress's `/feed/` — that URL was not preserved. The owner has decided not to add a `/feed/` alias: existing subscribers at that URL will 404, accepted.
- **Favicon** is sourced from WordPress's site-icon crop, `cropped-aerie_icon.webp` (512x512), not the uncropped 1024x1024 `aerie_icon.webp` upload, whose framing (more padding around the circle) differs. The 512 master is stored as `assets/images/aerie-icon.webp` and **remains the single source for every icon on the site** — see Icon Overrides above for how it drives every published icon path, including the committed `static/favicon.ico`.
- **Date archives** (`/YYYY/MM/`) are NOT generated. Hugo has no built-in date-archive generation; `GroupByDate`/`GroupByPublishDate` group posts inside a template but don't emit pages at those URLs. Reproducing them would require a generated stub page per month with a `url:` frontmatter override, plus a new stub every future month — rejected as ongoing maintenance for URLs with negligible inbound links.
- **Excluded content:** the post at `/2025/04/01/__trashed/` was a WordPress deleted-post artifact and was NOT migrated. 14 posts migrated, not 15.
- **`Uncategorized` category retained.** It was originally dropped as a WordPress default placeholder, then restored to preserve `/category/uncategorized/`. That parity rationale is now moot — the URL is `/categories/uncategorized/` and the old one 404s — but the category is kept as-is; its two posts (`hello-sf`, `what-topics`) carry `categories: ["Uncategorized"]`. Dropping it is now a plain content edit to those two files, not a script setting.
- **All 14 posts' `description:` values are hand-written**, not derived from WordPress's auto-excerpts, and follow the description convention documented under Commands → Authoring loop above. **Durable warning:** `scripts/migrate-wordpress.py` regenerates descriptions from the WordPress excerpt and would **destroy** this hand-written text. This is one of the reasons that script must never be re-run.

## Deployment

Push to `main` → GitHub Actions builds with Hugo and deploys to GitHub Pages. Workflow at `.github/workflows/deploy.yml`.

The GitHub Pages custom domain is `brosnahan.org`, set via `static/CNAME` (containing `brosnahan.org`) plus the domain configured in repo Settings → Pages — both are required; doing only one of the two leaves the site unreachable. `config/_default/hugo.toml` declares `baseURL = "https://brosnahan.org/"`. `deploy.yml` still passes `--baseURL "${{ steps.pages.outputs.base_url }}/"`, which supersedes whatever the config says at build time regardless, and now resolves to the custom domain since it's set in Settings → Pages.

## DNS and Email

`brosnahan.org` is registered at **Namecheap**, and DNS is hosted there too, via Namecheap's free **BasicDNS** service (nameservers `dns1.registrar-servers.com` / `dns2.registrar-servers.com`) — registrar and DNS host are the same account, so there is no separate provider to keep in sync when records change. Registry expiry is **2027-07-24**; the domain carries `clientTransferProhibited` (transfer-locked), which is Namecheap's default anti-hijacking posture rather than something turned on deliberately for this project.

There is no DNSSEC and no CAA record on the zone, both left off on purpose. A CAA record would restrict certificate issuance to a single named CA, but the marginal security benefit for a personal blog is small, and a misconfigured CAA record is a well-documented way to silently break a host's *automatic* certificate renewal — a real risk given how this site's own certificate provisioning has already behaved once (see below), so the tradeoff wasn't judged worth it.

### Web Records

DNS points the domain at GitHub Pages using GitHub's documented apex-plus-`www` pattern:

| Record | Value |
|--------|-------|
| `brosnahan.org` A | 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 |
| `brosnahan.org` AAAA | 2606:50c0:8000::153, 2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153 |
| `www` CNAME | `nbrosnahan.github.io` |

`www` is not a second copy of the site — it resolves through GitHub's own redirect to whichever domain is configured as canonical in Settings → Pages, which here is the apex. Live behavior is two redirects, both expected: `http://` → 301 → `https://`, and `www.brosnahan.org` → 301 → `brosnahan.org`. HTTPS enforcement is a checkbox in repo Settings → Pages; the certificate itself is issued by Let's Encrypt and renews automatically once provisioned — see the next section for what reaching "provisioned" actually took.

### Certificate Provisioning: GitHub Gives No Retry Button

**GitHub only begins Let's Encrypt provisioning once the custom domain is set in Settings → Pages *and* DNS already resolves to GitHub** — there is no API call or UI control to request or retry issuance on demand; the domain field itself is the only lever. That matters because provisioning can stall with no diagnosable cause: on this domain the certificate sat in state `authorization_created` for **over three hours** with DNS fully correct, no CAA record blocking anything, and the domain already showing as verified. Nothing about that state changed on its own, and there was nothing to poll or nudge to move it along.

**The only remedy that worked was removing and re-adding the custom domain**, which restarts provisioning from scratch:

```bash
gh api repos/nbrosnahan/AerieWebsite/pages -X PUT -f cname=""
gh api repos/nbrosnahan/AerieWebsite/pages -X PUT -f cname="brosnahan.org"
```

(equivalently, clearing and retyping the domain in Settings → Pages). That produced an issued certificate within minutes, after three hours of the previous attempt going nowhere. Check current state with:

```bash
gh api repos/nbrosnahan/AerieWebsite/pages
```

and read `https_certificate.state` — `authorization_created` means still pending; wait for `approved`, the terminal success state and the only one `https_enforced` can be set from. An absent/null `https_certificate` is a different problem, not a stall: it means provisioning hasn't started at all, usually because DNS isn't resolving to GitHub yet or the domain isn't actually set.

`https_enforced` cannot be set until the certificate actually exists: requesting enforcement too early gets a 404 (`The certificate does not exist yet`) from the API. Once the certificate is issued, set it with:

```bash
gh api repos/nbrosnahan/AerieWebsite/pages -X PUT -F https_enforced=true
```

**Note the `-F`, not `-f`.** `-F` sends a real JSON boolean; `-f` sends the literal string `"true"`, which the API rejects with a 422.

**Enabling HTTPS enforcement is not the last step — one more deploy is required afterward.** `deploy.yml` passes `--baseURL "${{ steps.pages.outputs.base_url }}/"` to `hugo`, and that Pages API value only flips from `http://` to `https://` once enforcement is turned on. Every URL a build generated before that point — canonical links, RSS entries, the sitemap — still says `http://` until a *subsequent* workflow run picks up the now-`https://` value. Trigger a rebuild (any push to `main`) after flipping enforcement rather than assuming the already-deployed site updates itself.

### Email — Receive-only Forwarding

The domain receives mail but sends none — there is no mailbox, no SMTP submission, nothing capable of originating mail *as* `brosnahan.org`. MX records point at Namecheap's free email-forwarding service:

| Priority | Host |
|----------|------|
| 10 | eforward1.registrar-servers.com |
| 10 | eforward2.registrar-servers.com |
| 10 | eforward3.registrar-servers.com |
| 15 | eforward4.registrar-servers.com |
| 20 | eforward5.registrar-servers.com |

Two aliases are configured: `hello@brosnahan.org`, the published contact address linked from the homepage profile block (the `email` entry in `params.author.links`, see Social Links above), and `dmarc-reports@brosnahan.org`, which exists solely to receive DMARC aggregate reports (see Mail Authentication below). Both forward to a personal inbox; neither is a real mailbox anyone logs into.

**The catch-all is deliberately left off — only these two explicit aliases exist.** A catch-all accepts mail for every guessed local part (`info@`, `admin@`, `sales@`, …), so dictionary-attack spam forwards through at no cost to the sender; with the catch-all off, mail to an unconfigured address simply bounces at the MX. This is also what makes `hello@` genuinely disposable: if it starts attracting spam it can be deleted and replaced with a freshly named alias, which is the entire reason a personal address isn't published directly in the first place.

### Mail Authentication (SPF / DKIM / DMARC)

SPF is a single TXT record: `v=spf1 include:spf.efwd.registrar-servers.com ~all`, authorizing Namecheap's forwarding infrastructure and costing 1 of SPF's 10 permitted DNS lookups.

**Never publish two SPF records on this zone.** It briefly carried both this record and a stale `include:spf.web-hosting.com` entry left behind by the retired WordPress cPanel host. Two SPF TXT records for one domain is a `permerror` under RFC 7208, not "the stricter of the two wins" — the practical effect is that SPF can never pass for the domain at all until the duplicate is removed.

There is no DKIM signing key. An orphaned `default._domainkey` record, another leftover from the old cPanel host, was removed; nothing on this domain signs outbound mail, which is consistent with the domain not sending any.

DMARC is a `_dmarc` TXT record: `v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s; rua=mailto:dmarc-reports@brosnahan.org`. `p=reject` is safe specifically *because* the domain sends no mail of its own — there is no legitimate outbound traffic for a strict policy to accidentally catch, so the policy only serves to make the domain unattractive to spoof. `ruf` (per-message failure reports) is deliberately omitted, since major receivers stopped honoring it years ago over the privacy implications of forwarding full message samples to a third party; the `fo` and `rf` tags were dropped along with it, since both only configure failure-report behavior. `pct` and `ri` were left out as restatements of their own defaults (100% and 86400s), not because they're unsupported.

As an inbound caveat rather than a misconfiguration: because the MX is a forwarder, other senders' own SPF technically breaks in transit — the envelope sender Namecheap re-emits to the personal inbox isn't the original sender's domain. Namecheap compensates with SRS (Sender Rewriting Scheme), and DKIM signatures usually survive forwarding intact, so most mail is unaffected — but mail from a handful of unusually strict senders may occasionally get filtered on the receiving end. That's a property of forwarding generally, not something wrong with this domain's setup.

### If This Domain Ever Needs to Send Mail

**Gmail's "send as" feature will not work with this configuration, and it will look like it should work.** Consumer Gmail sets the envelope sender to the underlying `@gmail.com` address and DKIM-signs outgoing mail with `d=gmail.com` — neither SPF nor DKIM ends up aligned to `brosnahan.org`, which is exactly what `adkim=s`/`aspf=s` (strict alignment) plus `p=reject` exist to catch. Mail sent that way gets refused, not quarantined.

Adding `include:_spf.google.com` to the SPF record is necessary if Gmail is ever used to send as this domain, but **it is not sufficient by itself** — it authorizes Google's sending IPs, but authorization isn't alignment, and DMARC under strict alignment checks alignment, not mere authorization.

Actually sending as `hello@brosnahan.org` requires a mail host that DKIM-signs outbound mail with `d=brosnahan.org` — Fastmail, Migadu, Zoho, and Google Workspace (the paid product, not consumer Gmail) all qualify; consumer Gmail's free "send mail as" does not, regardless of any SPF change. The safe sequence, if this is ever done: drop DMARC to `p=none` first, stand up the new mail host, confirm SPF/DKIM alignment is actually passing in the aggregate reports arriving at `dmarc-reports@brosnahan.org`, and only then move the policy back to `p=reject`. Going straight to send-as while `p=reject` is still published means the very first message bounces.
