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

**Decisions:**
- Cleared the GitHub Pages custom domain deliberately, ahead of the content migration rather than after: brosnahan.org is currently a live WordPress 7.0.2 site with 15 posts on non-GitHub hosting, so cutting over DNS before the migration would take that site offline with nothing to replace it. Publishing to the default `nbrosnahan.github.io/AerieWebsite/` URL first lets the GitHub Pages pipeline be verified end-to-end before the cutover.
- Switched `archetypes/default.md` to `draft: true` by default so the authoring loop (`make new-post` → `make run-site` → flip `draft: false` → push) has a safe default; new posts no longer accidentally ship live.
- Outstanding for a future session: the WordPress→Hugo migration of the 15 existing posts from brosnahan.org, writing a real `hugo.toml` meta description (current one is a placeholder), and the DNS cutover itself (repoint brosnahan.org at GitHub Pages, restore `static/CNAME` with `brosnahan.org`, re-set the custom domain in repo Settings → Pages — both steps are required together, per the note now in `CLAUDE.md`).
