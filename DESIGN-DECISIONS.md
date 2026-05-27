# Design Decisions

Key architectural and product decisions with rationale. Reference this when questioning past choices or considering changes.

---

## DD-01: No authentication system

**Decision:** No login, no user accounts, no password hashing, no session auth.

**Rationale:** This is a local Streamlit app running on one Mac. macOS login already gates physical access. Adding app-level auth creates friction on every launch for zero security gain. The original plan had a full auth system with user table, password hashing, and session management. That's 200+ lines of code and a user_id foreign key dependency across all tables, solving a problem that doesn't exist.

**Consequence:** No user_id column in any table. Single-user by design. If multi-user is ever needed, that's a different product.

**Risk:** If someone else uses the same Mac account, they see conversion history and password profile names (not passwords, those are in Keychain). Acceptable for a personal tool.

---

## DD-02: Metadata-only history

**Decision:** SQLite stores only conversion metadata (filename, extension, engine, status, duration, timestamp). No document content, no Markdown output, no file paths to stored documents.

**Rationale:** The app's privacy promise is that nothing persists after you close it except a log of what you converted and when. Storing Markdown content would create a shadow archive of bank statements. Storing file paths would reference files that no longer exist. Metadata-only keeps the history useful (audit trail, re-conversion reference) without creating a liability.

**Trade-off:** Users can't "re-download" a previously converted file. They must re-convert. This is intentional.

---

## DD-03: Glob patterns for filename matching (not regex)

**Decision:** Password profile filename_match_pattern uses glob syntax (e.g., `*HDFC*statement*`), not regex.

**Rationale:** The user will create these patterns in a UI text field. Glob patterns are intuitive: `*HDFC*` means "contains HDFC". Regex would be more powerful but requires knowledge most users don't have, is error-prone in UI input, and is overkill for matching bank statement filenames. Python's `fnmatch` module handles glob matching natively.

**Implementation:** Use `fnmatch.fnmatch(filename.lower(), pattern.lower())` for case-insensitive matching.

---

## DD-04: Keychain service name convention

**Decision:** Keychain entries use `pmc.password-profile.{profile_id}` as service name and `profile-{profile_id}` as account name.

**Rationale:** Namespaced to avoid collisions with other apps. Using profile_id (integer from SQLite) rather than profile_name because profile names can change. The keychain reference in SQLite stores the service and account names, not the password.

---

## DD-05: Flat-ish file structure

**Decision:** Maximum 2 levels under src/. Five subdirectories: converters, security, db, export, pages.

**Rationale:** The original plan had 6 subdirectories including auth/ and ui/. Auth is removed (DD-01). ui/ renamed to pages/ for Streamlit convention clarity. Each directory has 2-4 files. Total Python files: approximately 18. This is manageable for a solo builder working with AI coding tools. Deeper nesting increases cognitive load and makes AI prompts less precise because the agent has to navigate more structure.

---

## DD-06: Optional engines in separate requirements file

**Decision:** Core dependencies in requirements.txt. PyMuPDF4LLM, Docling, and Marker in requirements-optional.txt.

**Rationale:** Marker alone pulls in PyTorch (2-5GB). Docling has its own heavy dependency tree. Bundling these into requirements.txt means every install takes 20+ minutes and 5+ GB of disk. Most conversions use MarkItDown. Optional engines should be opt-in. The app detects whether each engine is installed and shows friendly guidance if not.

**Implementation:**
```python
def is_engine_available(engine_name: str) -> bool:
    try:
        if engine_name == "pymupdf4llm":
            import pymupdf4llm
        elif engine_name == "docling":
            import docling
        elif engine_name == "marker":
            import marker
        return True
    except ImportError:
        return False
```

---

## DD-07: Temp cleanup on startup (crash recovery)

**Decision:** On every app launch, wipe everything in temp/ except .gitkeep.

**Rationale:** If the app crashes mid-conversion, a decrypted bank statement PDF could be left in temp/. Post-conversion cleanup (try/finally) handles the normal case, but crashes bypass finally blocks if the process is killed. Startup cleanup is the safety net. It costs nothing (temp/ should be empty between sessions anyway) and closes the crash-state security gap.

---

## DD-08: YouTube and audio deferred to Phase 9

**Decision:** YouTube URL conversion and audio file conversion are not part of the core build (Phases 1-6).

**Rationale:** MarkItDown's YouTube support requires yt-dlp (system dependency, Homebrew install, frequent breakage due to YouTube changes). Audio support requires ffmpeg (another system dependency) and potentially speech recognition libraries. These are system-level dependencies, not pip packages. They add install complexity, break easily, and are not part of the core use case (document/PDF conversion). Building them early would create debugging distractions during the critical Phases 2-5 window.

---

## DD-09: 50MB file size limit

**Decision:** Default max upload size is 50MB, configurable in Settings.

**Rationale:** Streamlit's default upload limit is 200MB, which is too generous for a local app that processes files in memory. A 200MB PDF converted to Markdown could consume 500MB+ of RAM. Bank statement PDFs are typically 1-5MB. DOCX/PPTX files rarely exceed 30MB unless they contain embedded media. 50MB is generous enough for real use cases and conservative enough to prevent memory issues.

**Configuration:** Stored in .env as MAX_FILE_SIZE_MB. Editable in Settings page. Applied to Streamlit's file_uploader via `st.set_option` or custom validation.

---

## DD-10: Conversion status includes "partial"

**Decision:** conversion_status can be 'success', 'failed', or 'partial'.

**Rationale:** Some files convert partially. MarkItDown might extract text from 80% of a PDF and fail on embedded images. Rather than treating this as a binary pass/fail, 'partial' status lets the user know they got something but it may be incomplete. The UI should show partial results with a warning, not discard them.

**Implementation:** The converter returns a tuple of (markdown_content, status, error_message). If content is non-empty but an error occurred, status is 'partial'.
