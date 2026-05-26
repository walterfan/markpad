const state = {
  files: [],
  activePath: null,
  activeMtime: null,
  filter: "",
  renderTimer: null,
  collapsedDirs: new Set(),
  sidebarHidden: false,
  editorHidden: false,
  previewHidden: false,
  theme: "paper",
};

const themes = {
  clear: {
    label: "Clear",
    bgColor: "#f6f8fb",
    panelBg: "#ffffff",
    textColor: "#172033",
    mutedColor: "#526071",
    borderColor: "#cbd5e1",
    hoverColor: "#e8f1ff",
    activeColor: "#cfe3ff",
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 18,
    lineHeight: 1.7,
  },
  paper: {
    label: "Paper",
    bgColor: "#f6eedf",
    panelBg: "#fffaf0",
    textColor: "#2b2418",
    mutedColor: "#6f624f",
    borderColor: "#d8c8ad",
    hoverColor: "#f1e2c6",
    activeColor: "#e9d2a8",
    fontFamily: 'Charter, "Iowan Old Style", Georgia, serif',
    fontSize: 19,
    lineHeight: 1.78,
  },
  dark: {
    label: "Dark",
    bgColor: "#111827",
    panelBg: "#1f2937",
    textColor: "#f3f4f6",
    mutedColor: "#cbd5e1",
    borderColor: "#475569",
    hoverColor: "#334155",
    activeColor: "#0f766e",
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 18,
    lineHeight: 1.75,
  },
};

const els = {
  appLayout: document.getElementById("app-layout"),
  sidebar: document.getElementById("sidebar"),
  fileList: document.getElementById("file-list"),
  fileCount: document.getElementById("file-count"),
  filter: document.getElementById("filter"),
  activePath: document.getElementById("active-path"),
  status: document.getElementById("status"),
  statusFooter: document.getElementById("status-footer"),
  totalFiles: document.getElementById("total-files"),
  charCount: document.getElementById("char-count"),
  themeStatus: document.getElementById("theme-status"),
  openThemeSettings: document.getElementById("open-theme-settings"),
  closeThemeSettings: document.getElementById("close-theme-settings"),
  themeDialog: document.getElementById("theme-dialog"),
  themeButtons: document.querySelectorAll("[data-theme]"),
  editor: document.getElementById("editor"),
  preview: document.getElementById("preview"),
  save: document.getElementById("save"),
  translate: document.getElementById("translate"),
  editorPane: document.getElementById("editor-pane"),
  previewPane: document.getElementById("preview-pane"),
  divider: document.getElementById("divider"),
  workspace: document.getElementById("workspace"),
  toggleSidebar: document.getElementById("toggle-sidebar"),
  toggleEditor: document.getElementById("toggle-editor"),
  togglePreview: document.getElementById("toggle-preview"),
};

function setStatus(message) {
  els.status.textContent = message;
  els.statusFooter.textContent = message;
}

function updateStats() {
  const total = state.files.length;
  els.totalFiles.textContent = `Files: ${total}`;
  els.charCount.textContent = `Characters: ${els.editor.value.length}`;
  els.themeStatus.textContent = `Theme: ${themes[state.theme].label}`;
}

function loadDisplaySettings() {
  const saved = localStorage.getItem("markpad.theme");
  if (saved && themes[saved]) {
    state.theme = saved;
  }
}

function applyDisplaySettings() {
  const theme = themes[state.theme];
  const root = document.documentElement;
  root.style.setProperty("--reader-bg", theme.bgColor);
  root.style.setProperty("--reader-panel-bg", theme.panelBg);
  root.style.setProperty("--reader-text", theme.textColor);
  root.style.setProperty("--reader-muted", theme.mutedColor);
  root.style.setProperty("--reader-border", theme.borderColor);
  root.style.setProperty("--reader-hover", theme.hoverColor);
  root.style.setProperty("--reader-active", theme.activeColor);
  root.style.setProperty("--reader-font-family", theme.fontFamily);
  root.style.setProperty("--reader-font-size", `${theme.fontSize}px`);
  root.style.setProperty("--reader-line-height", String(theme.lineHeight));
  for (const button of els.themeButtons) {
    button.classList.toggle("active", button.dataset.theme === state.theme);
    button.setAttribute("aria-pressed", String(button.dataset.theme === state.theme));
  }
  updateStats();
}

