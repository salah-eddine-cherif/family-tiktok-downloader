from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from html import escape as html_escape, unescape as html_unescape
import json
import mimetypes
import re
import subprocess
import uuid
import os
import urllib.request
import urllib.parse

app = FastAPI(title="TikTok Downloader")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "assets").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.middleware("http")
async def no_cache_static_debug(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith("/static/index.js") or request.url.path.endswith("/static/index.css"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


TOOLS = ["all", "video", "image", "story"]

PATHS = {
    "en": {
        "all": "/tiktok-downloader",
        "video": "/tiktok-video-downloader",
        "image": "/tiktok-image-downloader",
        "story": "/tiktok-story-downloader",
    },
    "fr": {
        "all": "/fr/telecharger-tiktok",
        "video": "/fr/telecharger-video-tiktok",
        "image": "/fr/telecharger-image-tiktok",
        "story": "/fr/telecharger-story-tiktok",
    },
    "ar": {
        "all": "/ar/tahmil-tiktok",
        "video": "/ar/tahmil-video-tiktok",
        "image": "/ar/tahmil-image-tiktok",
        "story": "/ar/tahmil-story-tiktok",
    },
}

PAGES = {
    "en": {
        "all": {
            "title": "TikTok Downloader - Videos, Stories and Photos",
            "description": "Paste a TikTok link, detect the media type, preview videos, stories or photos, then download the available file directly to your device.",
            "heading": "TikTok <span>Videos, Stories & Photos</span> Downloader",
            "subtitle": "Paste a TikTok link, preview the media type, then download videos, photos, stories or slideshows when available.",
            "placeholder": "Paste TikTok video, photo, story or slideshow link...",
            "button": "Detect Preview",
        },
        "video": {
            "title": "TikTok Video Downloader - Preview and Download Videos",
            "description": "Download TikTok videos online. Paste a TikTok video link, preview it, then download the best available MP4.",
            "heading": "TikTok <span>Video</span> Downloader",
            "subtitle": "Paste a TikTok video link, preview it, then download the best available MP4 version.",
            "placeholder": "Paste TikTok video link here...",
            "button": "Detect Video",
        },
        "image": {
            "title": "TikTok Photo / Carousel Downloader - Save TikTok Images and Slideshows",
            "description": "Download TikTok photos and slideshow images online. Paste a TikTok photo link, preview it, then save available image files.",
            "heading": "TikTok <span>Photo</span> Downloader",
            "subtitle": "Paste a TikTok photo, slideshow or carousel link, preview available images, then download what you need.",
            "placeholder": "Paste TikTok photo, slideshow or carousel link here...",
            "button": "Detect Photo",
        },
        "story": {
            "title": "TikTok Story Downloader - Save TikTok Stories",
            "description": "Download TikTok stories online when available. Paste a TikTok story link, preview it, then download the available media.",
            "heading": "TikTok <span>Story</span> Downloader",
            "subtitle": "Paste a TikTok story link, preview available story media, then download the right file.",
            "placeholder": "Paste TikTok story link here...",
            "button": "Detect Story",
        },
    },
    "fr": {
        "all": {
            "title": "Télécharger TikTok - Vidéos, Stories et Photos",
            "description": "Collez un lien TikTok, détectez le type de média, prévisualisez les vidéos, stories ou photos, puis téléchargez le fichier disponible.",
            "heading": "Télécharger <span>Vidéos, Stories & Photos TikTok</span>",
            "subtitle": "Collez un lien TikTok, prévisualisez le type de média, puis téléchargez les vidéos, photos, stories ou slideshows disponibles.",
            "placeholder": "Collez un lien TikTok vidéo, photo, story ou slideshow...",
            "button": "Détecter l’aperçu",
        },
        "video": {
            "title": "Télécharger Vidéo TikTok - Prévisualiser et Télécharger",
            "description": "Téléchargez des vidéos TikTok en ligne. Collez un lien vidéo TikTok, prévisualisez-le, puis téléchargez la meilleure version MP4 disponible.",
            "heading": "Télécharger <span>Vidéo TikTok</span>",
            "subtitle": "Collez un lien vidéo TikTok, prévisualisez-le, puis téléchargez la meilleure version MP4 disponible.",
            "placeholder": "Collez le lien vidéo TikTok ici...",
            "button": "Détecter la vidéo",
        },
        "image": {
            "title": "Télécharger Photo / Carrousel TikTok - Images et Slideshows",
            "description": "Téléchargez des photos TikTok et images de slideshow en ligne. Collez un lien photo TikTok, prévisualisez-le, puis enregistrez les images disponibles.",
            "heading": "Télécharger <span>Photo / Carrousel TikTok</span>",
            "subtitle": "Collez un lien photo, slideshow ou carrousel TikTok, prévisualisez les images disponibles, puis téléchargez ce dont vous avez besoin.",
            "placeholder": "Collez le lien photo, slideshow ou carrousel TikTok ici...",
            "button": "Détecter la photo",
        },
        "story": {
            "title": "Télécharger Story TikTok - Enregistrer des Stories TikTok",
            "description": "Téléchargez des stories TikTok en ligne quand elles sont disponibles. Collez un lien story TikTok, prévisualisez-le, puis téléchargez le média.",
            "heading": "Télécharger <span>Story TikTok</span>",
            "subtitle": "Collez un lien story TikTok, prévisualisez le média disponible, puis téléchargez le bon fichier.",
            "placeholder": "Collez le lien story TikTok ici...",
            "button": "Détecter la story",
        },
    },
    "ar": {
        "all": {
            "title": "تحميل تيك توك - فيديوهات، ستوري وصور",
            "description": "الصق رابط TikTok، اكتشف نوع الوسائط، عاين الفيديوهات أو الستوري أو الصور، ثم حمّل الملف المتاح مباشرة على جهازك.",
            "heading": "تحميل <span>فيديوهات، ستوري وصور TikTok</span>",
            "subtitle": "الصق رابط TikTok، عاين نوع الوسائط، ثم حمّل الفيديوهات أو الصور أو الستوري أو السلايدشو عند توفرها.",
            "placeholder": "الصق رابط TikTok فيديو أو صورة أو ستوري أو slideshow...",
            "button": "كشف المعاينة",
        },
        "video": {
            "title": "تحميل فيديو TikTok - معاينة وتحميل الفيديوهات",
            "description": "حمّل فيديوهات TikTok أونلاين. الصق رابط فيديو TikTok، عاينه، ثم حمّل أفضل نسخة MP4 متاحة.",
            "heading": "تحميل <span>فيديو TikTok</span>",
            "subtitle": "الصق رابط فيديو TikTok، عاينه، ثم حمّل أفضل نسخة MP4 متاحة.",
            "placeholder": "الصق رابط فيديو TikTok هنا...",
            "button": "كشف الفيديو",
        },
        "image": {
            "title": "تحميل صور TikTok - حفظ الصور، سلايدشو وكاروسيل",
            "description": "حمّل صور TikTok وصور السلايدشو أونلاين. الصق رابط صورة TikTok، عاينها، ثم احفظ الصور المتاحة.",
            "heading": "تحميل <span>صور TikTok</span>",
            "subtitle": "الصق رابط صورة أو slideshow أو كاروسيل من TikTok، عاين الصور المتاحة، ثم حمّل ما تحتاجه.",
            "placeholder": "الصق رابط صورة أو slideshow أو كاروسيل من TikTok هنا...",
            "button": "كشف الصورة",
        },
        "story": {
            "title": "تحميل ستوري TikTok - حفظ Stories TikTok",
            "description": "حمّل Stories TikTok أونلاين عندما تكون متاحة. الصق رابط Story من TikTok، عاينه، ثم حمّل الوسائط المتاحة.",
            "heading": "تحميل <span>ستوري TikTok</span>",
            "subtitle": "الصق رابط Story من TikTok، عاين الوسائط المتاحة، ثم حمّل الملف الصحيح.",
            "placeholder": "الصق رابط Story TikTok هنا...",
            "button": "كشف الستوري",
        },
    },
}

TAB_LABELS = {
    "en": {"all": "All TikTok Downloader", "video": "Video", "image": "Photo / Carousel", "story": "Story"},
    "fr": {"all": "Télécharger TikTok", "video": "Vidéo", "image": "Photo / Carousel", "story": "Story"},
    "ar": {"all": "الكل", "video": "فيديو", "image": "صور / كاروسيل", "story": "ستوري"},
}

MODE_LABELS = {
    "all": "TikTok media",
    "video": "TikTok video",
    "image": "TikTok photo",
    "story": "TikTok story",
}

def safe_url(url: str) -> bool:
    return url.startswith(("http://", "https://")) and "tiktok" in url.lower()

def safe_filename(filename: str) -> str:
    return Path(filename).name

def run_cmd(args, timeout=600):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

def guess_kind(info: dict, url: str) -> str:
    url_l = url.lower()
    if "story" in url_l or "/stories/" in url_l:
        return "story"

    entries = info.get("entries") or []
    if isinstance(entries, list) and len(entries) > 1:
        return "image"

    ext = (info.get("ext") or "").lower()
    duration = info.get("duration")
    vcodec = (info.get("vcodec") or "").lower()
    formats = info.get("formats") or []

    if duration or ext in {"mp4", "webm", "mov"} or any((f.get("vcodec") or "none") != "none" for f in formats if isinstance(f, dict)):
        return "video"

    if info.get("thumbnail") or info.get("thumbnails"):
        return "image"

    return "all"


def detect_kind_from_url(url: str) -> str:
    lower = url.lower()

    # URL-first TikTok classification.
    # TikTok /photo/ pages are photos, slideshows, or carousel-like posts.
    if "/photo/" in lower:
        return "image"

    if "/story" in lower or "/stories/" in lower:
        return "story"

    if "/video/" in lower:
        return "video"

    return "unknown"

def tiktok_oembed_info(url: str) -> dict:
    api = "https://www.tiktok.com/oembed?url=" + urllib.parse.quote(url, safe="")
    req = urllib.request.Request(
        api,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )

    with urllib.request.urlopen(req, timeout=20) as res:
        raw = res.read().decode("utf-8", errors="replace")
        return json.loads(raw)

def preview_from_oembed(url: str, forced_kind: str, warning: str = "") -> dict:
    try:
        data = tiktok_oembed_info(url)
    except Exception as e:
        data = {}

    title = data.get("title") or f"TikTok {forced_kind}"
    author = data.get("author_name") or ""
    thumbnail = data.get("thumbnail_url") or ""

    return {
        "kind": forced_kind,
        "title": title,
        "uploader": author,
        "thumbnail": thumbnail,
        "duration": "",
        "webpage_url": url,
        "items": [
            {
                "index": 1,
                "title": title,
                "thumbnail": thumbnail,
                "duration": "",
                "ext": "jpg" if forced_kind == "image" else "",
            }
        ],
        "warning": warning,
        "oembed_fallback": True,
    }

def download_url_to_output(file_url: str, prefix: str, ext: str = "jpg") -> Path:
    job_id = str(uuid.uuid4())
    ext = ext.strip(".") or "jpg"
    out = OUTPUT_DIR / f"{prefix}_{job_id}.{ext}"

    req = urllib.request.Request(
        file_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as res:
        out.write_bytes(res.read())

    return out


def preview_from_url_only(url: str, forced_kind: str, warning: str = "") -> dict:
    media_id = ""
    m = re.search(r"/(?:photo|video)/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    pretty = "TikTok Photo / Carousel" if forced_kind == "image" else "TikTok Story" if forced_kind == "story" else "TikTok Video" if forced_kind == "video" else "TikTok media"
    title = f"{pretty} #{media_id}" if media_id else pretty

    return {
        "kind": forced_kind,
        "title": title,
        "uploader": "",
        "thumbnail": "",
        "duration": "",
        "webpage_url": url,
        "items": [
            {
                "index": 1,
                "title": title,
                "thumbnail": "",
                "duration": "",
                "ext": "jpg" if forced_kind == "image" else "mp4" if forced_kind == "video" else "",
            }
        ],
        "warning": warning,
        "url_first_fallback": True,
    }


def fetch_tiktok_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.tiktok.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8", errors="replace")

def _walk_json(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk_json(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_json(value)

def _first_text_value(obj, keys):
    if isinstance(obj, dict):
        for key in keys:
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in obj.values():
            found = _first_text_value(value, keys)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _first_text_value(value, keys)
            if found:
                return found
    return ""

def _collect_urls_from_image_url(image_url_obj):
    urls = []

    if isinstance(image_url_obj, str) and image_url_obj.startswith("http"):
        urls.append(image_url_obj)

    if isinstance(image_url_obj, dict):
        for key in ("urlList", "url_list", "urls", "imageURLList", "image_url_list"):
            value = image_url_obj.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.startswith("http"):
                        urls.append(item)
            elif isinstance(value, str) and value.startswith("http"):
                urls.append(value)

        for key in ("url", "uri"):
            value = image_url_obj.get(key)
            if isinstance(value, str) and value.startswith("http"):
                urls.append(value)

    return urls

def _extract_image_urls_from_image_post(image_post):
    urls = []

    if not isinstance(image_post, dict):
        return urls

    images = image_post.get("images") or image_post.get("imageList") or image_post.get("image_list") or []
    if isinstance(images, dict):
        images = list(images.values())

    if isinstance(images, list):
        for image in images:
            if not isinstance(image, dict):
                continue

            candidates = [
                image.get("imageURL"),
                image.get("imageUrl"),
                image.get("image_url"),
                image.get("displayImage"),
                image.get("display_image"),
                image.get("url"),
            ]

            for candidate in candidates:
                urls.extend(_collect_urls_from_image_url(candidate))

            # Some TikTok JSON nests deeply inside each image object.
            for nested in _walk_json(image):
                for key in ("imageURL", "imageUrl", "image_url", "displayImage", "display_image"):
                    if key in nested:
                        urls.extend(_collect_urls_from_image_url(nested.get(key)))

    # Fallback: walk full imagePost for TikTok image/CDN URLs.
    for nested in _walk_json(image_post):
        for key, value in nested.items():
            if key.lower() in {"urllist", "url_list", "imageurllist", "image_url_list"}:
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.startswith("http"):
                            urls.append(item)
            elif isinstance(value, str) and value.startswith("http") and ("tiktok" in value or "tos-" in value or "p16-" in value):
                if any(token in value.lower() for token in ["image", "photo", "tos", "p16"]):
                    urls.append(value)

    return clean_real_image_urls(urls)


def looks_like_real_tiktok_image_url(url: str) -> bool:
    if not isinstance(url, str) or not url.startswith("http"):
        return False

    low = url.lower()

    # Never accept scripts/static SDK files as images.
    blocked = [
        ".js", ".css", ".wasm", ".map",
        "secsdk", "slardar", "sdk-web", "browser.oci",
        "static-tx", "tiktok-infra", "/obj/static",
        "captcha", "verify", "challenge",
        "avatar", "music", "cover",
    ]
    if any(x in low for x in blocked):
        return False

    # Strong image hints from TikTok/CDN URLs.
    image_hints = [
        "image", "photo", "tos-", "p16-", "p19-", "p21-",
        "tplv-", "jpeg", "jpg", "webp", "png",
    ]

    return any(x in low for x in image_hints)

def clean_real_image_urls(urls) -> list:
    clean = []
    seen = set()

    for u in urls or []:
        if not isinstance(u, str):
            continue

        u = u.replace("\\u002F", "/").replace("\\/", "/").replace("&amp;", "&").strip()

        if not looks_like_real_tiktok_image_url(u):
            continue

        if u not in seen:
            clean.append(u)
            seen.add(u)

    return clean


def extract_tiktok_photo_carousel(url: str) -> dict:
    html = fetch_tiktok_html(url)

    json_blobs = []

    # Modern TikTok hydration blob.
    for script_id in ("__UNIVERSAL_DATA_FOR_REHYDRATION__", "SIGI_STATE", "__NEXT_DATA__"):
        m = re.search(
            rf'<script[^>]+id="{re.escape(script_id)}"[^>]*>(.*?)</script>',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if m:
            raw = html_unescape(m.group(1).strip())
            json_blobs.append(raw)

    # Fallback: grab any script containing imagePost.
    for m in re.finditer(r"<script[^>]*>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE):
        raw = m.group(1)
        if "imagePost" in raw or "imageURL" in raw:
            json_blobs.append(html_unescape(raw.strip()))

    all_urls = []
    title = ""
    uploader = ""

    for raw in json_blobs:
        if not raw:
            continue

        # Clean some escaped HTML entities.
        raw = raw.replace("&quot;", '"').replace("&amp;", "&")

        try:
            data = json.loads(raw)
        except Exception:
            # Sometimes the script contains assignment-like JS; try to isolate JSON object.
            first = raw.find("{")
            last = raw.rfind("}")
            if first != -1 and last != -1 and last > first:
                try:
                    data = json.loads(raw[first:last + 1])
                except Exception:
                    continue
            else:
                continue

        if not title:
            title = _first_text_value(data, ["desc", "description", "title", "shareTitle"])
        if not uploader:
            uploader = _first_text_value(data, ["uniqueId", "nickname", "authorName", "author_name"])

        for node in _walk_json(data):
            if "imagePost" in node:
                all_urls.extend(_extract_image_urls_from_image_post(node.get("imagePost")))

            # Some structures expose itemStruct.imagePost.
            item_struct = node.get("itemStruct")
            if isinstance(item_struct, dict) and "imagePost" in item_struct:
                all_urls.extend(_extract_image_urls_from_image_post(item_struct.get("imagePost")))

    # Regex fallback for image-like TikTok CDN URLs only.
    if not all_urls:
        pattern = r'https?:\\?/\\?/[^"\\]+'
        for m in re.finditer(pattern, html):
            u = m.group(0).replace("\\u002F", "/").replace("\\/", "/")
            if looks_like_real_tiktok_image_url(u):
                all_urls.append(u)

    clean = clean_real_image_urls(all_urls)

    media_id = ""
    m = re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    return {
        "kind": "image",
        "title": title or (f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"),
        "uploader": uploader,
        "thumbnail": clean[0] if clean else "",
        "duration": "",
        "webpage_url": url,
        "image_urls": clean,
        "items": [
            {
                "index": i + 1,
                "title": f"TikTok carousel image {i + 1}",
                "thumbnail": image_url,
                "duration": "",
                "ext": "jpg",
            }
            for i, image_url in enumerate(clean)
        ],
        "warning": "" if clean else "Photo / Carousel link detected, but TikTok did not expose image URLs to this server request.",
        "photo_carousel_mode": True,
        "real_carousel_extract": bool(clean),
        "url_first_fallback": not bool(clean),
    }

def _ext_from_content_type(content_type: str, fallback: str = "jpg") -> str:
    content_type = (content_type or "").lower()
    if "webp" in content_type:
        return "webp"
    if "png" in content_type:
        return "png"
    if "jpeg" in content_type or "jpg" in content_type:
        return "jpg"
    return fallback

def download_image_urls_to_output(image_urls, prefix="tiktok_carousel") -> list:
    files = []

    for i, image_url in enumerate(image_urls, start=1):
        req = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": "https://www.tiktok.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as res:
            content_type = res.headers.get("Content-Type", "")
            if not str(content_type).lower().startswith("image/"):
                continue

            data = res.read()
            ext = _ext_from_content_type(content_type, "jpg")

        out = OUTPUT_DIR / f"{prefix}_{uuid.uuid4()}_{i}.{ext}"
        out.write_bytes(data)
        files.append(out)

    return files



def _provider_extract_urls(obj):
    urls = []

    def walk(value):
        if isinstance(value, dict):
            # Common provider field names
            for key in [
                "images", "image_urls", "imageUrls", "photo_urls", "photoUrls",
                "slides", "slideshow", "carousel", "pictures", "downloads",
                "media", "data", "result"
            ]:
                if key in value:
                    walk(value[key])

            # Direct image fields
            for key in ["url", "download_url", "downloadUrl", "src", "image", "photo", "thumbnail"]:
                v = value.get(key)
                if isinstance(v, str) and v.startswith("http"):
                    urls.append(v)

        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str) and value.startswith("http"):
            urls.append(value)

    walk(obj)

    clean = []
    seen = set()
    for u in urls:
        u = str(u).replace("\\u002F", "/").replace("\\/", "/").replace("&amp;", "&").strip()
        low = u.lower()

        if any(bad in low for bad in [".js", ".css", ".wasm", ".map", "secsdk", "slardar", "avatar", "music"]):
            continue

        if u not in seen:
            clean.append(u)
            seen.add(u)

    return clean

def fetch_tiktok_provider_carousel(url: str) -> dict | None:
    """
    Optional external/provider extractor for TikTok photo/slideshow/carousel links.

    Configure:
      export TIKTOK_PROVIDER_URL="https://your-provider-endpoint"
      export TIKTOK_PROVIDER_KEY="optional-key"

    Expected provider can return many possible schemas:
      {"images": ["https://...jpg"]}
      {"data": {"images": [...]}}
      {"result": {"slides": [{"url": "..."}]}}
    """
    provider_url = os.getenv("TIKTOK_PROVIDER_URL", "").strip()
    provider_key = os.getenv("TIKTOK_PROVIDER_KEY", "").strip()

    if not provider_url:
        return None

    payload = json.dumps({"url": url}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

    if provider_key:
        headers["Authorization"] = f"Bearer {provider_key}"
        headers["X-API-Key"] = provider_key

    req = urllib.request.Request(provider_url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            raw = res.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
    except Exception:
        return None

    image_urls = _provider_extract_urls(data)

    if not image_urls:
        return None

    media_id = ""
    m = re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = ""
    if isinstance(data, dict):
        title = data.get("title") or data.get("desc") or ""
        if not title and isinstance(data.get("data"), dict):
            title = data["data"].get("title") or data["data"].get("desc") or ""

    title = title or (f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel")

    return {
        "kind": "image",
        "title": title,
        "uploader": "",
        "thumbnail": image_urls[0],
        "duration": "",
        "webpage_url": url,
        "image_urls": image_urls,
        "items": [
            {
                "index": i + 1,
                "title": f"TikTok carousel image {i + 1}",
                "thumbnail": image_url,
                "duration": "",
                "ext": "jpg",
            }
            for i, image_url in enumerate(image_urls[:35])
        ],
        "warning": "",
        "photo_carousel_mode": True,
        "real_carousel_extract": True,
        "provider_extract": True,
        "url_first_fallback": False,
    }


def get_preview_info(url: str) -> dict:
    url_kind = detect_kind_from_url(url)

    # Real TikTok photo/slideshow/carousel extraction before yt-dlp.
    # yt-dlp often does not support /photo/ URLs, so parse TikTok page JSON first.
    if url_kind == "image":
        try:
            carousel = extract_tiktok_photo_carousel(url)
            if carousel.get("image_urls"):
                return carousel
        except Exception as e:
            # Continue to existing fallbacks below.
            pass

    cmd = ["yt-dlp", "-J", "--no-playlist", url]
    result = run_cmd(cmd, timeout=60)

    # Important: TikTok /photo/ links can fail in yt-dlp.
    # If that happens, do NOT show generic "unsupported"; use oEmbed thumbnail preview.
    if result.returncode != 0:
        err = result.stderr.strip()

        if url_kind in {"image", "story", "video"}:
            # Try TikTok oEmbed first for thumbnail/title.
            embed_preview = preview_from_oembed(
                url,
                url_kind,
                "Preview loaded with TikTok embed metadata because the downloader extractor could not read full media metadata yet."
            )

            # If oEmbed gives useful data, use it.
            if embed_preview.get("thumbnail") or embed_preview.get("title") not in {"TikTok image", "TikTok video", "TikTok story", "TikTok media"}:
                return embed_preview

            # Final fallback: classify from URL path so /photo/ still becomes Photo / Carousel.
            return preview_from_url_only(
                url,
                url_kind,
                "This TikTok link was classified from the URL path. A thumbnail was not available, but the media type is still detected."
            )

        return {
            "kind": "unknown",
            "title": "TikTok media",
            "uploader": "",
            "thumbnail": "",
            "duration": "",
            "items": [],
            "warning": err[-500:] or "Could not load preview metadata.",
        }

    try:
        info = json.loads(result.stdout)
    except Exception:
        info = {}

    kind = guess_kind(info, url)

    # URL path wins for TikTok photo/story pages because yt-dlp can misclassify or fail on slideshows.
    if url_kind in {"image", "story"}:
        kind = url_kind

    entries = info.get("entries") if isinstance(info.get("entries"), list) else []

    items = []
    if entries:
        for i, item in enumerate(entries[:30], start=1):
            if not isinstance(item, dict):
                continue
            items.append({
                "index": i,
                "title": item.get("title") or f"TikTok item {i}",
                "thumbnail": item.get("thumbnail") or "",
                "duration": item.get("duration") or "",
                "ext": item.get("ext") or "",
            })

    if not items:
        items.append({
            "index": 1,
            "title": info.get("title") or "TikTok media",
            "thumbnail": info.get("thumbnail") or "",
            "duration": info.get("duration") or "",
            "ext": info.get("ext") or "",
        })

    # If photo URL produced no useful thumbnail, use oEmbed as a better preview fallback.
    if url_kind == "image" and not (info.get("thumbnail") or (items and items[0].get("thumbnail"))):
        return preview_from_oembed(url, "image", "")

    return {
        "kind": kind,
        "title": info.get("title") or "TikTok media",
        "uploader": info.get("uploader") or info.get("channel") or "",
        "thumbnail": info.get("thumbnail") or (items[0].get("thumbnail") if items else ""),
        "duration": info.get("duration") or "",
        "webpage_url": info.get("webpage_url") or url,
        "items": items,
        "warning": "",
    }

def media_type_for(path: Path) -> str:
    guessed = mimetypes.guess_type(path.name)[0]
    return guessed or "application/octet-stream"

def collect_job_files(job_id: str):
    files = []
    for p in OUTPUT_DIR.glob(f"tiktok_{job_id}*"):
        if p.is_file() and not p.name.endswith((".part", ".ytdl", ".json")):
            files.append(p)
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

def download_with_ytdlp(url: str, mode: str):
    job_id = str(uuid.uuid4())

    if mode == "image" and detect_kind_from_url(url) == "image":
        try:
            carousel = extract_tiktok_photo_carousel(url)
            urls = carousel.get("image_urls") or []
            if urls:
                files = download_image_urls_to_output(urls, "tiktok_carousel")
                if files:
                    return files
        except Exception:
            pass

    if mode == "video":
        # Preserved working best-version video command from the old app.
        output_template = str(OUTPUT_DIR / f"tiktok_{job_id}.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-f", "best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ]
    elif mode == "image":
        output_template = str(OUTPUT_DIR / f"tiktok_{job_id}_%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "-o", output_template,
            url,
        ]
    else:
        output_template = str(OUTPUT_DIR / f"tiktok_{job_id}_%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-f", "best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ]

    result = run_cmd(cmd, timeout=600)

    # If image thumbnail mode creates nothing, fall back to normal yt-dlp download.
    files = collect_job_files(job_id)
    if mode == "image" and not files:
        # First fallback: normal yt-dlp attempt.
        fallback_template = str(OUTPUT_DIR / f"tiktok_{job_id}_fallback.%(ext)s")
        fallback = [
            "yt-dlp",
            "--no-playlist",
            "-o", fallback_template,
            url,
        ]
        result = run_cmd(fallback, timeout=600)
        files = collect_job_files(job_id)

    if mode == "image" and not files:
        # Final fallback: TikTok oEmbed thumbnail, so photo links still produce a useful image file.
        try:
            embed = tiktok_oembed_info(url)
            thumb = embed.get("thumbnail_url") or ""
            if thumb:
                files = [download_url_to_output(thumb, "tiktok_photo_preview", "jpg")]
        except Exception:
            pass

    if result.returncode != 0 and not files:
        raise HTTPException(status_code=500, detail=(result.stderr.strip()[-500:] or "TikTok download failed"))

    if not files:
        raise HTTPException(status_code=500, detail="No TikTok file was created")

    return files

EN_ROUTE_BLOCKS = {
    "all": (
        "All TikTok Downloader for Videos, Photos, Stories and Slideshows",
        [
            "Use All TikTok Downloader when you are not sure what type of TikTok link you copied. The tool detects videos, photo posts, slideshows and stories when the media is accessible, then shows a preview before download.",
            "This universal mode is helpful because TikTok links can point to different media formats. Instead of guessing, paste the link once, check the preview, and download only the file that matches your need."
        ],
    ),
    "video": (
        "TikTok Video Downloader with Preview Before Download",
        [
            "Use the Video tab for TikTok video links. The downloader keeps the working best-version MP4 workflow, so video links are processed using the strongest existing download behavior in your project.",
            "This page is built for users searching for a TikTok video downloader, TikTok MP4 downloader, or a quick way to save a TikTok video from a copied link."
        ],
    ),
    "image": (
        "TikTok Photo / Carousel Downloader for Images and Slideshows",
        [
            "Use the Photo tab for TikTok image posts and slideshow links when image media is available. The preview-first flow helps users check whether the link contains a photo, slideshow, or another media type.",
            "This page targets people who want to download TikTok photos, save TikTok slideshow images, or preview image content before saving it to their device."
        ],
    ),
    "story": (
        "TikTok Story Downloader for Available Story Media",
        [
            "Use the Story tab for TikTok story links. The tool attempts to detect available story media, show a preview, and download the accessible file when the source can be reached.",
            "Story availability may depend on whether the content is public, expired, restricted, deleted, or accessible to the downloader session."
        ],
    ),
}

FR_ROUTE_BLOCKS = {
    "all": (
        "Télécharger TikTok pour vidéos, photos, stories et slideshows",
        [
            "Utilisez Télécharger TikTok lorsque vous ne savez pas exactement quel type de lien TikTok vous avez copié. L’outil détecte les vidéos, photos, slideshows et stories lorsque le média est accessible, puis affiche une prévisualisation avant le téléchargement.",
            "Ce mode universel est utile parce qu’un lien TikTok peut pointer vers plusieurs formats. Collez le lien, vérifiez l’aperçu, puis téléchargez uniquement le fichier dont vous avez besoin."
        ],
    ),
    "video": (
        "Télécharger vidéo TikTok avec aperçu avant téléchargement",
        [
            "Utilisez l’onglet Vidéo pour les liens vidéo TikTok. Le téléchargement vidéo conserve le flux MP4 best-version déjà fonctionnel dans votre projet.",
            "Cette page cible les utilisateurs qui recherchent un téléchargeur vidéo TikTok, un téléchargement TikTok MP4 ou une façon rapide de sauvegarder une vidéo TikTok depuis un lien copié."
        ],
    ),
    "image": (
        "Télécharger photo TikTok pour images et slideshows",
        [
            "Utilisez l’onglet Photo pour les publications image et les liens slideshow TikTok lorsque les images sont disponibles. Le flux avec aperçu aide à vérifier le type de média avant de sauvegarder.",
            "Cette page cible les personnes qui veulent télécharger des photos TikTok, enregistrer des images de slideshow TikTok ou prévisualiser les images avant de les sauvegarder."
        ],
    ),
    "story": (
        "Télécharger story TikTok lorsque le média est disponible",
        [
            "Utilisez l’onglet Story pour les liens story TikTok. L’outil tente de détecter le média disponible, d’afficher un aperçu et de télécharger le fichier accessible.",
            "La disponibilité d’une story dépend du fait que le contenu soit public, non expiré, non supprimé, non restreint et accessible à la session du téléchargeur."
        ],
    ),
}

AR_ROUTE_BLOCKS = {
    "all": (
        "تحميل TikTok للفيديوهات والصور والستوري والسلايدشو",
        [
            "استخدم وضع تحميل TikTok الكامل عندما لا تعرف نوع الرابط الذي نسخته. تحاول الأداة اكتشاف الفيديوهات والصور، سلايدشو وكاروسيل والستوري عندما يكون المحتوى متاحًا، ثم تعرض المعاينة قبل التحميل.",
            "هذا الوضع مفيد لأن روابط TikTok قد تحتوي على أنواع مختلفة من الوسائط. الصق الرابط، تحقق من المعاينة، ثم حمّل الملف الذي تحتاجه فقط."
        ],
    ),
    "video": (
        "تحميل فيديو TikTok مع معاينة قبل التحميل",
        [
            "استخدم تبويب فيديو مع روابط فيديو TikTok. يحافظ هذا الوضع على طريقة تحميل MP4 الأفضل المتوفرة والموجودة أصلًا في مشروعك.",
            "هذه الصفحة مناسبة لمن يبحث عن تحميل فيديو TikTok أو تنزيل TikTok MP4 أو حفظ فيديو TikTok من رابط منسوخ."
        ],
    ),
    "image": (
        "تحميل صور TikTok والسلايدشو",
        [
            "استخدم تبويب صور مع منشورات الصور أو روابط slideshow من TikTok عندما تكون الصور متاحة. تساعد المعاينة على التأكد من نوع الوسائط قبل الحفظ.",
            "هذه الصفحة تستهدف من يريد تحميل صور TikTok أو حفظ صور slideshow أو معاينة الصور قبل تنزيلها."
        ],
    ),
    "story": (
        "تحميل ستوري TikTok عندما تكون الوسائط متاحة",
        [
            "استخدم تبويب ستوري مع روابط TikTok Story. تحاول الأداة اكتشاف الوسائط المتاحة، عرض المعاينة، ثم تحميل الملف إذا كان قابلًا للوصول.",
            "توفر الستوري يعتمد على كون المحتوى عامًا، غير منتهي، غير محذوف، غير مقيد، ومتاحًا لجلسة التحميل."
        ],
    ),
}

def _seo_route_block(lang: str, tool: str) -> str:
    blocks = AR_ROUTE_BLOCKS if lang == "ar" else FR_ROUTE_BLOCKS if lang == "fr" else EN_ROUTE_BLOCKS
    heading, paragraphs = blocks.get(tool, blocks["all"])
    p_html = "\n".join(f"        <p>{html_escape(p)}</p>" for p in paragraphs)
    return f"""      <div id="routeSpecificSeo" class="route-seo-block seo-block">
        <h2>{html_escape(heading)}</h2>
{p_html}
      </div>"""

def route_seo(lang: str, tool: str) -> str:
    route_block = _seo_route_block(lang, tool)

    if lang == "fr":
        return f"""
    <section id="seoContent" class="seo-section">
      <div class="seo-hero">
        <h2>Télécharger des vidéos, stories, photos, slideshows et carrousels TikTok</h2>
        <p>
          Ce téléchargeur TikTok est conçu pour offrir un flux plus clair que les pages de téléchargement simples :
          collez un lien, détectez le type de média, prévisualisez le résultat, puis téléchargez uniquement le fichier nécessaire.
          Il prend en charge les vidéos TikTok, les photos, les slideshows et les stories lorsque le contenu est accessible.
        </p>
      </div>

      <div class="seo-grid">
        <div class="seo-card">
          <strong>Télécharger TikTok Vidéo</strong>
          <p>Utilisez l’onglet Vidéo pour les liens vidéo TikTok. Le téléchargement vidéo conserve la meilleure version MP4 disponible grâce au flux existant.</p>
        </div>
        <div class="seo-card">
          <strong>Télécharger TikTok Photo / Carousel</strong>
          <p>Utilisez l’onglet Photo pour les publications image et les slideshows TikTok lorsque les images sont disponibles.</p>
        </div>
        <div class="seo-card">
          <strong>Télécharger TikTok Story</strong>
          <p>Utilisez l’onglet Story pour les liens story TikTok. L’outil tente d’afficher un aperçu et de télécharger le média accessible.</p>
        </div>
      </div>

{route_block}

      <div class="seo-block">
        <h2>Pourquoi ce téléchargeur TikTok est différent</h2>
        <p>
          Beaucoup d’outils demandent simplement de coller un lien et d’attendre. Cette page utilise une logique de prévisualisation :
          un lien vidéo affiche un aperçu vidéo, un lien photo, slideshow ou carrousel affiche le média disponible, et un lien story est traité séparément.
          Cela réduit les erreurs et aide les utilisateurs à choisir le bon fichier avant de lancer le téléchargement.
        </p>
      </div>

      <div class="seo-block">
        <h2>Comment télécharger depuis TikTok</h2>
        <div class="seo-steps">
          <div class="seo-step"><div><strong>Copiez le lien TikTok</strong><span>Ouvrez TikTok, choisissez la vidéo, la photo, le slideshow ou la story, puis copiez le lien de partage.</span></div></div>
          <div class="seo-step"><div><strong>Choisissez le bon onglet</strong><span>Sélectionnez Tout, Vidéo, Photo ou Story. Chaque onglet aide à filtrer le type de contenu attendu.</span></div></div>
          <div class="seo-step"><div><strong>Prévisualisez le média</strong><span>Cliquez sur la détection pour vérifier le titre, le créateur, la miniature et le type de média avant de télécharger.</span></div></div>
          <div class="seo-step"><div><strong>Téléchargez sur votre appareil</strong><span>Cliquez sur Télécharger. Le fichier sera enregistré par votre navigateur, généralement dans le dossier Téléchargements.</span></div></div>
        </div>
      </div>

      <div class="seo-block">
        <h2>Types de liens TikTok pris en charge</h2>
        <p>
          L’outil est pensé pour les liens vidéo TikTok, les photos TikTok, les slideshows TikTok et les stories TikTok quand le contenu est accessible.
          Il fonctionne dans les navigateurs modernes comme Chrome, Safari, Firefox, Edge, ainsi que sur iPhone, Android, tablette et ordinateur.
        </p>
        <div class="seo-internal-links">
          <a href="/fr/telecharger-tiktok">Télécharger TikTok</a>
          <a href="/fr/telecharger-video-tiktok">Télécharger TikTok Vidéo</a>
          <a href="/fr/telecharger-image-tiktok">Télécharger TikTok Photo</a>
          <a href="/fr/telecharger-story-tiktok">Télécharger TikTok Story</a>
        </div>
        <div class="seo-keywords">
          <span>Télécharger vidéo TikTok</span>
          <span>Télécharger photo TikTok</span>
          <span>Télécharger story TikTok</span>
          <span>Télécharger slideshow TikTok</span>
          <span>TikTok downloader en ligne</span>
          <span>Télécharger TikTok sur iPhone</span>
          <span>Télécharger TikTok sur Android</span>
          <span>Prévisualiser TikTok avant téléchargement</span>
        </div>
      </div>

      <div class="seo-block">
        <h2>Dépannage des téléchargements TikTok</h2>
        <p>
          Si l’aperçu ou le téléchargement échoue, vérifiez que le lien TikTok est complet, public et accessible.
          Certains contenus peuvent être supprimés, privés, restreints, expirés, bloqués par connexion ou indisponibles à la session de téléchargement.
        </p>
      </div>

      <div class="seo-faq">
        <h2>FAQ du téléchargeur TikTok</h2>
        <details><summary>Puis-je télécharger une vidéo TikTok ?</summary><p>Oui. Utilisez Vidéo ou Tout, collez le lien TikTok, détectez l’aperçu, puis téléchargez le fichier MP4 disponible.</p></details>
        <details><summary>Puis-je télécharger des photos TikTok ?</summary><p>Oui, lorsque le lien contient des images ou un slideshow accessible. Utilisez l’onglet Photo pour vérifier le média.</p></details>
        <details><summary>Puis-je télécharger une story TikTok ?</summary><p>Oui, si la story est encore disponible et accessible. Utilisez l’onglet Story pour lancer la détection.</p></details>
        <details><summary>Est-ce que cela fonctionne sur iPhone et Android ?</summary><p>Oui. L’outil fonctionne dans le navigateur, donc il peut être utilisé sur mobile, tablette et ordinateur.</p></details>
        <details><summary>Pourquoi un lien TikTok peut-il échouer ?</summary><p>Le lien peut échouer si le contenu est privé, supprimé, expiré, restreint ou non accessible.</p></details>
      </div>

      <div class="seo-disclaimer">Utilisez cet outil uniquement pour votre propre contenu, des médias publics ou du contenu que vous avez l’autorisation de sauvegarder.</div>
    </section>
"""

    if lang == "ar":
        return f"""
    <section id="seoContent" class="seo-section">
      <div class="seo-hero">
        <h2>تحميل فيديوهات، ستوري، صور وسلايدشو TikTok</h2>
        <p>
          تم تصميم أداة تحميل TikTok هذه لتقديم تجربة أوضح من صفحات التحميل البسيطة:
          الصق الرابط، اكتشف نوع الوسائط، عاين النتيجة، ثم حمّل الملف الذي تحتاجه فقط.
          تدعم الأداة فيديوهات TikTok والصور، سلايدشو وكاروسيل والستوري عندما يكون المحتوى متاحًا.
        </p>
      </div>

      <div class="seo-grid">
        <div class="seo-card">
          <strong>تحميل TikTok Video</strong>
          <p>استخدم تبويب فيديو مع روابط فيديو TikTok. يحافظ تحميل الفيديو على أفضل نسخة MP4 متاحة باستخدام الطريقة الموجودة في مشروعك.</p>
        </div>
        <div class="seo-card">
          <strong>تحميل TikTok Photo / Carousel</strong>
          <p>استخدم تبويب صور مع منشورات الصور أو السلايدشو عندما تكون الصور متاحة.</p>
        </div>
        <div class="seo-card">
          <strong>تحميل TikTok Story</strong>
          <p>استخدم تبويب ستوري مع روابط TikTok Story. تحاول الأداة عرض المعاينة وتحميل الوسائط المتاحة.</p>
        </div>
      </div>

{route_block}

      <div class="seo-block">
        <h2>لماذا أداة تحميل TikTok هذه مختلفة؟</h2>
        <p>
          الكثير من أدوات التحميل تطلب منك لصق الرابط والانتظار فقط. هذه الصفحة تعتمد على المعاينة:
          رابط الفيديو يعرض معاينة فيديو، رابط الصور أو السلايدشو يعرض الوسائط المتاحة، ورابط الستوري تتم معالجته بشكل منفصل.
          هذا يقلل الأخطاء ويساعد المستخدم على اختيار الملف الصحيح قبل التحميل.
        </p>
      </div>

      <div class="seo-block">
        <h2>كيفية التحميل من TikTok</h2>
        <div class="seo-steps">
          <div class="seo-step"><div><strong>انسخ رابط TikTok</strong><span>افتح TikTok واختر الفيديو أو الصورة أو السلايدشو أو الستوري، ثم انسخ رابط المشاركة.</span></div></div>
          <div class="seo-step"><div><strong>اختر التبويب الصحيح</strong><span>اختر الكل، فيديو، صور أو ستوري. كل تبويب يساعد على عرض نوع المحتوى المناسب.</span></div></div>
          <div class="seo-step"><div><strong>عاين الوسائط</strong><span>اضغط على كشف المعاينة للتحقق من العنوان، المنشئ، الصورة المصغرة ونوع الوسائط قبل التحميل.</span></div></div>
          <div class="seo-step"><div><strong>حمّل إلى جهازك</strong><span>اضغط على تحميل. سيحفظ المتصفح الملف غالبًا داخل مجلد التنزيلات.</span></div></div>
        </div>
      </div>

      <div class="seo-block">
        <h2>أنواع روابط TikTok المدعومة</h2>
        <p>
          الأداة مخصصة لروابط فيديو TikTok، صور TikTok، slideshow TikTok وTikTok Story عندما يكون المحتوى متاحًا.
          تعمل داخل المتصفح على Chrome وSafari وFirefox وEdge وعلى iPhone وAndroid والتابلت والكمبيوتر.
        </p>
        <div class="seo-internal-links">
          <a href="/ar/tahmil-tiktok">تحميل TikTok</a>
          <a href="/ar/tahmil-video-tiktok">تحميل TikTok Video</a>
          <a href="/ar/tahmil-image-tiktok">تحميل TikTok Photo</a>
          <a href="/ar/tahmil-story-tiktok">تحميل TikTok Story</a>
        </div>
        <div class="seo-keywords">
          <span>تحميل فيديو TikTok</span>
          <span>تحميل صور TikTok</span>
          <span>تحميل ستوري TikTok</span>
          <span>تحميل slideshow TikTok</span>
          <span>TikTok downloader online</span>
          <span>تحميل TikTok على iPhone</span>
          <span>تحميل TikTok على Android</span>
          <span>معاينة TikTok قبل التحميل</span>
        </div>
      </div>

      <div class="seo-block">
        <h2>حل مشاكل تحميل TikTok</h2>
        <p>
          إذا فشلت المعاينة أو التحميل، تأكد أن الرابط كامل، عام وقابل للوصول.
          بعض المحتوى قد يكون خاصًا، محذوفًا، منتهيًا، مقيدًا، يتطلب تسجيل دخول أو غير متاح لجلسة التحميل.
        </p>
      </div>

      <div class="seo-faq">
        <h2>أسئلة شائعة حول تحميل TikTok</h2>
        <details><summary>هل يمكنني تحميل فيديو TikTok؟</summary><p>نعم. استخدم فيديو أو الكل، الصق الرابط، اكشف المعاينة ثم حمّل ملف MP4 المتاح.</p></details>
        <details><summary>هل يمكنني تحميل صور TikTok؟</summary><p>نعم، إذا كان الرابط يحتوي على صور أو slideshow متاح. استخدم تبويب صور للتحقق من الوسائط.</p></details>
        <details><summary>هل يمكنني تحميل ستوري TikTok؟</summary><p>نعم، إذا كانت الستوري لا تزال متاحة وقابلة للوصول. استخدم تبويب ستوري للكشف عنها.</p></details>
        <details><summary>هل يعمل على iPhone وAndroid؟</summary><p>نعم. تعمل الأداة داخل المتصفح ويمكن استخدامها على الهاتف أو التابلت أو الكمبيوتر.</p></details>
        <details><summary>لماذا قد يفشل رابط TikTok؟</summary><p>قد يفشل الرابط إذا كان المحتوى خاصًا، محذوفًا، منتهيًا، مقيدًا أو غير قابل للوصول.</p></details>
      </div>

      <div class="seo-disclaimer">استخدم هذه الأداة فقط مع محتواك الخاص أو الوسائط العامة أو المحتوى الذي لديك إذن بحفظه.</div>
    </section>
"""

    return f"""
    <section id="seoContent" class="seo-section">
      <div class="seo-hero">
        <h2>Download TikTok Videos, Stories, Photos, Slideshows and Carousels</h2>
        <p>
          This TikTok downloader is built around a clearer flow than simple paste-and-wait pages:
          paste a link, detect the media type, preview the result, then download only the file you need.
          It supports TikTok videos, photo posts, slideshows and stories when the media is available and accessible.
        </p>
      </div>

      <div class="seo-grid">
        <div class="seo-card">
          <strong>TikTok Video Downloader</strong>
          <p>Use the Video tab for TikTok video links. The existing video downloader keeps the best available MP4 workflow from your working version.</p>
        </div>
        <div class="seo-card">
          <strong>TikTok Photo / Carousel Downloader</strong>
          <p>Use the Photo tab for TikTok photo, slideshow or carousel links when image media is available.</p>
        </div>
        <div class="seo-card">
          <strong>TikTok Story Downloader</strong>
          <p>Use the Story tab for TikTok story links. The tool attempts to detect and download available story media when accessible.</p>
        </div>
      </div>

{route_block}

      <div class="seo-block">
        <h2>Why This TikTok Downloader Is Different</h2>
        <p>
          Many downloader pages make users paste a link and wait without knowing what will happen. This page is designed around detection and preview.
          A video link shows a video-focused preview, a photo, slideshow or carousel link can be checked before saving, and story links are handled separately.
          This makes the tool easier to use on mobile and helps users avoid downloading the wrong file.
        </p>
      </div>

      <div class="seo-block">
        <h2>How to Download TikTok Media</h2>
        <div class="seo-steps">
          <div class="seo-step"><div><strong>Copy the TikTok link</strong><span>Open TikTok, choose the video, photo, slideshow or story you want to save, then copy the share link.</span></div></div>
          <div class="seo-step"><div><strong>Choose the correct downloader tab</strong><span>Select All, Video, Photo or Story. Each tab helps filter the preview toward the media type you expect.</span></div></div>
          <div class="seo-step"><div><strong>Preview before downloading</strong><span>Click Detect Preview to check the title, creator, thumbnail and detected media type before downloading.</span></div></div>
          <div class="seo-step"><div><strong>Download to your device</strong><span>Click the download button. Your browser saves the file directly, usually in your Downloads folder.</span></div></div>
        </div>
      </div>

      <div class="seo-block">
        <h2>Supported TikTok Link Types</h2>
        <p>
          The downloader is designed for common TikTok URLs including video links, photo posts, slideshow posts and story links when the content is accessible.
          It works from modern browsers including Chrome, Safari, Firefox and Edge, on iPhone, Android, tablets and desktop computers.
        </p>
        <div class="seo-internal-links">
          <a href="/tiktok-downloader">All TikTok Downloader</a>
          <a href="/tiktok-video-downloader">TikTok Video Downloader</a>
          <a href="/tiktok-image-downloader">TikTok Photo / Carousel Downloader</a>
          <a href="/tiktok-story-downloader">TikTok Story Downloader</a>
        </div>
        <div class="seo-keywords">
          <span>TikTok video downloader</span>
          <span>TikTok photo downloader</span>
          <span>TikTok story downloader</span>
          <span>TikTok slideshow downloader</span>
          <span>Download TikTok on iPhone</span>
          <span>Download TikTok on Android</span>
          <span>Preview TikTok before download</span>
          <span>TikTok MP4 downloader</span>
        </div>
      </div>

      <div class="seo-block">
        <h2>Troubleshooting TikTok Downloads</h2>
        <p>
          If a preview or download does not load, check that the TikTok link is complete, public and accessible.
          Some content may be private, deleted, restricted, expired, blocked by login access, or not available to the configured downloader session.
          TikTok may also limit saving when the creator has not enabled download permissions.
        </p>
      </div>

      <div class="seo-faq">
        <h2>TikTok Downloader FAQ</h2>
        <details><summary>Can I download TikTok videos?</summary><p>Yes. Choose Video or All mode, paste the TikTok URL, detect the preview, then download the available MP4 file.</p></details>
        <details><summary>Can I download TikTok photos?</summary><p>Yes, when the link contains accessible image or slideshow media. Use the Photo tab to check the preview.</p></details>
        <details><summary>Can I download TikTok stories?</summary><p>Yes, when the story is still available and accessible. Use the Story tab to detect and download available story media.</p></details>
        <details><summary>Does this work on iPhone, Android and desktop?</summary><p>Yes. The tool runs in the browser and can be used from phones, tablets and desktop computers.</p></details>
        <details><summary>Why does a TikTok link sometimes fail?</summary><p>A link may fail if the content is private, deleted, expired, restricted, requires login access, or is not available to the downloader session.</p></details>
        <details><summary>Where do downloaded TikTok files go?</summary><p>Your browser handles the download. Most browsers save files to the Downloads folder unless you choose another location.</p></details>
        <details><summary>Is this tool affiliated with TikTok?</summary><p>No. This tool is independent and is not affiliated with TikTok, Douyin or ByteDance.</p></details>
      </div>

      <div class="seo-disclaimer">Use this downloader only for your own content, public media, or content you have permission to save. Do not use it to violate platform rules, copyrights or privacy rights.</div>
    </section>
"""

def render_index(tool: str = "all", lang: str = "en", base_url: str = "") -> str:
    tool = tool if tool in TOOLS else "all"
    lang = lang if lang in PAGES else "en"
    page = PAGES[lang][tool]
    paths = PATHS[lang]
    base = base_url.rstrip("/") if base_url else ""

    html_lang = 'lang="ar" dir="rtl"' if lang == "ar" else f'lang="{lang}"'
    current_flag = "🇸🇦" if lang == "ar" else "🇫🇷" if lang == "fr" else "🇺🇸"

    ui = {
        "en": {
            "eyebrow": "Fast, friendly & browser-based",
            "brand_note": "the easy media helper",
            "paste": "Paste",
            "clear": "Clear",
            "secure": "No account needed",
            "preview": "Preview before saving",
            "devices": "Works on every device",
            "tools": "Choose a format",
            "footer": "Independent downloader for media you own or have permission to save.",
            "privacy": "Your link is processed only to prepare the requested media.",
            "menu": "Open menu",
        },
        "fr": {
            "eyebrow": "Rapide, simple et dans votre navigateur",
            "brand_note": "l’assistant média facile",
            "paste": "Coller",
            "clear": "Effacer",
            "secure": "Aucun compte requis",
            "preview": "Aperçu avant téléchargement",
            "devices": "Compatible avec tous les appareils",
            "tools": "Choisissez un format",
            "footer": "Outil indépendant pour les médias que vous possédez ou avez l’autorisation d’enregistrer.",
            "privacy": "Votre lien est traité uniquement pour préparer le média demandé.",
            "menu": "Ouvrir le menu",
        },
        "ar": {
            "eyebrow": "سريع وسهل ويعمل من المتصفح",
            "brand_note": "مساعد الوسائط السهل",
            "paste": "لصق",
            "clear": "مسح",
            "secure": "بدون إنشاء حساب",
            "preview": "معاينة قبل الحفظ",
            "devices": "يعمل على كل الأجهزة",
            "tools": "اختر الصيغة",
            "footer": "أداة مستقلة للوسائط التي تملكها أو لديك إذن بحفظها.",
            "privacy": "تتم معالجة الرابط فقط لتجهيز الوسائط المطلوبة.",
            "menu": "فتح القائمة",
        },
    }[lang]

    tab_icons = {
        "all": "✦",
        "video": "▶",
        "audio": "♫",
        "story": "◉",
    }
    tabs = []
    for tab in TOOLS:
        active = " active" if tab == tool else ""
        current = ' aria-current="page"' if tab == tool else ""
        tabs.append(
            f'<a href="{paths[tab]}" class="tool-tab{active}" data-tool="{tab}"{current}>'
            f'<span class="tool-tab-icon" aria-hidden="true">{tab_icons.get(tab, "•")}</span>'
            f'<span>{TAB_LABELS[lang][tab]}</span></a>'
        )

    alternates = []
    for alt in ("en", "fr", "ar"):
        alternates.append(f'<link rel="alternate" hreflang="{alt}" href="{base}{PATHS[alt][tool]}">')
    alternates.append(f'<link rel="alternate" hreflang="x-default" href="{base}{PATHS["en"][tool]}">')

    lang_menu = f"""
      <div class="lang-picker" aria-label="Language selector">
        <button type="button" class="lang-current" aria-haspopup="true" aria-expanded="false" onclick="event.preventDefault(); event.stopPropagation(); const picker=this.closest('.lang-picker'); picker.classList.toggle('open'); this.setAttribute('aria-expanded', picker.classList.contains('open') ? 'true' : 'false');">
          <span class="lang-current-flag">{current_flag}</span><span class="lang-chevron">⌄</span>
        </button>
        <div class="lang-menu" role="menu">
          <a href="/tiktok-downloader" role="menuitem"><span class="lang-flag">🇺🇸</span><span>English</span></a>
          <a href="/fr/telecharger-tiktok" role="menuitem"><span class="lang-flag">🇫🇷</span><span>Français</span></a>
          <a href="/ar/tahmil-tiktok" role="menuitem"><span class="lang-flag">🇸🇦</span><span>العربية</span></a>
        </div>
      </div>
"""

    body_lang = f'data-lang="{lang}"' if lang != "en" else ""
    note = "Use only your own content or content you have permission to download." if lang == "en" else "Utilisez uniquement votre propre contenu ou du contenu que vous avez l’autorisation de télécharger." if lang == "fr" else "استخدم فقط محتواك الخاص أو المحتوى الذي لديك إذن بتحميله."

    return f"""<!doctype html>
<html {html_lang}>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html_escape(page['title'])} · Grabfrog</title>
  <meta name="description" content="{html_escape(page['description'])}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{base}{paths[tool]}">
  {chr(10).join(alternates)}
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@400;500;600;700&family=Caveat:wght@500;700&display=swap" />
  <link rel="icon" type="image/svg+xml" href="/static/assets/favicon.svg">
  <meta name="theme-color" content="#f7f4e8">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{html_escape(page['title'])}">
  <meta property="og:description" content="{html_escape(page['description'])}">
  <meta property="og:image" content="{base}/static/assets/og-tiktok-downloader.svg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html_escape(page['title'])}">
  <meta name="twitter:description" content="{html_escape(page['description'])}">
  <meta name="twitter:image" content="{base}/static/assets/og-tiktok-downloader.svg">
  <link rel="stylesheet" href="/static/index.css?v=grabfrog_ui_v1" />
</head>
<body data-selected-tool="{tool}" {body_lang}>
<script>window.PLATFORM_SLUG = "tiktok";</script>

<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{paths['all']}" aria-label="Grabfrog TikTok Downloader home">
      <span class="brand-mark" aria-hidden="true">
        <span class="frog-eye frog-eye-left"></span><span class="frog-eye frog-eye-right"></span>
        <span class="frog-smile"></span>
      </span>
      <span class="brand-copy"><strong>Grabfrog</strong><small>{html_escape(ui['brand_note'])}</small></span>
    </a>
    <nav class="header-links" aria-label="Primary navigation">
      <a href="{paths['video']}">{TAB_LABELS[lang]['video']}</a>
      <a href="{paths['audio']}">{TAB_LABELS[lang]['audio']}</a>
      <a href="{paths['story']}">{TAB_LABELS[lang]['story']}</a>
    </nav>
    {lang_menu}
  </div>
</header>

<main>
  <section class="hero-section">
    <div class="hero-orb hero-orb-one" aria-hidden="true"></div>
    <div class="hero-orb hero-orb-two" aria-hidden="true"></div>
    <div class="hero-copy">
      <div class="eyebrow"><span>●</span>{html_escape(ui['eyebrow'])}</div>
      <h1 class="mini-brand">{page['heading']}</h1>
      <p class="mini-subtitle">{html_escape(page['subtitle'])}</p>
      <div class="scribble-note" aria-hidden="true">TikTok in. Your file out. <span>↘</span></div>
    </div>

    <section class="dashboard" aria-label="TikTok downloader">
      <div class="dashboard-topline">
        <div>
          <span class="field-label">{html_escape(ui['tools'])}</span>
          <span class="live-dot"><i></i> online</span>
        </div>
      </div>

      <nav id="toolTabs" class="tool-tabs" aria-label="TikTok downloader tools">
        {' '.join(tabs)}
      </nav>

      <form id="downloadForm" novalidate>
        <div class="input-row">
          <div class="url-field">
            <span class="url-icon" aria-hidden="true">↗</span>
            <input id="urlInput" type="url" name="url" inputmode="url" autocomplete="url" spellcheck="false" placeholder="{html_escape(page['placeholder'])}" aria-label="{html_escape(page['placeholder'])}" required>
            <div class="input-actions">
              <button id="clearBtn" class="input-action clear-action" type="button" aria-label="{html_escape(ui['clear'])}" title="{html_escape(ui['clear'])}">×</button>
              <button id="pasteBtn" class="input-action paste-action" type="button">{html_escape(ui['paste'])}</button>
            </div>
          </div>
          <button id="inspectBtn" class="primary-action" type="submit">
            <span>{html_escape(page['button'])}</span><span class="button-arrow" aria-hidden="true">→</span>
          </button>
        </div>
        <input type="hidden" id="modeInput" name="mode" value="{tool}">
      </form>

      <div id="status" class="status" role="status" aria-live="polite"></div>
      <div id="progressWrap" class="progress-wrap" style="display:none;" aria-live="polite">
        <div class="progress-meta"><span id="progressText">Preparing...</span><span id="progressPct">0%</span></div>
        <div class="progress-bar"><div id="progressFill"></div></div>
      </div>

      <section id="preview" class="preview" style="display:none;"></section>
      <section id="downloads" class="downloads" style="display:none;"></section>

      <div class="trust-row" aria-label="Tool benefits">
        <span><b aria-hidden="true">✓</b>{html_escape(ui['secure'])}</span>
        <span><b aria-hidden="true">⌁</b>{html_escape(ui['preview'])}</span>
        <span><b aria-hidden="true">◇</b>{html_escape(ui['devices'])}</span>
      </div>
      <p class="note">{html_escape(note)}</p>
    </section>
  </section>

  <div class="content-wrap">
    {route_seo(lang, tool)}
  </div>
</main>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-brand"><span class="footer-frog">●</span><strong>Grabfrog</strong></div>
    <p>{html_escape(ui['footer'])}</p>
    <small>{html_escape(ui['privacy'])}</small>
  </div>
</footer>

<script src="/static/index.js?v=grabfrog_ui_v1"></script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return render_index("all", "en", str(request.base_url).rstrip("/"))

@app.get("/tiktok-downloader", response_class=HTMLResponse)
def en_all(request: Request):
    return render_index("all", "en", str(request.base_url).rstrip("/"))

@app.get("/tiktok-video-downloader", response_class=HTMLResponse)
def en_video(request: Request):
    return render_index("video", "en", str(request.base_url).rstrip("/"))

@app.get("/tiktok-image-downloader", response_class=HTMLResponse)
def en_image(request: Request):
    return render_index("image", "en", str(request.base_url).rstrip("/"))

@app.get("/tiktok-story-downloader", response_class=HTMLResponse)
def en_story(request: Request):
    return render_index("story", "en", str(request.base_url).rstrip("/"))

@app.get("/fr/telecharger-tiktok", response_class=HTMLResponse)
def fr_all(request: Request):
    return render_index("all", "fr", str(request.base_url).rstrip("/"))

@app.get("/fr/telecharger-video-tiktok", response_class=HTMLResponse)
def fr_video(request: Request):
    return render_index("video", "fr", str(request.base_url).rstrip("/"))

@app.get("/fr/telecharger-image-tiktok", response_class=HTMLResponse)
def fr_image(request: Request):
    return render_index("image", "fr", str(request.base_url).rstrip("/"))

@app.get("/fr/telecharger-story-tiktok", response_class=HTMLResponse)
def fr_story(request: Request):
    return render_index("story", "fr", str(request.base_url).rstrip("/"))

@app.get("/ar/tahmil-tiktok", response_class=HTMLResponse)
def ar_all(request: Request):
    return render_index("all", "ar", str(request.base_url).rstrip("/"))

@app.get("/ar/tahmil-video-tiktok", response_class=HTMLResponse)
def ar_video(request: Request):
    return render_index("video", "ar", str(request.base_url).rstrip("/"))

@app.get("/ar/tahmil-image-tiktok", response_class=HTMLResponse)
def ar_image(request: Request):
    return render_index("image", "ar", str(request.base_url).rstrip("/"))

@app.get("/ar/tahmil-story-tiktok", response_class=HTMLResponse)
def ar_story(request: Request):
    return render_index("story", "ar", str(request.base_url).rstrip("/"))

@app.get("/video-downloader")
def old_video():
    return RedirectResponse("/tiktok-video-downloader", status_code=301)

@app.get("/image-downloader")
def old_image():
    return RedirectResponse("/tiktok-image-downloader", status_code=301)

@app.get("/story-downloader")
def old_story():
    return RedirectResponse("/tiktok-story-downloader", status_code=301)

@app.post("/api/preview-tiktok")
def preview_tiktok(url: str = Form(...), mode: str = Form("all")):
    if not safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid TikTok URL")

    selected = mode if mode in TOOLS else "all"
    url_kind = detect_kind_from_url(url)

    # HARD OVERRIDE:
    # TikTok /photo/ links need a strong extractor. Try provider/API first,
    # then browser/local fallback.
    info = None
    if url_kind == "image":
        provider_info = fetch_tiktok_provider_carousel(url)
        if provider_info:
            info = provider_info
            info["preview_source"] = "provider_carousel"

        if info is None:
            try:
                info = extract_tiktok_photo_carousel_playwright(url)
                if info:
                    info["preview_source"] = "playwright_route_override"
            except Exception as e:
                info = preview_from_url_only(
                    url,
                    "image",
                    f"Photo / Carousel link detected, but browser extraction failed: {type(e).__name__}: {str(e)[:180]}"
                )
                info["preview_source"] = "playwright_route_exception"

    if info is None:
        info = get_preview_info(url)
        info["preview_source"] = info.get("preview_source") or "default_get_preview_info"

    detected = info.get("kind") or "unknown"

    # Story fallback: TikTok stories can sometimes resolve as /video/ pages.
    story_video_fallback = selected == "story" and detected == "video" and "/video/" in url.lower()

    # URL-first override: /photo/ is image/photo-carousel.
    if url_kind == "image":
        detected = "image"

    final_detected = "story" if story_video_fallback else detected
    photo_carousel_mode = final_detected == "image" and "/photo/" in url.lower()

    allowed = selected == "all" or selected == final_detected or story_video_fallback
    suggestion = final_detected if final_detected in TOOLS else "all"

    info["selected"] = selected
    info["detected"] = final_detected
    info["raw_detected"] = detected
    info["photo_carousel_mode"] = bool(photo_carousel_mode)
    info["story_video_fallback"] = bool(story_video_fallback)
    info["allowed"] = bool(allowed)
    info["strict_allowed"] = bool(allowed)
    info["suggestion"] = suggestion
    info["mode_mismatch"] = not bool(allowed)

    return info

@app.post("/download-tiktok")
def download_tiktok(url: str = Form(...), mode: str = Form("video")):
    if not safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid TikTok URL")

    mode = mode if mode in TOOLS else "video"
    if mode == "all":
        mode = "video"

    files = download_with_ytdlp(url, mode)

    payload_files = []
    for p in files:
        payload_files.append({
            "filename": p.name,
            "download_url": f"/download/{p.name}",
            "media_type": media_type_for(p),
            "size": p.stat().st_size,
        })

    return {
        "download_url": payload_files[0]["download_url"],
        "filename": payload_files[0]["filename"],
        "files": payload_files,
        "mode": mode,
    }

@app.get("/download/{filename}")
def download(filename: str):
    clean = safe_filename(filename)
    file_path = OUTPUT_DIR / clean

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type=media_type_for(file_path), filename=clean)

@app.get("/robots.txt")
def robots_txt():
    return Response("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n", media_type="text/plain")

@app.get("/sitemap.xml")
def sitemap_xml(request: Request):
    base = str(request.base_url).rstrip("/")
    urls = []
    for lang_paths in PATHS.values():
        urls.extend(lang_paths.values())

    body = ['<?xml version="1.0" encoding="UTF-8"?>']
    body.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        body.append(f"  <url><loc>{base}{url}</loc></url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")

# === PLAYWRIGHT TIKTOK PHOTO/CAROUSEL EXTRACTOR OVERRIDE START ===

_old_get_preview_info_before_playwright = get_preview_info
_old_download_with_ytdlp_before_playwright = download_with_ytdlp

def _pw_is_bad_asset_url(url: str) -> bool:
    low = (url or "").lower()

    bad = [
        ".js", ".css", ".map", ".wasm",
        "secsdk", "slardar", "sdk-web", "browser.oci",
        "static-tx", "tiktok-infra", "/obj/static",
        "captcha", "verify", "challenge",
        "avatar", "music", "cover",
        "logo", "sprite", "favicon",
    ]

    return any(x in low for x in bad)

def _pw_looks_like_image_url(url: str) -> bool:
    if not isinstance(url, str) or not url.startswith("http"):
        return False

    low = url.lower()

    if _pw_is_bad_asset_url(low):
        return False

    good = [
        "p16-", "p19-", "p21-", "tos-", "tplv-",
        "tiktokcdn", "tiktokcdn-us", "byteimg",
        ".jpg", ".jpeg", ".png", ".webp",
        "image", "photo",
    ]

    return any(x in low for x in good)

def _pw_clean_image_urls(urls):
    clean = []
    seen = set()

    for u in urls or []:
        if not isinstance(u, str):
            continue

        u = u.replace("\\u002F", "/").replace("\\/", "/").replace("&amp;", "&").strip()

        # srcset can contain "url 720w"
        if " " in u and u.startswith("http"):
            u = u.split(" ")[0].strip()

        if not _pw_looks_like_image_url(u):
            continue

        if u not in seen:
            clean.append(u)
            seen.add(u)

    return clean

def extract_tiktok_photo_carousel_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import re as _re

    image_urls = []
    title = ""
    uploader = ""

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = browser.new_context(
            viewport={"width": 390, "height": 920},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.tiktok.com/",
            },
        )

        page = context.new_page()

        seen_resources = []

        def on_response(response):
            try:
                rurl = response.url
                ctype = response.headers.get("content-type", "")
                if str(ctype).lower().startswith("image/") and _pw_looks_like_image_url(rurl):
                    seen_resources.append(rurl)
            except Exception:
                pass

        page.on("response", on_response)

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6500)

        # Trigger lazy loading / carousel assets.
        for _ in range(6):
            page.mouse.wheel(0, 650)
            page.wait_for_timeout(700)

        # Try keyboard/right arrow navigation for carousel slides.
        for _ in range(12):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(450)

        data = page.evaluate(
            """() => {
                const urls = [];

                const push = (v) => {
                    if (!v) return;
                    if (Array.isArray(v)) {
                        v.forEach(push);
                        return;
                    }
                    if (typeof v === 'string') {
                        urls.push(v);
                    }
                };

                document.querySelectorAll('img').forEach(img => {
                    push(img.currentSrc);
                    push(img.src);
                    push(img.getAttribute('src'));
                    push(img.getAttribute('data-src'));
                    push(img.getAttribute('data-original'));
                    push(img.getAttribute('srcset'));
                });

                document.querySelectorAll('source').forEach(src => {
                    push(src.getAttribute('srcset'));
                    push(src.getAttribute('src'));
                });

                document.querySelectorAll('*').forEach(el => {
                    const bg = getComputedStyle(el).backgroundImage || '';
                    const matches = [...bg.matchAll(/url\\(["']?(.*?)["']?\\)/g)];
                    matches.forEach(m => push(m[1]));
                });

                try {
                    performance.getEntriesByType('resource').forEach(r => push(r.name));
                } catch (e) {}

                const title =
                    document.querySelector('meta[property="og:title"]')?.content ||
                    document.querySelector('title')?.innerText ||
                    document.title ||
                    '';

                const desc =
                    document.querySelector('meta[property="og:description"]')?.content ||
                    '';

                return { urls, title, desc };
            }"""
        )

        browser.close()

    raw_urls = []
    raw_urls.extend(seen_resources)
    raw_urls.extend(data.get("urls") or [])

    # Split srcset values.
    expanded = []
    for u in raw_urls:
        if isinstance(u, str) and "," in u:
            for part in u.split(","):
                expanded.append(part.strip().split(" ")[0])
        else:
            expanded.append(u)

    clean = _pw_clean_image_urls(expanded)

    # Prefer larger TikTok image/CDN resources by rough URL quality.
    clean = sorted(
        clean,
        key=lambda u: (
            0 if any(x in u.lower() for x in ["avatar", "music", "cover"]) else 1,
            len(u),
        ),
        reverse=True,
    )

    # Deduplicate again after sorting.
    final = []
    seen = set()
    for u in clean:
        if u not in seen:
            final.append(u)
            seen.add(u)

    # Safety: if only tiny/static assets got through, do not fake success.
    image_urls = final[:35]

    media_id = ""
    m = _re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = (data.get("title") or "").strip()
    if not title or "download tiktok" in title.lower():
        title = f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"

    return {
        "kind": "image",
        "title": title,
        "uploader": uploader,
        "thumbnail": image_urls[0] if image_urls else "",
        "duration": "",
        "webpage_url": url,
        "image_urls": image_urls,
        "items": [
            {
                "index": i + 1,
                "title": f"TikTok carousel image {i + 1}",
                "thumbnail": image_url,
                "duration": "",
                "ext": "jpg",
            }
            for i, image_url in enumerate(image_urls)
        ] or [
            {
                "index": 1,
                "title": f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel",
                "thumbnail": "",
                "duration": "",
                "ext": "jpg",
            }
        ],
        "warning": "" if image_urls else "Photo / Carousel link detected, but the browser extractor could not access the carousel image URLs. TikTok may be blocking this request.",
        "photo_carousel_mode": True,
        "real_carousel_extract": bool(image_urls),
        "playwright_extract": True,
        "url_first_fallback": not bool(image_urls),
    }

def get_preview_info(url: str) -> dict:
    # Browser-render TikTok /photo/ links first.
    if detect_kind_from_url(url) == "image":
        try:
            data = extract_tiktok_photo_carousel_playwright(url)
            if data.get("image_urls"):
                return data
        except Exception as e:
            # Fall back to the previous non-browser extractor.
            pass

    return _old_get_preview_info_before_playwright(url)

def download_with_ytdlp(url: str, mode: str):
    # Browser-render TikTok /photo/ links first for real carousel image downloads.
    if mode == "image" and detect_kind_from_url(url) == "image":
        try:
            data = extract_tiktok_photo_carousel_playwright(url)
            urls = data.get("image_urls") or []
            if urls:
                return download_image_urls_to_output(urls, "tiktok_carousel")
        except Exception:
            pass

    return _old_download_with_ytdlp_before_playwright(url, mode)

# === PLAYWRIGHT TIKTOK PHOTO/CAROUSEL EXTRACTOR OVERRIDE END ===

# === PERSISTENT TIKTOK PROFILE CAROUSEL EXTRACTOR OVERRIDE START ===

_old_extract_tiktok_photo_carousel_playwright_profile = extract_tiktok_photo_carousel_playwright

def extract_tiktok_photo_carousel_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import re as _re

    profile_dir = str((BASE_DIR / "playwright_profiles" / "tiktok").resolve())
    image_urls = []
    seen_resources = []

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            viewport={"width": 390, "height": 920},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.tiktok.com/",
            },
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.new_page()

        def on_response(response):
            try:
                rurl = response.url
                ctype = response.headers.get("content-type", "")
                if str(ctype).lower().startswith("image/") and _pw_looks_like_image_url(rurl):
                    seen_resources.append(rurl)
            except Exception:
                pass

        page.on("response", on_response)

        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)

        # scroll/tap/right-key to trigger lazy carousel assets
        for _ in range(5):
            page.mouse.wheel(0, 650)
            page.wait_for_timeout(700)

        for _ in range(16):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(450)

        data = page.evaluate(
            """() => {
                const urls = [];

                const push = (v) => {
                    if (!v) return;
                    if (Array.isArray(v)) return v.forEach(push);
                    if (typeof v === 'string') urls.push(v);
                };

                document.querySelectorAll('img').forEach(img => {
                    push(img.currentSrc);
                    push(img.src);
                    push(img.getAttribute('src'));
                    push(img.getAttribute('data-src'));
                    push(img.getAttribute('data-original'));
                    push(img.getAttribute('srcset'));
                });

                document.querySelectorAll('source').forEach(src => {
                    push(src.getAttribute('srcset'));
                    push(src.getAttribute('src'));
                });

                document.querySelectorAll('*').forEach(el => {
                    const bg = getComputedStyle(el).backgroundImage || '';
                    const matches = [...bg.matchAll(/url\\(["']?(.*?)["']?\\)/g)];
                    matches.forEach(m => push(m[1]));
                });

                try {
                    performance.getEntriesByType('resource').forEach(r => push(r.name));
                } catch (e) {}

                return {
                    urls,
                    title: document.querySelector('meta[property="og:title"]')?.content || document.title || '',
                    bodyText: document.body ? document.body.innerText.slice(0, 1000) : '',
                    html: document.documentElement ? document.documentElement.outerHTML.slice(0, 5000) : ''
                };
            }"""
        )

        context.close()

    raw_urls = []
    raw_urls.extend(seen_resources)
    raw_urls.extend(data.get("urls") or [])

    expanded = []
    for u in raw_urls:
        if isinstance(u, str) and "," in u:
            for part in u.split(","):
                expanded.append(part.strip().split(" ")[0])
        else:
            expanded.append(u)

    clean = _pw_clean_image_urls(expanded)

    # keep only non-static real-looking images
    final = []
    seen = set()
    for u in clean:
        low = u.lower()
        if any(x in low for x in ["secsdk", "slardar", ".js", ".css", "/obj/static", "avatar", "music"]):
            continue
        if u not in seen:
            final.append(u)
            seen.add(u)

    media_id = ""
    m = _re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = (data.get("title") or "").strip()
    if not title or "download tiktok" in title.lower():
        title = f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"

    warning = ""
    if not final:
        body_text = (data.get("bodyText") or "").lower()
        if "log in" in body_text or "captcha" in body_text or "verify" in body_text:
            warning = "TikTok is asking this browser session to log in or pass verification before carousel images are exposed."
        else:
            warning = "Photo / Carousel link detected, but TikTok did not expose carousel image URLs to this browser session."

    return {
        "kind": "image",
        "title": title,
        "uploader": "",
        "thumbnail": final[0] if final else "",
        "duration": "",
        "webpage_url": url,
        "image_urls": final,
        "items": [
            {
                "index": i + 1,
                "title": f"TikTok carousel image {i + 1}",
                "thumbnail": image_url,
                "duration": "",
                "ext": "jpg",
            }
            for i, image_url in enumerate(final[:35])
        ] or [
            {
                "index": 1,
                "title": f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel",
                "thumbnail": "",
                "duration": "",
                "ext": "jpg",
            }
        ],
        "warning": warning,
        "photo_carousel_mode": True,
        "real_carousel_extract": bool(final),
        "playwright_extract": True,
        "persistent_profile": True,
        "url_first_fallback": not bool(final),
    }

# === PERSISTENT TIKTOK PROFILE CAROUSEL EXTRACTOR OVERRIDE END ===

# === TIKTOK CAROUSEL SCREENSHOT FALLBACK OVERRIDE START ===

_old_extract_tiktok_photo_carousel_playwright_before_screenshot = extract_tiktok_photo_carousel_playwright
_old_download_with_ytdlp_before_screenshot = download_with_ytdlp

def _hash_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def _screenshot_carousel_slides(page, max_slides: int = 12) -> list:
    files = []
    hashes = set()

    for i in range(max_slides):
        out = OUTPUT_DIR / f"tiktok_carousel_screen_{uuid.uuid4()}_{i+1}.png"

        # Screenshot the viewport. This guarantees we show what the browser can actually see.
        page.screenshot(path=str(out), full_page=False)

        digest = _hash_file(out)
        if digest not in hashes:
            hashes.add(digest)
            files.append(out)
        else:
            out.unlink(missing_ok=True)

        # Try several navigation methods for carousel/photo posts.
        try:
            page.keyboard.press("ArrowRight")
        except Exception:
            pass

        try:
            page.mouse.wheel(520, 0)
        except Exception:
            pass

        try:
            page.touchscreen.tap(350, 450)
        except Exception:
            pass

        page.wait_for_timeout(850)

    return files

def extract_tiktok_photo_carousel_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import re as _re

    profile_dir = str((BASE_DIR / "playwright_profiles" / "tiktok").resolve())
    direct_urls = []
    seen_resources = []

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            viewport={"width": 430, "height": 920},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.tiktok.com/",
            },
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.new_page()

        def on_response(response):
            try:
                rurl = response.url
                ctype = response.headers.get("content-type", "")
                if str(ctype).lower().startswith("image/") and _pw_looks_like_image_url(rurl):
                    seen_resources.append(rurl)
            except Exception:
                pass

        page.on("response", on_response)

        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)

        # Trigger lazy loading.
        for _ in range(4):
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(600)

        data = page.evaluate(
            """() => {
                const urls = [];

                const push = (v) => {
                    if (!v) return;
                    if (Array.isArray(v)) return v.forEach(push);
                    if (typeof v === 'string') urls.push(v);
                };

                document.querySelectorAll('img').forEach(img => {
                    push(img.currentSrc);
                    push(img.src);
                    push(img.getAttribute('src'));
                    push(img.getAttribute('data-src'));
                    push(img.getAttribute('srcset'));
                });

                document.querySelectorAll('source').forEach(src => {
                    push(src.getAttribute('srcset'));
                    push(src.getAttribute('src'));
                });

                try {
                    performance.getEntriesByType('resource').forEach(r => push(r.name));
                } catch(e) {}

                return {
                    urls,
                    title: document.querySelector('meta[property="og:title"]')?.content || document.title || '',
                    bodyText: document.body ? document.body.innerText.slice(0, 1200) : ''
                };
            }"""
        )

        raw_urls = []
        raw_urls.extend(seen_resources)
        raw_urls.extend(data.get("urls") or [])

        expanded = []
        for u in raw_urls:
            if isinstance(u, str) and "," in u:
                for part in u.split(","):
                    expanded.append(part.strip().split(" ")[0])
            else:
                expanded.append(u)

        direct_urls = _pw_clean_image_urls(expanded)

        # If TikTok hides direct image URLs, capture visible carousel slides as screenshots.
        screenshot_files = []
        if not direct_urls:
            screenshot_files = _screenshot_carousel_slides(page, max_slides=12)

        context.close()

    media_id = ""
    m = _re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = (data.get("title") or "").strip()
    if not title or "download tiktok" in title.lower():
        title = f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"

    # Direct real image URLs case.
    if direct_urls:
        return {
            "kind": "image",
            "title": title,
            "uploader": "",
            "thumbnail": direct_urls[0],
            "duration": "",
            "webpage_url": url,
            "image_urls": direct_urls,
            "items": [
                {
                    "index": i + 1,
                    "title": f"TikTok carousel image {i + 1}",
                    "thumbnail": image_url,
                    "duration": "",
                    "ext": "jpg",
                }
                for i, image_url in enumerate(direct_urls[:35])
            ],
            "warning": "",
            "photo_carousel_mode": True,
            "real_carousel_extract": True,
            "playwright_extract": True,
            "screenshot_fallback": False,
            "persistent_profile": True,
            "url_first_fallback": False,
        }

    # Screenshot fallback case: this shows what the browser actually sees.
    if screenshot_files:
        return {
            "kind": "image",
            "title": title,
            "uploader": "",
            "thumbnail": f"/download/{screenshot_files[0].name}",
            "duration": "",
            "webpage_url": url,
            "image_urls": [],
            "screenshot_files": [p.name for p in screenshot_files],
            "items": [
                {
                    "index": i + 1,
                    "title": f"TikTok carousel screenshot {i + 1}",
                    "thumbnail": f"/download/{p.name}",
                    "duration": "",
                    "ext": "png",
                }
                for i, p in enumerate(screenshot_files)
            ],
            "warning": "TikTok did not expose direct carousel image URLs, so this preview uses browser screenshots of the carousel slides.",
            "photo_carousel_mode": True,
            "real_carousel_extract": True,
            "playwright_extract": True,
            "screenshot_fallback": True,
            "persistent_profile": True,
            "url_first_fallback": False,
        }

    return {
        "kind": "image",
        "title": title,
        "uploader": "",
        "thumbnail": "",
        "duration": "",
        "webpage_url": url,
        "image_urls": [],
        "items": [
            {
                "index": 1,
                "title": title,
                "thumbnail": "",
                "duration": "",
                "ext": "jpg",
            }
        ],
        "warning": "TikTok Photo / Carousel detected, but this browser session could not access or screenshot the carousel images.",
        "photo_carousel_mode": True,
        "real_carousel_extract": False,
        "playwright_extract": True,
        "screenshot_fallback": False,
        "persistent_profile": True,
        "url_first_fallback": True,
    }

def download_with_ytdlp(url: str, mode: str):
    if mode == "image" and detect_kind_from_url(url) == "image":
        provider_data = fetch_tiktok_provider_carousel(url)
        if provider_data and provider_data.get("image_urls"):
            return download_image_urls_to_output(provider_data.get("image_urls"), "tiktok_provider_carousel")

        try:
            data = extract_tiktok_photo_carousel_playwright(url)

            # If real direct images exist, download them.
            urls = data.get("image_urls") or []
            if urls:
                return download_image_urls_to_output(urls, "tiktok_carousel")

            # If screenshot fallback exists, return those files.
            screenshot_names = data.get("screenshot_files") or []
            screenshot_paths = []
            for name in screenshot_names:
                p = OUTPUT_DIR / safe_filename(name)
                if p.exists():
                    screenshot_paths.append(p)

            if screenshot_paths:
                return screenshot_paths
        except Exception:
            pass

    return _old_download_with_ytdlp_before_screenshot(url, mode)

# === TIKTOK CAROUSEL SCREENSHOT FALLBACK OVERRIDE END ===

# === TIKTOK CAROUSEL SCREENSHOT FALLBACK OVERRIDE START ===

_old_extract_tiktok_photo_carousel_playwright_before_screenshot = extract_tiktok_photo_carousel_playwright
_old_download_with_ytdlp_before_screenshot = download_with_ytdlp

def _hash_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def _screenshot_carousel_slides(page, max_slides: int = 12) -> list:
    files = []
    hashes = set()

    for i in range(max_slides):
        out = OUTPUT_DIR / f"tiktok_carousel_screen_{uuid.uuid4()}_{i+1}.png"

        # Screenshot the viewport. This guarantees we show what the browser can actually see.
        page.screenshot(path=str(out), full_page=False)

        digest = _hash_file(out)
        if digest not in hashes:
            hashes.add(digest)
            files.append(out)
        else:
            out.unlink(missing_ok=True)

        # Try several navigation methods for carousel/photo posts.
        try:
            page.keyboard.press("ArrowRight")
        except Exception:
            pass

        try:
            page.mouse.wheel(520, 0)
        except Exception:
            pass

        try:
            page.touchscreen.tap(350, 450)
        except Exception:
            pass

        page.wait_for_timeout(850)

    return files

def extract_tiktok_photo_carousel_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import re as _re

    profile_dir = str((BASE_DIR / "playwright_profiles" / "tiktok").resolve())
    direct_urls = []
    seen_resources = []

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            viewport={"width": 430, "height": 920},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.tiktok.com/",
            },
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.new_page()

        def on_response(response):
            try:
                rurl = response.url
                ctype = response.headers.get("content-type", "")
                if str(ctype).lower().startswith("image/") and _pw_looks_like_image_url(rurl):
                    seen_resources.append(rurl)
            except Exception:
                pass

        page.on("response", on_response)

        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)

        # Trigger lazy loading.
        for _ in range(4):
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(600)

        data = page.evaluate(
            """() => {
                const urls = [];

                const push = (v) => {
                    if (!v) return;
                    if (Array.isArray(v)) return v.forEach(push);
                    if (typeof v === 'string') urls.push(v);
                };

                document.querySelectorAll('img').forEach(img => {
                    push(img.currentSrc);
                    push(img.src);
                    push(img.getAttribute('src'));
                    push(img.getAttribute('data-src'));
                    push(img.getAttribute('srcset'));
                });

                document.querySelectorAll('source').forEach(src => {
                    push(src.getAttribute('srcset'));
                    push(src.getAttribute('src'));
                });

                try {
                    performance.getEntriesByType('resource').forEach(r => push(r.name));
                } catch(e) {}

                return {
                    urls,
                    title: document.querySelector('meta[property="og:title"]')?.content || document.title || '',
                    bodyText: document.body ? document.body.innerText.slice(0, 1200) : ''
                };
            }"""
        )

        raw_urls = []
        raw_urls.extend(seen_resources)
        raw_urls.extend(data.get("urls") or [])

        expanded = []
        for u in raw_urls:
            if isinstance(u, str) and "," in u:
                for part in u.split(","):
                    expanded.append(part.strip().split(" ")[0])
            else:
                expanded.append(u)

        direct_urls = _pw_clean_image_urls(expanded)

        # If TikTok hides direct image URLs, capture visible carousel slides as screenshots.
        screenshot_files = []
        if not direct_urls:
            screenshot_files = _screenshot_carousel_slides(page, max_slides=12)

        context.close()

    media_id = ""
    m = _re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = (data.get("title") or "").strip()
    if not title or "download tiktok" in title.lower():
        title = f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"

    # Direct real image URLs case.
    if direct_urls:
        return {
            "kind": "image",
            "title": title,
            "uploader": "",
            "thumbnail": direct_urls[0],
            "duration": "",
            "webpage_url": url,
            "image_urls": direct_urls,
            "items": [
                {
                    "index": i + 1,
                    "title": f"TikTok carousel image {i + 1}",
                    "thumbnail": image_url,
                    "duration": "",
                    "ext": "jpg",
                }
                for i, image_url in enumerate(direct_urls[:35])
            ],
            "warning": "",
            "photo_carousel_mode": True,
            "real_carousel_extract": True,
            "playwright_extract": True,
            "screenshot_fallback": False,
            "persistent_profile": True,
            "url_first_fallback": False,
        }

    # Screenshot fallback case: this shows what the browser actually sees.
    if screenshot_files:
        return {
            "kind": "image",
            "title": title,
            "uploader": "",
            "thumbnail": f"/download/{screenshot_files[0].name}",
            "duration": "",
            "webpage_url": url,
            "image_urls": [],
            "screenshot_files": [p.name for p in screenshot_files],
            "items": [
                {
                    "index": i + 1,
                    "title": f"TikTok carousel screenshot {i + 1}",
                    "thumbnail": f"/download/{p.name}",
                    "duration": "",
                    "ext": "png",
                }
                for i, p in enumerate(screenshot_files)
            ],
            "warning": "TikTok did not expose direct carousel image URLs, so this preview uses browser screenshots of the carousel slides.",
            "photo_carousel_mode": True,
            "real_carousel_extract": True,
            "playwright_extract": True,
            "screenshot_fallback": True,
            "persistent_profile": True,
            "url_first_fallback": False,
        }

    return {
        "kind": "image",
        "title": title,
        "uploader": "",
        "thumbnail": "",
        "duration": "",
        "webpage_url": url,
        "image_urls": [],
        "items": [
            {
                "index": 1,
                "title": title,
                "thumbnail": "",
                "duration": "",
                "ext": "jpg",
            }
        ],
        "warning": "TikTok Photo / Carousel detected, but this browser session could not access or screenshot the carousel images.",
        "photo_carousel_mode": True,
        "real_carousel_extract": False,
        "playwright_extract": True,
        "screenshot_fallback": False,
        "persistent_profile": True,
        "url_first_fallback": True,
    }

def download_with_ytdlp(url: str, mode: str):
    if mode == "image" and detect_kind_from_url(url) == "image":
        try:
            data = extract_tiktok_photo_carousel_playwright(url)

            # If real direct images exist, download them.
            urls = data.get("image_urls") or []
            if urls:
                return download_image_urls_to_output(urls, "tiktok_carousel")

            # If screenshot fallback exists, return those files.
            screenshot_names = data.get("screenshot_files") or []
            screenshot_paths = []
            for name in screenshot_names:
                p = OUTPUT_DIR / safe_filename(name)
                if p.exists():
                    screenshot_paths.append(p)

            if screenshot_paths:
                return screenshot_paths
        except Exception:
            pass

    return _old_download_with_ytdlp_before_screenshot(url, mode)

# === TIKTOK CAROUSEL SCREENSHOT FALLBACK OVERRIDE END ===

# === ONE-POST-ONLY TIKTOK CAROUSEL SCREENSHOT OVERRIDE START ===

def _screenshot_one_post_carousel_slides(page, max_slides: int = 10) -> list:
    """
    Capture only the currently opened TikTok post/carousel view.
    This avoids collecting every image resource loaded by TikTok's page.
    """
    files = []
    hashes = set()
    duplicate_streak = 0

    def capture_slide(index: int):
        out = OUTPUT_DIR / f"tiktok_one_post_slide_{uuid.uuid4()}_{index}.png"

        # Prefer the main article/post area. If TikTok changes markup, fallback to viewport.
        try:
            article = page.locator("article").first
            if article.count() > 0:
                article.screenshot(path=str(out))
            else:
                page.screenshot(path=str(out), full_page=False)
        except Exception:
            page.screenshot(path=str(out), full_page=False)

        return out

    for i in range(1, max_slides + 1):
        out = capture_slide(i)

        try:
            digest = _hash_file(out)
        except Exception:
            digest = str(out.stat().st_size)

        if digest in hashes:
            duplicate_streak += 1
            out.unlink(missing_ok=True)
        else:
            duplicate_streak = 0
            hashes.add(digest)
            files.append(out)

        # Stop when navigation is no longer changing the visible carousel.
        if duplicate_streak >= 2:
            break

        # Try carousel navigation without scrolling the whole feed.
        try:
            page.keyboard.press("ArrowRight")
        except Exception:
            pass

        try:
            page.mouse.click(370, 460)
        except Exception:
            pass

        page.wait_for_timeout(750)

    return files

def extract_tiktok_photo_carousel_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import re as _re

    profile_dir = str((BASE_DIR / "playwright_profiles" / "tiktok").resolve())

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            viewport={"width": 430, "height": 920},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.tiktok.com/",
            },
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(7500)

        # Do not collect all page resources. Only screenshot the visible post/carousel.
        screenshot_files = _screenshot_one_post_carousel_slides(page, max_slides=10)

        data = page.evaluate(
            """() => {
                return {
                    title: document.querySelector('meta[property="og:title"]')?.content || document.title || '',
                    bodyText: document.body ? document.body.innerText.slice(0, 1000) : ''
                };
            }"""
        )

        context.close()

    media_id = ""
    m = _re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = (data.get("title") or "").strip()
    if not title or "download tiktok" in title.lower():
        title = f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"

    if screenshot_files:
        return {
            "kind": "image",
            "title": title,
            "uploader": "",
            "thumbnail": f"/download/{screenshot_files[0].name}",
            "duration": "",
            "webpage_url": url,
            "image_urls": [],
            "screenshot_files": [p.name for p in screenshot_files],
            "items": [
                {
                    "index": i + 1,
                    "title": f"TikTok carousel slide {i + 1}",
                    "thumbnail": f"/download/{p.name}",
                    "duration": "",
                    "ext": "png",
                }
                for i, p in enumerate(screenshot_files)
            ],
            "warning": "TikTok did not expose direct image URLs, so this preview uses screenshots of this single carousel post only.",
            "photo_carousel_mode": True,
            "real_carousel_extract": True,
            "playwright_extract": True,
            "screenshot_fallback": True,
            "one_post_only": True,
            "persistent_profile": True,
            "url_first_fallback": False,
        }

    return {
        "kind": "image",
        "title": title,
        "uploader": "",
        "thumbnail": "",
        "duration": "",
        "webpage_url": url,
        "image_urls": [],
        "items": [
            {
                "index": 1,
                "title": title,
                "thumbnail": "",
                "duration": "",
                "ext": "jpg",
            }
        ],
        "warning": "TikTok Photo / Carousel detected, but this browser session could not screenshot the post.",
        "photo_carousel_mode": True,
        "real_carousel_extract": False,
        "playwright_extract": True,
        "screenshot_fallback": False,
        "one_post_only": True,
        "persistent_profile": True,
        "url_first_fallback": True,
    }

# === ONE-POST-ONLY TIKTOK CAROUSEL SCREENSHOT OVERRIDE END ===

# === STRONG ONE-POST CAROUSEL SWIPE OVERRIDE START ===

def _try_advance_tiktok_carousel(page) -> bool:
    """
    Try to move to the next image inside the current TikTok photo/carousel post.
    Uses next buttons if present, then phone-like swipe gestures.
    """
    advanced = False

    # Try visible next/right arrow buttons first.
    selectors = [
        'button[aria-label*="next" i]',
        'button[aria-label*="Next" i]',
        'button[aria-label*="suivant" i]',
        'button[aria-label*="right" i]',
        'button[data-e2e*="next" i]',
        '[role="button"][aria-label*="next" i]',
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                loc.click(timeout=1200)
                page.wait_for_timeout(900)
                advanced = True
                break
        except Exception:
            pass

    # Keyboard fallback.
    try:
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(650)
        advanced = True
    except Exception:
        pass

    # Strong mobile-like swipe left across the post.
    try:
        page.mouse.move(370, 470)
        page.mouse.down()
        page.wait_for_timeout(100)
        page.mouse.move(260, 470, steps=8)
        page.mouse.move(150, 470, steps=8)
        page.mouse.move(55, 470, steps=8)
        page.mouse.up()
        page.wait_for_timeout(950)
        advanced = True
    except Exception:
        pass

    # Second swipe lower in case the image area is lower.
    try:
        page.mouse.move(375, 600)
        page.mouse.down()
        page.wait_for_timeout(100)
        page.mouse.move(230, 600, steps=8)
        page.mouse.move(70, 600, steps=8)
        page.mouse.up()
        page.wait_for_timeout(900)
        advanced = True
    except Exception:
        pass

    return advanced

def _screenshot_one_post_carousel_slides(page, max_slides: int = 12) -> list:
    files = []
    hashes = set()
    duplicate_streak = 0

    def capture_slide(index: int):
        out = OUTPUT_DIR / f"tiktok_one_post_slide_{uuid.uuid4()}_{index}.png"

        # Screenshot viewport/post. Viewport is safer for TikTok mobile carousel.
        page.screenshot(path=str(out), full_page=False)
        return out

    # Ensure carousel/post is centered and loaded.
    try:
        page.mouse.wheel(0, 180)
        page.wait_for_timeout(1200)
    except Exception:
        pass

    for i in range(1, max_slides + 1):
        out = capture_slide(i)

        try:
            digest = _hash_file(out)
        except Exception:
            digest = str(out.stat().st_size)

        if digest in hashes:
            duplicate_streak += 1
            out.unlink(missing_ok=True)
        else:
            duplicate_streak = 0
            hashes.add(digest)
            files.append(out)

        if duplicate_streak >= 2:
            break

        _try_advance_tiktok_carousel(page)

    return files

def extract_tiktok_photo_carousel_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import re as _re

    profile_dir = str((BASE_DIR / "playwright_profiles" / "tiktok").resolve())

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            viewport={"width": 430, "height": 920},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.tiktok.com/",
            },
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)

        # Try to close popups if present.
        for text in ["Not now", "Maybe later", "Continue as guest", "Accept all", "Accept"]:
            try:
                page.get_by_text(text, exact=False).first.click(timeout=1000)
                page.wait_for_timeout(600)
            except Exception:
                pass

        screenshot_files = _screenshot_one_post_carousel_slides(page, max_slides=12)

        data = page.evaluate(
            """() => {
                return {
                    title: document.querySelector('meta[property="og:title"]')?.content || document.title || '',
                    bodyText: document.body ? document.body.innerText.slice(0, 1000) : ''
                };
            }"""
        )

        context.close()

    media_id = ""
    m = _re.search(r"/photo/([0-9]+)", url)
    if m:
        media_id = m.group(1)

    title = (data.get("title") or "").strip()
    if not title or "download tiktok" in title.lower():
        title = f"TikTok Photo / Carousel #{media_id}" if media_id else "TikTok Photo / Carousel"

    if screenshot_files:
        return {
            "kind": "image",
            "title": title,
            "uploader": "",
            "thumbnail": f"/download/{screenshot_files[0].name}",
            "duration": "",
            "webpage_url": url,
            "image_urls": [],
            "screenshot_files": [p.name for p in screenshot_files],
            "items": [
                {
                    "index": i + 1,
                    "title": f"TikTok carousel slide {i + 1}",
                    "thumbnail": f"/download/{p.name}",
                    "duration": "",
                    "ext": "png",
                }
                for i, p in enumerate(screenshot_files)
            ],
            "warning": "TikTok did not expose direct image URLs, so this preview uses screenshots of this single carousel post only.",
            "photo_carousel_mode": True,
            "real_carousel_extract": True,
            "playwright_extract": True,
            "screenshot_fallback": True,
            "one_post_only": True,
            "swipe_navigation": True,
            "persistent_profile": True,
            "url_first_fallback": False,
        }

    return {
        "kind": "image",
        "title": title,
        "uploader": "",
        "thumbnail": "",
        "duration": "",
        "webpage_url": url,
        "image_urls": [],
        "items": [
            {
                "index": 1,
                "title": title,
                "thumbnail": "",
                "duration": "",
                "ext": "jpg",
            }
        ],
        "warning": "TikTok Photo / Carousel detected, but this browser session could not screenshot the post.",
        "photo_carousel_mode": True,
        "real_carousel_extract": False,
        "playwright_extract": True,
        "screenshot_fallback": False,
        "one_post_only": True,
        "swipe_navigation": True,
        "persistent_profile": True,
        "url_first_fallback": True,
    }

# === STRONG ONE-POST CAROUSEL SWIPE OVERRIDE END ===



# === TIKTOK MP3 FEATURE OVERRIDE START ===

TOOLS = ["all", "video", "audio", "story"]

PATHS = {
    "en": {
        "all": "/tiktok-downloader",
        "video": "/tiktok-video-downloader",
        "audio": "/tiktok-mp3-downloader",
        "story": "/tiktok-story-downloader",
    },
    "fr": {
        "all": "/fr/telecharger-tiktok",
        "video": "/fr/telecharger-video-tiktok",
        "audio": "/fr/telecharger-mp3-tiktok",
        "story": "/fr/telecharger-story-tiktok",
    },
    "ar": {
        "all": "/ar/tahmil-tiktok",
        "video": "/ar/tahmil-video-tiktok",
        "audio": "/ar/tahmil-mp3-tiktok",
        "story": "/ar/tahmil-story-tiktok",
    },
}

TAB_LABELS = {
    "en": {"all": "All TikTok Downloader", "video": "Video", "audio": "MP3", "story": "Story"},
    "fr": {"all": "Télécharger TikTok", "video": "Vidéo", "audio": "MP3", "story": "Story"},
    "ar": {"all": "الكل", "video": "فيديو", "audio": "MP3", "story": "ستوري"},
}

PAGES = {
    "en": {
        "all": {
            "title": "TikTok Downloader - Videos, MP3 Audio and Stories",
            "description": "Paste a TikTok link, preview the media type, then download TikTok videos, extract MP3 audio, or handle story links when available.",
            "heading": "TikTok <span>Videos, MP3 & Stories</span> Downloader",
            "subtitle": "Paste a TikTok link, preview the media type, then download video or extract MP3 audio when available.",
            "placeholder": "Paste TikTok video, story or audio link...",
            "button": "Detect Preview",
        },
        "video": {
            "title": "TikTok Video Downloader - Preview and Download Videos",
            "description": "Download TikTok videos online. Paste a TikTok video link, preview it, then download the best available MP4.",
            "heading": "TikTok <span>Video</span> Downloader",
            "subtitle": "Paste a TikTok video link, preview it, then download the best available MP4 version.",
            "placeholder": "Paste TikTok video link here...",
            "button": "Detect Video",
        },
        "audio": {
            "title": "TikTok to MP3 Converter - Extract TikTok Audio",
            "description": "Convert TikTok videos to MP3 audio online. Paste a TikTok link, preview it, then extract the audio as an MP3 file.",
            "heading": "TikTok to <span>MP3</span> Converter",
            "subtitle": "Paste a TikTok video link, preview it, then extract the audio as an MP3 file.",
            "placeholder": "Paste TikTok video link to extract MP3 audio...",
            "button": "Detect MP3",
        },
        "story": {
            "title": "TikTok Story Downloader - Save TikTok Stories",
            "description": "Download TikTok stories online when available. Paste a TikTok story link, preview it, then download the available media.",
            "heading": "TikTok <span>Story</span> Downloader",
            "subtitle": "Paste a TikTok story link, preview available story media, then download the right file.",
            "placeholder": "Paste TikTok story link here...",
            "button": "Detect Story",
        },
    },
    "fr": {
        "all": {
            "title": "Télécharger TikTok - Vidéos, MP3 et Stories",
            "description": "Collez un lien TikTok, prévisualisez le média, puis téléchargez la vidéo, extrayez l’audio MP3 ou traitez les stories disponibles.",
            "heading": "Télécharger <span>Vidéos, MP3 & Stories TikTok</span>",
            "subtitle": "Collez un lien TikTok, prévisualisez le type de média, puis téléchargez la vidéo ou extrayez l’audio MP3.",
            "placeholder": "Collez un lien TikTok vidéo, story ou audio...",
            "button": "Détecter l’aperçu",
        },
        "video": {
            "title": "Télécharger Vidéo TikTok - Prévisualiser et Télécharger",
            "description": "Téléchargez des vidéos TikTok en ligne. Collez un lien vidéo TikTok, prévisualisez-le, puis téléchargez la meilleure version MP4 disponible.",
            "heading": "Télécharger <span>Vidéo TikTok</span>",
            "subtitle": "Collez un lien vidéo TikTok, prévisualisez-le, puis téléchargez la meilleure version MP4 disponible.",
            "placeholder": "Collez le lien vidéo TikTok ici...",
            "button": "Détecter la vidéo",
        },
        "audio": {
            "title": "Convertir TikTok en MP3 - Extraire l’audio TikTok",
            "description": "Convertissez une vidéo TikTok en audio MP3. Collez un lien TikTok, prévisualisez-le, puis extrayez l’audio au format MP3.",
            "heading": "Convertir TikTok en <span>MP3</span>",
            "subtitle": "Collez un lien vidéo TikTok, prévisualisez-le, puis extrayez l’audio au format MP3.",
            "placeholder": "Collez le lien TikTok pour extraire l’audio MP3...",
            "button": "Détecter MP3",
        },
        "story": {
            "title": "Télécharger Story TikTok - Enregistrer des Stories TikTok",
            "description": "Téléchargez des stories TikTok en ligne quand elles sont disponibles. Collez un lien story TikTok, prévisualisez-le, puis téléchargez le média.",
            "heading": "Télécharger <span>Story TikTok</span>",
            "subtitle": "Collez un lien story TikTok, prévisualisez le média disponible, puis téléchargez le bon fichier.",
            "placeholder": "Collez le lien story TikTok ici...",
            "button": "Détecter la story",
        },
    },
    "ar": {
        "all": {
            "title": "تحميل TikTok - فيديوهات، MP3 وستوري",
            "description": "الصق رابط TikTok، عاين نوع الوسائط، ثم حمّل الفيديو أو استخرج الصوت MP3 أو تعامل مع الستوري المتاحة.",
            "heading": "تحميل <span>فيديوهات، MP3 وستوري TikTok</span>",
            "subtitle": "الصق رابط TikTok، عاين نوع الوسائط، ثم حمّل الفيديو أو استخرج الصوت بصيغة MP3.",
            "placeholder": "الصق رابط TikTok فيديو أو ستوري أو صوت...",
            "button": "كشف المعاينة",
        },
        "video": {
            "title": "تحميل فيديو TikTok - معاينة وتحميل الفيديوهات",
            "description": "حمّل فيديوهات TikTok أونلاين. الصق رابط فيديو TikTok، عاينه، ثم حمّل أفضل نسخة MP4 متاحة.",
            "heading": "تحميل <span>فيديو TikTok</span>",
            "subtitle": "الصق رابط فيديو TikTok، عاينه، ثم حمّل أفضل نسخة MP4 متاحة.",
            "placeholder": "الصق رابط فيديو TikTok هنا...",
            "button": "كشف الفيديو",
        },
        "audio": {
            "title": "تحويل TikTok إلى MP3 - استخراج صوت TikTok",
            "description": "حوّل فيديو TikTok إلى ملف MP3. الصق رابط TikTok، عاينه، ثم استخرج الصوت بصيغة MP3.",
            "heading": "تحويل TikTok إلى <span>MP3</span>",
            "subtitle": "الصق رابط فيديو TikTok، عاينه، ثم استخرج الصوت بصيغة MP3.",
            "placeholder": "الصق رابط TikTok لاستخراج الصوت MP3...",
            "button": "كشف MP3",
        },
        "story": {
            "title": "تحميل ستوري TikTok - حفظ Stories TikTok",
            "description": "حمّل Stories TikTok أونلاين عندما تكون متاحة. الصق رابط Story من TikTok، عاينه، ثم حمّل الوسائط المتاحة.",
            "heading": "تحميل <span>ستوري TikTok</span>",
            "subtitle": "الصق رابط Story من TikTok، عاين الوسائط المتاحة، ثم حمّل الملف الصحيح.",
            "placeholder": "الصق رابط Story TikTok هنا...",
            "button": "كشف الستوري",
        },
    },
}

def route_seo(lang: str, tool: str) -> str:
    if lang == "fr":
        return """
    <section id="seoContent" class="seo-section">
      <div class="seo-hero">
        <h2>Télécharger TikTok en vidéo ou convertir TikTok en MP3</h2>
        <p>Collez un lien TikTok, prévisualisez le média, puis téléchargez la vidéo ou extrayez l’audio au format MP3.</p>
      </div>
      <div class="seo-grid">
        <div class="seo-card"><strong>Télécharger TikTok Vidéo</strong><p>Utilisez l’onglet Vidéo pour obtenir la meilleure version MP4 disponible.</p></div>
        <div class="seo-card"><strong>Convertir TikTok en MP3</strong><p>Utilisez l’onglet MP3 pour extraire l’audio d’une vidéo TikTok sous forme de fichier MP3.</p></div>
        <div class="seo-card"><strong>Télécharger TikTok Story</strong><p>Utilisez l’onglet Story pour les liens story TikTok lorsque le média est accessible.</p></div>
      </div>
      <div class="seo-block">
        <h2>Comment convertir TikTok en MP3</h2>
        <div class="seo-steps">
          <div class="seo-step"><div><strong>Copiez le lien TikTok</strong><span>Copiez le lien de la vidéo TikTok dont vous voulez extraire l’audio.</span></div></div>
          <div class="seo-step"><div><strong>Choisissez MP3</strong><span>Ouvrez l’onglet MP3, collez le lien, puis lancez la détection.</span></div></div>
          <div class="seo-step"><div><strong>Prévisualisez</strong><span>Vérifiez le titre, le créateur et la miniature avant de convertir.</span></div></div>
          <div class="seo-step"><div><strong>Téléchargez l’audio</strong><span>Cliquez sur Télécharger MP3 pour enregistrer l’audio sur votre appareil.</span></div></div>
        </div>
      </div>
      <div class="seo-block">
        <h2>Outils TikTok pris en charge</h2>
        <div class="seo-internal-links">
          <a href="/fr/telecharger-tiktok">Télécharger TikTok</a>
          <a href="/fr/telecharger-video-tiktok">Télécharger TikTok Vidéo</a>
          <a href="/fr/telecharger-mp3-tiktok">Convertir TikTok en MP3</a>
          <a href="/fr/telecharger-story-tiktok">Télécharger TikTok Story</a>
        </div>
      </div>
      <div class="seo-disclaimer">Utilisez cet outil uniquement pour votre propre contenu, des médias publics ou du contenu que vous avez l’autorisation de sauvegarder.</div>
    </section>
"""
    if lang == "ar":
        return """
    <section id="seoContent" class="seo-section">
      <div class="seo-hero">
        <h2>تحميل فيديو TikTok أو تحويل TikTok إلى MP3</h2>
        <p>الصق رابط TikTok، عاين الوسائط، ثم حمّل الفيديو أو استخرج الصوت بصيغة MP3.</p>
      </div>
      <div class="seo-grid">
        <div class="seo-card"><strong>تحميل TikTok Video</strong><p>استخدم تبويب فيديو لتحميل أفضل نسخة MP4 متاحة.</p></div>
        <div class="seo-card"><strong>تحويل TikTok إلى MP3</strong><p>استخدم تبويب MP3 لاستخراج صوت فيديو TikTok كملف MP3.</p></div>
        <div class="seo-card"><strong>تحميل TikTok Story</strong><p>استخدم تبويب ستوري لروابط TikTok Story عندما تكون الوسائط متاحة.</p></div>
      </div>
      <div class="seo-block">
        <h2>كيفية تحويل TikTok إلى MP3</h2>
        <div class="seo-steps">
          <div class="seo-step"><div><strong>انسخ رابط TikTok</strong><span>انسخ رابط الفيديو الذي تريد استخراج الصوت منه.</span></div></div>
          <div class="seo-step"><div><strong>اختر MP3</strong><span>افتح تبويب MP3، الصق الرابط، ثم شغّل المعاينة.</span></div></div>
          <div class="seo-step"><div><strong>عاين قبل التحويل</strong><span>تحقق من العنوان والمنشئ والصورة المصغرة قبل استخراج الصوت.</span></div></div>
          <div class="seo-step"><div><strong>حمّل الصوت</strong><span>اضغط تحميل MP3 لحفظ الصوت على جهازك.</span></div></div>
        </div>
      </div>
      <div class="seo-block">
        <h2>أدوات TikTok المدعومة</h2>
        <div class="seo-internal-links">
          <a href="/ar/tahmil-tiktok">تحميل TikTok</a>
          <a href="/ar/tahmil-video-tiktok">تحميل TikTok Video</a>
          <a href="/ar/tahmil-mp3-tiktok">تحويل TikTok إلى MP3</a>
          <a href="/ar/tahmil-story-tiktok">تحميل TikTok Story</a>
        </div>
      </div>
      <div class="seo-disclaimer">استخدم هذه الأداة فقط مع محتواك الخاص أو الوسائط العامة أو المحتوى الذي لديك إذن بحفظه.</div>
    </section>
"""
    return """
    <section id="seoContent" class="seo-section">
      <div class="seo-hero">
        <h2>Download TikTok Videos or Convert TikTok to MP3</h2>
        <p>Paste a TikTok link, preview the media, download the video, or extract the audio as an MP3 file.</p>
      </div>
      <div class="seo-grid">
        <div class="seo-card"><strong>TikTok Video Downloader</strong><p>Use the Video tab to download the best available MP4 version from a TikTok video link.</p></div>
        <div class="seo-card"><strong>TikTok to MP3 Converter</strong><p>Use the MP3 tab to extract audio from a TikTok video and save it as an MP3 file.</p></div>
        <div class="seo-card"><strong>TikTok Story Downloader</strong><p>Use the Story tab for TikTok story links when the media is accessible.</p></div>
      </div>
      <div class="seo-block">
        <h2>How to Convert TikTok to MP3</h2>
        <div class="seo-steps">
          <div class="seo-step"><div><strong>Copy the TikTok link</strong><span>Open TikTok and copy the video link you want to extract audio from.</span></div></div>
          <div class="seo-step"><div><strong>Choose the MP3 tab</strong><span>Open TikTok to MP3, paste the link, and start detection.</span></div></div>
          <div class="seo-step"><div><strong>Preview before converting</strong><span>Check the title, creator and thumbnail before starting the MP3 extraction.</span></div></div>
          <div class="seo-step"><div><strong>Download the audio</strong><span>Click Download MP3 and your browser will save the audio file.</span></div></div>
        </div>
      </div>
      <div class="seo-block">
        <h2>Supported TikTok Tools</h2>
        <div class="seo-internal-links">
          <a href="/tiktok-downloader">All TikTok Downloader</a>
          <a href="/tiktok-video-downloader">TikTok Video Downloader</a>
          <a href="/tiktok-mp3-downloader">TikTok to MP3 Converter</a>
          <a href="/tiktok-story-downloader">TikTok Story Downloader</a>
        </div>
      </div>
      <div class="seo-disclaimer">Use this tool only for your own content, public media, or content you have permission to save. Do not use it to violate platform rules, copyrights or privacy rights.</div>
    </section>
"""

_old_download_with_ytdlp_before_mp3 = download_with_ytdlp

def download_with_ytdlp(url: str, mode: str):
    if mode == "audio":
        job_id = str(uuid.uuid4())
        output_template = str(OUTPUT_DIR / f"tiktok_{job_id}.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_template,
            url,
        ]

        result = run_cmd(cmd, timeout=600)
        files = collect_job_files(job_id)

        if result.returncode != 0 and not files:
            raise HTTPException(status_code=500, detail=(result.stderr.strip()[-500:] or "TikTok MP3 extraction failed"))

        mp3_files = [p for p in files if p.suffix.lower() == ".mp3"]
        if mp3_files:
            return mp3_files

        if files:
            return files

        raise HTTPException(status_code=500, detail="No TikTok MP3 file was created")

    return _old_download_with_ytdlp_before_mp3(url, mode)

# Remove old preview route + old image routes
app.router.routes = [
    r for r in app.router.routes
    if not (
        (getattr(r, "path", "") == "/api/preview-tiktok" and "POST" in getattr(r, "methods", set()))
        or getattr(r, "path", "") in {
            "/tiktok-image-downloader",
            "/fr/telecharger-image-tiktok",
            "/ar/tahmil-image-tiktok",
        }
    )
]

@app.post("/api/preview-tiktok")
def preview_tiktok(url: str = Form(...), mode: str = Form("all")):
    if not safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid TikTok URL")

    selected = mode if mode in TOOLS else "all"
    info = get_preview_info(url)

    raw_detected = info.get("kind") or "unknown"
    detected = raw_detected

    audio_from_video = selected == "audio" and raw_detected == "video"
    if audio_from_video:
        detected = "audio"

    story_video_fallback = selected == "story" and raw_detected == "video" and "/video/" in url.lower()
    if story_video_fallback:
        detected = "story"

    allowed = selected == "all" or selected == detected or audio_from_video or story_video_fallback
    suggestion = detected if detected in TOOLS else "all"

    info["selected"] = selected
    info["detected"] = detected
    info["raw_detected"] = raw_detected
    info["audio_from_video"] = bool(audio_from_video)
    info["story_video_fallback"] = bool(story_video_fallback)
    info["allowed"] = bool(allowed)
    info["strict_allowed"] = bool(allowed)
    info["suggestion"] = suggestion
    info["mode_mismatch"] = not bool(allowed)

    return info

@app.get("/tiktok-mp3-downloader", response_class=HTMLResponse)
def en_audio(request: Request):
    return render_index("audio", "en", str(request.base_url).rstrip("/"))

@app.get("/fr/telecharger-mp3-tiktok", response_class=HTMLResponse)
def fr_audio(request: Request):
    return render_index("audio", "fr", str(request.base_url).rstrip("/"))

@app.get("/ar/tahmil-mp3-tiktok", response_class=HTMLResponse)
def ar_audio(request: Request):
    return render_index("audio", "ar", str(request.base_url).rstrip("/"))

@app.get("/tiktok-image-downloader")
def redirect_old_image_page_to_mp3():
    return RedirectResponse("/tiktok-mp3-downloader", status_code=301)

@app.get("/fr/telecharger-image-tiktok")
def redirect_old_fr_image_page_to_mp3():
    return RedirectResponse("/fr/telecharger-mp3-tiktok", status_code=301)

@app.get("/ar/tahmil-image-tiktok")
def redirect_old_ar_image_page_to_mp3():
    return RedirectResponse("/ar/tahmil-mp3-tiktok", status_code=301)

# === TIKTOK MP3 FEATURE OVERRIDE END ===



# === CLEAN JSON DOWNLOAD ROUTE OVERRIDE START ===

app.router.routes = [
    r for r in app.router.routes
    if not (getattr(r, "path", "") == "/download-tiktok" and "POST" in getattr(r, "methods", set()))
]

@app.post("/download-tiktok")
def download_tiktok(url: str = Form(...), mode: str = Form("video")):
    if not safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid TikTok URL")

    mode = mode if mode in TOOLS else "video"

    # All mode defaults to video unless frontend explicitly asks for audio/story.
    if mode == "all":
        mode = "video"

    try:
        files = download_with_ytdlp(url, mode)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TikTok download failed: {type(e).__name__}: {str(e)[:300]}"
        )

    payload_files = []
    for p in files:
        payload_files.append({
            "filename": p.name,
            "download_url": f"/download/{p.name}",
            "media_type": media_type_for(p),
            "size": p.stat().st_size,
        })

    if not payload_files:
        raise HTTPException(status_code=500, detail="No downloadable TikTok file was created")

    return {
        "download_url": payload_files[0]["download_url"],
        "filename": payload_files[0]["filename"],
        "files": payload_files,
        "mode": mode,
    }

# === CLEAN JSON DOWNLOAD ROUTE OVERRIDE END ===

# === FINAL NON-RECURSIVE TIKTOK DOWNLOADER OVERRIDE START ===

def download_with_ytdlp(url: str, mode: str):
    """
    Final clean downloader.
    No old wrapper calls. No recursion.
    Supports:
      - video: best MP4
      - story: best MP4 fallback
      - audio: TikTok to MP3
    """
    job_id = str(uuid.uuid4())

    if mode == "audio":
        output_template = str(OUTPUT_DIR / f"tiktok_{job_id}.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_template,
            url,
        ]

    else:
        # Video and story both download as best available video.
        output_template = str(OUTPUT_DIR / f"tiktok_{job_id}.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-f", "best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url,
        ]

    result = run_cmd(cmd, timeout=600)
    files = collect_job_files(job_id)

    if result.returncode != 0 and not files:
        msg = result.stderr.strip() or result.stdout.strip() or "TikTok download failed"
        raise HTTPException(status_code=500, detail=msg[-700:])

    if mode == "audio":
        mp3_files = [p for p in files if p.suffix.lower() == ".mp3"]
        if mp3_files:
            return mp3_files

    if files:
        return files

    raise HTTPException(status_code=500, detail="No TikTok file was created")

# === FINAL NON-RECURSIVE TIKTOK DOWNLOADER OVERRIDE END ===
