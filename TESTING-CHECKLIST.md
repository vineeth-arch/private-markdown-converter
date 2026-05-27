# Testing Checklist

Manual testing checklist for each phase. Run these after every phase commit. Security tests are non-negotiable.

---

## After every phase (universal checks)

- [ ] App starts without errors: `streamlit run app.py`
- [ ] Sidebar navigation works, all pages load
- [ ] temp/ directory is cleaned on startup
- [ ] No .pdf, .docx, or other document files exist in temp/ after closing the app
- [ ] No passwords appear in terminal output
- [ ] data/app.db does not contain document content or passwords (open with `sqlite3 data/app.db` and inspect)

---

## Phase 1: Skeleton

- [ ] App launches at localhost:8501
- [ ] All 5 navigation items work (Convert, History, Password Profiles, Settings, Help)
- [ ] Each page shows its placeholder header
- [ ] Settings page shows file size limit
- [ ] Help page shows supported file types
- [ ] temp/ exists with .gitkeep
- [ ] data/ exists with .gitkeep

---

## Phase 2: MarkItDown conversion

- [ ] Upload a simple PDF, convert, see Markdown preview
- [ ] Upload a DOCX, convert, see Markdown preview
- [ ] Upload a PPTX, convert, see result
- [ ] Upload a CSV, convert, see result
- [ ] Download .md file, open it, content is correct
- [ ] Upload a file larger than 50MB, see size limit error
- [ ] Upload an unsupported file type, see clear error message
- [ ] After conversion, check temp/ is empty (no leftover files)
- [ ] Upload multiple files, see results for each
- [ ] Corrupt file upload shows error, doesn't crash app

---

## Phase 3: Password PDF unlock

- [ ] Upload a non-encrypted PDF, converts normally without password prompt
- [ ] Upload an encrypted PDF, password field appears
- [ ] Enter correct password, PDF converts successfully
- [ ] Enter wrong password, see friendly error message (not a stack trace)
- [ ] After conversion, check temp/ has no decrypted PDF files
- [ ] Kill the app mid-conversion (Ctrl+C), restart, check temp/ is cleaned
- [ ] Password is not visible in terminal output
- [ ] Password is not in any error message

Test with actual bank statement PDFs from:
- [ ] HDFC Bank
- [ ] SBI
- [ ] ICICI
- [ ] Any other bank you use

---

## Phase 4: Keychain password profiles

- [ ] Create a new password profile (name + password)
- [ ] Profile appears in Password Profiles page
- [ ] Password is NOT visible anywhere in the UI
- [ ] Create a profile with filename pattern (e.g., *HDFC*)
- [ ] Upload an encrypted PDF with "HDFC" in filename, profile is auto-suggested
- [ ] Select the suggested profile, conversion works
- [ ] Upload an encrypted PDF with no matching pattern, manual entry works
- [ ] Edit a profile name, change is saved
- [ ] Update a profile's password, new password works for conversion
- [ ] Delete a profile, confirm it's gone from UI
- [ ] After deleting, check macOS Keychain Access app: the entry should be removed
- [ ] Check SQLite: password_profiles table has NO password column
- [ ] After manual password entry on encrypted PDF, offered to save as new profile

---

## Phase 5: SQLite history

- [ ] Convert a file, check History page shows the record
- [ ] Record shows: date, filename, file type, engine, status, duration
- [ ] Record does NOT show: file content, Markdown content, password, file path
- [ ] Convert multiple files, all appear in history
- [ ] Failed conversion shows "failed" status with error message
- [ ] Clear history button works (with confirmation)
- [ ] After clearing, History page is empty
- [ ] Open data/app.db directly, inspect conversion_history table, confirm metadata only
- [ ] Run: `SELECT * FROM conversion_history;` and verify no content columns

---

## Phase 6: Batch ZIP export

- [ ] Convert 3+ files in one session
- [ ] "Download all as ZIP" button appears
- [ ] Download ZIP, extract it, all .md files are present
- [ ] Filenames are clean (original-name.md format)
- [ ] Duplicate filenames get -2, -3 suffix
- [ ] Single file conversion does NOT show ZIP button
- [ ] After downloading ZIP, temp/ has no ZIP files remaining

---

## Phase 7-10: Advanced engines

- [ ] PDF engine selector appears on Convert page
- [ ] MarkItDown (default) works for all file types
- [ ] PyMuPDF4LLM works for PDF files (if installed)
- [ ] Docling works for PDF files (if installed)
- [ ] Marker works for PDF files (if installed)
- [ ] If optional engine not installed, friendly message shown (not crash)
- [ ] Non-PDF files still use MarkItDown regardless of engine selection
- [ ] History records which engine was used
- [ ] Uninstalling an optional engine doesn't break the app

---

## Security smoke test (run periodically)

```bash
# Check no documents are stored
find data/ -type f ! -name "*.db" ! -name "*.db-wal" ! -name "*.db-shm" ! -name ".gitkeep"
# Should return nothing

# Check no temp files persist
find temp/ -type f ! -name ".gitkeep"
# Should return nothing

# Check SQLite has no content
sqlite3 data/app.db "SELECT sql FROM sqlite_master WHERE type='table';"
# Verify no content/markdown/password columns

# Check SQLite data
sqlite3 data/app.db "SELECT * FROM conversion_history LIMIT 5;"
# Verify only metadata fields

# Check no passwords in SQLite
sqlite3 data/app.db "SELECT * FROM password_profiles LIMIT 5;"
# Verify no password column, only keychain references
```
