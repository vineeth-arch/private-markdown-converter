# CLAUDE.md

## Project identity

**Name:** Private Markdown Converter
**Repo:** private-markdown-converter (GitHub, private)
**Type:** Local-only Streamlit web app for macOS
**Builder:** Solo developer using Claude Code + Cursor + Codex
**Status:** Pre-build, architecture finalized

A private local Streamlit app that converts documents and password-protected PDFs into clean Markdown. Runs entirely on the user's machine. No cloud uploads, no document storage, no content logging. Primary use case: recurring bank statement PDF conversion with saved password profiles stored in macOS Keychain.

---

## Behavioral rules (coding agent)

These rules override speed. Follow them even when the task feels trivial.

### Think before coding

- State assumptions explicitly before writing code. If uncertain, ask.
- If multiple interpretations exist, present them. Do not pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what is confusing. Ask.

### Simplicity first

- No features beyond what was asked.
- No abstractions for single-use code.
- No speculative "flexibility" or "configurability" that was not requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### Surgical changes

- Do not "improve" adjacent code, comments, or formatting.
- Do not refactor things that are not broken.
- Match existing style, even if you would do it differently.
- If you notice unrelated dead code, mention it. Do not delete it.
- Remove imports, variables, and functions that YOUR changes made unused.
- Do not remove pre-existing dead code unless asked.
- The test: every changed line should trace directly to the request.

### Goal-driven execution

- Transform tasks into verifiable goals before coding.
- For multi-step tasks, state a brief plan with verification checks. Wait for approval before executing.
- Loop until verified. Do not declare "done" without checking that the app runs.

### One prompt, one workstream

- Do not bundle concerns. One prompt solves one thing.
- If the request adds something outside the current phase, push back before writing code.
- Stay inside committed scope. Reference BUILD-PHASES.md if scope is ambiguous.

---

## Critical rules

Repeat these in working memory before writing any code:

1. **Never store original documents** anywhere permanently. Temp files only, deleted after conversion.
2. **Never store decrypted PDFs** permanently. Unlock into temp, convert, delete immediately.
3. **Never store Markdown content** in the database. User downloads it or it is gone.
4. **Never store passwords in SQLite.** Saved passwords go through `keyring` to macOS Keychain only.
5. **Never log, print, or display passwords** in any output, error message, or debug trace.
6. **Wipe the temp directory on every app startup** as crash-recovery safety net.
7. **Single-user local app.** No auth system, no user accounts, no login flow. macOS login is the access gate.
8. **No user_id foreign keys** in any table. All tables are single-user by design.
9. **Metadata-only history.** conversion_history stores filenames, timestamps, engine, status, duration. Nothing else.
10. **Graceful engine degradation.** If an optional PDF engine is not installed, show a friendly message. Never crash. Never break MarkItDown fallback.

---

## Design system: Neo-Brutalism

The app uses a colorful neo-brutalist visual language. Every UI element should feel bold, tactile, and intentional. No soft gradients, no subtle shadows, no muted palettes. This is a tool that looks like it means business.

### Design principles

- **Thick borders.** Every card, button, input, and container gets a 3px solid border in near-black.
- **Hard drop shadows.** Offset shadows (4px 4px or 5px 5px), zero blur, colored or near-black. Elements feel like they are sitting on the page.
- **Vivid flat color.** Saturated, high-contrast colors. No gradients. No opacity tricks. Solid fills.
- **Chunky elements.** Generous padding, large click targets, bold type. Nothing dainty.
- **High contrast text.** Dark text on light backgrounds. White text on dark/colored backgrounds. No gray-on-gray.
- **Visible structure.** The grid is not hidden. Sections are clearly bounded. Visual hierarchy through size and color, not subtlety.
- **Playful but functional.** The aesthetic is bold and energetic, but every element serves a purpose. No decoration without function.

### Color palette

