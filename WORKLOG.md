# WORKLOG

## 2026-07-18 — Rebrand to The Aerie, clear placeholder content, prep for blog migration

**Goal:** Rebrand the site from "Tumbling Potato" (tumblingpotato.org) to "The Aerie" (brosnahan.org), rename the repo/directory accordingly, and prepare the codebase to receive a WordPress→Hugo content migration.

**Done:**
- Removed placeholder content: deleted `content/posts/beginnings.md`; cleared the placeholder body of `content/about.md`. `content/posts/` is now empty, staged for a migration of 15 posts from brosnahan.org.
- Rewrote `LICENSE`: copyright now Nick Brosnahan (was "Tumbling Potato"), reworded to be content-focused (writing/posts/images plus templates and styles) rather than software-focused, dropped the software warranty/liability boilerplate. Remains all-rights-reserved, deliberately not open source.
- Bumped the Hugo version pin 0.157.0 → 0.164.0 in `.github/workflows/deploy.yml`; upgraded local Homebrew Hugo to match.
- Config: `languageCode = "en-us"` → `locale = "en-US"` in `hugo.toml` (the `languageCode` key was deprecated in Hugo 0.158.0; `locale` takes an RFC 5646 tag).
- `layouts/_default/baseof.html`: `lang="{{ .Site.Language.Lang }}"` → `lang="{{ .Site.Language.Locale }}"`. `.Lang` returns the language key (`en`) and ignored the locale entirely; verified the rendered output changed from `<html lang=en>` to `<html lang=en-US>`.
- Rebrand: `hugo.toml` title → "The Aerie", tagline → "The stairs are a feature", baseURL → `https://brosnahan.org/`, meta description replaced (currently a generic placeholder pending real copy); `content/_index.md` title → "The Aerie"; `layouts/partials/footer.html` copyright → "Nick Brosnahan".
- Renamed the repo and directory `TPWebsite` → `AerieWebsite`; GitHub repo renamed (remote auto-updated), `to-be-reviewed` topic removed. Project catalog entry renamed `tp-website.md` → `aerie-website.md` with its badly stale "90s under-construction splash page" description rewritten, catalog index reordered alphabetically, and `project-colors.zsh` regenerated (these live in the chezmoi repo, committed separately).
- Added `Makefile` (targets: `help` as default goal, `build-site`, `run-site`, `new-post`, `clean`, `preflight`). `run-site` runs `hugo server -D --navigateToChanged` and opens Safari after polling the port until the server responds.
- `archetypes/default.md`: `draft: false` → `draft: true`, so new posts preview locally via `make run-site` but stay out of the production build until explicitly published. Verified end-to-end: a test draft produced 0 matches in the production build and 5 in the `-D` preview.
- Deleted `static/CNAME` and cleared the GitHub Pages custom domain, so the site currently publishes to `https://nbrosnahan.github.io/AerieWebsite/` — this lets publishing be verified before the DNS cutover.
- Rewrote `README.md` and `CLAUDE.md` — they had still described a 90s "under construction" splash page with Comic Sans, marquee, and a `worker-icon.html` partial, all removed back in commit 8c6eff0 and never documented. Both now describe the actual minimal blog and the `make`-based workflow. `CLAUDE.md`'s architecture table also dropped the `static/CNAME` row (file no longer exists) and the Deployment section now explains the cleared-custom-domain state and the cutover steps.
- Cleared a stale `.git/index.lock` left over from an interrupted operation in April, which had been silently blocking git index writes.
- Nothing in this session was deployed, pushed, or committed to a DNS provider — all changes are local to the working tree.
- Configured Hugo URL parity with WordPress ahead of the content migration: `[permalinks]` for the `/:year/:month/:day/:slug/` post structure, `[permalinks.term]` for the singular `/tag/` and `/category/` segments, a `/who-am-i/` → `/about/` alias, and a new `content/photography.md` preserving `/photography/`. Verified against a probe post.
- Fixed URL generation for the GitHub Pages project subpath: layouts passed leading-slash arguments to `relURL`/`absURL`, which Hugo treats as root-relative, so nav links, tag links, and RSS references would have 404'd at `https://nbrosnahan.github.io/AerieWebsite/`. Nav active-state checks were broken the same way (comparing `.RelPermalink` against hardcoded root paths). Verified correct at both the subpath and root baseURLs, so the cutover needs no further template changes.

