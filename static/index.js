const form = document.getElementById("downloadForm");
const urlInput = document.getElementById("urlInput");
const statusBox = document.getElementById("status");
const preview = document.getElementById("preview");
const downloads = document.getElementById("downloads");
const progressWrap = document.getElementById("progressWrap");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const progressPct = document.getElementById("progressPct");
const inspectBtn = document.getElementById("inspectBtn");
const pasteBtn = document.getElementById("pasteBtn");
const clearBtn = document.getElementById("clearBtn");

let currentDetection = null;
let progressTimer = null;

function setBusy(isBusy) {
  inspectBtn.disabled = Boolean(isBusy);
  inspectBtn.classList.toggle("loading", Boolean(isBusy));
  inspectBtn.setAttribute("aria-busy", isBusy ? "true" : "false");
}

function syncInputActions() {
  if (!clearBtn) return;
  clearBtn.classList.toggle("visible", Boolean(urlInput.value.trim()));
}

async function pasteTikTokUrl() {
  try {
    const text = await navigator.clipboard.readText();
    if (!text) throw new Error("Clipboard is empty");
    urlInput.value = text.trim();
    urlInput.focus();
    syncInputActions();
    scheduleAutoDetect("paste");
  } catch (err) {
    urlInput.focus();
    statusBox.textContent = currentLang() === "fr"
      ? "Collez le lien TikTok dans le champ."
      : currentLang() === "ar"
        ? "الصق رابط TikTok في الحقل."
        : "Paste the TikTok link into the field.";
  }
}

function selectedTool() {
  return document.body.dataset.selectedTool || "all";
}

function currentLang() {
  return document.documentElement.lang === "ar" ? "ar" : document.documentElement.lang === "fr" ? "fr" : "en";
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, s => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[s]));
}

function kindName(kind) {
  const lang = currentLang();
  const names = {
    en: { video: "Video",
      audio: "MP3", image: "Photo / Carousel", story: "Story", all: "TikTok media", unknown: "TikTok media" },
    fr: { video: "Vidéo",
      audio: "MP3", image: "Photo / Carousel", story: "Story", all: "Média TikTok", unknown: "Média TikTok" },
    ar: { video: "فيديو",
      audio: "MP3", image: "صور / كاروسيل", story: "ستوري", all: "وسائط TikTok", unknown: "وسائط TikTok" }
  };
  return (names[lang] || names.en)[kind] || kind;
}

function toolPath(tool) {
  const lang = currentLang();
  const paths = {
    en: {
      all: "/tiktok-downloader",
      video: "/tiktok-video-downloader",
      audio: "/tiktok-mp3-downloader",
      story: "/tiktok-story-downloader"
    },
    fr: {
      all: "/fr/telecharger-tiktok",
      video: "/fr/telecharger-video-tiktok",
      audio: "/fr/telecharger-mp3-tiktok",
      story: "/fr/telecharger-story-tiktok"
    },
    ar: {
      all: "/ar/tahmil-tiktok",
      video: "/ar/tahmil-video-tiktok",
      audio: "/ar/tahmil-mp3-tiktok",
      story: "/ar/tahmil-story-tiktok"
    }
  };
  return (paths[lang] || paths.en)[tool] || (paths[lang] || paths.en).all;
}

function toolDisplayName(tool) {
  const lang = currentLang();
  const names = {
    en: {
      all: "All TikTok Downloader",
      video: "TikTok Video Downloader",
      audio: "TikTok to MP3 Converter",
      story: "TikTok Story Downloader"
    },
    fr: {
      all: "Télécharger TikTok",
      video: "Télécharger TikTok Vidéo",
      audio: "Convertir TikTok en MP3",
      story: "Télécharger TikTok Story"
    },
    ar: {
      all: "تحميل TikTok",
      video: "تحميل TikTok Video",
      audio: "تحويل TikTok إلى MP3",
      story: "تحميل TikTok Story"
    }
  };
  return (names[lang] || names.en)[tool] || (names[lang] || names.en).all;
}

function downloadButtonLabel(tool) {
  const lang = currentLang();
  if (tool === "audio") return lang === "fr" ? "Télécharger MP3" : lang === "ar" ? "تحميل MP3" : "Download MP3";
  if (lang === "fr") return `Télécharger ${kindName(tool)}`;
  if (lang === "ar") return `تحميل ${kindName(tool)}`;
  return `Download ${kindName(tool)}`;
}