```css
:root {
    /* ---- Core ---- */
    --bg-page:        #FFF8F0;     /* warm cream, main background */
    --bg-surface:     #FFFFFF;     /* white, card/container fill */
    --border:         #1E1E1E;     /* near-black, all borders and shadows */
    --text-primary:   #1E1E1E;     /* near-black, body text */
    --text-secondary: #4A4A4A;     /* dark gray, secondary text */

    /* ---- Vivid accent palette ---- */
    --color-orange:   #FF6B35;     /* primary action, CTA buttons, active states */
    --color-yellow:   #FFD23F;     /* warnings, highlights, badges */
    --color-blue:     #3A86FF;     /* links, info states, secondary actions */
    --color-green:    #06D6A0;     /* success states, confirmations */
    --color-red:      #EF476F;     /* errors, destructive actions, alerts */
    --color-purple:   #7B61FF;     /* tags, engine labels, metadata */
    --color-cyan:     #00CFE8;     /* progress bars, active indicators */

    /* ---- Semantic mapping ---- */
    --action-primary:   var(--color-orange);
    --action-secondary: var(--color-blue);
    --status-success:   var(--color-green);
    --status-error:     var(--color-red);
    --status-warning:   var(--color-yellow);
    --status-info:      var(--color-blue);
    --accent-tag:       var(--color-purple);
    --accent-progress:  var(--color-cyan);

    /* ---- Shadows ---- */
    --shadow-sm:  3px 3px 0 var(--border);
    --shadow-md:  5px 5px 0 var(--border);
    --shadow-lg:  8px 8px 0 var(--border);

    /* ---- Borders ---- */
    --border-width:   3px;
    --border-style:   var(--border-width) solid var(--border);
    --radius:         12px;        /* slightly rounded, not pill-shaped */
}
```

### Typography

Import from Google Fonts. Do not use Inter, Roboto, Arial, or system defaults.

```css
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --font-display: 'Archivo Black', sans-serif;   /* page titles, section headers */
    --font-body:    'Plus Jakarta Sans', sans-serif; /* body text, labels, buttons */
    --font-mono:    'JetBrains Mono', monospace;     /* code, file names, technical values */
}
```

**Usage rules:**
- Page titles (h1): Archivo Black, 28-32px, uppercase optional for page headers
- Section headers (h2): Archivo Black, 20-24px
- Subsection headers (h3): Plus Jakarta Sans Bold (700), 16-18px
- Body text: Plus Jakarta Sans Regular (400), 15-16px
- Labels and captions: Plus Jakarta Sans Medium (500), 13-14px
- Buttons: Plus Jakarta Sans SemiBold (600), 14-15px, uppercase with letter-spacing
- Code/filenames/technical values: JetBrains Mono Regular (400), 13-14px
- Table data: Plus Jakarta Sans Regular (400), 14px

### Component patterns

**Buttons (primary action):**
```css
.btn-primary {
    background: var(--color-orange);
    color: white;
    border: var(--border-style);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    padding: 12px 24px;
    font-family: var(--font-body);
    font-weight: 600;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    cursor: pointer;
    transition: transform 0.1s, box-shadow 0.1s;
}
.btn-primary:hover {
    transform: translate(2px, 2px);
    box-shadow: 1px 1px 0 var(--border);
}
.btn-primary:active {
    transform: translate(3px, 3px);
    box-shadow: none;
}
```

**Buttons (secondary):** Same pattern, `background: var(--color-blue)`.
**Buttons (destructive):** Same pattern, `background: var(--color-red)`.

**Cards/containers:**
```css
.card {
    background: var(--bg-surface);
    border: var(--border-style);
    border-radius: var(--radius);
    box-shadow: var(--shadow-md);
    padding: 24px;
}
```

**Input fields:**
```css
.input {
    background: var(--bg-surface);
    border: var(--border-style);
    border-radius: var(--radius);
    padding: 12px 16px;
    font-family: var(--font-body);
    font-size: 15px;
    box-shadow: inset 2px 2px 0 rgba(0,0,0,0.05);
}
.input:focus {
    outline: none;
    box-shadow: var(--shadow-sm);
    border-color: var(--color-blue);
}
```

**Status badges:**
```css
.badge {
    display: inline-block;
    padding: 4px 12px;
    border: 2px solid var(--border);
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 500;
}
.badge-success { background: var(--color-green); color: var(--border); }
.badge-error   { background: var(--color-red);   color: white; }
.badge-warning { background: var(--color-yellow); color: var(--border); }
.badge-info    { background: var(--color-purple); color: white; }
```

**File upload zone:**
```css
.upload-zone {
    background: var(--bg-page);
    border: var(--border-width) dashed var(--border);
    border-radius: var(--radius);
    padding: 48px;
    text-align: center;
    transition: background 0.2s;
}
.upload-zone:hover {
    background: var(--color-yellow);
}
```

