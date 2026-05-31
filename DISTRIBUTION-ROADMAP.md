# Distribution Roadmap

Private Markdown Converter is evolving into a **desktop-installed local web app**:

- users install it like a normal desktop app
- the app starts a local service on `localhost`
- the UI opens in the browser
- files stay on the user's machine
- saved passwords stay in the user's OS credential store

This is intentionally different from a hosted SaaS product. The privacy model remains local-first.

## v1 distribution target

Ship a downloadable macOS release for non-technical users with:

- a double-clickable launcher
- a stop app
- no Python, `venv`, or `pip` steps required for end users
- local-only file processing
- Keychain-backed saved password profiles

## Packaging strategy

### Runtime model

- Keep the current browser UI + local engine architecture
- Keep the current Streamlit runtime for v1 distribution
- Bundle Python, dependencies, and launcher assets into a user-installable package

### User-facing deliverables

- macOS app bundle(s)
- installer-friendly distribution artifact such as DMG
- first-run onboarding
- launch and stop controls without Terminal

### Platform order

1. macOS first
2. Optional Windows follow-up if demand justifies replacing macOS Keychain assumptions with a cross-platform credential-store strategy

## Security model that must not change

- No cloud uploads
- No persisted original documents
- No persisted decrypted PDFs
- No persisted Markdown content
- No passwords in SQLite
- Saved passwords stay in the local OS credential store
- Temp cleanup remains mandatory on startup and after conversion

## Short-term implementation work

### Release hardening

- Make launcher packaging reliable across clean machines
- Add first-run environment validation for:
  - local writable data directory
  - temp cleanup access
  - browser launch
  - credential-store access
- Add versioned release notes and upgrade instructions

### Install experience

- Replace repo-clone setup for end users with a packaged download flow
- Reduce or eliminate Gatekeeper friction through signing and notarization when ready
- Validate launch after OS reboot and repeat launch behavior

### Operational basics

- Define a release process for building, smoke testing, and publishing app bundles
- Add safe crash diagnostics that exclude document content, passwords, and Markdown output
- Decide how app updates will be communicated before adding auto-update behavior

## Mid-term evolution

- Add update checks or auto-update support
- Add import/export for non-sensitive settings if needed
- Consider replacing Streamlit with a dedicated local frontend + backend only if product UX or packaging constraints justify the cost

## Explicit non-goals for this distribution path

- Hosted SaaS as the first release model
- Server-side file processing
- Multi-user auth
- Team workspaces
- Cloud content storage
- API-first architecture

## Release readiness criteria

A public downloadable release is ready when:

- a non-technical user can install and launch it without Terminal
- encrypted PDF conversion works in the packaged app
- saved password profiles work in the packaged app
- no sensitive content appears in logs or local metadata stores
- repeated launches do not create duplicate servers
- stop behavior is predictable and visible
- upgrade instructions are tested