function wrongModeMessage(selected, detected) {
  const lang = currentLang();
  const suggested = toolDisplayName(detected);

  if (lang === "fr") {
    return `Ce lien ressemble à ${kindName(detected)}. Cliquez sur le bouton ci-dessous pour ouvrir ${suggested} et télécharger le bon média.`;
  }

  if (lang === "ar") {
    return `يبدو أن هذا الرابط يحتوي على ${kindName(detected)}. اضغط على الزر بالأسفل لفتح ${suggested} وتحميل الوسائط الصحيحة.`;
  }

  return `This link looks like ${kindName(detected)}. Click the button below to open ${suggested} and download the right media.`;
}

function setProgress(value, text) {
  const pct = Math.max(0, Math.min(100, Number(value || 0)));
  progressWrap.style.display = "block";
  progressFill.style.width = `${pct}%`;
  progressPct.textContent = `${Math.round(pct)}%`;
  progressText.textContent = text || "Working...";
}

function startProgress(text) {
  clearInterval(progressTimer);
  let value = 8;
  setProgress(value, text);
  progressTimer = setInterval(() => {
    value = Math.min(92, value + Math.random() * 9);
    setProgress(value, text);
  }, 450);
}

function finishProgress(text) {
  clearInterval(progressTimer);
  setProgress(100, text || "Done");
}

function resetOutput() {
  preview.style.display = "none";
  downloads.style.display = "none";
  preview.innerHTML = "";
  downloads.innerHTML = "";
  currentDetection = null;
}

function previewText(key, fallback = "") {
  const lang = currentLang();

  const dict = {
    en: {
      selectedTab: "Selected tab",
      detectedType: "Detected type",
      items: "Items",
      creator: "Creator",
      duration: "Duration",
      seconds: "seconds",
      format: "Format",
      chooseCard: "Preview the available TikTok media below. Photo links may include slideshow/carousel images when TikTok exposes them.",
      noPreview: "No preview",
      mediaDetected: "TikTok media detected",
      storyFallback: "TikTok returned this story as video media, so it can be downloaded from the Story tab."
    },
    fr: {
      selectedTab: "Onglet sélectionné",
      detectedType: "Type détecté",
      items: "Éléments",
      creator: "Créateur",
      duration: "Durée",
      seconds: "secondes",
      format: "Format",
      chooseCard: "Prévisualisez le média TikTok disponible ci-dessous. Les liens photo peuvent inclure des images slideshow/carrousel quand TikTok les expose.",
      noPreview: "Aucun aperçu",
      mediaDetected: "Média TikTok détecté",
      storyFallback: "TikTok a renvoyé cette story comme média vidéo, elle peut donc être téléchargée depuis l’onglet Story."
    },
    ar: {
      selectedTab: "التبويب المختار",
      detectedType: "النوع المكتشف",
      items: "العناصر",
      creator: "المنشئ",
      duration: "المدة",
      seconds: "ثانية",
      format: "الصيغة",
      chooseCard: "عاين وسائط TikTok المتاحة بالأسفل. روابط الصور قد تحتوي على slideshow أو كاروسيل عندما يتيحها TikTok.",
      noPreview: "لا توجد معاينة",
      mediaDetected: "تم اكتشاف وسائط TikTok",
      storyFallback: "أعاد TikTok هذه الستوري كوسائط فيديو، لذلك يمكن تحميلها من تبويب الستوري."
    }
  };

  return (dict[lang] && dict[lang][key]) || dict.en[key] || fallback;
}

