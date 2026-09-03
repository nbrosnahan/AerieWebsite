.DEFAULT_GOAL := help

.PHONY: help build-site run-site new-post check-post-names clean preflight lint-markdown lint-markdown-fix

MARKDOWNLINT_CONFIG := $(HOME)/.claude/.markdownlint-cli2.jsonc

help: ## Print available targets with one-line descriptions
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

build-site: ## Production build (hugo --gc --minify) into public/
	hugo --gc --minify

# NOTE: run-site deliberately does NOT depend on build-site, unlike the
# usual run-<platform> convention. `hugo server` builds in memory and
# watches for changes; a preceding `hugo --minify` would only produce a
# stale public/ directory that the server ignores.
#
# -D includes drafts, so local preview intentionally differs from what
# deploys: .github/workflows/deploy.yml runs plain `hugo --minify`, so
# drafts stay unpublished on the live site.
#
# --baseURL http://localhost:1313/ overrides config/_default/hugo.toml's
# production baseURL, which is the custom domain https://brosnahan.org/.
# Without this override, `hugo server` inherits that production domain and
# serves everything with links pointed at brosnahan.org instead of
# localhost, so the polling loop and Safari below would be pointed at the
# wrong host. The explicit localhost root pins the local dev server to
# localhost rather than the production domain.
run-site: ## Serve with drafts + live navigation, open in Safari once ready
	@echo "Starting Hugo server (drafts enabled) at http://localhost:1313/ ..."
	@( \
		for i in $$(seq 1 15); do \
			if curl -fs -o /dev/null http://localhost:1313/; then \
				open -a Safari http://localhost:1313/; \
				exit 0; \
			fi; \
			sleep 1; \
		done; \
		echo "Warning: server did not respond after 15 attempts; not opening Safari." >&2 \
	) & \
	hugo server -D --navigateToChanged --baseURL http://localhost:1313/

new-post: ## Create a new post from the archetype (TITLE=<slug> required)
	@if [ -z "$(TITLE)" ]; then \
		echo "Usage: make new-post TITLE=<slug>"; \
		echo "  Example: make new-post TITLE=my-first-post"; \
		exit 1; \
	fi
	@# Posts are filed under content/posts/<YYYY>/YYYY-MM-DD-<slug>.md -- the
	@# year directory is on-disk filing only (no _index.md, so it is not a
	@# Hugo section) and the date is only a filing prefix within it: the
	@# archetype strips both back off into the slug: field, and
	@# config/_default/hugo.toml's [permalinks.page] block strips the year
	@# back out of the URL, so the URL stays /posts/<slug>/. Pass TITLE
	@# without a date. `hugo new` creates the year directory on its own.
	hugo new posts/$$(date +%Y)/$$(date +%F)-$(TITLE).md

# Guards the content/posts/<YYYY>/YYYY-MM-DD-<slug> layout. It needs
# guarding because nothing else catches a violation: `hugo new
# posts/<year>/<name>.md` with an undated name or a mismatched year
# produces a perfectly valid post (the archetype only STRIPS a date
# prefix, it cannot add one, and it has no idea which directory it was
# invoked under), new posts are draft: true so a build never renders
# them, and once published the slug: field means the URL is correct
# regardless. Only `make new-post` applies the convention, so this is
# what makes it hold for files created any other way.
#
# _index.md is the section list page, not a post, and is exempt at the
# top level of content/posts/ -- but forbidden inside a year directory:
# an _index.md there promotes that directory to a real Hugo section
# (config/_default/hugo.toml's [permalinks.page] block strips the year
# back out of a post's URL, but that only works because the year
# directory is otherwise just a path segment, not a section). A section
# would generate /posts/<year>/ archive pages and make Congo's list.html
# render .Pages as year links instead of posts -- so this is checked
# explicitly, not left to fall out of the other rules.
check-post-names: ## Verify every post lives at content/posts/<YYYY>/YYYY-MM-DD-<slug>, with no _index.md in a year dir
	@status=0; \
	bad_top=$$(find content/posts -mindepth 1 -maxdepth 1 \
		! -name '_index.md' \
		! -name '[0-9][0-9][0-9][0-9]' \
		-print); \
	if [ -n "$$bad_top" ]; then \
		echo "ERROR: content/posts/ may only contain _index.md and YYYY year directories:" >&2; \
		echo "$$bad_top" | sed 's/^/  /' >&2; \
		status=1; \
	fi; \
	for yeardir in content/posts/[0-9][0-9][0-9][0-9]; do \
		[ -d "$$yeardir" ] || continue; \
		year=$$(basename "$$yeardir"); \
		if [ -e "$$yeardir/_index.md" ]; then \
			echo "ERROR: $$yeardir/_index.md is forbidden -- an _index.md inside a year directory promotes it to a real Hugo section, generating /posts/$$year/ archive pages and making Congo's list.html render year links instead of posts." >&2; \
			status=1; \
		fi; \
		for entry in $$(find "$$yeardir" -mindepth 1 -maxdepth 1 ! -name '_index.md' -print); do \
			name=$$(basename "$$entry"); \
			case "$$name" in \
				[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*) \
					entryyear=$${name%%-*}; \
					if [ "$$entryyear" != "$$year" ]; then \
						echo "ERROR: $$entry's date prefix ($$entryyear) does not match its year directory ($$year)" >&2; \
						status=1; \
					fi ;; \
				*) \
					echo "ERROR: $$entry does not match YYYY-MM-DD-<slug>" >&2; \
					status=1 ;; \
			esac; \
		done; \
	done; \
	if [ "$$status" -ne 0 ]; then \
		echo "" >&2; \
		echo "Create posts with: make new-post TITLE=<slug>" >&2; \
		exit 1; \
	fi
	@echo "Post filenames OK."

clean: ## Remove public/ and resources/_gen
	rm -rf public resources/_gen

lint-markdown: ## Lint every Markdown file — zero warnings required
	markdownlint-cli2 --config $(MARKDOWNLINT_CONFIG) 'content/**/*.md' '!content/ideas/_previous/**'

lint-markdown-fix: ## Auto-fix fixable Markdown issues (rewrites files in place)
	markdownlint-cli2 --fix --config $(MARKDOWNLINT_CONFIG) 'content/**/*.md' '!content/ideas/_previous/**'

# The steps are chained with && rather than ;. With ; a failing step only
# prints its error and preflight carries on, exiting 0 on the strength of
# whatever ran last -- the gate would report success while a check had
# actually failed. Verified before the fix: check-post-names failing still
# let build-site run and preflight still passed. Keep the && chain.
preflight: ## Pre-merge gate: clean + check-post-names + build-site (skip with SKIP_PREFLIGHT=1)
	@if [ "$(SKIP_PREFLIGHT)" = "1" ]; then \
		echo "SKIP_PREFLIGHT=1 set; skipping preflight."; \
	else \
		$(MAKE) clean && \
		$(MAKE) check-post-names && \
		$(MAKE) build-site && \
		$(MAKE) lint-markdown; \
	fi
