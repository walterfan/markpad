const state = {
  files: [],
  activePath: null,
  activeAbsolutePath: null,
  activeMtime: null,
  selectedDirectory: "",
  deleteTarget: null,
  filter: "",
  renderTimer: null,
  collapsedDirs: new Set(),
  sidebarHidden: false,
  editorHidden: false,
  previewHidden: false,
  llmAvailable: false,
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
  createFile: document.getElementById("create-file"),
  deleteFile: document.getElementById("delete-file"),
  llmEditForm: document.getElementById("llm-edit-form"),
  llmEditPrompt: document.getElementById("llm-edit-prompt"),
  llmEditApply: document.getElementById("llm-edit-apply"),
  save: document.getElementById("save"),
  shutdown: document.getElementById("shutdown"),
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

function pathFromUrl() {
  const directPath = decodeURIComponent(window.location.pathname).replace(/^\/+/, "");
  if (directPath) {
    return directPath;
  }
  return new URLSearchParams(window.location.search).get("path");
}

function absolutePathFromUrl() {
  return new URLSearchParams(window.location.search).get("absolutePath");
}

function urlForPath(path) {
  if (!path) {
    return "/";
  }
  return `/${path.split("/").map(encodeURIComponent).join("/")}`;
}

function setPathInUrl(path, mode = "push") {
  if (!window.history?.pushState) {
    return;
  }
  const targetUrl = urlForPath(path);
  const currentUrl = `${window.location.pathname}${window.location.search}`;
  if (currentUrl === targetUrl) {
    return;
  }
  const method = mode === "replace" ? "replaceState" : "pushState";
  window.history[method]({ path }, "", targetUrl);
}

function setAbsolutePathInUrl(path, mode = "push") {
  if (!window.history?.pushState) {
    return;
  }
  const targetUrl = path ? `/?absolutePath=${encodeURIComponent(path)}` : "/";
  const currentUrl = `${window.location.pathname}${window.location.search}`;
  if (currentUrl === targetUrl) {
    return;
  }
  const method = mode === "replace" ? "replaceState" : "pushState";
  window.history[method]({ absolutePath: path }, "", targetUrl);
}

function isAbsolutePath(value) {
  const trimmed = value.trim();
  return trimmed.startsWith("/") || /^[A-Za-z]:[\\/]/.test(trimmed);
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
  state.llmAvailable = config.translate_available;
  if (config.translate_available) {
    els.translate.disabled = false;
    els.translate.title = `Translate selected text, or all Markdown if nothing is selected, with ${config.llm_model}`;
    updateLlmEditButtonState();
    els.llmEditPrompt.title = `Update selected text, or all Markdown if nothing is selected, with ${config.llm_model}`;
  } else {
    els.translate.disabled = true;
    els.translate.title = "Set LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY to enable translation";
    els.llmEditApply.disabled = true;
    els.llmEditPrompt.title = "Set LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY to enable LLM editing";
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
    const folderRow = document.createElement("div");
    folderRow.className = "tree-row";
    folderRow.classList.toggle("selected", isDeleteTarget("folder", dirPath));
    folderRow.appendChild(makeTargetCheckbox("folder", dirPath, `Select folder ${dirPath}`));

    const folderButton = document.createElement("button");
    folderButton.className = "folder-button";
    folderButton.classList.toggle("active", state.selectedDirectory === dirPath);
    folderButton.type = "button";
    folderButton.dataset.path = dirPath;
    folderButton.innerHTML = `
      <span aria-hidden="true">${collapsed ? "▸" : "▾"}</span>
      <span>${escapeHtml(dirName)}</span>
    `;
    folderButton.addEventListener("click", () => {
      state.selectedDirectory = dirPath;
      if (state.collapsedDirs.has(dirPath)) {
        state.collapsedDirs.delete(dirPath);
      } else {
        state.collapsedDirs.add(dirPath);
      }
      renderFileList();
    });
    folderRow.appendChild(folderButton);
    parent.appendChild(folderRow);

    if (!collapsed) {
      const childContainer = document.createElement("div");
      childContainer.className = "tree-children";
      parent.appendChild(childContainer);
      renderTreeNode(child, childContainer, dirPath);
    }
  }

  for (const file of files) {
    const fileRow = document.createElement("div");
    fileRow.className = "tree-row";
    fileRow.classList.toggle("selected", isDeleteTarget("file", file.path));
    fileRow.appendChild(makeTargetCheckbox("file", file.path, `Select file ${file.path}`));

    const button = document.createElement("button");
    button.className = `file-button ${file.path === state.activePath ? "active" : ""}`;
    button.dataset.path = file.path;
    button.type = "button";
    button.innerHTML = `
      <span>${escapeHtml(file.name)}</span>
      <span class="file-dir">${escapeHtml(file.directory || ".")}</span>
    `;
    button.addEventListener("click", () => {
      state.selectedDirectory = file.directory || "";
      openFile(file.path).catch((error) => setStatus(error.message));
    });
    fileRow.appendChild(button);
    parent.appendChild(fileRow);
  }
}

function makeTargetCheckbox(type, path, label) {
  const checkbox = document.createElement("input");
  checkbox.className = "target-checkbox";
  checkbox.type = "checkbox";
  checkbox.checked = isDeleteTarget(type, path);
  checkbox.setAttribute("aria-label", label);
  checkbox.addEventListener("change", () => {
    state.deleteTarget = checkbox.checked ? { type, path } : null;
    updateDeleteButtonState();
    renderFileList();
  });
  return checkbox;
}

function isDeleteTarget(type, path) {
  return state.deleteTarget?.type === type && state.deleteTarget.path === path;
}

function updateDeleteButtonState() {
  els.deleteFile.disabled = !state.deleteTarget;
}

function updateLlmEditButtonState() {
  els.llmEditApply.disabled = !state.llmAvailable || !els.llmEditPrompt.value.trim();
}

async function createFile() {
  const directory = state.selectedDirectory;
  const directoryLabel = directory || ".";
  const name = window.prompt(`Create Markdown file in ${directoryLabel}`, "untitled.md");
  if (name === null) return;
  if (!name.trim()) {
    setStatus("File name is required");
    return;
  }

  const created = await apiJson("/api/files", {
    method: "POST",
    body: JSON.stringify({ directory, name: name.trim() }),
  });
  await loadFiles();
  await openFile(created.path);
  setStatus("Created");
}

async function deleteSelectedTarget() {
  if (!state.deleteTarget) {
    setStatus("Select a file or folder before deleting");
    return;
  }
  const { type, path } = state.deleteTarget;
  const label = type === "folder" ? `folder "${path}" and all of its contents` : `file "${path}"`;
  if (!window.confirm(`Delete ${label}? This cannot be undone.`)) {
    return;
  }

  await apiJson("/api/files", {
    method: "DELETE",
    body: JSON.stringify({ type, path }),
  });
  if (activePathDeleted(type, path)) {
    clearActiveFile();
  }
  state.deleteTarget = null;
  if (
    type === "folder" &&
    (state.selectedDirectory === path || state.selectedDirectory.startsWith(`${path}/`))
  ) {
    state.selectedDirectory = "";
  }
  updateDeleteButtonState();
  await loadFiles();
  setStatus("Deleted");
}

function activePathDeleted(type, path) {
  if (!state.activePath) return false;
  return type === "file" ? state.activePath === path : state.activePath.startsWith(`${path}/`);
}

function clearActiveFile({ historyMode = "push" } = {}) {
  state.activePath = null;
  state.activeAbsolutePath = null;
  state.activeMtime = null;
  els.activePath.textContent = "Select a Markdown file";
  els.editor.value = "";
  els.preview.innerHTML = "";
  if (historyMode) {
    setPathInUrl(null, historyMode);
  }
  renderFileList();
  updateStats();
}

async function openFile(path, { historyMode = "push" } = {}) {
  try {
    const file = await apiJson(`/api/file?path=${encodeURIComponent(path)}`);
    state.activePath = file.path;
    state.activeAbsolutePath = null;
    state.activeMtime = file.mtime;
    state.selectedDirectory = file.path.includes("/") ? file.path.split("/").slice(0, -1).join("/") : "";
    els.activePath.textContent = file.path;
    els.editor.value = file.content;
    if (historyMode) {
      setPathInUrl(file.path, historyMode);
    }
    updateStats();
    renderFileList();
    await renderPreview();
    setStatus("Loaded");
  } catch (error) {
    setStatus(`Missing file: ${error.message}`);
  }
}

async function openAbsoluteFile(path, { historyMode = "push" } = {}) {
  try {
    const file = await apiJson(`/api/absolute-file?path=${encodeURIComponent(path.trim())}`);
    state.activePath = null;
    state.activeAbsolutePath = file.path;
    state.activeMtime = file.mtime;
    state.selectedDirectory = "";
    state.deleteTarget = null;
    els.activePath.textContent = file.path;
    els.editor.value = file.content;
    if (historyMode) {
      setAbsolutePathInUrl(file.path, historyMode);
    }
    updateDeleteButtonState();
    updateStats();
    renderFileList();
    await renderPreview();
    setStatus("Loaded absolute Markdown file");
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
  if (!state.activePath && !state.activeAbsolutePath) {
    setStatus("Select a Markdown file before saving");
    return;
  }
  const path = state.activeAbsolutePath || state.activePath;
  const endpoint = state.activeAbsolutePath ? "/api/absolute-file" : "/api/file";
  const saved = await apiJson(endpoint, {
    method: "POST",
    body: JSON.stringify({ path, content: els.editor.value }),
  });
  if (state.activeAbsolutePath) {
    state.activePath = null;
    state.activeAbsolutePath = saved.path;
  } else {
    state.activePath = saved.path;
    state.activeAbsolutePath = null;
  }
  state.activeMtime = saved.mtime;
  setStatus("Saved");
  await loadFiles();
}

async function shutdownServer() {
  const confirmed = window.confirm(
    "Shut down the markpad server? Unsaved changes will be lost and this page will stop working.",
  );
  if (!confirmed) {
    return;
  }
  els.shutdown.disabled = true;
  setStatus("Shutting down server...");
  try {
    const response = await fetch("/api/shutdown", { method: "POST" });
    if (!response.ok) {
      throw new Error(`Shutdown failed: HTTP ${response.status}`);
    }
  } catch (error) {
    els.shutdown.disabled = false;
    throw error;
  }
  renderShutdownNotice();
}

function renderShutdownNotice() {
  setStatus("Server stopped");
  const notice = document.createElement("div");
  notice.style.cssText =
    "position:fixed;inset:0;display:flex;align-items:center;justify-content:center;" +
    "background:rgba(15,23,42,0.85);color:#f8fafc;font-size:1.125rem;z-index:9999;" +
    "text-align:center;padding:1.5rem;";
  notice.innerHTML =
    "<div>" +
    "<h2 style=\"font-size:1.5rem;font-weight:600;margin-bottom:0.5rem;\">markpad has stopped</h2>" +
    "<p>The backend server has been shut down. You can close this tab.</p>" +
    "</div>";
  document.body.appendChild(notice);
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

async function editMarkdownWithPrompt() {
  const instruction = els.llmEditPrompt.value.trim();
  if (!instruction) {
    setStatus("Enter an edit prompt");
    return;
  }

  const selectionStart = els.editor.selectionStart;
  const selectionEnd = els.editor.selectionEnd;
  const hasSelection = selectionEnd > selectionStart;
  const source = hasSelection
    ? els.editor.value.slice(selectionStart, selectionEnd)
    : els.editor.value;
  if (!source.trim()) {
    setStatus("Nothing to update");
    return;
  }

  els.llmEditApply.disabled = true;
  setStatus(hasSelection ? "Updating selected Markdown..." : "Updating document...");
  try {
    await streamMarkdownEdit({
      source,
      instruction,
      selectionStart,
      selectionEnd,
      hasSelection,
    });
    updateStats();
    await renderPreview();
    setStatus("Updated");
  } finally {
    updateLlmEditButtonState();
  }
}

async function streamMarkdownEdit({
  source,
  instruction,
  selectionStart,
  selectionEnd,
  hasSelection,
}) {
  const response = await fetch("/api/edit/stream", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content: source, instruction }),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  if (!response.body) {
    const { content } = await apiJson("/api/edit", {
      method: "POST",
      body: JSON.stringify({ content: source, instruction }),
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

async function loadInitialFiles() {
  await loadFiles();
  const initialAbsolutePath = absolutePathFromUrl();
  if (initialAbsolutePath) {
    await openAbsoluteFile(initialAbsolutePath, { historyMode: "replace" });
    return;
  }
  const initialPath = pathFromUrl();
  if (initialPath) {
    await openFile(initialPath, { historyMode: "replace" });
  }
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
els.filter.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || !isAbsolutePath(els.filter.value)) {
    return;
  }
  event.preventDefault();
  openAbsoluteFile(els.filter.value).catch((error) => setStatus(error.message));
});
els.editor.addEventListener("input", schedulePreview);
els.llmEditPrompt.addEventListener("input", updateLlmEditButtonState);
els.llmEditForm.addEventListener("submit", (event) => {
  event.preventDefault();
  editMarkdownWithPrompt().catch((error) => setStatus(error.message));
});
els.createFile.addEventListener("click", () => createFile().catch((error) => setStatus(error.message)));
els.deleteFile.addEventListener("click", () =>
  deleteSelectedTarget().catch((error) => setStatus(error.message)),
);
els.save.addEventListener("click", () => saveFile().catch((error) => setStatus(error.message)));
els.shutdown.addEventListener("click", () => shutdownServer().catch((error) => setStatus(error.message)));
els.translate.addEventListener("click", () => translateMarkdown().catch((error) => setStatus(error.message)));
els.toggleSidebar.addEventListener("click", toggleSidebar);
els.toggleEditor.addEventListener("click", toggleEditorPane);
els.togglePreview.addEventListener("click", togglePreviewPane);
window.addEventListener("popstate", () => {
  const absolutePath = absolutePathFromUrl();
  if (absolutePath) {
    openAbsoluteFile(absolutePath, { historyMode: null }).catch((error) =>
      setStatus(`Missing file: ${error.message}`),
    );
    return;
  }
  const path = pathFromUrl();
  if (path) {
    openFile(path, { historyMode: null }).catch((error) => setStatus(`Missing file: ${error.message}`));
  } else {
    clearActiveFile({ historyMode: null });
  }
});
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
updateDeleteButtonState();
loadServerConfig().catch(() => setStatus("LLM translation config unavailable"));
loadInitialFiles().catch((error) => setStatus(error.message));
connectWebsocket();