function renderTikTokMediaGrid(data, detected, tool) {
  const items = Array.isArray(data.items) && data.items.length
    ? data.items
    : [{
        index: 1,
        title: data.title || "TikTok media",
        thumbnail: data.thumbnail || "",
        duration: data.duration || "",
        ext: ""
      }];

  const hasRealMedia =
    detected !== "image" ||
    data.real_carousel_extract === true ||
    items.some(item => item.thumbnail && String(item.thumbnail).startsWith("http"));

  let html = `
    <div class="story-header">
      <span class="badge">${escapeHtml(kindName(detected))} detected</span>
      <h2>${escapeHtml(data.title || "TikTok media")}</h2>
      <div class="meta">
        ${data.uploader ? `${previewText("creator")}: @${escapeHtml(data.uploader)}<br>` : ""}
        ${previewText("items")}: ${items.length}<br>
        ${hasRealMedia ? previewText("chooseCard") : "TikTok photo/carousel was detected, but the actual image files were not exposed to this server session."}
      </div>
    </div>
  `;

  if (!hasRealMedia && detected === "image") {
    html += `
      <div class="blocked-carousel-card">
        <div class="blocked-icon">⚠️</div>
        <h3>TikTok carousel images are blocked</h3>
        <p>
          This is a real TikTok Photo / Carousel link, but TikTok did not expose the image URLs to the downloader session.
          The page can detect the media type, but it cannot safely preview or download the carousel images until a provider/API or verified browser session exposes them.
        </p>
        <a class="download-action" href="${escapeHtml(data.webpage_url || "#")}" target="_blank" rel="noopener">
          Open original TikTok post
        </a>
      </div>
    `;

    preview.innerHTML = html;
    preview.style.display = "block";
    return;
  }

  html += `<div class="media-grid">`;

  items.forEach((item, i) => {
    const thumb = item.thumbnail
      ? `<img src="${item.thumbnail}" alt="TikTok preview">`
      : `<div class="empty-thumb">${escapeHtml(previewText("noPreview"))}</div>`;

    html += `
      <div class="media-card">
        ${thumb}
        <div class="title">${i + 1}. ${escapeHtml(item.title || data.title || "TikTok media")}</div>
        <div class="type">
          ${escapeHtml(kindName(detected))}
          ${item.duration ? ` • ${escapeHtml(item.duration)} ${escapeHtml(previewText("seconds"))}` : ""}
          ${item.ext ? ` • ${escapeHtml(item.ext)}` : ""}
        </div>
      </div>
    `;
  });

  html += `
    </div>
    ${data.photo_carousel_mode ? `<div class="meta photo-carousel-note">${data.real_carousel_extract ? `Carousel images extracted: ${(data.items || []).length}. Download will save all available images.` : `Photo / Carousel link detected, but image URLs were not exposed to this server session.`}</div>` : ""}
    ${data.story_video_fallback ? `<div class="meta story-fallback-note">${escapeHtml(previewText("storyFallback"))}</div>` : ""}
    <div class="preview-actions">
      <button class="download-action" type="button" onclick="downloadCurrent()">
        ${escapeHtml(downloadButtonLabel(tool === "all" ? detected : tool))}
      </button>
      ${mp3ExtraButton(detected, tool)}
    </div>
  `;

  preview.innerHTML = html;
  preview.style.display = "block";
}