**Decisions:**
- Cleared the GitHub Pages custom domain deliberately, ahead of the content migration rather than after: brosnahan.org is currently a live WordPress 7.0.2 site with 15 posts on non-GitHub hosting, so cutting over DNS before the migration would take that site offline with nothing to replace it. Publishing to the default `nbrosnahan.github.io/AerieWebsite/` URL first lets the GitHub Pages pipeline be verified end-to-end before the cutover.
- Switched `archetypes/default.md` to `draft: true` by default so the authoring loop (`make new-post` → `make run-site` → flip `draft: false` → push) has a safe default; new posts no longer accidentally ship live.
- Outstanding for a future session: the WordPress→Hugo migration of the 15 existing posts from brosnahan.org, writing a real `hugo.toml` meta description (current one is a placeholder), and the DNS cutover itself (repoint brosnahan.org at GitHub Pages, restore `static/CNAME` with `brosnahan.org`, re-set the custom domain in repo Settings → Pages — both steps are required together, per the note now in `CLAUDE.md`).
- Images migrate to Hugo-idiomatic paths rather than preserving the `wp-content/uploads/` tree; originals, not WordPress's resized derivatives.
- RSS stays at Hugo's `/index.xml` rather than reproducing WordPress's `/feed/`.
- Date archives are dropped — Hugo has no config-level support, and per-month stub pages were judged not worth the perpetual maintenance for URLs with negligible inbound links.
- The `__trashed` post is excluded from the migration (14 posts, not 15).

## 2026-07-18 — WordPress→Hugo content migration

**Goal:** Migrate the live brosnahan.org WordPress content (posts, the about page, images) into Hugo, per the URL-parity and content decisions recorded in the previous session.

**Done:**
- Wrote `scripts/migrate-wordpress.py` — stdlib-only, no third-party deps, idempotent/re-runnable. Fetches from the live WordPress REST API and writes `content/posts/<slug>.md`, `content/about.md` (body only), and `static/images/<basename>`.
- Migrated 14 posts to `content/posts/<slug>.md`. `content/photography.md` was already migrated by hand in a prior session and was left untouched.
- Migrated the body of WordPress page `who-am-i` (id 14) into `content/about.md`, preserving its existing frontmatter, including the load-bearing `aliases: ["/who-am-i/"]`.
- Migrated 8 original images (full-res PNGs with alpha, JPEGs with intact iPhone EXIF — confirmed not the `.avif` derivatives) into `static/images/`.
- Fixed two bugs the migration surfaced: a trailing-punctuation slug divergence (see Decisions) and adjacent `<em> </em>` + `<em>` spans in WordPress HTML that were converting to malformed markdown — the converter now merges adjacent `<em>` runs and lifts whitespace out of each span.
- Verified: `make preflight` passes (79 pages); all 14 post URLs match the live WordPress `link` field exactly; all 22 in-use tags match `/tag/<slug>/`; `/who-am-i/` alias resolves to `/about/`; no `.avif`, `wp-content`, or raw HTML-entity leakage in `content/` or `public/`.
- Updated `CLAUDE.md`'s Content Migration section from in-progress to completed-state, and added `scripts/migrate-wordpress.py` and `static/images/` to the architecture table.

