# Grabfrog TikTok UI Update

This package contains the active project files with the new Grabfrog-style responsive HTML/CSS interface.

## Replace your current files

From your existing project folder:

```bash
cp app.py app.py.before_grabfrog_ui
cp static/index.css static/index.css.before_grabfrog_ui
cp static/index.js static/index.js.before_grabfrog_ui
```

Then copy the new `app.py` and `static/` folder over the existing project.

## Run

```bash
source .venv/bin/activate
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/tiktok-downloader`.

## Preserved features

- TikTok preview API
- Video download
- MP3 extraction
- Story mode
- Automatic URL detection after paste
- Strict mode/type handling
- English, French, and Arabic routes
- Arabic RTL layout
- Progress, status, errors, multiple files, and download actions
- SEO, canonical, hreflang, Open Graph, robots, and sitemap output
