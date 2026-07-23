# Family TikTok Downloader — Render deployment

This directory is the small deployment copy. Do not upload the old `.venv`, browser profiles, backups, or generated media.

## 1. Test Docker locally (optional)

```bash
docker build -t family-tiktok-downloader .
docker run --rm -p 8000:10000 \
  -e FAMILY_USERNAME=family \
  -e FAMILY_PASSWORD='choose-a-strong-password' \
  family-tiktok-downloader
```

Open `http://127.0.0.1:8000`.

## 2. Push to GitHub

Create an empty private GitHub repository, then run from this directory:

```bash
git init
git add .
git commit -m "Prepare TikTok downloader for Render"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## 3. Deploy with Render Blueprint

1. Open Render Dashboard.
2. Choose **New → Blueprint**.
3. Connect the GitHub repository.
4. Render detects `render.yaml`.
5. Enter values for `FAMILY_USERNAME` and `FAMILY_PASSWORD` when prompted.
6. Apply the Blueprint.
7. Open the generated `onrender.com` URL after the deploy becomes Live.

The browser will ask for the family username and password.

## Notes

- The free service sleeps when idle, so the first visit after inactivity can be slow.
- Generated files are temporary. That is intentional for this downloader.
- The Docker image installs FFmpeg for MP3 conversion.
- This lightweight deployment does not install a Playwright Chromium browser. Video, MP3, and story downloads use yt-dlp; browser-heavy photo/carousel fallback is not intended for Render Free.
- Keep one download running at a time because the free instance is small.