**Sidebar navigation:**
- Background: var(--border) (near-black, full dark sidebar)
- Nav items: white text, Plus Jakarta Sans SemiBold
- Active item: var(--color-orange) background with white text, slight indent
- Hover: var(--color-blue) background

**Tables (history page):**
- Header row: var(--border) background, white text, Archivo Black
- Body rows: alternating var(--bg-surface) and var(--bg-page)
- Row border-bottom: 2px solid var(--border)
- Status column uses badge component

### Streamlit custom CSS injection

All custom styling is injected at the top of app.py using `st.markdown()` with `unsafe_allow_html=True`. Create a dedicated CSS string or file at `src/styles/theme.css` (loaded and injected at startup).

```python
# In app.py, at the top after page config
def inject_custom_css():
    css_path = Path("src/styles/theme.css")
    if css_path.exists():
        css = css_path.read_text()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

### Streamlit element targeting

Streamlit renders its own HTML. To style Streamlit components, use these CSS selectors:

```css
/* Main app background */
.stApp { background-color: var(--bg-page); }

/* Sidebar */
[data-testid="stSidebar"] { background-color: var(--border); }
[data-testid="stSidebar"] .stMarkdown { color: white; }

/* Buttons */
.stButton > button {
    background: var(--color-orange);
    color: white;
    border: var(--border-style);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    font-family: var(--font-body);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stButton > button:hover {
    transform: translate(2px, 2px);
    box-shadow: 1px 1px 0 var(--border);
}

/* Text inputs */
.stTextInput > div > div > input {
    border: var(--border-style);
    border-radius: var(--radius);
    font-family: var(--font-body);
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: var(--border-width) dashed var(--border);
    border-radius: var(--radius);
    padding: 20px;
}

/* Expanders */
.streamlit-expanderHeader {
    border: var(--border-style);
    border-radius: var(--radius);
    background: var(--bg-surface);
    font-family: var(--font-body);
    font-weight: 600;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--bg-surface);
    border: var(--border-style);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    padding: 16px;
}

/* Alerts */
.stAlert { border-radius: var(--radius); border-width: var(--border-width); }

