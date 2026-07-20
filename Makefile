.DEFAULT_GOAL := help

.PHONY: help build-site run-site new-post clean preflight

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
	hugo new posts/$(TITLE).md

clean: ## Remove public/ and resources/_gen
	rm -rf public resources/_gen

preflight: ## Pre-merge gate: clean + build-site (skip with SKIP_PREFLIGHT=1)
	@if [ "$(SKIP_PREFLIGHT)" = "1" ]; then \
		echo "SKIP_PREFLIGHT=1 set; skipping preflight."; \
	else \
		$(MAKE) clean; \
		$(MAKE) build-site; \
	fi
