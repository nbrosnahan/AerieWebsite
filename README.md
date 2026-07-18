# The Aerie — Website

The official website for [brosnahan.org](https://brosnahan.org).

A minimal, hand-built Hugo blog — no theme, no npm, no build tooling beyond Hugo itself — deployed to GitHub Pages.

## Local Development

Requires Hugo extended v0.164.0+.

```bash
make run-site
```

The site will be available at `http://localhost:1313`. Drafts are enabled locally,
so new posts (`make new-post TITLE=<slug>`), which default to `draft: true`,
are visible in preview but stay out of the production build until the flag
is flipped to `false`.

Run `make help` to list all targets.

## Build

```bash
make build-site
```

Output goes to `./public/`.

## Deployment

Push to `main` — GitHub Actions builds and deploys to GitHub Pages automatically.