function setTheme(themeName) {
  if (!themes[themeName]) return;
  state.theme = themeName;
  localStorage.setItem("markpad.theme", state.theme);
  applyDisplaySettings();
}

function openThemeDialog() {
  if (typeof els.themeDialog.showModal === "function") {
    els.themeDialog.showModal();
  } else {
    els.themeDialog.setAttribute("open", "");
  }
}

function closeThemeDialog() {
  if (typeof els.themeDialog.close === "function") {
    els.themeDialog.close();
  } else {
    els.themeDialog.removeAttribute("open");
  }
}

function applyServerConfig(config) {
  if (config.translate_available) {
    els.translate.disabled = false;
    els.translate.title = `Translate selected text, or all Markdown if nothing is selected, with ${config.llm_model}`;
  } else {
    els.translate.disabled = true;
    els.translate.title = "Set LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY to enable translation";
  }
}

async function loadServerConfig() {
  const config = await apiJson("/api/config");
  applyServerConfig(config);
}

function loadSidebarSettings() {
  state.sidebarHidden = localStorage.getItem("markpad.sidebarHidden") === "true";
}

function applySidebarSettings() {
  els.appLayout.classList.toggle("sidebar-hidden", state.sidebarHidden);
  els.toggleSidebar.classList.toggle("active", !state.sidebarHidden);
  els.toggleSidebar.setAttribute("aria-pressed", String(!state.sidebarHidden));
  els.toggleSidebar.title = state.sidebarHidden ? "Show file pane" : "Hide file pane";
  els.toggleSidebar.setAttribute("aria-label", els.toggleSidebar.title);
}

function toggleSidebar() {
  state.sidebarHidden = !state.sidebarHidden;
  localStorage.setItem("markpad.sidebarHidden", String(state.sidebarHidden));
  applySidebarSettings();
}

function loadPaneSettings() {
  state.editorHidden = localStorage.getItem("markpad.editorHidden") === "true";
  state.previewHidden = localStorage.getItem("markpad.previewHidden") === "true";
  if (state.editorHidden && state.previewHidden) {
    state.editorHidden = false;
    state.previewHidden = false;
  }
}

function savePaneSettings() {
  localStorage.setItem("markpad.editorHidden", String(state.editorHidden));
  localStorage.setItem("markpad.previewHidden", String(state.previewHidden));
}

function applyPaneSettings() {
  els.editorPane.classList.toggle("hidden-pane", state.editorHidden);
  els.previewPane.classList.toggle("hidden-pane", state.previewHidden);
  els.divider.style.display = state.editorHidden || state.previewHidden ? "none" : "block";
  els.toggleEditor.classList.toggle("active", !state.editorHidden);
  els.togglePreview.classList.toggle("active", !state.previewHidden);
  els.toggleEditor.setAttribute("aria-pressed", String(!state.editorHidden));
  els.togglePreview.setAttribute("aria-pressed", String(!state.previewHidden));
  els.toggleEditor.title = state.editorHidden ? "Show Markdown pane" : "Hide Markdown pane";
  els.togglePreview.title = state.previewHidden ? "Show HTML pane" : "Hide HTML pane";
  els.toggleEditor.setAttribute("aria-label", els.toggleEditor.title);
  els.togglePreview.setAttribute("aria-label", els.togglePreview.title);
  if (!state.editorHidden && !state.previewHidden) {
    els.editorPane.style.flexBasis = els.editorPane.style.flexBasis || "50%";
    els.previewPane.style.flexBasis = els.previewPane.style.flexBasis || "50%";
  }
}

function toggleEditorPane() {
  state.editorHidden = !state.editorHidden;
  if (state.editorHidden && state.previewHidden) {
    state.previewHidden = false;
  }
  savePaneSettings();
  applyPaneSettings();
}

function togglePreviewPane() {
  state.previewHidden = !state.previewHidden;
  if (state.editorHidden && state.previewHidden) {
    state.editorHidden = false;
  }
  savePaneSettings();
  applyPaneSettings();
}

async function apiJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json();
}

async function readApiError(response) {
  const text = await response.text();
  if (!text) return response.statusText;
  try {
    const payload = JSON.parse(text);
    return payload.detail || text;
  } catch {
    return text;
  }
}

async function loadFiles() {
  state.files = await apiJson("/api/files");
  renderFileList();
  updateStats();
}

