# Grimmealie — Import cookbook recipes into Mealie

Capture recipe pages from your [Grimmory](https://grimmory.org) / BookLore ebook reader and import them into [Mealie](https://mealie.io) using OpenAI image-to-recipe parsing.

## How it works

1. You open a cookbook page in Grimmory's reader
2. You capture it — either via bookmarklet (in-browser) or CLI (Playwright)
3. The screenshot is sent to Mealie's `POST /api/recipes/create/image` endpoint
4. Mealie uses OpenAI to OCR and parse the recipe, then saves it

For recipes spanning multiple pages, you capture each page and they're uploaded together in one request so OpenAI sees the full recipe.

---

## Option 1: Bookmarklet (recommended for occasional use)

The bookmarklet uses your browser's built-in screen capture API — no install needed.

### Setup

1. Open `bookmarklet.html` in any browser:

   ```
   open bookmarklet.html
   ```

2. Enter your Mealie details:
   - **Mealie URL**: `https://mealie.vandijke.xyz`
   - **Mealie API Key**: your long-lived API token

3. Click **Generate Bookmarklets**

4. Two bookmarklets appear. Drag **both** to your bookmarks bar:

   | Bookmarklet | Purpose |
   |---|---|
   | **📷 Capture page** | Captures current viewport and stores it |
   | **📤 Upload all** | Sends all stored captures to Mealie |

### Usage

**Single page recipe** (or two-page spread visible at once):
1. Navigate to the recipe page in Grimmory
2. Click **📷 Capture page** → in the dialog, select **this tab** → alert confirms capture
3. Click **📤 Upload all** → alert shows new recipe slug

**Recipe spanning 2 pages** (need to flip):
1. Navigate to **page 1** → click **📷 Capture page** → select tab → *"Captured! (1 page so far)"*
2. Flip to **page 2** → click **📷 Capture page** → select tab → *"Captured! (2 pages so far)"*
3. Click **📤 Upload all** → both pages sent together → recipe created

**Recipe with unrelated pages** (not adjacent):
Same as above — capture each page individually, then upload all at once.

### Limitations

- The screen-picker dialog appears for **every** capture (this is a browser security requirement)
- Only works on **HTTPS** sites (Grimmory uses HTTPS, so this is fine)
- Your Mealie URL and API key are stored in the bookmarklet code itself

---

## Option 2: CLI (`grimmealie`, recommended for bulk imports)

Uses Playwright to open a real browser. You navigate manually, the tool captures and uploads.

### Setup

```bash
cd mealie-import
uv sync
```

One-time Playwright browser install (already done):

```bash
uv run python -m playwright install chromium
```

### Usage

Run in interactive mode:

```bash
uv run grimmealie interactive
```

It will prompt you for:
- Grimmory URL (default: `https://booklore.vandijke.xyz`)
- Book ID (from the URL, e.g. `27944` in `/ebook-reader/book/27944`)
- Mealie URL and API key
- Whether login is needed

**Workflow inside the CLI:**

| You type | What happens |
|---|---|
| *(just press Enter)* | Captures the current browser viewport |
| `u` | Uploads all captured screenshots to Mealie |
| `q` | Quits without uploading |

1. A browser opens to your book
2. Navigate to the first recipe page using the **browser** (click, swipe, use arrow keys)
3. Press **Enter** in the terminal to capture it
4. Flip to the next recipe page in the browser, press **Enter** again
5. Repeat for all pages of the recipe
6. Type **`u`** and press Enter — all pages are uploaded together
7. Navigate to the next recipe in the book, repeat

---

## Requirements

| | Bookmarklet | CLI |
|---|---|---|
| Browser | Chrome/Firefox/Edge (any modern) | Chromium (installed by Playwright) |
| Dependencies | None | Python 3.10+, uv |
| Mealie | API key, OpenAI enabled | API key, OpenAI enabled |
| Installation | Open one HTML file | `uv sync` |

### Mealie prerequisites

Mealie must have:
- `OPENAI_ENABLED=true` in its config
- `OPENAI_ENABLE_IMAGE_SERVICES=true` in its config
- A valid OpenAI API key configured

The endpoint used: `POST /api/recipes/create/image`

---

## Architecture

```
Grimmory reader ──► Screenshot ──► Mealie API ──► OpenAI ──► Recipe saved
                                  POST /api/recipes/create/image
                                  (multipart, one or more images)
```

- **Bookmarklet**: uses `navigator.mediaDevices.getDisplayMedia()` — captures pixels, no CSP issues
- **CLI**: uses Playwright `page.screenshot()` — renders the Angular SPA in a headful browser
