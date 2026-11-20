// AquaGuard Client Application
document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentMode = "image"; // 'image' or 'video'
  let currentSpeedMode = "turbo"; // 'turbo', 'balanced', or 'detailed'
  let selectedFile = null;
  let availableClasses = [];
  let categoryGroups = {};
  let selectedClasses = new Set();
  let progressInterval = null;

  // DOM Elements
  const tabImage = document.getElementById("tabImage");
  const tabVideo = document.getElementById("tabVideo");
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const uploadPrompt = document.getElementById("uploadPrompt");
  const fileSelectedView = document.getElementById("fileSelectedView");
  const selectedFileName = document.getElementById("selectedFileName");
  const selectedFileSize = document.getElementById("selectedFileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const formatHint = document.getElementById("formatHint");
  const videoOptionsPanel = document.getElementById("videoOptionsPanel");
  const speedModeLabel = document.getElementById("speedModeLabel");
  const speedModeDesc = document.getElementById("speedModeDesc");
  const btnSpeedTurbo = document.getElementById("btnSpeedTurbo");
  const btnSpeedBalanced = document.getElementById("btnSpeedBalanced");
  const btnSpeedDetailed = document.getElementById("btnSpeedDetailed");
  const confRange = document.getElementById("confRange");
  const confVal = document.getElementById("confVal");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const analyzeBtnText = document.getElementById("analyzeBtnText");
  const classesCheckboxGrid = document.getElementById("classesCheckboxGrid");
  const selectedClassesCount = document.getElementById("selectedClassesCount");
  const selectAllClasses = document.getElementById("selectAllClasses");
  const deselectAllClasses = document.getElementById("deselectAllClasses");
  const classesToggle = document.getElementById("classesToggle");
  const classesListContainer = document.getElementById("classesListContainer");
  const classesChevron = document.getElementById("classesChevron");

  // Results DOM Elements
  const emptyResultsState = document.getElementById("emptyResultsState");
  const loadingResultsState = document.getElementById("loadingResultsState");
  const loadingStatusText = document.getElementById("loadingStatusText");
  const activeResultsView = document.getElementById("activeResultsView");
  const metricTotalDetections = document.getElementById("metricTotalDetections");
  const metricSeverityBadge = document.getElementById("metricSeverityBadge");
  const metricCategoriesCount = document.getElementById("metricCategoriesCount");
  const metricInferenceTime = document.getElementById("metricInferenceTime");
  const imageViewerContainer = document.getElementById("imageViewerContainer");
  const annotatedImage = document.getElementById("annotatedImage");
  const videoViewerContainer = document.getElementById("videoViewerContainer");
  const annotatedVideo = document.getElementById("annotatedVideo");
  const timelineEventsList = document.getElementById("timelineEventsList");
  const contaminantsList = document.getElementById("contaminantsList");
  const mediaDimsText = document.getElementById("mediaDimsText");
  const exportBtnGroup = document.getElementById("exportBtnGroup");
  const downloadResultBtn = document.getElementById("downloadResultBtn");
  const downloadBtnLabel = document.getElementById("downloadBtnLabel");
  const viewerTitle = document.getElementById("viewerTitle");

  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Fetch Available Classes from Backend
  async function loadClasses() {
    try {
      const res = await fetch("/api/classes");
      const data = await res.json();
      availableClasses = data.classes || [];
      categoryGroups = data.groups || {};
      selectedClasses = new Set(availableClasses);
      renderClassFilters();
    } catch (err) {
      console.warn("Could not load classes:", err);
    }
  }

  // Render Target Class Filters
  function renderClassFilters() {
    classesCheckboxGrid.innerHTML = "";
    availableClasses.forEach((cls) => {
      const label = document.createElement("label");
      label.className =
        "flex items-center space-x-2 p-2 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200/80 cursor-pointer transition select-none shadow-xs";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = selectedClasses.has(cls);
      cb.className = "accent-cyan-600 rounded cursor-pointer w-3.5 h-3.5";
      cb.addEventListener("change", () => {
        if (cb.checked) {
          selectedClasses.add(cls);
        } else {
          selectedClasses.delete(cls);
        }
        updateClassesCount();
      });

      const span = document.createElement("span");
      span.className = "text-slate-700 capitalize truncate font-medium text-xs";
      span.textContent = cls;

      label.appendChild(cb);
      label.appendChild(span);
      classesCheckboxGrid.appendChild(label);
    });
    updateClassesCount();
  }

  function updateClassesCount() {
    selectedClassesCount.textContent = selectedClasses.size;
  }

  // Checkbox bulk actions
  selectAllClasses.addEventListener("click", () => {
    selectedClasses = new Set(availableClasses);
    classesCheckboxGrid.querySelectorAll("input[type=checkbox]").forEach((cb) => (cb.checked = true));
    updateClassesCount();
  });

  deselectAllClasses.addEventListener("click", () => {
    selectedClasses.clear();
    classesCheckboxGrid.querySelectorAll("input[type=checkbox]").forEach((cb) => (cb.checked = false));
    updateClassesCount();
  });

  // Accordion toggle
  classesToggle.addEventListener("click", () => {
    classesListContainer.classList.toggle("hidden");
    classesChevron.classList.toggle("rotate-180");
  });

  // Switch Media Mode
  function setMode(mode) {
    currentMode = mode;
    clearFile();

    if (mode === "image") {
      tabImage.className =
        "flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 transition bg-cyan-600 text-white shadow-sm";
      tabVideo.className =
        "flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 transition text-slate-600 hover:text-slate-900 hover:bg-slate-100";
      fileInput.accept = ".png,.jpg,.jpeg";
      formatHint.textContent = "Supported: PNG, JPG, JPEG (Max 25MB)";
      videoOptionsPanel.classList.add("hidden");
      analyzeBtnText.textContent = "Analyze Image";
    } else {
      tabVideo.className =
        "flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 transition bg-cyan-600 text-white shadow-sm";
      tabImage.className =
        "flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 transition text-slate-600 hover:text-slate-900 hover:bg-slate-100";
      fileInput.accept = ".mp4,.mkv";
      formatHint.textContent = "Supported: MP4, MKV (Max 150MB)";
      videoOptionsPanel.classList.remove("hidden");
      analyzeBtnText.textContent = "Analyze Video Footage";
    }
    if (window.lucide) window.lucide.createIcons();
  }

  tabImage.addEventListener("click", () => setMode("image"));
  tabVideo.addEventListener("click", () => setMode("video"));

  // Speed Mode Selectors
  function setSpeedMode(mode) {
    currentSpeedMode = mode;
    const btnActiveClasses = "py-1.5 px-2 rounded-lg font-bold text-center transition bg-white text-slate-900 shadow-xs border border-slate-200/80";
    const btnInactiveClasses = "py-1.5 px-2 rounded-lg font-medium text-center text-slate-500 hover:text-slate-900 transition";

    btnSpeedTurbo.className = mode === "turbo" ? btnActiveClasses : btnInactiveClasses;
    btnSpeedBalanced.className = mode === "balanced" ? btnActiveClasses : btnInactiveClasses;
    btnSpeedDetailed.className = mode === "detailed" ? btnActiveClasses : btnInactiveClasses;

    if (mode === "turbo") {
      speedModeLabel.textContent = "⚡ Turbo (~15-25s)";
      speedModeLabel.className = "font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-[11px]";
      speedModeDesc.textContent = "Accelerated direct keyframe seek (6 samples) — processes in ~15-25 seconds.";
    } else if (mode === "balanced") {
      speedModeLabel.textContent = "⚖️ Balanced (~30-45s)";
      speedModeLabel.className = "font-bold text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 text-[11px]";
      speedModeDesc.textContent = "Evenly spaced keyframes (10 samples) — good balance of speed & coverage.";
    } else {
      speedModeLabel.textContent = "🔬 Detailed (~60-90s)";
      speedModeLabel.className = "font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 text-[11px]";
      speedModeDesc.textContent = "High-density sampling (16 samples) — thorough scan across footage.";
    }
  }

  if (btnSpeedTurbo) btnSpeedTurbo.addEventListener("click", () => setSpeedMode("turbo"));
  if (btnSpeedBalanced) btnSpeedBalanced.addEventListener("click", () => setSpeedMode("balanced"));
  if (btnSpeedDetailed) btnSpeedDetailed.addEventListener("click", () => setSpeedMode("detailed"));

  // Sliders
  confRange.addEventListener("input", (e) => {
    confVal.textContent = parseFloat(e.target.value).toFixed(2);
  });

  // DropZone Events
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    const ext = "." + file.name.split(".").pop().toLowerCase();
    const isImage = [".png", ".jpg", ".jpeg"].includes(ext);
    const isVideo = [".mp4", ".mkv"].includes(ext);

    if (currentMode === "image" && !isImage) {
      alert("Please select a valid image format (.png, .jpg, .jpeg)");
      return;
    }
    if (currentMode === "video" && !isVideo) {
      alert("Please select a valid video format (.mp4, .mkv)");
      return;
    }

    selectedFile = file;
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = formatBytes(file.size);

    uploadPrompt.classList.add("hidden");
    fileSelectedView.classList.remove("hidden");
    analyzeBtn.disabled = false;
    if (window.lucide) window.lucide.createIcons();
  }

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });

  function clearFile() {
    selectedFile = null;
    fileInput.value = "";
    uploadPrompt.classList.remove("hidden");
    fileSelectedView.classList.add("hidden");
    analyzeBtn.disabled = true;
    if (window.lucide) window.lucide.createIcons();
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // Analyze Action
  analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    if (selectedClasses.size === 0) {
      alert("Please select at least one pollutant category to detect.");
      return;
    }

    // Prepare UI for loading
    emptyResultsState.classList.add("hidden");
    activeResultsView.classList.add("hidden");
    loadingResultsState.classList.remove("hidden");
    analyzeBtn.disabled = true;

    if (currentMode === "video") {
      const messages = [
        "Applying direct keyframe seek (skipping redundant video decoding)...",
        "Running accelerated Grounding DINO vision model...",
        "Identifying surface debris & water pollutants across timeline...",
        "Generating annotated video preview & pollution timeline...",
      ];
      let msgIdx = 0;
      loadingStatusText.textContent = messages[0];
      progressInterval = setInterval(() => {
        msgIdx = (msgIdx + 1) % messages.length;
        loadingStatusText.textContent = messages[msgIdx];
      }, 4000);
    } else {
      loadingStatusText.textContent = "Analyzing image pixels for water surface debris...";
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("threshold", confRange.value);
    formData.append("text_threshold", confRange.value);
    formData.append("classes", JSON.stringify(Array.from(selectedClasses)));

    if (currentMode === "video") {
      formData.append("speed_mode", currentSpeedMode);
    }

    const endpoint = currentMode === "video" ? "/api/detect/video" : "/api/detect/image";

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
      }

      if (!response.ok) {
        let errMessage = "Detection request failed.";
        try {
          const errData = await response.json();
          errMessage = errData.detail || errMessage;
        } catch (_) {}
        throw new Error(errMessage);
      }

      const result = await response.json();
      displayResults(result);
    } catch (error) {
      alert(`Error: ${error.message}`);
      loadingResultsState.classList.add("hidden");
      emptyResultsState.classList.remove("hidden");
    } finally {
      if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
      }
      analyzeBtn.disabled = false;
      if (window.lucide) window.lucide.createIcons();
    }
  });

  // Display Inference Results
  function displayResults(data) {
    loadingResultsState.classList.add("hidden");
    activeResultsView.classList.remove("hidden");

    // Metrics
    metricTotalDetections.textContent = data.total_detections || 0;
    metricInferenceTime.textContent = `${data.processing_time_sec}s`;
    const uniqueClasses = Object.keys(data.counts_by_class || {});
    metricCategoriesCount.textContent = uniqueClasses.length;

    // Severity Badge
    const sev = data.severity || { level: "Clean", color: "#10b981", description: "" };
    metricSeverityBadge.textContent = sev.level;
    metricSeverityBadge.style.backgroundColor = `${sev.color}15`;
    metricSeverityBadge.style.color = sev.color;
    metricSeverityBadge.style.borderColor = `${sev.color}40`;

    // Dimensions
    mediaDimsText.textContent = `${data.width} × ${data.height} px`;

    // Download Button
    exportBtnGroup.classList.remove("hidden");
    downloadResultBtn.href = data.annotated_url;
    downloadResultBtn.setAttribute("download", data.annotated_filename);
    downloadBtnLabel.textContent =
      data.media_type === "video" ? "Download Video" : "Download Image";

    if (data.media_type === "image") {
      viewerTitle.textContent = "Annotated Image Canvas";
      imageViewerContainer.classList.remove("hidden");
      videoViewerContainer.classList.add("hidden");
      annotatedImage.src = `${data.annotated_url}?t=${Date.now()}`;
    } else {
      const modeStr = (data.speed_mode || "turbo").toUpperCase();
      viewerTitle.textContent = `Video Analysis (${data.duration_sec}s) — ${data.sampled_frames} keyframes in ${data.processing_time_sec}s [${modeStr}]`;
      imageViewerContainer.classList.add("hidden");
      videoViewerContainer.classList.remove("hidden");
      annotatedVideo.src = `${data.annotated_url}?t=${Date.now()}`;
      renderVideoTimeline(data.timeline || []);
    }

    renderContaminantsBreakdown(data.counts_by_class || {});
    if (window.lucide) window.lucide.createIcons();
  }

  // Render Video Timeline Events
  function renderVideoTimeline(events) {
    timelineEventsList.innerHTML = "";
    if (events.length === 0) {
      timelineEventsList.innerHTML =
        '<p class="text-slate-400 italic text-[11px]">No debris detected in sampled frames.</p>';
      return;
    }

    events.forEach((ev) => {
      const row = document.createElement("div");
      row.className =
        "flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs";

      const left = document.createElement("div");
      left.className = "flex items-center space-x-2";

      const timeBadge = document.createElement("span");
      timeBadge.className =
        "px-2 py-0.5 rounded font-mono font-bold bg-cyan-50 text-cyan-700 border border-cyan-200 text-[11px]";
      timeBadge.textContent = ev.time_formatted;

      const labelsSummary = Object.entries(ev.labels)
        .map(([lbl, count]) => `${lbl} (${count})`)
        .join(", ");
      const labelsSpan = document.createElement("span");
      labelsSpan.className = "text-slate-700 font-medium capitalize";
      labelsSpan.textContent = labelsSummary;

      left.appendChild(timeBadge);
      left.appendChild(labelsSpan);

      const countBadge = document.createElement("span");
      countBadge.className = "text-slate-500 font-semibold";
      countBadge.textContent = `${ev.count} items`;

      row.appendChild(left);
      row.appendChild(countBadge);
      timelineEventsList.appendChild(row);
    });
  }

  // Render Contaminants Breakdown Badges
  function renderContaminantsBreakdown(counts) {
    contaminantsList.innerHTML = "";
    const keys = Object.keys(counts);

    if (keys.length === 0) {
      contaminantsList.innerHTML =
        '<p class="text-slate-400 italic text-xs col-span-2">No pollution objects detected above the confidence threshold.</p>';
      return;
    }

    keys.forEach((cat) => {
      const count = counts[cat];
      const card = document.createElement("div");
      card.className =
        "flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/90 shadow-xs";

      const name = document.createElement("span");
      name.className = "capitalize font-semibold text-slate-800 text-xs";
      name.textContent = cat;

      const badge = document.createElement("span");
      badge.className =
        "px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-50 text-cyan-700 border border-cyan-200";
      badge.textContent = `${count} detected`;

      card.appendChild(name);
      card.appendChild(badge);
      contaminantsList.appendChild(card);
    });
  }

  // Check Backend Health
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        const devText = document.getElementById("deviceStatusText");
        devText.textContent = `AI Engine: ${data.device.toUpperCase()}`;
      }
    } catch (_) {}
  }

  // Initialize
  loadClasses();
  checkHealth();
});