function renderFileList() {
  const filtered = state.files.filter((file) =>
    file.path.toLowerCase().includes(state.filter.toLowerCase()),
  );
  els.fileCount.textContent = `${filtered.length} file${filtered.length === 1 ? "" : "s"}`;
  els.fileList.innerHTML = "";
  const tree = buildFileTree(filtered);
  renderTreeNode(tree, els.fileList, "");
}

function buildFileTree(files) {
  const root = { dirs: new Map(), files: [] };
  for (const file of files) {
    const parts = file.path.split("/");
    const fileName = parts.pop();
    let node = root;
    for (const part of parts) {
      if (!node.dirs.has(part)) {
        node.dirs.set(part, { dirs: new Map(), files: [] });
      }
      node = node.dirs.get(part);
    }
    node.files.push({ ...file, name: fileName || file.name });
  }
  return root;
}

function renderTreeNode(node, parent, currentPath) {
  const dirs = [...node.dirs.entries()].sort(([left], [right]) => left.localeCompare(right));
  const files = [...node.files].sort((left, right) => left.name.localeCompare(right.name));

  for (const [dirName, child] of dirs) {
    const dirPath = currentPath ? `${currentPath}/${dirName}` : dirName;
    const collapsed = state.collapsedDirs.has(dirPath);
    const folderButton = document.createElement("button");
    folderButton.className = "folder-button";
    folderButton.type = "button";
    folderButton.dataset.path = dirPath;
    folderButton.innerHTML = `
      <span aria-hidden="true">${collapsed ? "▸" : "▾"}</span>
      <span>${escapeHtml(dirName)}</span>
    `;
    folderButton.addEventListener("click", () => {
      if (state.collapsedDirs.has(dirPath)) {
        state.collapsedDirs.delete(dirPath);
      } else {
        state.collapsedDirs.add(dirPath);
      }
      renderFileList();
    });
    parent.appendChild(folderButton);

    if (!collapsed) {
      const childContainer = document.createElement("div");
      childContainer.className = "tree-children";
      parent.appendChild(childContainer);
      renderTreeNode(child, childContainer, dirPath);
    }
  }

  for (const file of files) {
    const button = document.createElement("button");
    button.className = `file-button ${file.path === state.activePath ? "active" : ""}`;
    button.dataset.path = file.path;
    button.type = "button";
    button.innerHTML = `
      <span>${escapeHtml(file.name)}</span>
      <span class="file-dir">${escapeHtml(file.directory || ".")}</span>
    `;
    button.addEventListener("click", () => openFile(file.path));
    parent.appendChild(button);
  }
}

async function openFile(path) {
  try {
    const file = await apiJson(`/api/file?path=${encodeURIComponent(path)}`);
    state.activePath = file.path;
    state.activeMtime = file.mtime;
    els.activePath.textContent = file.path;
    els.editor.value = file.content;
    updateStats();
    renderFileList();
    await renderPreview();
    setStatus("Loaded");
  } catch (error) {
    setStatus(`Missing file: ${error.message}`);
  }
}

async function renderPreview() {
  const { html } = await apiJson("/api/render", {
    method: "POST",
    body: JSON.stringify({ path: state.activePath, content: els.editor.value }),
  });
  els.preview.innerHTML = html;
  renderMermaid();
}

function schedulePreview() {
  updateStats();
  clearTimeout(state.renderTimer);
  state.renderTimer = setTimeout(() => {
    renderPreview().catch((error) => setStatus(`Render failed: ${error.message}`));
  }, 150);
}

async function saveFile() {
  if (!state.activePath) {
    setStatus("Select a Markdown file before saving");
    return;
  }
  const saved = await apiJson("/api/file", {
    method: "POST",
    body: JSON.stringify({ path: state.activePath, content: els.editor.value }),
  });
  state.activeMtime = saved.mtime;
  setStatus("Saved");
  await loadFiles();
}

async function translateMarkdown() {
  const selectionStart = els.editor.selectionStart;
  const selectionEnd = els.editor.selectionEnd;
  const hasSelection = selectionEnd > selectionStart;
  const source = hasSelection
    ? els.editor.value.slice(selectionStart, selectionEnd)
    : els.editor.value;
  if (!source.trim()) {
    setStatus("Nothing to translate");
    return;
  }

  els.translate.disabled = true;
  setStatus(hasSelection ? "Translating selected text..." : "Translating document...");
  try {
    await streamTranslation({
      source,
      selectionStart,
      selectionEnd,
      hasSelection,
    });
    updateStats();
    await renderPreview();
    setStatus("Translated");
  } finally {
    await loadServerConfig().catch(() => {
      els.translate.disabled = false;
    });
  }
}