function renderPreview(data) {
  const tool = selectedTool();
  const detected = data.story_video_fallback ? "story" : (data.detected || data.suggestion || data.kind || "unknown");
  const allowed = tool === "all" || data.strict_allowed === true || data.allowed === true;

  const title = data.title || "TikTok media";
  const thumb = data.thumbnail || (data.items && data.items[0] ? data.items[0].thumbnail : "");
  const warning = data.warning ? `<div class="meta">${escapeHtml(data.warning)}</div>` : "";

  // Strict mismatch view: no wrong media preview/title/download.
  if (!allowed) {
    const suggestedTool = detected && detected !== "unknown" ? detected : "all";

    preview.innerHTML = `
      <div class="wrong-tool-card" data-selected="${escapeHtml(tool)}" data-detected="${escapeHtml(detected)}">
        <span class="badge">No matching ${escapeHtml(kindName(tool))} preview</span>
        <h2>${escapeHtml(kindName(detected))} link detected</h2>
        <div class="meta">
          ${escapeHtml(previewText("selectedTab"))}: ${escapeHtml(kindName(tool))}<br>
          ${escapeHtml(previewText("detectedType"))}: ${escapeHtml(kindName(detected))}
        </div>
        <div class="wrong-tool-box">
          <div class="meta">${escapeHtml(wrongModeMessage(tool, suggestedTool))}</div>
          <a class="download-action" href="${toolPath(suggestedTool)}">${escapeHtml(toolDisplayName(suggestedTool))}</a>
        </div>
      </div>
    `;

    preview.style.display = "block";
    return;
  }

  const items = Array.isArray(data.items) ? data.items : [];

  // Instagram-style grid for stories/photos/slideshows/multiple items.
  if (detected === "story" || detected === "image" || items.length > 1) {
    renderTikTokMediaGrid(data, detected, tool);
    return;
  }

  const downloadKind = tool === "all" ? detected : tool;
  const thumbHtml = thumb
    ? `<img class="thumb" src="${thumb}" alt="TikTok preview">`
    : `<div class="empty-thumb">${escapeHtml(previewText("noPreview"))}</div>`;

  preview.innerHTML = `
    <div class="preview-main" data-selected="${escapeHtml(tool)}" data-detected="${escapeHtml(detected)}" data-allowed="1">
      ${thumbHtml}
      <div>
        <span class="badge">${escapeHtml(kindName(detected))} detected</span>
        <h2>${escapeHtml(title)}</h2>
        <div class="meta">
          ${escapeHtml(previewText("selectedTab"))}: ${escapeHtml(kindName(tool))}<br>
          ${escapeHtml(previewText("detectedType"))}: ${escapeHtml(kindName(detected))}<br>
          ${data.uploader ? `${escapeHtml(previewText("creator"))}: @${escapeHtml(data.uploader)}<br>` : ""}
          ${data.duration ? `${escapeHtml(previewText("duration"))}: ${escapeHtml(data.duration)} ${escapeHtml(previewText("seconds"))}<br>` : ""}
          ${escapeHtml(previewText("items"))}: ${items.length || 1}
        </div>
        ${warning ? `<div class="meta preview-warning">${escapeHtml(data.url_first_fallback ? "Photo / Carousel link detected from TikTok URL. Preview thumbnail may be unavailable, but this is still the correct tab." : data.warning)}</div>` : ""}
        ${data.photo_carousel_mode ? `<div class="meta photo-carousel-note">${data.real_carousel_extract ? `Carousel images extracted: ${(data.items || []).length}. Download will save all available images.` : `Photo / Carousel link detected, but image URLs were not exposed to this server request.`}</div>` : ""}
        ${data.story_video_fallback ? `<div class="meta story-fallback-note">${escapeHtml(previewText("storyFallback"))}</div>` : ""}
        <div class="preview-actions-inline">
          <button class="download-action" type="button" onclick="downloadCurrent()">
            ${escapeHtml(downloadButtonLabel(downloadKind))}
          </button>
          ${mp3ExtraButton(detected, tool)}
        </div>
      </div>
    </div>
  `;

  preview.style.display = "block";
}


async function readJsonOrThrow(res, fallbackMessage = "Request failed") {
  const text = await res.text();

  let data = null;
  try {
    data = text ? JSON.parse(text) : {};
  } catch (e) {
    throw new Error(`${fallbackMessage}: ${text.slice(0, 220) || res.statusText}`);
  }

  if (!res.ok) {
    throw new Error(data.detail || data.error || fallbackMessage);
  }

  return data;
}


async function detectPreview() {
  resetOutput();

  const formData = new FormData();
  formData.append("url", urlInput.value.trim());
  formData.append("mode", selectedTool());

  startProgress(currentLang() === "fr" ? "Détection du média..." : currentLang() === "ar" ? "جاري كشف الوسائط..." : "Detecting media...");
  statusBox.textContent = "";

  try {
    const res = await fetch("/api/preview-tiktok", { method: "POST", body: formData });
    const data = await readJsonOrThrow(res, "Preview failed");

    currentDetection = data;

    finishProgress(currentLang() === "fr" ? "Aperçu prêt" : currentLang() === "ar" ? "المعاينة جاهزة" : "Preview ready");
    statusBox.textContent = currentLang() === "fr" ? "Aperçu prêt." : currentLang() === "ar" ? "المعاينة جاهزة." : "Preview ready.";

    renderPreview(data);
  } catch (err) {
    clearInterval(progressTimer);
    statusBox.textContent = err.message;
  }
}

async function downloadCurrent() {
  if (!currentDetection) return;

  const tool = selectedTool();
  const detected = currentDetection.detected || currentDetection.suggestion || currentDetection.kind || "video";

  if (tool !== "all" && currentDetection.strict_allowed !== true && currentDetection.allowed !== true) {
    statusBox.textContent = wrongModeMessage(tool, detected);
    return;
  }

  const finalMode = tool === "all" ? detected : tool;

  const formData = new FormData();
  formData.append("url", urlInput.value.trim());
  formData.append("mode", finalMode);

  startProgress(currentLang() === "fr" ? "Téléchargement..." : currentLang() === "ar" ? "جاري التحميل..." : "Downloading...");
  setBusy(true);

  try {
    const res = await fetch("/download-tiktok", { method: "POST", body: formData });
    const data = await readJsonOrThrow(res, "Download failed");

    finishProgress(currentLang() === "fr" ? "Terminé" : currentLang() === "ar" ? "تم" : "Done");
    statusBox.textContent = currentLang() === "fr" ? "Téléchargement prêt." : currentLang() === "ar" ? "التحميل جاهز." : "Download ready.";

    if (data.files && data.files.length > 1) {
      downloads.innerHTML = data.files.map(file => `
        <a class="download-file" href="${file.download_url}" download>${escapeHtml(file.filename)}</a>
      `).join("");
      downloads.style.display = "block";
    } else {
      window.location.href = data.download_url;
    }
  } catch (err) {
    clearInterval(progressTimer);
    statusBox.textContent = err.message;
  } finally {
    setBusy(false);
  }
}


