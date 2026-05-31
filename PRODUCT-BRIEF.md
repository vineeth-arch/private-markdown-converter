# Product Brief: Private Markdown Converter

## Problem

Converting password-protected PDFs (bank statements, financial documents) and other document types into clean Markdown is currently a fragmented, manual process. Existing tools either require cloud uploads (privacy risk), don't handle encrypted PDFs, or need terminal commands for every conversion.

For someone who processes monthly bank statements across multiple banks, the friction compounds: find the file, remember the password, open a tool, convert, download, repeat. There's no local tool that handles the full loop privately.

## Product objective

A downloadable desktop-installed local web app that converts documents to Markdown with one-click simplicity, handles password-protected PDFs securely, remembers PDF passwords in the system keychain, and keeps a metadata-only audit trail. Nothing leaves the machine.

## Core user

Solo professional on macOS who regularly converts documents to Markdown for note-taking, archival, or downstream processing and wants a normal app install experience instead of repo cloning or terminal setup. Primary use case: monthly bank statement PDFs with known passwords.

## Core workflow

```
1. Launch installed app
2. App opens browser UI on `localhost`
3. Upload file(s) or paste YouTube URL
4. If PDF is encrypted:
   a. Auto-suggest saved password profile if filename matches
   b. Or enter password manually
   c. Unlock temporarily, convert, delete unlocked copy
5. Preview Markdown output
6. Download .md file (or batch ZIP)
7. Metadata logged to history (no content stored)
8. Temp files wiped
```

## What makes this different from existing tools

| Feature | This app | Pandoc CLI | Online converters | MarkItDown CLI |
|---|---|---|---|---|
| No cloud upload | Yes | Yes | No | Yes |
| GUI (no terminal) | Yes | No | Yes | No |
| Password PDF support | Yes | No | Some | No |
| Saved password profiles | Yes (keychain) | No | No | No |
| Multiple PDF engines | Yes | No | No | No |
| Metadata history | Yes | No | No | No |
| Batch export | Yes | Script needed | Limited | Script needed |

## Supported file types

### Phase 2 (core)
- PDF, DOCX, PPTX, XLSX
- HTML, CSV, JSON, XML, EPUB
- Images (via MarkItDown)
- ZIP (batch conversion)

### Phase 10 (deferred)
- YouTube URLs (requires yt-dlp)
- Audio files (requires ffmpeg)

## Non-goals (will not build)

- Cloud storage or sync
- Hosted SaaS as the primary v1 delivery model
- AI-powered content cleanup or summarization
- OCR for scanned documents (unless a PDF engine provides it)
- Multi-user or team features
- API or headless mode
- Mobile support
- Document search or indexing
- Content storage in database

## Success criteria for v1

1. Can convert a password-protected HDFC bank statement PDF to clean Markdown in under 30 seconds
2. Can save the HDFC password profile and have it auto-suggested next month
3. Can batch-convert 5 bank statement PDFs and download as a single ZIP
4. No original documents, decrypted files, or Markdown content persisted after session
5. App launches with a double-click (no terminal commands)
6. Conversion history shows metadata only
7. A non-technical macOS user can install and launch the app without creating a Python environment

## Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| MarkItDown API changes | Blocks all conversion | Pin version, abstract behind router |
| Marker adds 2-5GB PyTorch dependency | Bloats app, packaging nightmare | Keep optional, separate requirements file |
| pikepdf can't handle some bank PDF encryption | Core use case broken | Test with actual bank statements early in Phase 4 |
| Streamlit file uploader has 200MB default limit | Large files fail silently | Set explicit 50MB limit with clear error |
| Temp file persists after crash | Decrypted PDF left on disk | Startup cleanup routine wipes temp/ |
| keyring doesn't work in packaged app | Password profiles break | Test keyring in packaged context during Phase 12 |
| Packaging still depends on developer tooling | End users cannot self-serve install | Add bundled-runtime distribution and clean-machine install validation |
| yt-dlp breaks due to YouTube changes | YouTube conversion fails | Defer to Phase 10, make clearly optional |
