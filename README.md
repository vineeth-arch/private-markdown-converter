# Private Markdown Converter

A desktop-installed local web app for macOS that converts documents and password-protected PDFs into clean Markdown. It runs a local service on your machine, opens in the browser on `localhost`, and keeps files on your device.

This is **not yet** a standalone downloadable installer for non-technical users. The current install path still requires local Python setup, dependency installation, and building the `.app` from this repo.

## Privacy principles

- No cloud uploads. All processing happens locally.
- Uploaded files are deleted from `temp/` immediately after conversion.
- Converted Markdown is never stored — download it or it is gone.
- PDF passwords are stored only in macOS Keychain, never in the app database.
- The history log contains filenames and timestamps only. No document content.

## Install the macOS app

**Current requirements:** macOS, Python 3.11+

This app is a **desktop-installed local web app**. You build the app bundle from this repo, install it into `Applications`, and it launches a local browser UI on `http://localhost:8501`.

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd private-markdown-converter
   ```
2. Create the virtual environment:
   ```bash
   python3 -m venv .venv
   ```
3. Activate it:
   ```bash
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Make the launcher and build scripts executable:
   ```bash
   chmod +x launch.sh stop.sh build-app.sh make-icon.sh "Start Private Markdown Converter.command"
   ```
6. Optional: generate a custom app icon from a PNG:
   ```bash
   bash make-icon.sh path/to/your-image.png
   ```
7. Build the macOS app:
   ```bash
   bash build-app.sh
   ```
8. Drag `Private Markdown Converter.app` into your `Applications` folder.
9. First launch only: right-click `Private Markdown Converter.app` and choose `Open`.
10. After that, launch it normally with a single click from `Applications` or the Dock.

Important packaging constraint:
- the `.app` can live in `Applications`
- the project folder itself must stay where it is
- if the project folder moves, rerun `bash build-app.sh` and replace the installed app

## Supported file types

| Type | Extension |
|------|-----------|
| PDF (including password-protected) | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx` |
| HTML | `.html`, `.htm` |
| CSV | `.csv` |
| JSON | `.json` |
| XML | `.xml` |
| EPUB | `.epub` |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp` |
| ZIP | `.zip` (contents converted individually) |

## Launch and use

When you launch `Private Markdown Converter.app`:

- it starts the local service if it is not already running
- it opens your browser to `http://localhost:8501`
- if the app is already running, launching it again should reopen the browser instead of starting a second server

First-launch Gatekeeper note:
- on the first run, macOS may warn that the app is from an unnotarized source
- use right-click -> `Open` once to approve it

## Stop the app

Quit `Private Markdown Converter.app` from the Dock or app menu to stop the local service.

Fallback maintenance path:

```bash
bash stop.sh
```

`stop.sh` is useful if the local service is still running and you want to stop it from Terminal.

## Rebuild after moving or updating the project

Rerun this whenever you move the project folder or want a fresh app build after updates:

```bash
bash build-app.sh
```

The generated `.app` contains helper scripts that point back to the current repo path, so moving the project without rebuilding will break app launching.

## Developer setup and alternate launch paths

If you want to run the app without the packaged `.app`:

- double-click `Start Private Markdown Converter.command`
- or run:
  ```bash
  bash launch.sh
  ```

This is the developer-oriented path. The main install flow for normal usage is the built `.app` in `Applications`.

## Product direction and roadmap

The intended product direction is still a **downloadable local app**, not a hosted SaaS web app.

- users install it like a normal desktop app
- the app launches a local service and opens a browser UI
- sensitive files never need to pass through our servers
- saved passwords remain in the user's local OS credential store

Today, that install flow still depends on local Python and dependency setup. A future bundled-runtime release would remove the need for users to manage `venv`, `pip`, and Python manually.

See [DISTRIBUTION-ROADMAP.md](/Users/vineethnair/Vibe%20Code/private-markdown-converter/DISTRIBUTION-ROADMAP.md) for the packaging and release roadmap.

## Distribution roadmap

The current repo supports local launcher packaging for development and manual distribution. The next product step is a user-downloadable release that bundles the runtime so end users do not need Python, `venv`, or `pip`.

Near-term goals:

1. Reliable packaged launch on clean macOS machines
2. First-run validation for browser launch, writable local directories, and Keychain access
3. Signed/notarized distribution to reduce Gatekeeper friction
4. A repeatable release checklist for packaging, smoke tests, and upgrades

The full roadmap lives in [DISTRIBUTION-ROADMAP.md](/Users/vineethnair/Vibe%20Code/private-markdown-converter/DISTRIBUTION-ROADMAP.md).

## Optional PDF engines

```bash
pip install -r requirements-optional.txt
```

Adds: PyMuPDF4LLM, Docling, Marker (Phase 7–10).

## Database

```bash
sqlite3 data/app.db   # inspect conversion history metadata
```

## Verify temp directory is clean

```bash
ls temp/
```

Only `.gitkeep` should appear. The app wipes `temp/` on every startup as a crash-recovery safety net.
