# Private Markdown Converter

A desktop-installed local web app for macOS that converts documents and password-protected PDFs into clean Markdown. It runs a local service on your machine, opens in the browser on `localhost`, and keeps files on your device.

## Privacy principles

- No cloud uploads. All processing happens locally.
- Uploaded files are deleted from `temp/` immediately after conversion.
- Converted Markdown is never stored — download it or it is gone.
- PDF passwords are stored only in macOS Keychain, never in the app database.
- The history log contains filenames and timestamps only. No document content.

## Product direction

The intended product direction is a **downloadable local app**, not a hosted SaaS web app.

- users install it like a normal desktop app
- the app launches a local service and opens a browser UI
- sensitive files never need to pass through our servers
- saved passwords remain in the user's local OS credential store

See [DISTRIBUTION-ROADMAP.md](/Users/vineethnair/Vibe%20Code/private-markdown-converter/DISTRIBUTION-ROADMAP.md) for the packaging and release roadmap.

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

## First-time setup

**Requirements:** Python 3.11+, macOS

1. Clone the repo
   ```bash
   git clone <repo-url>
   cd private-markdown-converter
   ```
2. Create a virtual environment:
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
5. Make launchers executable (one time only):
   ```bash
   chmod +x launch.sh stop.sh build-app.sh make-icon.sh "Start Private Markdown Converter.command"
   ```

## Launching the app

Double-click: `Start Private Markdown Converter.command`

Or from Terminal:

```bash
bash launch.sh
```

The app opens at `http://localhost:8501` in your browser.

## Stopping the app

Double-click: `stop.sh`

Or from Terminal:

```bash
bash stop.sh
```

## First-launch Gatekeeper warning

On first double-click, macOS may block the file because it is from an unnotarized source. Right-click the file and select Open, then confirm. You only need to do this once per file.

## Creating the macOS app launcher

After completing first-time setup and confirming `launch.sh` works:

### Option A: Use the default icon (fastest)

```bash
bash build-app.sh
```

### Option B: Use a custom icon

1. Prepare a PNG image, at least 1024x1024 pixels
2. Convert it to `.icns` format:
   ```bash
   bash make-icon.sh path/to/your-image.png
   ```
3. Build the apps:
   ```bash
   bash build-app.sh
   ```

### Install the apps

After `build-app.sh` completes:

1. Drag `Private Markdown Converter.app` to your Applications folder or Dock
2. Drag `Stop Private Markdown Converter.app` to your Applications folder or Dock
3. First launch only: right-click -> Open (Gatekeeper warning, one time)
4. From then on: single click or Dock tap launches the app

### Rebuilding after updates

If you move the project folder or pull significant updates, re-run:

```bash
bash build-app.sh
```

The generated `.app` bundles contain the current path back to `launch.sh` and `stop.sh`. If the project moves, rebuild them.

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