/* Dataframes / tables */
.stDataFrame { border: var(--border-style); border-radius: var(--radius); }
```

### Visual identity details

**App header:** Each page gets a colored header bar at the top. Use different accent colors per section:
- Convert: var(--color-orange) background
- History: var(--color-blue) background
- Password Profiles: var(--color-purple) background
- Settings: var(--color-cyan) background
- Help: var(--color-green) background

Implementation pattern:
```python
def page_header(title: str, color: str):
    st.markdown(
        f"""
        <div style="
            background: {color};
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 20px 28px;
            margin-bottom: 24px;
        ">
            <h1 style="
                font-family: 'Archivo Black', sans-serif;
                color: white;
                margin: 0;
                font-size: 28px;
                text-shadow: 2px 2px 0 rgba(0,0,0,0.2);
            ">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
```

**Empty states:** When a page has no data (no history, no profiles), show a large centered illustration-style message using the accent color for that page, not a generic gray placeholder.

**Loading/progress:** Use var(--color-cyan) for progress bars. Use chunky spinner animation, not the default Streamlit spinner if possible.

---

## Tech stack

- Python 3.11+
- Streamlit (UI framework)
- SQLite (metadata-only history, WAL mode)
- MarkItDown (default conversion engine, Microsoft)
- pikepdf (PDF password unlock)
- keyring (macOS Keychain integration for saved passwords)
- PyMuPDF4LLM, Docling, Marker (optional advanced PDF engines, added later)

---

## Architecture principles

- Flat-ish file structure. No more than 2 levels of nesting under src/.
- Every file has one clear job.
- Conversion engine logic stays isolated from UI code.
- Password/security logic stays isolated from everything except the unlock step.
- Streamlit session_state for in-session data only. No persistent state outside SQLite metadata.
- All temporary files go into the `temp/` directory with cleanup on startup and after each conversion.
- File size limit: 50MB default, configurable in settings.
- Progress indication required for any operation over 2 seconds.

---

## File structure

```
private-markdown-converter/
├── app.py                          # Entry point, nav routing, CSS injection, temp cleanup
├── requirements.txt
├── requirements-optional.txt       # PyMuPDF4LLM, Docling, Marker
├── README.md
├── CLAUDE.md                       # This file
├── .gitignore
├── .env.example
├── src/
│   ├── styles/
│   │   └── theme.css               # Neo-brutalism custom CSS
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── router.py               # Routes file type to correct engine
│   │   ├── markitdown_engine.py    # Default engine
│   │   ├── pymupdf4llm_engine.py   # Optional
│   │   ├── docling_engine.py       # Optional
│   │   └── marker_engine.py        # Optional
│   ├── security/
│   │   ├── __init__.py
│   │   ├── pdf_unlock.py           # pikepdf unlock logic
│   │   ├── password_vault.py       # keyring read/write
│   │   └── temp_cleanup.py         # Startup + post-conversion cleanup
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLite connection, table creation
│   │   ├── history.py              # Conversion history CRUD
│   │   └── password_profiles.py    # Profile metadata CRUD
│   ├── export/
│   │   ├── __init__.py
│   │   └── zip_export.py           # Batch ZIP download
│   └── pages/
│       ├── __init__.py
│       ├── convert_page.py
│       ├── history_page.py
│       ├── password_profiles_page.py
│       ├── settings_page.py
│       └── help_page.py
├── data/
│   └── .gitkeep
├── temp/
│   └── .gitkeep
└── tests/
    └── .gitkeep
```

---

## SQLite schema

```sql
-- No users table. Single-user local app.

CREATE TABLE IF NOT EXISTS conversion_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_file_name TEXT NOT NULL,
    original_file_extension TEXT NOT NULL,
    file_size_bytes INTEGER,
    conversion_engine TEXT NOT NULL,
    conversion_status TEXT NOT NULL,  -- 'success', 'failed', 'partial'
    output_file_name TEXT,
    conversion_duration_seconds REAL,
    error_message TEXT,
    converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT NOT NULL UNIQUE,
    filename_match_pattern TEXT,       -- glob pattern, e.g. *HDFC*statement*
    keychain_service_name TEXT NOT NULL,
    keychain_account_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);
```

---

## Coding standards

- Python 3.11+ syntax
- Type hints on all function signatures
- Docstrings on all public functions (one-liner is fine for simple functions)
- No wildcard imports
- No print() for debugging in committed code; use logging module
- Error messages shown to user must be non-technical and helpful
- All file paths use pathlib, not os.path string concatenation
- Constants in UPPER_SNAKE_CASE at module level
- No global mutable state outside Streamlit session_state

---

## Streamlit conventions

- Use `st.sidebar` for navigation only
- Use `st.spinner()` for any operation over 2 seconds
- Use `st.progress()` for batch operations
- Use `st.error()`, `st.warning()`, `st.success()` for user feedback
- Use `st.session_state` for in-session data (converted files, current selections)
- Never store sensitive data in session_state (passwords, decrypted content)
- File uploader max size: 50MB default
- Inject custom CSS from src/styles/theme.css at the top of every page load
- Use page_header() function for consistent neo-brutalist page titles
- Use custom HTML via st.markdown(unsafe_allow_html=True) for styled components that Streamlit CSS selectors cannot reach

---

## Commands

```bash
streamlit run app.py                        # launch the app locally
pip install -r requirements.txt             # install core dependencies
pip install -r requirements-optional.txt    # install optional PDF engines
sqlite3 data/app.db                         # inspect the local database
ls temp/                                    # verify temp directory is clean
```

---

## Git workflow

Always work on the main branch. Do not create feature branches or worktrees.

After every prompt that results in a working app (runs without errors):

```bash
git add .
git commit -m "<type>: <description>"
git push origin main
```

Commit types: `chore`, `feat`, `fix`, `refactor`, `docs`

Commit messages for each phase:

```
chore: initialize streamlit app structure with neo-brutalist theme
feat: add markitdown conversion engine
feat: add password-protected pdf unlock
feat: add keychain password profiles
feat: add sqlite conversion history
feat: add batch zip export
feat: add pymupdf4llm pdf engine
feat: add docling pdf engine
feat: add youtube and audio conversion
feat: add marker pdf engine
refactor: address architecture review
docs: add local packaging and launcher
```

---

## What NOT to build

- User authentication / login system
- Cloud sync or cloud storage
- AI cleanup or summarization of converted content
- OCR (unless a PDF engine provides it natively)
- RAG or search over converted documents
- Billing, subscription, or team features
- Document storage or content database
- Electron/Tauri wrapper (too early)
- API endpoints (this is a local UI app)
- Gradients, soft shadows, muted palettes, or any "safe" corporate design