async function streamTranslation({ source, selectionStart, selectionEnd, hasSelection }) {
  const response = await fetch("/api/translate/stream", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content: source, target_language: "Chinese" }),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  if (!response.body) {
    const { content } = await apiJson("/api/translate", {
      method: "POST",
      body: JSON.stringify({ content: source, target_language: "Chinese" }),
    });
    replaceTranslatedText({ content, selectionStart, selectionEnd, hasSelection });
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let content = "";
  let replaceEnd = hasSelection ? selectionEnd : els.editor.value.length;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    content += decoder.decode(value, { stream: true });
    replaceEnd = replaceTranslatedText({
      content,
      selectionStart,
      selectionEnd: replaceEnd,
      hasSelection,
    });
    schedulePreview();
  }
  content += decoder.decode();
  if (content) {
    replaceTranslatedText({
      content,
      selectionStart,
      selectionEnd: replaceEnd,
      hasSelection,
    });
  }
}

function replaceTranslatedText({ content, selectionStart, selectionEnd, hasSelection }) {
  if (hasSelection) {
    els.editor.setRangeText(content, selectionStart, selectionEnd, "select");
    return selectionStart + content.length;
  }
  els.editor.value = content;
  return content.length;
}

function initDivider() {
  let dragging = false;
  els.divider.addEventListener("mousedown", () => {
    dragging = true;
    document.body.style.cursor = "col-resize";
  });
  window.addEventListener("mouseup", () => {
    dragging = false;
    document.body.style.cursor = "";
  });
  window.addEventListener("mousemove", (event) => {
    if (!dragging) return;
    const rect = els.workspace.getBoundingClientRect();
    const left = Math.max(288, Math.min(event.clientX - rect.left, rect.width - 288));
    const leftPercent = (left / rect.width) * 100;
    els.editorPane.style.flexBasis = `${leftPercent}%`;
    els.previewPane.style.flexBasis = `${100 - leftPercent}%`;
  });
}

function renderMermaid() {
  if (!window.mermaid) return;
  window.mermaid.initialize({ startOnLoad: false });
  window.mermaid.run({ querySelector: ".mermaid" }).catch((error) => {
    for (const block of document.querySelectorAll(".diagram-mermaid")) {
      const errorEl = block.querySelector(".diagram-error");
      if (errorEl) {
        errorEl.textContent = error.message || "Mermaid rendering failed";
        errorEl.classList.remove("hidden");
      }
    }
  });
}

function connectWebsocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
  socket.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    if (message.type !== "files-changed") return;
    await loadFiles();
    if (state.activePath && message.changes.some((change) => change.path.endsWith(state.activePath))) {
      setStatus("File changed on disk; reload to see external changes");
    }
  };
  socket.onclose = () => setTimeout(connectWebsocket, 1000);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

els.filter.addEventListener("input", () => {
  state.filter = els.filter.value;
  renderFileList();
});
els.editor.addEventListener("input", schedulePreview);
els.save.addEventListener("click", () => saveFile().catch((error) => setStatus(error.message)));
els.translate.addEventListener("click", () => translateMarkdown().catch((error) => setStatus(error.message)));
els.toggleSidebar.addEventListener("click", toggleSidebar);
els.toggleEditor.addEventListener("click", toggleEditorPane);
els.togglePreview.addEventListener("click", togglePreviewPane);
els.openThemeSettings.addEventListener("click", openThemeDialog);
els.closeThemeSettings.addEventListener("click", closeThemeDialog);
els.themeDialog.addEventListener("click", (event) => {
  if (event.target === els.themeDialog) {
    closeThemeDialog();
  }
});
for (const button of els.themeButtons) {
  button.addEventListener("click", () => {
    setTheme(button.dataset.theme);
    closeThemeDialog();
  });
}
initDivider();
loadDisplaySettings();
applyDisplaySettings();
loadSidebarSettings();
applySidebarSettings();
loadPaneSettings();
applyPaneSettings();
loadServerConfig().catch(() => setStatus("LLM translation config unavailable"));
loadFiles().catch((error) => setStatus(error.message));
connectWebsocket();