function shouldShowMp3Extra(detected, tool) {
  return tool !== "audio" && (tool === "video" || tool === "story" || detected === "video" || detected === "story");
}

function mp3ExtraButton(detected, tool) {
  if (!shouldShowMp3Extra(detected, tool)) return "";

  const lang = currentLang();
  const label = lang === "fr" ? "Télécharger MP3" : lang === "ar" ? "تحميل MP3" : "Download MP3";

  return `
    <button class="download-action mp3-secondary-action" type="button" onclick="downloadAsMp3()">
      ${escapeHtml(label)}
    </button>
  `;
}

async function downloadAsMp3() {
  const formData = new FormData();
  formData.append("url", urlInput.value.trim());
  formData.append("mode", "audio");

  startProgress(currentLang() === "fr" ? "Extraction MP3..." : currentLang() === "ar" ? "جاري استخراج MP3..." : "Extracting MP3...");
  setBusy(true);

  try {
    const res = await fetch("/download-tiktok", { method: "POST", body: formData });
    const data = await readJsonOrThrow(res, "MP3 extraction failed");

    finishProgress(currentLang() === "fr" ? "MP3 prêt" : currentLang() === "ar" ? "MP3 جاهز" : "MP3 ready");
    statusBox.textContent = currentLang() === "fr" ? "MP3 prêt." : currentLang() === "ar" ? "MP3 جاهز." : "MP3 ready.";

    if (data.files && data.files.length > 1) {
      downloads.innerHTML = data.files.map(file => `
        <a class="download-file" href="${file.download_url}" download>${escapeHtml(file.filename)}</a>
      `).join("");
      downloads.style.display = "block";
    } else {
      window.location.href = data.download_url;
    }
  } catch (err) {
    clearInterval(progressTimer);
    statusBox.textContent = err.message;
  } finally {
    setBusy(false);
  }
}


if (pasteBtn) pasteBtn.addEventListener("click", pasteTikTokUrl);
if (clearBtn) clearBtn.addEventListener("click", () => {
  urlInput.value = "";
  lastAutoDetectedUrl = "";
  clearTimeout(autoDetectTimer);
  clearInterval(progressTimer);
  resetOutput();
  progressWrap.style.display = "none";
  statusBox.textContent = "";
  syncInputActions();
  urlInput.focus();
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  await detectPreview();
});

document.addEventListener("click", (e) => {
  document.querySelectorAll(".lang-picker.open").forEach(picker => {
    if (!picker.contains(e.target)) picker.classList.remove("open");
  });
});

/* Auto-detect TikTok URL on paste/input */
let autoDetectTimer = null;
let lastAutoDetectedUrl = "";

function isLikelyTikTokUrl(value) {
  const text = String(value || "").trim();
  return /^https?:\/\/.+tiktok\.com\//i.test(text);
}

function scheduleAutoDetect(reason = "input") {
  const value = urlInput.value.trim();

  clearTimeout(autoDetectTimer);

  if (!isLikelyTikTokUrl(value)) return;
  if (value === lastAutoDetectedUrl && currentDetection) return;

  autoDetectTimer = setTimeout(async () => {
    const latest = urlInput.value.trim();

    if (!isLikelyTikTokUrl(latest)) return;
    if (latest === lastAutoDetectedUrl && currentDetection) return;

    lastAutoDetectedUrl = latest;
    await detectPreview();
  }, reason === "paste" ? 250 : 700);
}

urlInput.addEventListener("paste", () => {
  setTimeout(() => scheduleAutoDetect("paste"), 50);
});

urlInput.addEventListener("input", () => {
  currentDetection = null;
  syncInputActions();
  scheduleAutoDetect("input");
});


syncInputActions();
