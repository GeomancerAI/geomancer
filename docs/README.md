# Geomancer Docs Site

This directory contains the static website and support pages for Geomancer. It is a presentation and distribution surface, not the authoritative source for application architecture, backend workflow, or active alpha development priorities.

## Scope

- marketing and landing pages
- download and early-access pages
- support pages such as docs, privacy, and terms
- static assets for the web presence

## Architecture Relationship

- The project source of truth for active product direction is the root [README](../README.md).
- The source of truth for version and milestone history is the root `CHANGELOG.md`.
- The docs site should stay aligned with current alpha messaging, especially the desktop-app direction and alpha-stage status.
- Backend architecture decisions should be documented at the repo root or in dedicated engineering docs, not only here.

## Structure

```text
docs/
  index.html
  download.html
  early-access.html
  docs.html
  privacy.html
  terms.html
  assets/
    css/
    images/
    js/
    icons/
  README.md
```

## Local Preview

Open `index.html` directly in a browser for a quick preview, or serve the folder with a simple local static server if you want normal asset loading behavior.

## Maintenance Notes

- Keep product-status language consistent with the repo root docs.
- If a backend or desktop pass changes public-facing expectations, update this folder only as needed to keep messaging accurate.
- Avoid treating this folder as the engineering source of truth for system behavior.
