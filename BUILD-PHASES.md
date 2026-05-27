# Build Phases

Revised and corrected build sequence. Each phase produces a working, committable milestone.

## Phase overview

| Phase | Feature | Tool | Commit message |
|---|---|---|---|
| 1 | Project skeleton + Streamlit UI shell | Claude Code | `chore: initialize streamlit app structure` |
| 2 | MarkItDown conversion (core file types) | Claude Code | `feat: add markitdown conversion engine` |
| 3 | Password-protected PDF unlock | Claude Code | `feat: add password-protected pdf unlock` |
| 4 | Keychain password profiles | Claude Code | `feat: add keychain password profiles` |
| 5 | SQLite metadata-only history | Claude Code | `feat: add sqlite conversion history` |
| 6 | Batch ZIP export | Claude Code | `feat: add batch zip export` |
| 7 | PyMuPDF4LLM engine | Claude Code | `feat: add pymupdf4llm pdf engine` |
| 8 | Docling engine | Claude Code | `feat: add docling pdf engine` |
| 9 | YouTube + audio support | Claude Code | `feat: add youtube and audio conversion` |
| 10 | Marker engine (optional, heavy) | Claude Code | `feat: add marker pdf engine` |
| 11 | Architecture review | Claude Code / Codex | `refactor: address architecture review` |
| 12 | macOS app launcher packaging | Claude Code | `docs: add local packaging and launcher` |

## Key changes from original plan

- **Auth system removed entirely.** Single-user local app, no user_id anywhere.
- **Keychain profiles moved up to Phase 4.** This is the core differentiator and the primary use case (bank statements). Build it early, test it early.
- **YouTube + audio deferred to Phase 9.** These need system-level dependencies (yt-dlp, ffmpeg) and are not part of the core document conversion workflow.
- **Marker isolated in Phase 10.** PyTorch dependency makes this a packaging risk. Keep it last.
- **File structure flattened.** `src/ui/` renamed to `src/pages/`. Auth directory removed.

---

## Phase 1: Project skeleton

### Goal
Working Streamlit app with sidebar navigation and placeholder pages.

### Prompt for Claude Code

```
You are an expert Python product engineer.

Read CLAUDE.md and SECURITY-RULES.md in this project before writing any code.

Build Phase 1: project skeleton and app foundation for Private Markdown Converter.

Create the file structure defined in CLAUDE.md. Specifically:

1. Create app.py with:
   - Streamlit page config (wide layout, "Private Markdown Converter" title)
   - Sidebar navigation: Convert, History, Password Profiles, Settings, Help
   - Page routing to placeholder pages
   - Temp directory cleanup on startup (see SECURITY-RULES.md pattern)

2. Create all src/ files with placeholder implementations:
   - src/pages/convert_page.py: placeholder with st.header("Convert")
   - src/pages/history_page.py: placeholder
   - src/pages/password_profiles_page.py: placeholder
   - src/pages/settings_page.py: placeholder with file size limit setting (default 50MB)
   - src/pages/help_page.py: placeholder with supported file types list
   - src/converters/router.py: stub
   - src/converters/markitdown_engine.py: stub
   - src/security/pdf_unlock.py: stub
   - src/security/password_vault.py: stub
   - src/security/temp_cleanup.py: implement startup cleanup
   - src/db/database.py: stub
   - src/db/history.py: stub
   - src/db/password_profiles.py: stub
   - src/export/zip_export.py: stub
   - All __init__.py files

3. Create requirements.txt with: streamlit, python-dotenv

4. Create .gitignore per SECURITY-RULES.md

5. Create .env.example with: MAX_FILE_SIZE_MB=50

6. Create README.md with: project purpose, privacy principles, setup instructions, supported file types

7. Create data/.gitkeep and temp/.gitkeep

Do not implement conversion, database, password handling, or auth.
Do not store original documents, decrypted PDFs, Markdown content, or passwords in the app database. Store only metadata. Store saved passwords only through the system keychain using keyring.

After implementation, list all created files and explain how to run the app.
```

---

## Phase 2: MarkItDown conversion

### Goal
Upload files, convert to Markdown via MarkItDown, preview, download.

### Prompt for Claude Code