**Decisions:**
- Every post's frontmatter now carries an explicit `slug:` pinned to the WordPress slug, not left to Hugo's title-derived fallback. Cause: the SB 63 post's title ends in a literal period, and Hugo's slug sanitizer (unlike WordPress's `sanitize_title()`) doesn't strip trailing punctuation, which silently broke URL parity for that post until `slug:` was added. Recorded as a durable note in `CLAUDE.md` since a future title edit could accidentally remove the field.
- `superman-sneak-peek`'s YouTube iframe was converted to Hugo's built-in `{{< youtube >}}` shortcode (figures likewise use `{{< figure >}}`), avoiding the need for `markup.goldmark.renderer.unsafe`. This corrects a prior `CLAUDE.md` claim that the source content had "no embeds," which was wrong.
- Images went to a flat `static/images/` rather than page bundles — only 3 posts carry images (8 total), so a flat tree was cheap and keeps `content/posts/` uniform.
- `uncategorized` (a WordPress default placeholder) was dropped as a real category, with the owner's explicit sign-off that `/category/uncategorized/` will 404 after the DNS cutover.
- **Reversed, later in the day:** the owner asked for `uncategorized` restored, temporarily, preferring URL parity with the live site (`/category/uncategorized/` stays live) over dropping a WordPress default placeholder. Implemented as a single-lever, trivially-reversible change: `hello-sf` and `what-topics` now carry `categories: ["Uncategorized"]`, and `scripts/migrate-wordpress.py`'s `DROP_CATEGORY_SLUGS` constant is empty by default (was `{"uncategorized"}`) so a future re-run doesn't silently diverge from what's on disk.
- Outstanding for a future session: hand-writing real post `description:` values (current ones are WordPress's truncated 55-word auto-excerpts feeding `<meta name="description">`), and the DNS cutover itself (still pending per the prior session's entry).
- All 14 posts' `description:` values were hand-rewritten in this session, closing the item above: each is kept under 160 characters, ends on a complete sentence, and contains no bare URLs. The rewrite also fixed two source-level defects surfaced along the way: `svbcs-2025-el-camino-real-ride`'s WordPress excerpt read "El Camino RealRide" because the excerpt generator joined text across a hard line break in the body, and `sf-is-still-mostly-empty-above-40`'s description was previously a bare truncated URL.

## 2026-07-18 — Drop WordPress-era conventions for Hugo defaults

**Goal:** Strip every WordPress-parity convention from the site and adopt Hugo defaults, accepting the resulting URL breakage. No post text, image, or hand-written description may be lost or altered in the process.

**Done:**
- `hugo.toml`: deleted the `[permalinks]` block (`/:year/:month/:day/:slug/`), the `[permalinks.term]` block (singular `/tag/` and `/category/`), and the `capitalizeListTitles = false` override with its explanatory comment. URLs are now Hugo defaults: `/posts/<slug>/`, `/tags/<slug>/`, `/categories/<slug>/`.
- Removed the explicit `slug:` frontmatter field from all 14 posts. Default permalinks derive the slug from the filename, and every filename already equalled the desired slug, so all 14 post slugs are unchanged.
- Normalized all 22 tag names to proper display form (`cycling` → `Cycling`, `svbc` → `SVBC`, `door lock` → `Door Lock`, `ecrr2025` → `ECRR2025`, …). Verified every normalized name urlizes to its previous slug, so no tag URL moved. Categories were already proper-cased and were left alone.
- Converted the two image-bearing posts to page bundles: `cities-moving` (3 images) and `i-got-tired-of-changing-batteries` (5 images) became `content/posts/<slug>/index.md` with their images alongside, moved via `git mv`. Figure shortcodes rewritten from `src="/images/<file>"` to bundle-relative `src="<file>"`; captions and alt text untouched. `static/` no longer exists.
- Removed `aliases: ["/who-am-i/"]` from `content/about.md`.
- Marked `scripts/migrate-wordpress.py` HISTORICAL — DO NOT RE-RUN with a banner at the top of its module docstring. Its logic is otherwise unmodified.
- Simplified `layouts/partials/header.html`'s Tags active-state check to the `tags/` prefix alone (the `tag/` branch existed only for the singular term URLs).
- Rewrote `CLAUDE.md`'s Content Migration section: the URL-parity table is replaced by a Hugo-defaults URL table plus an explicit note that parity was abandoned and which old URLs now 404; the `slug:` warning is replaced by a statement that slugs come from filenames (so the trailing-punctuation hazard no longer exists) and that renaming the file is how to change a URL; the architecture table's `static/images/` row became a page-bundles row; the migration script row and the `--force`/`uncategorized` bullets now reflect the script being historical. Added a note that restoring the custom domain means recreating `static/` for `CNAME`.

**Verification:**
- `make preflight` passes (81 pages, 8 non-page files, 0 aliases, 0 static files).
- No content lost: rendered body word counts are identical for all 14 posts against a build of `a70328c`, and a word-by-word comparison shows the *only* differences anywhere are the intended tag-label capitalizations. All 14 `description:` values are byte-identical (matching md5 over the full set).
- All 22 tag slugs and 6 category slugs are unchanged; all 14 post slugs match their previous filenames.
- Term page `<h1>`s render correctly at the default `capitalizeListTitles`: `SVBC`, `ECRR2025`, `Door Lock`, `AI`, `UPS`, `DIY`, `SF`, `IoT` all survive intact.
- All 8 images present in a bundle and returning 200; `static/images/` gone with no image orphaned.
- Crawled all 59 internal URLs from `/` on a root-baseURL server: zero 404s. `/who-am-i/`, `/2025/05/31/cities-moving/`, and `/tag/svbc/` correctly 404. Nav highlights on `/tags/` and `/tags/<slug>/` only.

**Decisions:**
- **Normalize taxonomy display names rather than keep `capitalizeListTitles = false`.** The override existed solely so lowercase WordPress-era tag names would render as authored. Authoring the names in display form instead removes the config dependency entirely and is strictly better presentation. This works because Hugo's title caser only uppercases each word's first rune and leaves the remainder alone, so acronyms like `SVBC` and `ECRR2025` are not mangled into `Svbc`. The tradeoff: new tags must now be authored in display form, since a lowercase tag will render lowercase.
- **Archive the migration script rather than update or delete it.** It still documents exactly what was pulled from WordPress and how, which is worth keeping, but it now emits conventions the site has abandoned and would clobber hand-written descriptions. A banner is the cheapest durable guard; updating it to match the new conventions would be maintaining a script that must never run again.
- **Drop the `/who-am-i/` alias** and accept the 404, consistent with abandoning parity everywhere else. Keeping one alias while dated post permalinks and singular term URLs all break would be inconsistent for negligible benefit.