```
You are an expert Python product engineer.

Read CLAUDE.md and SECURITY-RULES.md before writing any code.

Build Phase 2: MarkItDown conversion for Private Markdown Converter.

The app skeleton from Phase 1 is already working.

Requirements:

1. Add markitdown to requirements.txt.

2. Implement src/converters/markitdown_engine.py:
   - Function: convert_file(filepath: Path) -> str (returns Markdown string)
   - Handle conversion errors gracefully
   - Return error message string on failure, not exception

3. Implement src/converters/router.py:
   - Route file by extension to appropriate engine
   - For now, all files go to MarkItDown
   - PDF routing will be extended later for alternative engines

4. Update src/pages/convert_page.py:
   - File uploader (multiple files allowed)
   - Accepted types: pdf, docx, pptx, xlsx, html, csv, json, xml, epub, png, jpg, jpeg, gif, zip
   - Max file size from settings (default 50MB)
   - Convert button
   - st.spinner during conversion
   - Markdown preview using st.markdown
   - Raw Markdown in st.text_area (copyable)
   - Download button for .md file
   - For multiple files: show results in tabs or expanders
   - Store converted results in st.session_state for current session only

5. Temp file handling:
   - Save uploaded files to temp/ with UUID filenames
   - Delete temp files after conversion in a try/finally block
   - Follow patterns in SECURITY-RULES.md

6. Do NOT add:
   - YouTube URL input (deferred to Phase 9)
   - Audio conversion (deferred to Phase 9)
   - Password PDF handling (Phase 3)
   - History logging (Phase 5)

Do not store original documents, decrypted PDFs, Markdown content, or passwords in the app database.

After coding: summarize changed files. Explain how to test with one PDF and one DOCX.
```

---

## Phase 3: Password-protected PDF unlock

### Prompt for Claude Code

```
You are an expert Python product engineer.

Read CLAUDE.md and SECURITY-RULES.md before writing any code. Pay special attention to the PDF unlock rules and temp file rules.

Build Phase 3: password-protected PDF handling using pikepdf.

Requirements:

1. Add pikepdf to requirements.txt.

2. Implement src/security/pdf_unlock.py following the exact patterns in SECURITY-RULES.md:
   - is_pdf_encrypted(filepath) -> bool
   - unlock_pdf(filepath, password, temp_dir) -> Path
   - Use UUID filenames for unlocked temp files
   - Raise ValueError for wrong password with safe message
   - Raise RuntimeError for other failures with safe message

3. Update src/pages/convert_page.py:
   - After file upload, check if any PDF is encrypted
   - If encrypted, show a password input field for that file
   - Add a "Saved Profiles" selector (placeholder for now, functional in Phase 4)
   - On convert: unlock first, then convert the unlocked temp file
   - Delete unlocked temp file in finally block regardless of outcome
   - If password is wrong: show "The password appears to be incorrect. Please check and try again."
   - If PDF is not encrypted: convert normally, no password prompt

4. Never log, print, or include the password in any error message.

5. Never store the decrypted PDF. Delete it immediately after conversion.

Do not store original documents, decrypted PDFs, Markdown content, or passwords in the app database.

After coding: summarize changes. Explain how to test with a password-protected PDF.
```

---

## Phase 4: Keychain password profiles

### Prompt for Claude Code

```
You are an expert Python product engineer.

Read CLAUDE.md and SECURITY-RULES.md before writing any code. Pay special attention to the password handling rules and password vault patterns.

Build Phase 4: saved password profiles using macOS Keychain via keyring.

Requirements:

1. Add keyring to requirements.txt.

2. Implement src/security/password_vault.py following SECURITY-RULES.md patterns:
   - save_password(profile_id, password)
   - get_password(profile_id) -> str | None
   - delete_password(profile_id)
   - Use service name format: pmc.password-profile.{profile_id}

3. Implement src/db/password_profiles.py:
   - CRUD operations for password_profiles table (schema in CLAUDE.md)
   - No password column in the table. Passwords in keychain only.
   - Filename match patterns use glob syntax (e.g., *HDFC*statement*)

4. Update src/pages/password_profiles_page.py:
   - List all saved profiles (name, pattern, created date, last used)
   - Create new profile: name, filename pattern (optional), password
   - Edit profile: update name, pattern, or password
   - Delete profile: remove from both SQLite and keychain
   - Show info text: "Saved passwords are stored in your macOS Keychain, not inside the app database."
   - Never display saved passwords. Show only profile name and pattern.

5. Update src/pages/convert_page.py:
   - When an encrypted PDF is detected:
     a. Check if filename matches any saved profile pattern (glob match)
     b. If match found, auto-select that profile and show suggestion
     c. Show dropdown of all saved profiles as alternative
     d. Keep manual password entry as fallback
   - After successful conversion with a profile, update last_used_at
   - After successful manual password entry on an encrypted PDF, offer to save as new profile

6. Initialize database tables on startup in app.py if not already done.

Do not store original documents, decrypted PDFs, Markdown content, or passwords in the app database. Store saved passwords only through the system keychain using keyring.

After coding: summarize changes. Explain how to test creating a profile and using it for conversion.
```

---

## Phase 5: SQLite metadata-only history

### Prompt for Claude Code

```
You are an expert Python product engineer.

Read CLAUDE.md and SECURITY-RULES.md before writing any code.

Build Phase 5: SQLite metadata-only conversion history.

Requirements:

1. Implement src/db/database.py:
   - SQLite connection to data/app.db
   - WAL mode enabled
   - Create tables on init (conversion_history and password_profiles if not exists)
   - Use schema from CLAUDE.md (no user_id, single-user)

2. Implement src/db/history.py:
   - add_record(filename, extension, engine, status, output_name, file_size, duration, error_msg)
   - get_all_records() -> list
   - clear_history()
   - get_records_by_date_range(start, end) -> list

3. Update conversion flow to log metadata after each conversion:
   - filename, extension, engine used, success/failed/partial, duration, file size
   - Do NOT log: file content, Markdown output, passwords, file paths

4. Update src/pages/history_page.py:
   - Table showing: date, filename, file type, engine, status, duration, output name
   - Sort by date descending (most recent first)
   - Clear history button with confirmation

5. data/app.db is in .gitignore. Confirmed.

Do not store original documents, decrypted PDFs, Markdown content, or passwords in the app database. Store only metadata.

After coding: summarize changes. Explain how to verify history is metadata-only.
```

---

## Phase 6: Batch ZIP export

### Prompt for Claude Code

```
Read CLAUDE.md and SECURITY-RULES.md.

Build Phase 6: batch ZIP export.

When multiple files are converted in one session, allow downloading all Markdown outputs as a single ZIP.

Requirements:

1. Implement src/export/zip_export.py:
   - create_zip(files: dict[str, str], temp_dir: Path) -> Path
     (files = {output_filename: markdown_content})
   - Handle duplicate filenames by appending -2, -3, etc.
   - Return path to temp ZIP file
   - ZIP created in temp/ directory

2. Update convert page:
   - After batch conversion (2+ files), show "Download all as ZIP" button
   - Single file: show individual download button only
   - ZIP is generated on button click, not pre-generated

3. Clean up ZIP file after download where practical.

4. Markdown content stays in session_state during session only. Not persisted.

Do not store original documents, decrypted PDFs, Markdown content, or passwords in the app database.
```

---

## Phases 7-10: Advanced engines and deferred features

These follow the same pattern. Prompts are in the original plan document with these adjustments:

- **Phase 7 (PyMuPDF4LLM):** Add to requirements-optional.txt, not requirements.txt. Implement graceful fallback if not installed.
- **Phase 8 (Docling):** Same optional treatment. Test with structured PDFs.
- **Phase 9 (YouTube + Audio):** Requires yt-dlp and ffmpeg as system dependencies. Document Homebrew install steps in README. Make clearly optional.
- **Phase 10 (Marker):** Requires PyTorch. Add to requirements-optional.txt. Warn about 2-5GB install size. Test packaging impact.

---

## Phase 11: Architecture review

Use the review prompt from the original plan, but update it to reflect:
- No auth system exists (correct, by design)
- No user_id in any table (correct, single-user)
- Check temp cleanup crash recovery
- Check keyring integration edge cases
- Check that no content is stored in SQLite

---

## Phase 12: macOS launcher packaging

Use the packaging prompt from the original plan. Key addition:

```
Additional constraint: test that keyring (macOS Keychain access) works correctly when the app is launched from the packaged launcher, not just from terminal. Some packaging approaches break keychain access.
```
