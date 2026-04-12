let bridge = null;
let THREE = null;
let OrbitControls = null;
let GLTFLoader = null;

const promptInput = document.getElementById("prompt-input");
const generateButton = document.getElementById("generate-button");
const toolbeltImageButton = document.getElementById("toolbelt-image");
const toolbeltMicButton = document.getElementById("toolbelt-mic");
const toolbeltImproveButton = document.getElementById("toolbelt-improve");
const toolbeltSettingsButton = document.getElementById("toolbelt-settings");
const composerQuickMenu = document.getElementById("composer-quick-menu");
const quickClearConversationButton = document.getElementById("quick-clear-conversation");
const quickToggleAutoscrollButton = document.getElementById("quick-toggle-autoscroll");
const quickToggleTimestampsButton = document.getElementById("quick-toggle-timestamps");
const promptImproverModal = document.getElementById("prompt-improver-modal");
const promptImproverBackdrop = document.getElementById("prompt-improver-backdrop");
const closePromptImproverButton = document.getElementById("close-prompt-improver");
const promptImproverOriginal = document.getElementById("prompt-improver-original");
const promptImproverSuggestion = document.getElementById("prompt-improver-suggestion");
const usePromptSuggestionButton = document.getElementById("use-prompt-suggestion");
const keepOriginalPromptButton = document.getElementById("keep-original-prompt");
const openBlenderButton = document.getElementById("open-blender-button");
const backendStatus = document.getElementById("backend-status");
const systemAiStatus = document.getElementById("system-ai-status");
const systemBlenderStatus = document.getElementById("system-blender-status");
const scriptPath = document.getElementById("script-path");
const logOutput = document.getElementById("log-output");
const logsModal = document.getElementById("logs-modal");
const logsBackdrop = document.getElementById("logs-backdrop");
const showLogsButton = document.getElementById("show-logs-button");
const closeLogsButton = document.getElementById("close-logs-button");
const footerVersion = document.getElementById("footer-version");
const sessionTitle = document.getElementById("sessionTitle");
const metricLength = document.getElementById("metric-length");
const metricWidth = document.getElementById("metric-width");
const metricHeight = document.getElementById("metric-height");
const reviewStatus = document.getElementById("review-status");
const metricModelFamily = document.getElementById("metric-model-family");
const printabilityBase = document.getElementById("printability-base");
const printabilityOverhang = document.getElementById("printability-overhang");
const meshPreview = document.getElementById("mesh-preview");
const meshExport = document.getElementById("mesh-export");
const meshQuality = document.getElementById("mesh-quality");
const conversationThread = document.getElementById("conversation-thread");
const generationStatus = document.getElementById("generation-status");
const readinessState = document.getElementById("readiness-state");
const propertiesEmptyState = document.getElementById("properties-empty-state");
const propertiesDimensionsSection = document.getElementById("properties-dimensions-section");
const propertiesWallsSection = document.getElementById("properties-walls-section");
const propertiesFeaturesSection = document.getElementById("properties-features-section");
const currentModelDimensions = document.getElementById("current-model-dimensions");
const currentModelWalls = document.getElementById("current-model-walls");
const currentModelFeatures = document.getElementById("current-model-features");
const setupWizard = document.getElementById("setup-wizard");
const setupStatusTitle = document.getElementById("setup-status-title");
const setupStatusText = document.getElementById("setup-status-text");
const setupSteps = document.getElementById("setup-steps");
const setupDetectButton = document.getElementById("setup-detect-button");
const setupPullButton = document.getElementById("setup-pull-button");
const setupSmokeButton = document.getElementById("setup-smoke-button");
const setupRefreshButton = document.getElementById("setup-refresh-button");
const setupHelpText = document.getElementById("setup-help-text");
const viewPlanButton = document.getElementById("view-plan-button");

const viewerRenderSurface = document.getElementById("viewer-render-surface");
const viewerOverlay = document.getElementById("viewer-overlay");
const viewerOverlayTitle = document.getElementById("viewer-overlay-title");
const viewerOverlayText = document.getElementById("viewer-overlay-text");
const viewerOverlaySpinner = document.getElementById("viewer-overlay-spinner");
const viewerModeSolid = document.getElementById("viewer-mode-solid");
const viewerModeWireframe = document.getElementById("viewer-mode-wireframe");
const viewerFocusButton = document.getElementById("viewer-focus-button");
const viewerResetButton = document.getElementById("viewer-reset-button");
const viewerToolOrbit = document.getElementById("viewer-tool-orbit");
const viewerToolPan = document.getElementById("viewer-tool-pan");
const viewerToolZoom = document.getElementById("viewer-tool-zoom");
const viewerOrbitControl = document.getElementById("viewer-orbit-control");
const viewerOrbitThumb = document.getElementById("viewer-orbit-thumb");
const viewerAxisScene = document.getElementById("viewer-axis-scene");
const viewerAutoOrbitToggle = document.getElementById("viewer-auto-orbit-toggle");
const newConversationButton = document.getElementById("new-conversation-button");
const topnavTabs = Array.from(document.querySelectorAll(".topnav-tab"));
const modeWorkspace = document.getElementById("mode-workspace");
const modeModels = document.getElementById("mode-models");
const modeProjects = document.getElementById("mode-projects");
const modeTemplates = document.getElementById("mode-templates");
const modelsSearchInput = document.getElementById("models-search-input");
const modelsSortSelect = document.getElementById("models-sort-select");
const modelsTotalCount = document.getElementById("models-total-count");
const modelsFamilyFilters = document.getElementById("models-family-filters");
const modelsSidebarList = document.getElementById("models-sidebar-list");
const modelsGrid = document.getElementById("models-grid");
const modelsEmptyState = document.getElementById("models-empty-state");
const modelsEmptyCta = document.getElementById("models-empty-cta");
const modelsGoWorkspace = document.getElementById("models-go-workspace");
const modelsSelectionSummary = document.getElementById("models-selection-summary");
const modelsSelectionOpen = document.getElementById("models-selection-open");
const modelsSelectionDelete = document.getElementById("models-selection-delete");
let generationInFlight = false;
let activeSession = createEmptySession();
let librarySummary = { saved_model_count: 0, recent_saved_models: [], project_count: 0, template_count: 0, templates: [] };
let savedModels = [];
let hasLoadedInitialState = false;
let runtimeHealth = null;
let runtimeSetupFlow = [];
let chatMessages = [];
let hasSeededStartupConversation = false;
let autoScrollEnabled = true;
let timestampsEnabled = true;
let currentPromptSuggestion = "";
let currentSessionTitle = "Untitled";
let generationAnimationInterval = 0;
let generationAnimationFrame = 0;
let currentAppMode = "workspace";
let selectedSavedModelId = "";
let modelsSearchQuery = "";
let modelsSortMode = "newest";
let activeModelFamilyFilter = "all";
const STARTUP_EXAMPLE_PROMPTS = [
  "Wall bracket with four holes",
  "Desk cable clip",
  "Small electronics enclosure",
  "Planter with 3 mm walls",
];

const TAB_INTENTS = {
  workspace: "Active generation workspace",
  models: "Saved generated model library",
  projects: "Grouped model organization",
  templates: "Starter creations and capability examples",
};

const modeScreens = {
  workspace: modeWorkspace,
  models: modeModels,
  projects: modeProjects,
  templates: modeTemplates,
};

function appendLog(message) {
  const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const line = `[${timestamp}] ${message}`;
  logOutput.textContent = `${logOutput.textContent}\n${line}`.trim();
  logOutput.scrollTop = logOutput.scrollHeight;
}

function makeTimestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function scrollConversationToBottom() {
  if (!conversationThread || !autoScrollEnabled) {
    return;
  }
  conversationThread.scrollTop = conversationThread.scrollHeight;
}

function setComposerQuickMenuOpen(isOpen) {
  if (!composerQuickMenu) {
    return;
  }
  composerQuickMenu.hidden = !isOpen;
}

function setPromptImproverOpen(isOpen) {
  if (!promptImproverModal) {
    return;
  }
  promptImproverModal.hidden = !isOpen;
}

function updateConversationMenuLabels() {
  if (quickToggleAutoscrollButton) {
    quickToggleAutoscrollButton.textContent = `Auto-scroll: ${autoScrollEnabled ? "On" : "Off"}`;
  }
  if (quickToggleTimestampsButton) {
    quickToggleTimestampsButton.textContent = `Timestamps: ${timestampsEnabled ? "On" : "Off"}`;
  }
}

function buildPromptSuggestion(promptText) {
  const basePrompt = String(promptText || "").trim();
  if (!basePrompt) {
    return "Create a deterministic part with explicit overall dimensions, wall thickness if needed, and named features such as holes, cutouts, or mounting points.";
  }
  const normalized = basePrompt.replace(/\s+/g, " ").trim().replace(/[.]+$/, "");
  return `Create a deterministic part: ${normalized}. Include explicit overall dimensions in mm and call out any holes, cutouts, wall thicknesses, or mounting features needed for the geometry.`;
}

function setSessionTitle(title) {
  currentSessionTitle = title || "Untitled";
  if (sessionTitle) {
    sessionTitle.textContent = currentSessionTitle;
  }
}

function shortenFooterSummary(text) {
  const rawText = String(text || "").replace(/\s+/g, " ").trim();
  if (!rawText) {
    return "Ready for review.";
  }

  const normalized = rawText
    .replace(/^Prepared deterministic /i, "")
    .replace(/^Preparing /i, "")
    .replace(/^Review the current model here, then /i, "")
    .replace(/^Finish setup or /i, "");

  if (normalized.length <= 72) {
    return normalized;
  }
  return `${normalized.substring(0, 69).trim().replace(/[,:;.-]+$/, "")}...`;
}

function setReadinessStateText(text) {
  const fullText = String(text || "").trim() || "Ready for review.";
  readinessState.textContent = shortenFooterSummary(fullText);
  readinessState.title = fullText;
}

function setGenerationStatusText(text) {
  generationStatus.textContent = text || "Ready";
}

function bindClick(element, handler) {
  if (element) {
    element.addEventListener("click", handler);
  }
}

function generateSessionTitle(prompt) {
  const rawPrompt = String(prompt || "").trim();
  if (!rawPrompt) {
    return "Untitled";
  }

  let cleaned = rawPrompt.toLowerCase();
  cleaned = cleaned.replace(/\b\d+(\.\d+)?\s?(mm|cm|in|inch|inches)\b/g, " ");
  cleaned = cleaned.replace(/^[\s,.-]+/, "");
  cleaned = cleaned.replace(/\s+/g, " ").trim();

  if (!cleaned) {
    return "Untitled";
  }

  const words = cleaned.split(" ").filter(Boolean);
  while (words.length && /^[\d.-]+$/.test(words[0])) {
    words.shift();
  }

  let normalized = words.join(" ").trim();
  if (!normalized) {
    return "Untitled";
  }

  if (normalized.length > 50) {
    normalized = normalized.substring(0, 50).trim().replace(/[,:;.-]+$/, "");
  }

  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatLibraryTimestamp(value) {
  if (!value) {
    return "Unknown date";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown date";
  }
  return parsed.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function modelLibraryName(entry = {}) {
  return generateSessionTitle(entry.prompt || entry.plan?.request_text || entry.family_label || entry.family || "Untitled");
}

function modelLibraryFamily(entry = {}) {
  return sentenceCaseLabel(entry.family_label || entry.family || entry.plan?.family_label || entry.plan?.family || "Model");
}

function modelLibraryDimensions(entry = {}) {
  const dims = entry.plan?.dimensions || {};
  const lengthValue = dims.length_mm || dims.base_length_mm || dims.outer_diameter_mm || dims.large_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null;
  const widthValue = dims.width_mm || dims.depth_mm || dims.flange_width_mm || dims.small_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null;
  const heightValue = dims.height_mm || dims.vertical_height_mm || dims.base_height_mm || null;
  const formatted = [lengthValue, widthValue, heightValue]
    .filter((value) => typeof value === "number" && !Number.isNaN(value))
    .map((value) => Number(value.toFixed(2)).toString());
  return formatted.length ? `${formatted.join(" × ")} mm` : "Dimensions unavailable";
}

function normalizeSavedModelEntry(entry = {}) {
  return {
    ...entry,
    id: entry.id || "",
    name: modelLibraryName(entry),
    familyDisplay: modelLibraryFamily(entry),
    createdDisplay: formatLibraryTimestamp(entry.created_at),
    dimensionsDisplay: modelLibraryDimensions(entry),
    previewReady: entry.preview_export_status === "ready",
  };
}

function compactModelSelectionSummary(model) {
  if (!model) {
    return "Select a saved model to open or delete it.";
  }
  return `${model.name} · ${model.familyDisplay} · ${model.createdDisplay}`;
}

function getNormalizedSavedModels() {
  return savedModels.map((entry) => normalizeSavedModelEntry(entry));
}

function currentSelectedSavedModel() {
  return getNormalizedSavedModels().find((entry) => entry.id === selectedSavedModelId) || null;
}

function familyFilterOptions(models = []) {
  const uniqueFamilies = Array.from(new Set(models.map((entry) => entry.familyDisplay).filter(Boolean)));
  return ["All", ...uniqueFamilies.sort((left, right) => left.localeCompare(right))];
}

function filteredSavedModels() {
  const query = modelsSearchQuery.trim().toLowerCase();
  const filterValue = activeModelFamilyFilter.toLowerCase();
  const filtered = getNormalizedSavedModels().filter((entry) => {
    const matchesQuery = !query || [
      entry.name,
      entry.familyDisplay,
      entry.prompt || "",
      entry.validation_summary || "",
    ].some((value) => String(value).toLowerCase().includes(query));
    const matchesFamily = filterValue === "all" || entry.familyDisplay.toLowerCase() === filterValue;
    return matchesQuery && matchesFamily;
  });

  filtered.sort((left, right) => {
    if (modelsSortMode === "oldest") {
      return String(left.created_at || "").localeCompare(String(right.created_at || ""));
    }
    if (modelsSortMode === "name") {
      return left.name.localeCompare(right.name);
    }
    if (modelsSortMode === "family") {
      return left.familyDisplay.localeCompare(right.familyDisplay) || left.name.localeCompare(right.name);
    }
    return String(right.created_at || "").localeCompare(String(left.created_at || ""));
  });

  return filtered;
}

function ensureSelectedSavedModel(models = filteredSavedModels()) {
  if (!models.length) {
    selectedSavedModelId = "";
    return;
  }
  const stillExists = models.some((entry) => entry.id === selectedSavedModelId);
  if (!stillExists) {
    selectedSavedModelId = models[0].id;
  }
}

function renderModelsFamilyFilters(models = getNormalizedSavedModels()) {
  if (!modelsFamilyFilters) {
    return;
  }
  const options = familyFilterOptions(models);
  modelsFamilyFilters.innerHTML = options.map((label) => {
    const value = label.toLowerCase();
    const isActive = (activeModelFamilyFilter || "all") === value;
    return `<button class="models-filter-chip${isActive ? " is-active" : ""}" type="button" data-family-filter="${escapeHtml(value)}">${escapeHtml(label)}</button>`;
  }).join("");
}

function renderModelsSidebarList(models = filteredSavedModels()) {
  if (!modelsSidebarList) {
    return;
  }

  if (!models.length) {
    modelsSidebarList.innerHTML = '<p class="models-sidebar-empty">No models match the current view.</p>';
    return;
  }

  modelsSidebarList.innerHTML = models.map((model) => `
    <button
      class="models-sidebar-item${model.id === selectedSavedModelId ? " is-selected" : ""}"
      type="button"
      data-model-select="${escapeHtml(model.id)}"
      aria-label="Select ${escapeHtml(model.name)}"
    >
      <span class="models-sidebar-item-name">${escapeHtml(model.name)}</span>
      <span class="models-sidebar-item-meta">${escapeHtml(model.familyDisplay)}</span>
    </button>
  `).join("");
}

function renderModelsSelection(model) {
  if (!modelsSelectionSummary || !modelsSelectionOpen || !modelsSelectionDelete) {
    return;
  }
  modelsSelectionSummary.textContent = compactModelSelectionSummary(model);
  modelsSelectionSummary.title = model
    ? `${model.name}\n${model.dimensionsDisplay}\n${model.validation_summary || "No validation summary available."}`
    : "Select a saved model to open or delete it.";
  modelsSelectionOpen.disabled = !model?.script_path;
  modelsSelectionOpen.dataset.modelId = model?.id || "";
  modelsSelectionDelete.disabled = !model?.id;
  modelsSelectionDelete.dataset.modelId = model?.id || "";
}

function renderModelsGrid() {
  if (!modelsGrid || !modelsEmptyState || !modelsTotalCount) {
    return;
  }
  const normalizedModels = getNormalizedSavedModels();
  renderModelsFamilyFilters(normalizedModels);
  const visibleModels = filteredSavedModels();
  ensureSelectedSavedModel(visibleModels);
  const selectedModel = currentSelectedSavedModel();
  const hasSavedModels = normalizedModels.length > 0;

  modelsTotalCount.textContent = String(normalizedModels.length);
  renderModelsSidebarList(visibleModels);
  modelsEmptyState.toggleAttribute("hidden", hasSavedModels);
  modelsGrid.toggleAttribute("hidden", !hasSavedModels);

  if (!hasSavedModels) {
    modelsGrid.innerHTML = "";
    renderModelsSelection(null);
    return;
  }

  modelsGrid.innerHTML = visibleModels.map((model) => `
    <article class="model-card${model.id === selectedSavedModelId ? " is-selected" : ""}" data-model-id="${escapeHtml(model.id)}">
      <button class="model-card-surface" type="button" data-model-select="${escapeHtml(model.id)}" aria-label="Select ${escapeHtml(model.name)}">
        <div class="model-card-preview">
          <span class="model-card-badge">${escapeHtml(model.familyDisplay)}</span>
          <span class="model-card-glyph">&#9638;</span>
        </div>
        <div class="model-card-body">
          <h3 class="model-card-title">${escapeHtml(model.name)}</h3>
          <p class="model-card-meta">${escapeHtml(model.createdDisplay)}</p>
          <p class="model-card-submeta">${escapeHtml(model.dimensionsDisplay)}</p>
        </div>
      </button>
    </article>
  `).join("");

  if (!visibleModels.length) {
    modelsGrid.innerHTML = '<div class="models-filter-empty">No models match the current search or filter.</div>';
    renderModelsSelection(null);
    return;
  }

  renderModelsSelection(selectedModel);
}

function renderConversationThread() {
  if (!conversationThread) {
    return;
  }
  conversationThread.innerHTML = chatMessages.map((message) => {
    const checklist = Array.isArray(message.checklist) && message.checklist.length
      ? `<ul class="chat-checklist">${message.checklist.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
      : "";
    const examples = Array.isArray(message.examples) && message.examples.length
      ? `<div class="chat-example-row">${message.examples.map((item) => (
        `<button class="chat-example-chip" type="button" data-example-prompt="${escapeHtml(item)}">${escapeHtml(item)}</button>`
      )).join("")}</div>`
      : "";
    const title = message.title ? `<p class="chat-bubble-title">${escapeHtml(message.title)}</p>` : "";
    const avatar = message.role === "assistant"
      ? '<img class="chat-message-avatar chat-avatar" src="assets/chat/geo-chat-avatar.png" alt="Geomancer">'
      : "";
    return `
      <article class="chat-message chat-row is-${message.role}">
        ${avatar}
        <div class="chat-message-meta">
          <div class="chat-bubble">
            ${title}
            <p class="chat-bubble-text">${escapeHtml(message.text)}</p>
            ${checklist}
            ${examples}
          </div>
          ${timestampsEnabled ? `<span class="chat-message-time">${escapeHtml(message.timestamp)}</span>` : ""}
        </div>
      </article>
    `;
  }).join("");
  scrollConversationToBottom();
}

function addChatMessage(role, text, options = {}) {
  chatMessages.push({
    id: options.id || `${role}-${Date.now()}-${chatMessages.length}`,
    role,
    text,
    title: options.title || "",
    checklist: options.checklist || [],
    examples: options.examples || [],
    timestamp: options.timestamp || makeTimestamp(),
  });
  renderConversationThread();
}

function replaceLastAssistantMessage(text, options = {}) {
  for (let index = chatMessages.length - 1; index >= 0; index -= 1) {
    if (chatMessages[index].role === "assistant") {
      chatMessages[index] = {
        ...chatMessages[index],
        text,
        title: options.title ?? chatMessages[index].title,
        checklist: options.checklist ?? chatMessages[index].checklist,
        examples: options.examples ?? chatMessages[index].examples,
        timestamp: options.timestamp || makeTimestamp(),
      };
      renderConversationThread();
      return;
    }
  }
  addChatMessage("assistant", text, options);
}

function seedStartupConversationIfReady() {
  if (!runtimeReady() || hasSeededStartupConversation || chatMessages.length) {
    return;
  }
  hasSeededStartupConversation = true;
  addChatMessage("assistant", "Geomancer systems check completed. Local AI and Blender are ready.");
  addChatMessage("assistant", "Hello! What would you like to create today?\nNeed a starting point? Try one of these:", {
    examples: STARTUP_EXAMPLE_PROMPTS,
  });
}

function normalizeRuntimeHealth(rawHealth = {}) {
  return {
    setupCompleted: Boolean(rawHealth.setup_completed ?? rawHealth.setupCompleted),
    firstRunCompleted: Boolean(rawHealth.first_run_completed ?? rawHealth.firstRunCompleted),
    setupRequired: Boolean(rawHealth.setup_required ?? rawHealth.setupRequired),
    ollamaInstalled: Boolean(rawHealth.ollama_installed ?? rawHealth.ollamaInstalled),
    ollamaRunning: Boolean(rawHealth.ollama_running ?? rawHealth.ollamaRunning),
    ollamaVersion: rawHealth.ollama_version ?? rawHealth.ollamaVersion ?? "",
    ollamaModelName: rawHealth.ollama_model_name ?? rawHealth.ollamaModelName ?? "",
    ollamaModelReady: Boolean(rawHealth.ollama_model_ready ?? rawHealth.ollamaModelReady),
    blenderDetected: Boolean(rawHealth.blender_detected ?? rawHealth.blenderDetected),
    blenderPath: rawHealth.blender_path ?? rawHealth.blenderPath ?? "",
    runtimeHealthStatus: rawHealth.runtime_health_status ?? rawHealth.runtimeHealthStatus ?? "unknown",
    runtimeHealthMessage: rawHealth.runtime_health_message ?? rawHealth.runtimeHealthMessage ?? "Runtime health has not been checked yet.",
    nextStep: rawHealth.next_step ?? rawHealth.nextStep ?? "",
    availableModels: rawHealth.available_models ?? rawHealth.availableModels ?? [],
    recommendedModel: rawHealth.recommended_model ?? rawHealth.recommendedModel ?? "",
    issues: rawHealth.issues ?? [],
  };
}

function runtimeReady(health = runtimeHealth) {
  return Boolean(health && health.runtimeHealthStatus === "ready" && health.setupCompleted);
}

function setGenerationInFlight(isActive) {
  generationInFlight = isActive;
  document.body.classList.toggle("is-generating", isActive);
  if (isActive) {
    startGenerationAnimation();
  } else {
    stopGenerationAnimation();
  }
  setGenerating(isActive);
  if (runtimeHealth) {
    applyRuntimeGate({ runtimeHealth, setupFlow: runtimeSetupFlow });
  }
}

function createEmptySession() {
  return {
    generationId: "",
    requestText: "",
    promptText: "",
    plan: null,
    validation: null,
    classification: null,
    resultStatus: "",
    message: "",
    previewStatus: "",
    previewMessage: "",
    previewModelPath: "",
    previewAssetVersion: "",
    previewKey: "",
  };
}

async function resolveBridgeJson(rawValue, contextLabel) {
  const resolvedValue = rawValue && typeof rawValue.then === "function"
    ? await rawValue
    : rawValue;

  if (typeof resolvedValue === "string") {
    return JSON.parse(resolvedValue);
  }
  if (resolvedValue && typeof resolvedValue === "object") {
    return resolvedValue;
  }
  throw new Error(`${contextLabel} returned unsupported payload type: ${typeof resolvedValue}`);
}

function formatMm(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "Unavailable";
  }
  return `${Number(value.toFixed(2)).toString()} mm`;
}

function sentenceCaseStatus(value) {
  const text = String(value || "").replace(/_/g, " ").trim();
  if (!text) {
    return "Unknown";
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function formatTextValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Unavailable";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    return Number(value.toFixed(2)).toString();
  }
  return String(value);
}

function prettifyKey(key) {
  return key
    .replace(/_mm$/i, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function toSummaryLines(plan, validation, classification, resultStatus, previewStatus) {
  const lines = [];
  if (classification?.family_key || plan?.family_label) {
    lines.push(`Detected family: ${plan?.family_label || classification.family_key}`);
  }
  if (classification?.confidence) {
    lines.push(`Classifier confidence: ${Math.round(classification.confidence * 100)}%`);
  }
  if (plan?.recipe) {
    lines.push(`Recipe: ${plan.recipe}`);
  }
  if (previewStatus) {
    lines.push(`Preview export: ${previewStatus}`);
  }
  if (validation?.summary) {
    lines.push(validation.summary);
  } else if (resultStatus) {
    lines.push(`Generation status: ${resultStatus}`);
  }
  return lines.slice(0, 6);
}

function dimensionEntries(plan) {
  const entries = Object.entries(plan?.dimensions || {});
  if (!entries.length) {
    return [];
  }
  return entries.map(([key, value]) => [prettifyKey(key), value]);
}

function featureEntries(plan) {
  const entries = Object.entries(plan?.features || {});
  return entries.filter(([, value]) => value !== null && value !== undefined && value !== "" && value !== false);
}

function estimateVolumeCm3(plan) {
  const dimensions = plan?.dimensions || {};
  const values = Object.values(dimensions).filter((value) => typeof value === "number" && value > 0);
  if (!values.length) {
    return null;
  }
  if (dimensions.width_mm && dimensions.depth_mm && dimensions.height_mm) {
    return (dimensions.width_mm * dimensions.depth_mm * dimensions.height_mm) / 1000;
  }
  if (dimensions.diameter_mm && dimensions.height_mm) {
    const radius = dimensions.diameter_mm / 2;
    return (Math.PI * radius * radius * dimensions.height_mm) / 1000;
  }
  if (dimensions.outer_diameter_mm && dimensions.length_mm) {
    const radius = dimensions.outer_diameter_mm / 2;
    return (Math.PI * radius * radius * dimensions.length_mm) / 1000;
  }
  if (dimensions.large_diameter_mm && dimensions.length_mm) {
    const radius = dimensions.large_diameter_mm / 2;
    return (Math.PI * radius * radius * dimensions.length_mm) / 1000;
  }
  return null;
}

function formatInstrumentMm(value, hasPlan = false) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return hasPlan ? "N/A" : "—";
  }
  return formatMm(value);
}

function sentenceCaseLabel(text = "") {
  if (!text) {
    return "";
  }
  const normalized = String(text).replace(/[_-]+/g, " ").trim();
  if (!normalized) {
    return "";
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function familyDisplayLabel(plan) {
  if (!plan?.family) {
    return "";
  }
  return sentenceCaseLabel(prettifyKey(plan.family));
}

function recipeDisplayLabel(plan) {
  if (!plan?.recipe) {
    return "";
  }
  return sentenceCaseLabel(String(plan.recipe).replace(/^deterministic[_\s-]*/i, "Deterministic "));
}

function describeCurrentModel(plan, validation = null, uiState = "idle") {
  if (!plan) {
    if (uiState === "generating") {
      return `${animatedStateLabel("Generating")}\nPreparing the current model for review.`;
    }
    return "Ready to generate\nDescribe a part to begin.";
  }

  const family = familyDisplayLabel(plan) || "Model";
  const featureItems = featureEntries(plan).filter(([key]) => !key.includes("thickness") && !key.includes("wall"));
  const holeCount = featureItems.find(([key]) => key.includes("hole_count"))?.[1];
  const opening = featureItems.find(([key]) => key.includes("opening") || key.includes("cutout"));
  let summary = family;

  if (holeCount) {
    summary += ` with ${holeCount} mounting hole${Number(holeCount) === 1 ? "" : "s"}`;
  } else if (opening) {
    summary += ` with ${prettifyKey(opening[0]).toLowerCase()}`;
  }

  summary += validation?.warnings?.length ? " prepared for review." : " prepared for refinement.";
  return summary;
}

function wallThicknessValue(plan) {
  if (!plan) {
    return null;
  }
  const directThickness = Number(plan.shell_thickness_mm);
  if (directThickness > 0) {
    return directThickness;
  }
  const fromFeatures = featureEntries(plan)
    .find(([key, value]) => (key.includes("thickness") || key.includes("wall")) && Number(value) > 0);
  return fromFeatures ? Number(fromFeatures[1]) : null;
}

function previewReadinessLabel(plan, previewStatus, uiState = "idle") {
  if (!plan) {
    return uiState === "generating" ? animatedStateLabel("Preparing") : "Waiting";
  }
  if (previewStatus === "error") {
    return "Needs review";
  }
  if (previewStatus === "pending") {
    return "Preparing";
  }
  return "Ready";
}

function exportReadinessLabel(plan, previewStatus) {
  if (!plan) {
    return "Waiting";
  }
  if (previewStatus === "error") {
    return "Review in Blender";
  }
  return runtimeHealth?.blenderDetected ? "Ready in Blender" : "Blender needed";
}

function meshQualityLabel(plan, validation = null, uiState = "idle") {
  if (!plan) {
    return uiState === "generating" ? animatedStateLabel("Evaluating") : "Waiting";
  }
  return validation?.warnings?.length ? "Needs review" : "Structured";
}

function derivePrintabilityAssessment(plan, validation = null) {
  if (!plan) {
    return null;
  }

  const dims = plan.dimensions || {};
  const featureItems = featureEntries(plan);
  const warnings = validation?.warnings || [];

  const baseSpan = Math.max(
    Number(dims.base_width_mm) || 0,
    Number(dims.width_mm) || 0,
    Number(dims.depth_mm) || 0,
    Number(dims.outer_diameter_mm) || 0,
    Number(dims.diameter_mm) || 0,
    Number(dims.large_diameter_mm) || 0
  );
  const height = Math.max(
    Number(dims.height_mm) || 0,
    Number(dims.vertical_height_mm) || 0,
    Number(dims.base_height_mm) || 0
  );
  const aspectRatio = baseSpan > 0 ? height / baseSpan : null;

  let baseContact = "Review recommended";
  if (baseSpan > 0 && aspectRatio !== null) {
    if (aspectRatio <= 1.45) {
      baseContact = "Stable";
    } else if (aspectRatio <= 2.35) {
      baseContact = "Review recommended";
    } else {
      baseContact = "Needs support review";
    }
  }

  const overhangSignals = featureItems.filter(([key]) => key.includes("opening") || key.includes("cutout") || key.includes("hook") || key.includes("clip")).length;
  let overhangRisk = "Review recommended";
  if (warnings.length >= 2 || overhangSignals >= 2) {
    overhangRisk = "Needs support review";
  } else if (!warnings.length && !overhangSignals) {
    overhangRisk = "Likely manageable";
  }

  const thicknessValues = [
    Number(plan.shell_thickness_mm) || 0,
    ...featureItems
      .filter(([key]) => key.includes("thickness") || key.includes("wall"))
      .map(([, value]) => Number(value) || 0),
  ].filter((value) => value > 0);
  const thinnestFeature = thicknessValues.length ? Math.min(...thicknessValues) : null;

  let thinFeatures = "None detected";
  if (thinnestFeature !== null) {
    if (thinnestFeature < 1.6) {
      thinFeatures = "Review recommended";
    } else if (thinnestFeature < 2.4) {
      thinFeatures = "Fine detail present";
    }
  }

  let status = "Likely printable";
  if (warnings.length >= 2 || baseContact === "Needs support review" || overhangRisk === "Needs support review") {
    status = "Needs support review";
  } else if (warnings.length || baseContact === "Review recommended" || overhangRisk === "Review recommended" || thinFeatures === "Review recommended") {
    status = "Review recommended";
  }

  const note = status === "Likely printable"
    ? "Verify in Blender before export"
    : "Review orientation and support in Blender";

  return { status, baseContact, overhangRisk, thinFeatures, note, warnings };
}

function animatedStateLabel(base) {
  const dots = ".".repeat((generationAnimationFrame % 3) + 1);
  return `${base}${dots.padEnd(3, "\u00A0")}`;
}

function compactBottomPrintabilityLabel(value, fallback = "Waiting") {
  const text = String(value || "").trim();
  if (!text) {
    return fallback;
  }
  if (text === "Review recommended") {
    return "Needs review";
  }
  if (text === "Likely manageable") {
    return "Manageable";
  }
  return text;
}

function stopGenerationAnimation() {
  if (generationAnimationInterval) {
    window.clearInterval(generationAnimationInterval);
    generationAnimationInterval = 0;
  }
  generationAnimationFrame = 0;
}

function refreshGeneratingUI() {
  if (!generationInFlight) {
    return;
  }
  updateMetricsFromPlan(null, null, animatedStateLabel("Generating"), "generating");
  updateRightPanel(null, null, "generating");
  setGenerationStatusText(animatedStateLabel("Generating"));
}

function startGenerationAnimation() {
  stopGenerationAnimation();
  refreshGeneratingUI();
  generationAnimationInterval = window.setInterval(() => {
    generationAnimationFrame = (generationAnimationFrame + 1) % 3;
    refreshGeneratingUI();
  }, 420);
}

function updateMetricsFromPlan(plan, validation, generationText, uiState = "ready") {
  const dims = plan?.dimensions || {};
  const hasPlan = Boolean(plan);
  const printability = derivePrintabilityAssessment(plan, validation);
  const lengthValue = dims.length_mm || dims.base_length_mm || dims.outer_diameter_mm || dims.large_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null;
  const widthValue = dims.width_mm || dims.depth_mm || dims.flange_width_mm || dims.small_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null;
  const heightValue = dims.height_mm || dims.vertical_height_mm || dims.base_height_mm || null;
  metricLength.textContent = formatInstrumentMm(lengthValue, hasPlan);
  metricWidth.textContent = formatInstrumentMm(widthValue, hasPlan);
  metricHeight.textContent = formatInstrumentMm(heightValue, hasPlan);
  metricModelFamily.textContent = hasPlan
    ? (familyDisplayLabel(plan) || "Waiting")
    : (uiState === "generating" ? animatedStateLabel("Classifying") : "Waiting");
  reviewStatus.textContent = hasPlan
    ? compactBottomPrintabilityLabel(printability?.status, "Needs review")
    : (uiState === "generating" ? animatedStateLabel("Reviewing") : "Waiting");
  printabilityBase.textContent = hasPlan
    ? compactBottomPrintabilityLabel(printability?.baseContact, "Needs review")
    : (uiState === "generating" ? animatedStateLabel("Checking") : "Waiting");
  printabilityOverhang.textContent = hasPlan
    ? compactBottomPrintabilityLabel(printability?.overhangRisk, "Needs review")
    : (uiState === "generating" ? animatedStateLabel("Checking") : "Waiting");
  meshPreview.textContent = previewReadinessLabel(plan, activeSession.previewStatus, uiState);
  meshExport.textContent = exportReadinessLabel(plan, activeSession.previewStatus);
  meshQuality.textContent = meshQualityLabel(plan, validation, uiState);
  setGenerationStatusText(generationText || "Ready");
}

function renderListRows(container, items, formatter, emptyText = "Unavailable") {
  if (!items.length) {
    container.innerHTML = `<div class="check-row"><span class="checkmark">&#9672;</span><span>${emptyText}</span></div>`;
    return;
  }
  container.innerHTML = items.map(formatter).join("");
}

function renderDetailRows(container, items) {
  if (!container) {
    return;
  }
  container.innerHTML = items.map(([label, value]) => (
    `<div class="detail-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`
  )).join("");
}

function detailValueForEntry([key, value]) {
  return key.endsWith("_mm") ? formatMm(value) : formatTextValue(value);
}

function keyFeatureRowsForPlan(plan) {
  if (!plan) {
    return [];
  }

  const featureItems = featureEntries(plan);
  const preferredFeatures = [];
  const pushIfPresent = (predicate, labelOverride = null) => {
    featureItems.forEach(([key, value]) => {
      if (predicate(key) && !preferredFeatures.find(([label]) => label === (labelOverride || prettifyKey(key)))) {
        preferredFeatures.push([labelOverride || prettifyKey(key), detailValueForEntry([key, value])]);
      }
    });
  };

  pushIfPresent((key) => key.includes("hole_count"), "Holes");
  pushIfPresent((key) => key.includes("opening") || key.includes("cutout"), "Openings");
  pushIfPresent((key) => key.includes("shell") || key.includes("wall") || key.includes("thickness"), "Wall");
  pushIfPresent((key) => key.includes("flange"), "Flange");
  pushIfPresent((key) => key.includes("angle"), "Angle");

  const dimensions = Object.entries(plan.dimensions || {});
  dimensions.forEach(([key, value]) => {
    if ((key.includes("flange") || key.includes("angle") || key.includes("slot")) && !preferredFeatures.find(([label]) => label === prettifyKey(key))) {
      preferredFeatures.push([prettifyKey(key), detailValueForEntry([key, value])]);
    }
  });

  if (!preferredFeatures.length) {
    const fallbackCount = featureItems.length;
    if (fallbackCount > 0) {
      preferredFeatures.push(["Feature count", `${fallbackCount} features`]);
    }
  }

  return preferredFeatures.slice(0, 4);
}

function updateRightPanel(plan, validation = null, uiState = "idle") {
  const hasPlan = Boolean(plan);
  const dims = plan?.dimensions || {};
  const lengthValue = dims.length_mm || dims.base_length_mm || dims.outer_diameter_mm || dims.large_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null;
  const widthValue = dims.width_mm || dims.depth_mm || dims.flange_width_mm || dims.small_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null;
  const heightValue = dims.height_mm || dims.vertical_height_mm || dims.base_height_mm || null;
  const wallValue = wallThicknessValue(plan);
  const featureRows = keyFeatureRowsForPlan(plan).slice(0, 6);

  if (propertiesEmptyState) {
    propertiesEmptyState.dataset.state = hasPlan ? "ready" : uiState;
    propertiesEmptyState.hidden = hasPlan || uiState === "generating";
    propertiesEmptyState.textContent = "Generate a model to see dimensions, features, and print guidance.";
  }

  if (propertiesDimensionsSection) {
    propertiesDimensionsSection.hidden = !hasPlan;
  }
  if (propertiesWallsSection) {
    propertiesWallsSection.hidden = !hasPlan || !wallValue;
  }
  if (propertiesFeaturesSection) {
    propertiesFeaturesSection.hidden = !hasPlan || !featureRows.length;
  }

  if (!hasPlan) {
    if (propertiesEmptyState && uiState === "generating") {
      propertiesEmptyState.hidden = false;
      propertiesEmptyState.textContent = "Refreshing properties while the current model is prepared.";
    }
    if (currentModelDimensions) {
      currentModelDimensions.innerHTML = "";
    }
    if (currentModelWalls) {
      currentModelWalls.innerHTML = "";
    }
    if (currentModelFeatures) {
      currentModelFeatures.innerHTML = "";
    }
    return;
  }

  renderDetailRows(currentModelDimensions, [
    ["Length", formatInstrumentMm(lengthValue, true)],
    ["Width", formatInstrumentMm(widthValue, true)],
    ["Height", formatInstrumentMm(heightValue, true)],
  ]);

  if (wallValue && currentModelWalls) {
    renderDetailRows(currentModelWalls, [["Thickness", formatMm(Number(wallValue))]]);
  }

  if (currentModelFeatures) {
    renderDetailRows(currentModelFeatures, featureRows.map(([label, value]) => [label, value || "Yes"]));
  }
}

function updateHistoryPanel({ promptText = "", plan = null, validation = null, classification = null, resultStatus = "", message = "", previewStatus = "" }) {
  const summaryLines = toSummaryLines(plan, validation, classification, resultStatus, previewStatus);
  if (!promptText && !summaryLines.length && !message) {
    seedStartupConversationIfReady();
  }
}

function applyBackendSnapshot({ promptText = "", plan = null, validation = null, classification = null, resultStatus = "", message = "", previewStatus = "", previewMessage = "" }) {
  updateHistoryPanel({ promptText, plan, validation, classification, resultStatus, message, previewStatus });
  const uiState = resultStatus === "generating" ? "generating" : (plan ? "ready" : "idle");
  updateRightPanel(plan, validation, uiState);
  updateMetricsFromPlan(plan, validation, resultStatus === "ready" ? "Generation complete" : (resultStatus || "Ready"), uiState);
  setReadinessStateText(validation?.summary || message || previewMessage || "Review the current model here, then open it in Blender for local editing.");
}

function normalizeTerminalResult(result = {}) {
  return {
    generationId: result.generation_id || result.generationId || "",
    requestText: result.request_text || result.requestText || "",
    status: result.status || "error",
    rawStatus: result.raw_status || result.rawStatus || "",
    isTerminal: result.is_terminal !== false,
    message: result.message || "",
    plan: result.plan || null,
    validation: result.validation || null,
    classification: result.classification || null,
    previewModelPath: result.preview_model_path || result.previewModelPath || "",
    previewAssetVersion: result.preview_asset_version || result.previewAssetVersion || "",
    previewStatus: result.preview_export_status || result.previewExportStatus || "not_requested",
    previewMessage: result.preview_export_message || result.previewExportMessage || "",
    savedModelEntry: result.saved_model_entry || result.savedModelEntry || null,
  };
}

function terminalStatusLabel(status) {
  if (status === "ready") {
    return "Generation complete";
  }
  if (status === "unsupported") {
    return "Request not supported yet";
  }
  if (status === "validation_failed") {
    return "Request needs revision";
  }
  return "Generation error";
}

function setLogsModalOpen(isOpen) {
  if (!logsModal) {
    return;
  }
  logsModal.hidden = !isOpen;
}

function terminalViewerMessage(result) {
  if (result.status === "unsupported") {
    return result.message || "That request falls outside the current alpha geometry families.";
  }
  if (result.status === "validation_failed") {
    return result.message || "Add clearer supported dimensions or family details, then try again.";
  }
  if (result.previewStatus === "error") {
    return result.previewMessage || "Preview export failed. Geomancer will fall back to a lightweight viewer preview when possible.";
  }
  return result.message || "The current request could not be completed.";
}

async function applyTerminalResult(rawResult) {
  appendLog("[UI] terminal renderer entered");
  const result = normalizeTerminalResult(rawResult);
  const embeddedRuntimeHealth = rawResult.runtime_health || rawResult.runtimeHealth;
  if (embeddedRuntimeHealth) {
    applyRuntimeGate({ runtimeHealth: embeddedRuntimeHealth, setupFlow: runtimeSetupFlow });
  }
  const previewIdentity = previewIdentityFromResult(rawResult) || result.generationId;
  appendLog(`[UI] terminal payload parsed: request_text=${result.requestText || "none"}, generation_id=${result.generationId || "none"}, status=${result.status}, reason=${result.message || result.previewMessage || "none"}, preview_path=${result.previewModelPath || "none"}`);

  applyActiveSession({
    generationId: result.generationId,
    requestText: result.requestText,
    promptText: result.requestText,
    plan: result.plan,
    validation: result.validation,
    classification: result.classification,
    resultStatus: result.status,
    message: result.message,
    previewStatus: result.previewStatus,
    previewMessage: result.previewMessage,
    previewModelPath: result.previewModelPath,
    previewAssetVersion: result.previewAssetVersion,
    previewKey: previewIdentity,
  });
  appendLog("[UI] final terminal UI applied");
  const summaryLines = toSummaryLines(result.plan, result.validation, result.classification, result.status, result.previewStatus);
  if (result.classification?.family_key || result.plan?.family_label) {
    addChatMessage("assistant", `Detected family: ${result.plan?.family_label || result.classification.family_key}.`);
  }
  if (summaryLines.length) {
    addChatMessage("assistant", result.validation?.summary || "Normalization complete.", {
      title: "Generation update",
      checklist: summaryLines.slice(0, 5),
    });
  }
  if (result.savedModelEntry?.id) {
    appendLog(`Saved model entry updated: ${result.savedModelEntry.id}`);
  }

  if (result.status === "ready") {
    appendLog(`[UI] preview load started: generation_id=${result.generationId || "none"}, preview_path=${result.previewModelPath || "none"}`);
    appendLog(`[UI] backend-owned preview identity -> ${previewIdentity || "none"}`);
    try {
      await viewer.loadPreview({
        promptText: result.requestText,
        plan: result.plan,
        previewModelPath: result.previewModelPath,
        previewAssetVersion: result.previewAssetVersion,
        previewKey: previewIdentity,
      });
      appendLog(`[UI] preview load succeeded: generation_id=${result.generationId || "none"}`);
    } catch (error) {
      appendLog(`[UI] preview load failed: generation_id=${result.generationId || "unknown"}, error=${error}`);
      await viewer.loadPreview({
        promptText: result.requestText,
        plan: result.plan,
        previewModelPath: "",
        previewAssetVersion: "",
        previewKey: `${previewIdentity || result.generationId || "fallback"}-procedural`,
      });
      setReadinessStateText(terminalViewerMessage(result));
    }

    if (result.previewStatus === "error") {
      setReadinessStateText(terminalViewerMessage(result));
    }
    addChatMessage("assistant", "Preview ready.", {
      title: "Generation complete",
      checklist: summaryLines.length ? summaryLines.slice(0, 4) : ["Viewer updated.", "Review the model before Blender handoff."],
    });
    return;
  }

  setGenerationStatusText(terminalStatusLabel(result.status));
  setReadinessStateText(terminalViewerMessage(result));
  viewer.setError(terminalViewerMessage(result));
  addChatMessage("assistant", terminalViewerMessage(result), {
    title: terminalStatusLabel(result.status),
    checklist: summaryLines.slice(0, 4),
  });
}

async function handleTerminalFailure(message, options = {}) {
  const failureResult = {
    generation_id: options.generationId || activeSession.generationId || "",
    request_text: options.requestText || activeSession.requestText || promptInput.value.trim(),
    status: options.status || "error",
    raw_status: options.rawStatus || "ui_failure",
    is_terminal: true,
    message,
    classification: options.classification || {},
    plan: null,
    validation: null,
    preview_model_path: "",
    preview_asset_version: "",
    preview_export_status: "error",
    preview_export_message: message,
  };
  await applyTerminalResult(failureResult);
}

function setIdleSessionUI(reasonText = "Start a new generation when ready.") {
  updateRightPanel(null);
  updateMetricsFromPlan(null, null, "Waiting", "idle");
  setReadinessStateText("Submit a dimensional prompt to start a new local generation.");
  if (!chatMessages.length && runtimeReady()) {
    seedStartupConversationIfReady();
  } else if (!chatMessages.length && !runtimeReady()) {
    addChatMessage("assistant", reasonText);
  }
}

function resetActiveSession(options = {}) {
  const { reasonText = "Start a new generation when ready.", clearPrompt = true } = options;
  activeSession = createEmptySession();
  setSessionTitle("Untitled");
  setGenerationInFlight(false);
  if (clearPrompt) {
    promptInput.value = "";
  }
  chatMessages = [];
  hasSeededStartupConversation = false;
  renderConversationThread();
  setIdleSessionUI(reasonText);
  if (viewer.initialized) {
    viewer.setEmpty();
  }
  promptInput.focus();
}

function applyActiveSession(sessionUpdate) {
  activeSession = {
    ...activeSession,
    ...sessionUpdate,
  };
  setSessionTitle(generateSessionTitle(activeSession.promptText || activeSession.requestText || ""));
  applyBackendSnapshot(activeSession);
}

function renderSetupSteps(steps = []) {
  if (!steps.length) {
    setupSteps.innerHTML = '<div class="setup-step is-pending"><span class="setup-step-dot"></span><span>Setup progress has not been reported yet.</span></div>';
    return;
  }
  setupSteps.innerHTML = steps.map((step) => {
    const status = step.status || "pending";
    return `
      <div class="setup-step is-${status}">
        <span class="setup-step-dot"></span>
        <span>${step.label || step.id || "Step"}</span>
      </div>
    `;
  }).join("");
}

function applyRuntimeGate(state = {}) {
  const normalizedHealth = normalizeRuntimeHealth(state.runtimeHealth || state);
  runtimeHealth = normalizedHealth;
  const setupFlow = state.setupFlow || runtimeSetupFlow;
  runtimeSetupFlow = setupFlow;
  const ready = runtimeReady(normalizedHealth);
  const aiReady = normalizedHealth.ollamaInstalled && normalizedHealth.ollamaRunning && normalizedHealth.ollamaModelReady;
  const blenderReady = normalizedHealth.blenderDetected;

  setupWizard.hidden = ready;
  setupStatusTitle.textContent = ready ? "Workspace ready" : "Finish local setup";
  setupStatusText.textContent = normalizedHealth.runtimeHealthMessage || "Runtime health has not been checked yet.";
  setupHelpText.textContent = normalizedHealth.blenderDetected
    ? `Blender is configured at ${normalizedHealth.blenderPath || "the detected path"}.`
    : "Choose a local Blender install so Geomancer can preview and hand off deterministic output.";
  renderSetupSteps(setupFlow);

  const recommendedModel = normalizedHealth.ollamaModelName || normalizedHealth.recommendedModel || "the required AI model";
  setupPullButton.disabled = !normalizedHealth.ollamaInstalled || !normalizedHealth.ollamaRunning || normalizedHealth.ollamaModelReady;
  setupPullButton.textContent = normalizedHealth.ollamaModelReady ? "AI Ready" : `Set Up AI (${recommendedModel})`;
  setupSmokeButton.disabled = !normalizedHealth.ollamaInstalled || !normalizedHealth.ollamaRunning || !normalizedHealth.ollamaModelReady || !normalizedHealth.blenderDetected;
  setupSmokeButton.textContent = ready ? "Checked" : "Run Quick Check";

  promptInput.disabled = !ready;
  openBlenderButton.disabled = !normalizedHealth.blenderDetected;
  generateButton.disabled = !ready || generationInFlight;
  generateButton.textContent = generationInFlight ? "..." : "Go";

  if (!ready) {
    setReadinessStateText(normalizedHealth.runtimeHealthMessage || "Finish local setup before generating.");
    setGenerationStatusText("Setup required");
  }

  if (backendStatus) {
    backendStatus.textContent = ready ? "Ready" : sentenceCaseStatus(normalizedHealth.runtimeHealthStatus || "setup_required");
  }
  systemAiStatus.textContent = aiReady ? "Ready" : (normalizedHealth.ollamaInstalled ? "Setup needed" : "Not ready");
  systemBlenderStatus.textContent = blenderReady ? "Connected" : "Not configured";
  if (ready) {
    seedStartupConversationIfReady();
  }
}

function updatePassiveShellState(state) {
  librarySummary = state.librarySummary || librarySummary;
  savedModels = Array.isArray(state.savedModels) ? state.savedModels : savedModels;
  scriptPath.textContent = state.generatedScriptPath || "Unavailable";
  footerVersion.textContent = `v${state.version}`;
  renderModelsGrid();
  applyRuntimeGate(state);
}

function setActiveTab(tabName) {
  currentAppMode = tabName;
  topnavTabs.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === tabName);
  });
  Object.entries(modeScreens).forEach(([modeName, screen]) => {
    if (!screen) {
      return;
    }
    const isActive = modeName === tabName;
    screen.hidden = !isActive;
    screen.classList.toggle("is-active", isActive);
  });
  if (tabName === "models") {
    renderModelsGrid();
  }
  if (tabName === "workspace" && viewer?.initialized) {
    viewer.resize();
  }
  appendLog(`Tab selected: ${tabName} -> ${TAB_INTENTS[tabName] || "Unknown role"}`);
}

function setViewerOverlay(mode, title, text) {
  viewerOverlay.dataset.state = mode;
  viewerOverlayTitle.textContent = title;
  viewerOverlayText.textContent = text;
  viewerOverlaySpinner.hidden = mode !== "loading";
}

function toFileUrl(pathText) {
  if (!pathText) {
    return null;
  }
  const normalized = pathText.replace(/\\/g, "/");
  if (/^[a-z]+:\/\//i.test(normalized)) {
    return normalized;
  }
  if (/^[a-z]:\//i.test(normalized)) {
    return `file:///${encodeURI(normalized)}`;
  }
  return null;
}

function withCacheKey(url, cacheKey) {
  if (!url || !cacheKey) {
    return url;
  }
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}asset_version=${encodeURIComponent(cacheKey)}`;
}

function previewIdentityFromResult(result) {
  return result.preview_asset_version || result.previewAssetVersion || result.generation_id || result.generationId || "";
}

function getPromptPreviewKind(promptText = "", plan = null) {
  if (plan?.family) {
    if (plan.family === "enclosure" || plan.family === "housing_shell") {
      return "enclosure";
    }
    if (plan.family === "bracket") {
      return "bracket";
    }
    if (plan.family === "cable_clip") {
      return "clip";
    }
    if (plan.family === "planter_vessel") {
      return "planter";
    }
    if (plan.family === "adapter" || plan.family === "spacer_standoff") {
      return "cylinder";
    }
  }
  const normalized = String(promptText).toLowerCase();
  if (normalized.includes("enclosure") || normalized.includes("case") || normalized.includes("housing")) {
    return "enclosure";
  }
  if (normalized.includes("bracket")) {
    return "bracket";
  }
  if (normalized.includes("plate") || normalized.includes("panel")) {
    return "panel";
  }
  if (normalized.includes("cable clip") || normalized.includes("clip")) {
    return "clip";
  }
  if (normalized.includes("planter") || normalized.includes("pot")) {
    return "planter";
  }
  if (plan?.primitive === "sphere") {
    return "sphere";
  }
  if (plan?.primitive === "cylinder") {
    return "cylinder";
  }
  return "block";
}

class GeomancerViewer {
  constructor() {
    this.initialized = false;
    this.renderMode = "solid";
    this.interactionMode = "orbit";
    this.autoOrbitEnabled = false;
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.rootGroup = null;
    this.previewObject = null;
    this.contactShadow = null;
    this.gizmoRenderer = null;
    this.gizmoScene = null;
    this.gizmoCamera = null;
    this.gizmoCube = null;
    this.animationFrame = 0;
    this.resizeObserver = null;
    this.lastPreviewKey = "";
    this.orbitPointerId = null;
  }

  async init() {
    try {
      const deps = await Promise.all([
        import("./vendor/three/three.module.js"),
        import("./vendor/three/examples/jsm/controls/OrbitControls.js"),
        import("./vendor/three/examples/jsm/loaders/GLTFLoader.js"),
      ]);
      THREE = deps[0];
      OrbitControls = deps[1].OrbitControls;
      GLTFLoader = deps[2].GLTFLoader;
    } catch (error) {
      appendLog(`Viewer dependency load failed: ${error}`);
      setViewerOverlay(
        "error",
        "Viewer unavailable",
        "Three.js could not be loaded. Keep using generation and Blender actions while viewer dependencies are resolved."
      );
      return;
    }

    this.scene = new THREE.Scene();
    this.scene.background = null;
    this.scene.fog = new THREE.Fog(0xf3f5f3, 11, 26);

    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200);
    this.camera.position.set(5.8, 4.6, 6.9);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.className = "viewer-webgl";
    viewerRenderSurface.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = true;
    this.controls.autoRotate = false;
    this.controls.autoRotateSpeed = 0.6;
    this.controls.minDistance = 1.2;
    this.controls.maxDistance = 30;
    this.controls.target.set(0, 0.78, 0);
    this.controls.addEventListener("start", () => {
      if (this.autoOrbitEnabled) {
        this.setAutoOrbit(false);
      }
    });

    this.rootGroup = new THREE.Group();
    this.scene.add(this.rootGroup);

    this.scene.add(new THREE.HemisphereLight(0xffffff, 0xdde5e6, 1.35));

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.35);
    keyLight.position.set(4.5, 8, 6.5);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    keyLight.shadow.camera.left = -8;
    keyLight.shadow.camera.right = 8;
    keyLight.shadow.camera.top = 8;
    keyLight.shadow.camera.bottom = -8;
    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xf7fbfb, 0.65);
    fillLight.position.set(-5.5, 4.5, -3.5);
    this.scene.add(fillLight);

    const stageFloor = new THREE.Mesh(
      new THREE.CircleGeometry(7.4, 96),
      new THREE.MeshStandardMaterial({
        color: 0xe7ebe6,
        roughness: 0.98,
        metalness: 0.02,
      })
    );
    stageFloor.rotation.x = -Math.PI / 2;
    stageFloor.position.y = 0;
    stageFloor.receiveShadow = true;
    stageFloor.renderOrder = 0;
    this.rootGroup.add(stageFloor);

    const stageHalo = new THREE.Mesh(
      new THREE.RingGeometry(2.4, 7.05, 96),
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.2,
        side: THREE.DoubleSide,
        depthWrite: false,
      })
    );
    stageHalo.rotation.x = -Math.PI / 2;
    stageHalo.position.y = 0.0015;
    stageHalo.renderOrder = 1;
    this.rootGroup.add(stageHalo);

    const grid = new THREE.GridHelper(12, 24, 0xd4dbdd, 0xe7ecec);
    grid.position.y = 0.004;
    grid.material.opacity = 0.22;
    grid.material.transparent = true;
    grid.material.depthWrite = false;
    grid.renderOrder = 3;
    this.rootGroup.add(grid);

    this.contactShadow = new THREE.Mesh(
      new THREE.CircleGeometry(1, 72),
      new THREE.MeshBasicMaterial({
        color: 0x546068,
        transparent: true,
        opacity: 0.12,
        depthWrite: false,
      })
    );
    this.contactShadow.rotation.x = -Math.PI / 2;
    this.contactShadow.position.set(0, 0.0025, 0);
    this.contactShadow.renderOrder = 2;
    this.contactShadow.visible = false;
    this.rootGroup.add(this.contactShadow);

    this.initOrientationGizmo();

    this.bindControls();
    this.bindOrbitPad();
    this.setInteractionMode("orbit");
    this.setRenderMode("solid");
    this.resize();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(viewerRenderSurface);
    this.initialized = true;
    this.animate();
    setViewerOverlay(
      "empty",
      "Ready for a model",
      "Generate a part to review it here."
    );
  }

  bindControls() {
    bindClick(viewerModeSolid, () => this.setRenderMode("solid"));
    bindClick(viewerModeWireframe, () => this.setRenderMode("wireframe"));
    bindClick(viewerToolOrbit, () => this.setInteractionMode("orbit"));
    bindClick(viewerToolPan, () => this.setInteractionMode("pan"));
    bindClick(viewerToolZoom, () => this.setInteractionMode("zoom"));
    bindClick(viewerFocusButton, () => this.focusObject());
    bindClick(viewerResetButton, () => this.resetView());
    bindClick(viewerAutoOrbitToggle, () => this.setAutoOrbit(!this.autoOrbitEnabled));
  }

  animate() {
    this.animationFrame = window.requestAnimationFrame(() => this.animate());
    if (this.controls) {
      this.controls.autoRotate = this.autoOrbitEnabled;
      this.controls.update();
    }
    this.updateAxisIndicator();
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
    if (this.gizmoRenderer && this.gizmoScene && this.gizmoCamera) {
      this.gizmoRenderer.render(this.gizmoScene, this.gizmoCamera);
    }
  }

  initOrientationGizmo() {
    if (!viewerAxisScene || !THREE) {
      return;
    }

    this.gizmoScene = new THREE.Scene();
    this.gizmoCamera = new THREE.PerspectiveCamera(24, 1, 0.1, 10);
    this.gizmoCamera.position.set(2.1, 1.82, 2.45);
    this.gizmoCamera.lookAt(0, 0, 0);

    this.gizmoRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.gizmoRenderer.outputColorSpace = THREE.SRGBColorSpace;
    this.gizmoRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.gizmoRenderer.setClearColor(0x000000, 0);
    this.gizmoRenderer.domElement.className = "viewer-axis-canvas";
    viewerAxisScene.replaceChildren(this.gizmoRenderer.domElement);

    this.gizmoScene.add(new THREE.AmbientLight(0xf4fbfb, 1.95));

    const gizmoKeyLight = new THREE.DirectionalLight(0xffffff, 1.6);
    gizmoKeyLight.position.set(2.65, 3.4, 3.1);
    this.gizmoScene.add(gizmoKeyLight);

    const gizmoFillLight = new THREE.DirectionalLight(0xe0f5f4, 0.82);
    gizmoFillLight.position.set(-2.25, 1.95, -1.8);
    this.gizmoScene.add(gizmoFillLight);

    const gizmoRimLight = new THREE.PointLight(0x93e1de, 0.5, 8, 2);
    gizmoRimLight.position.set(0, 1.8, 2.2);
    this.gizmoScene.add(gizmoRimLight);

    const faceMaterials = [
      new THREE.MeshStandardMaterial({
        color: 0xd7eceb,
        emissive: 0x0f2d2f,
        emissiveIntensity: 0.035,
        roughness: 0.42,
        metalness: 0.08,
      }),
      new THREE.MeshStandardMaterial({
        color: 0xd7eceb,
        emissive: 0x0f2d2f,
        emissiveIntensity: 0.035,
        roughness: 0.42,
        metalness: 0.08,
      }),
      new THREE.MeshStandardMaterial({
        color: 0xe3f1f1,
        emissive: 0x123234,
        emissiveIntensity: 0.028,
        roughness: 0.38,
        metalness: 0.07,
      }),
      new THREE.MeshStandardMaterial({
        color: 0xe3f1f1,
        emissive: 0x123234,
        emissiveIntensity: 0.028,
        roughness: 0.38,
        metalness: 0.07,
      }),
      new THREE.MeshStandardMaterial({
        color: 0x9fe1dd,
        emissive: 0x5ebdbc,
        emissiveIntensity: 0.13,
        roughness: 0.3,
        metalness: 0.12,
      }),
      new THREE.MeshStandardMaterial({
        color: 0xcfdcde,
        emissive: 0x112628,
        emissiveIntensity: 0.022,
        roughness: 0.46,
        metalness: 0.06,
      }),
    ];

    this.gizmoCube = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.0, 1.0), faceMaterials);
    this.gizmoScene.add(this.gizmoCube);

    const cubeEdges = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(1.015, 1.015, 1.015)),
      new THREE.LineBasicMaterial({ color: 0x86ccc8, transparent: true, opacity: 0.82 })
    );
    this.gizmoCube.add(cubeEdges);

    this.resizeOrientationGizmo();
  }

  bindOrbitPad() {
    if (!viewerOrbitControl || !viewerOrbitThumb || !this.controls) {
      return;
    }

    const resetThumb = () => {
      viewerOrbitThumb.style.transform = "translate(-50%, -50%)";
    };

    viewerOrbitControl.addEventListener("pointerdown", (event) => {
      this.orbitPointerId = event.pointerId;
      viewerOrbitControl.setPointerCapture(event.pointerId);
      viewerOrbitControl.dataset.dragging = "true";
    });

    viewerOrbitControl.addEventListener("pointermove", (event) => {
      if (this.orbitPointerId !== event.pointerId || !this.controls) {
        return;
      }
      const rect = viewerOrbitControl.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const offsetX = Math.max(-28, Math.min(28, event.clientX - centerX));
      const offsetY = Math.max(-28, Math.min(28, event.clientY - centerY));
      viewerOrbitThumb.style.transform = `translate(calc(-50% + ${offsetX}px), calc(-50% + ${offsetY}px))`;
      if (this.autoOrbitEnabled) {
        this.setAutoOrbit(false);
      }
      this.rotateCameraBy(offsetX / 180, offsetY / 180);
    });

    const endDrag = (event) => {
      if (this.orbitPointerId !== event.pointerId) {
        return;
      }
      viewerOrbitControl.releasePointerCapture(event.pointerId);
      this.orbitPointerId = null;
      viewerOrbitControl.dataset.dragging = "false";
      resetThumb();
    };

    viewerOrbitControl.addEventListener("pointerup", endDrag);
    viewerOrbitControl.addEventListener("pointercancel", endDrag);
    resetThumb();
  }

  rotateCameraBy(deltaX, deltaY) {
    if (!this.camera || !this.controls || !THREE) {
      return;
    }
    const offset = this.camera.position.clone().sub(this.controls.target);
    const spherical = new THREE.Spherical().setFromVector3(offset);
    spherical.theta -= deltaX;
    spherical.phi = THREE.MathUtils.clamp(spherical.phi + deltaY, 0.25, Math.PI - 0.25);
    offset.setFromSpherical(spherical);
    this.camera.position.copy(this.controls.target).add(offset);
    this.camera.lookAt(this.controls.target);
    this.controls.update();
  }

  updateAxisIndicator() {
    if (!this.gizmoCube || !this.camera || !this.gizmoCamera || !THREE) {
      return;
    }
    // Match the main viewer's effective basis inside the gizmo's own camera space.
    // Using only inverse(mainCamera) ignores the fact that the gizmo itself is rendered
    // through a separate, already-rotated camera, which produces a visible basis mismatch.
    this.gizmoCube.quaternion
      .copy(this.gizmoCamera.quaternion)
      .multiply(this.camera.quaternion.clone().invert())
      .normalize();
  }

  resize() {
    if (!this.renderer || !this.camera) {
      return;
    }
    const { clientWidth, clientHeight } = viewerRenderSurface;
    if (!clientWidth || !clientHeight) {
      return;
    }
    this.camera.aspect = clientWidth / clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(clientWidth, clientHeight, false);
    this.resizeOrientationGizmo();
  }

  resizeOrientationGizmo() {
    if (!this.gizmoRenderer || !this.gizmoCamera || !viewerAxisScene) {
      return;
    }
    const baseSize = Math.min(viewerAxisScene.clientWidth || 102, viewerAxisScene.clientHeight || 102);
    const size = Math.max(62, Math.round(baseSize * 0.76));
    this.gizmoCamera.aspect = 1;
    this.gizmoCamera.updateProjectionMatrix();
    this.gizmoRenderer.setSize(size, size, false);
  }

  setInteractionMode(mode) {
    if (!this.controls || !THREE) {
      return;
    }
    this.interactionMode = mode;
    const { MOUSE } = THREE;
    if (mode === "pan") {
      this.controls.mouseButtons.LEFT = MOUSE.PAN;
      this.controls.mouseButtons.RIGHT = MOUSE.ROTATE;
    } else if (mode === "zoom") {
      this.controls.mouseButtons.LEFT = MOUSE.DOLLY;
      this.controls.mouseButtons.RIGHT = MOUSE.PAN;
    } else {
      this.controls.mouseButtons.LEFT = MOUSE.ROTATE;
      this.controls.mouseButtons.RIGHT = MOUSE.PAN;
    }
    viewerToolOrbit.classList.toggle("is-active", mode === "orbit");
    viewerToolPan.classList.toggle("is-active", mode === "pan");
    viewerToolZoom.classList.toggle("is-active", mode === "zoom");
  }

  setAutoOrbit(enabled) {
    this.autoOrbitEnabled = Boolean(enabled);
    if (this.controls) {
      this.controls.autoRotate = this.autoOrbitEnabled;
    }
    const icon = this.autoOrbitEnabled ? "⏸" : "▶";
    const label = this.autoOrbitEnabled ? "Pause auto-orbit" : "Start auto-orbit";
    viewerAutoOrbitToggle.textContent = icon;
    viewerAutoOrbitToggle.setAttribute("aria-pressed", this.autoOrbitEnabled ? "true" : "false");
    viewerAutoOrbitToggle.setAttribute("aria-label", label);
    viewerAutoOrbitToggle.setAttribute("title", label);
  }

  setRenderMode(mode) {
    this.renderMode = mode;
    viewerModeSolid.classList.toggle("is-active", mode === "solid");
    viewerModeWireframe.classList.toggle("is-active", mode === "wireframe");
    if (!this.previewObject) {
      return;
    }
    this.previewObject.traverse((child) => {
      if (child.isMesh && child.material) {
        const materials = Array.isArray(child.material) ? child.material : [child.material];
        materials.forEach((material) => {
          material.wireframe = mode === "wireframe";
        });
      }
    });
  }

  clearPreview() {
    if (!this.previewObject) {
      if (this.contactShadow) {
        this.contactShadow.visible = false;
      }
      return;
    }
    this.rootGroup.remove(this.previewObject);
    this.previewObject.traverse((child) => {
      if (child.geometry) {
        child.geometry.dispose();
      }
      if (child.material) {
        const materials = Array.isArray(child.material) ? child.material : [child.material];
        materials.forEach((material) => material.dispose());
      }
    });
    this.previewObject = null;
    if (this.contactShadow) {
      this.contactShadow.visible = false;
    }
  }

  createMaterial(color = 0xf6f7f8) {
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.38,
      metalness: 0.12,
    });
  }

  createRoundedBox(width, height, depth, radius, smoothness = 8) {
    const shape = new THREE.Shape();
    const x = -width / 2;
    const y = -height / 2;
    shape.moveTo(x + radius, y);
    shape.lineTo(x + width - radius, y);
    shape.quadraticCurveTo(x + width, y, x + width, y + radius);
    shape.lineTo(x + width, y + height - radius);
    shape.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    shape.lineTo(x + radius, y + height);
    shape.quadraticCurveTo(x, y + height, x, y + height - radius);
    shape.lineTo(x, y + radius);
    shape.quadraticCurveTo(x, y, x + radius, y);
    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth,
      bevelEnabled: true,
      bevelSegments: smoothness,
      steps: 1,
      bevelSize: radius,
      bevelThickness: radius,
      curveSegments: smoothness,
    });
    geometry.center();
    return geometry;
  }

  buildPreviewGroup({ promptText = "", plan = null }) {
    const group = new THREE.Group();
    const previewKind = getPromptPreviewKind(promptText, plan);
    const shellThickness = Number(plan?.shell_thickness_mm) || 3;

    if (previewKind === "enclosure") {
      const body = new THREE.Mesh(
        this.createRoundedBox(3.8, 1.2, 2.6, 0.12),
        this.createMaterial(0xf3f5f6)
      );
      body.castShadow = true;
      body.receiveShadow = true;
      group.add(body);

      for (let index = 0; index < 4; index += 1) {
        const foot = new THREE.Mesh(
          new THREE.BoxGeometry(0.3, 0.12, 0.22),
          this.createMaterial(0xd7dbde)
        );
        foot.position.set(index < 2 ? -1.35 : 1.35, -0.67, index % 2 === 0 ? -0.85 : 0.85);
        foot.castShadow = true;
        foot.receiveShadow = true;
        group.add(foot);
      }

      for (let index = 0; index < 10; index += 1) {
        const vent = new THREE.Mesh(
          new THREE.BoxGeometry(0.18, 0.03, 0.7),
          new THREE.MeshStandardMaterial({ color: 0xc8ced2, roughness: 0.5, metalness: 0.08 })
        );
        vent.position.set(-1.1 + index * 0.24, 0.62, -0.25);
        group.add(vent);
      }

      const portMaterial = new THREE.MeshStandardMaterial({ color: 0x2f363b, roughness: 0.36, metalness: 0.28 });
      [
        [-1.35, -0.1, 1.31, 0.34],
        [-0.8, -0.1, 1.31, 0.34],
        [0.15, -0.07, 1.31, 0.28],
        [0.82, -0.06, 1.31, 0.42],
        [1.42, -0.02, 1.31, 0.32],
      ].forEach(([x, y, z, width]) => {
        const port = new THREE.Mesh(new THREE.BoxGeometry(width, 0.18, 0.06), portMaterial);
        port.position.set(x, y, z);
        group.add(port);
      });

      group.rotation.x = -0.34;
      group.rotation.y = 0.54;
      group.position.y = 0.12;
    } else if (previewKind === "bracket") {
      const vertical = new THREE.Mesh(new THREE.BoxGeometry(0.55, 2.4, 0.45), this.createMaterial());
      const horizontal = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.45, 0.55), this.createMaterial(0xf1f4f4));
      vertical.position.set(-0.78, 0.6, 0);
      horizontal.position.set(0.18, -0.36, 0);
      vertical.castShadow = true;
      horizontal.castShadow = true;
      group.add(vertical, horizontal);
      group.rotation.y = 0.5;
    } else if (previewKind === "clip") {
      const arc = new THREE.Mesh(
        new THREE.TorusGeometry(1.1, 0.18, 24, 80, Math.PI * 1.45),
        this.createMaterial(0xf3f5f6)
      );
      const base = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.24, 0.7), this.createMaterial(0xeef2f2));
      arc.rotation.z = -0.2;
      base.position.set(-0.68, -0.88, 0);
      arc.castShadow = true;
      base.castShadow = true;
      group.add(arc, base);
      group.rotation.x = -0.36;
      group.rotation.y = 0.56;
    } else if (previewKind === "planter") {
      const pot = new THREE.Mesh(
        new THREE.CylinderGeometry(1.05, 0.8, 1.55, 48, 1, true),
        this.createMaterial(0xf4f6f7)
      );
      const rim = new THREE.Mesh(new THREE.TorusGeometry(1.02, 0.08, 16, 64), this.createMaterial(0xeef2f3));
      rim.rotation.x = Math.PI / 2;
      rim.position.y = 0.72;
      pot.castShadow = true;
      rim.castShadow = true;
      group.add(pot, rim);
      group.rotation.y = 0.38;
    } else if (previewKind === "sphere") {
      const radius = Math.max((Number(plan?.diameter_mm) || 120) / 100, 0.8);
      const sphere = new THREE.Mesh(new THREE.SphereGeometry(radius, 64, 64), this.createMaterial(0xf2f5f6));
      sphere.castShadow = true;
      sphere.receiveShadow = true;
      group.add(sphere);

      if (shellThickness > 0) {
        const ring = new THREE.Mesh(
          new THREE.TorusGeometry(radius * 0.78, 0.08, 18, 64),
          new THREE.MeshStandardMaterial({ color: 0xd8dfe2, roughness: 0.42, metalness: 0.1 })
        );
        ring.rotation.x = Math.PI / 2;
        ring.position.y = 0.2;
        group.add(ring);
      }
      group.rotation.y = 0.38;
    } else if (previewKind === "cylinder") {
      const cylinder = new THREE.Mesh(
        new THREE.CylinderGeometry(1.15, 1.15, 2.1, 48),
        this.createMaterial(0xf2f4f5)
      );
      cylinder.castShadow = true;
      group.add(cylinder);
      group.rotation.y = 0.34;
    } else {
      const block = new THREE.Mesh(
        this.createRoundedBox(2.5, 1.6, 1.9, 0.12),
        this.createMaterial(0xf3f5f6)
      );
      block.castShadow = true;
      block.receiveShadow = true;
      group.add(block);
      group.rotation.x = -0.24;
      group.rotation.y = 0.46;
    }

    group.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    return group;
  }

  collectRepresentativeVertices(object3D, maxSamples = 2400) {
    if (!object3D || !THREE) {
      return [];
    }
    const samples = [];
    const worldVertex = new THREE.Vector3();
    object3D.updateWorldMatrix(true, true);
    object3D.traverse((child) => {
      if (!child.isMesh || !child.geometry?.attributes?.position) {
        return;
      }
      const positions = child.geometry.attributes.position;
      const step = Math.max(1, Math.ceil(positions.count / Math.max(1, Math.floor(maxSamples / 6))));
      for (let index = 0; index < positions.count; index += step) {
        worldVertex.fromBufferAttribute(positions, index).applyMatrix4(child.matrixWorld);
        samples.push(worldVertex.clone());
        if (samples.length >= maxSamples) {
          break;
        }
      }
    });
    return samples;
  }

  jacobiEigenDecomposition(matrix) {
    const a = matrix.map((row) => row.slice());
    const v = [
      [1, 0, 0],
      [0, 1, 0],
      [0, 0, 1],
    ];

    for (let iteration = 0; iteration < 12; iteration += 1) {
      let p = 0;
      let q = 1;
      let maxValue = Math.abs(a[0][1]);
      if (Math.abs(a[0][2]) > maxValue) {
        maxValue = Math.abs(a[0][2]);
        p = 0;
        q = 2;
      }
      if (Math.abs(a[1][2]) > maxValue) {
        maxValue = Math.abs(a[1][2]);
        p = 1;
        q = 2;
      }
      if (maxValue < 1e-9) {
        break;
      }

      const angle = 0.5 * Math.atan2(2 * a[p][q], a[q][q] - a[p][p]);
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);

      for (let row = 0; row < 3; row += 1) {
        const arp = a[row][p];
        const arq = a[row][q];
        a[row][p] = (cosine * arp) - (sine * arq);
        a[row][q] = (sine * arp) + (cosine * arq);
      }

      for (let column = 0; column < 3; column += 1) {
        const apc = a[p][column];
        const aqc = a[q][column];
        a[p][column] = (cosine * apc) - (sine * aqc);
        a[q][column] = (sine * apc) + (cosine * aqc);
      }

      for (let row = 0; row < 3; row += 1) {
        const vrp = v[row][p];
        const vrq = v[row][q];
        v[row][p] = (cosine * vrp) - (sine * vrq);
        v[row][q] = (sine * vrp) + (cosine * vrq);
      }
    }

    return {
      values: [a[0][0], a[1][1], a[2][2]],
      vectors: [
        new THREE.Vector3(v[0][0], v[1][0], v[2][0]).normalize(),
        new THREE.Vector3(v[0][1], v[1][1], v[2][1]).normalize(),
        new THREE.Vector3(v[0][2], v[1][2], v[2][2]).normalize(),
      ],
    };
  }

  computePrincipalAxesFrame(object3D) {
    const points = this.collectRepresentativeVertices(object3D);
    if (points.length < 3) {
      const fallbackQuaternion = object3D.quaternion.clone();
      const fallbackAxes = [
        new THREE.Vector3(1, 0, 0).applyQuaternion(fallbackQuaternion).normalize(),
        new THREE.Vector3(0, 1, 0).applyQuaternion(fallbackQuaternion).normalize(),
        new THREE.Vector3(0, 0, 1).applyQuaternion(fallbackQuaternion).normalize(),
      ];
      return { axes: fallbackAxes, values: [3, 2, 1] };
    }

    const mean = new THREE.Vector3();
    points.forEach((point) => mean.add(point));
    mean.divideScalar(points.length);

    const covariance = [
      [0, 0, 0],
      [0, 0, 0],
      [0, 0, 0],
    ];
    points.forEach((point) => {
      const dx = point.x - mean.x;
      const dy = point.y - mean.y;
      const dz = point.z - mean.z;
      covariance[0][0] += dx * dx;
      covariance[0][1] += dx * dy;
      covariance[0][2] += dx * dz;
      covariance[1][0] += dy * dx;
      covariance[1][1] += dy * dy;
      covariance[1][2] += dy * dz;
      covariance[2][0] += dz * dx;
      covariance[2][1] += dz * dy;
      covariance[2][2] += dz * dz;
    });

    const eigen = this.jacobiEigenDecomposition(covariance);
    const ordered = eigen.values.map((value, index) => ({
      value,
      axis: eigen.vectors[index].clone(),
    })).sort((left, right) => right.value - left.value);

    const axes = ordered.map(({ axis }) => {
      const normalized = axis.normalize();
      const components = [Math.abs(normalized.x), Math.abs(normalized.y), Math.abs(normalized.z)];
      const dominantIndex = components.indexOf(Math.max(...components));
      if (normalized.getComponent(dominantIndex) < 0) {
        normalized.negate();
      }
      return normalized;
    });

    if (new THREE.Vector3().crossVectors(axes[0], axes[1]).dot(axes[2]) < 0) {
      axes[2].negate();
    }

    return {
      axes,
      values: ordered.map(({ value }) => value),
    };
  }

  collectDominantFaceClusters(object3D, maxTriangles = 1200) {
    if (!object3D || !THREE) {
      return [];
    }
    const clusters = [];
    const a = new THREE.Vector3();
    const b = new THREE.Vector3();
    const c = new THREE.Vector3();
    const edgeAB = new THREE.Vector3();
    const edgeAC = new THREE.Vector3();

    object3D.updateWorldMatrix(true, true);
    object3D.traverse((child) => {
      if (!child.isMesh || !child.geometry?.attributes?.position) {
        return;
      }
      const position = child.geometry.attributes.position;
      const indexArray = child.geometry.index?.array || null;
      const triangleCount = indexArray ? Math.floor(indexArray.length / 3) : Math.floor(position.count / 3);
      const step = Math.max(1, Math.ceil(triangleCount / maxTriangles));

      for (let triangleIndex = 0; triangleIndex < triangleCount; triangleIndex += step) {
        const i0 = indexArray ? indexArray[triangleIndex * 3] : triangleIndex * 3;
        const i1 = indexArray ? indexArray[(triangleIndex * 3) + 1] : (triangleIndex * 3) + 1;
        const i2 = indexArray ? indexArray[(triangleIndex * 3) + 2] : (triangleIndex * 3) + 2;
        a.fromBufferAttribute(position, i0).applyMatrix4(child.matrixWorld);
        b.fromBufferAttribute(position, i1).applyMatrix4(child.matrixWorld);
        c.fromBufferAttribute(position, i2).applyMatrix4(child.matrixWorld);

        edgeAB.subVectors(b, a);
        edgeAC.subVectors(c, a);
        const normal = new THREE.Vector3().crossVectors(edgeAB, edgeAC);
        const twiceArea = normal.length();
        if (twiceArea < 1e-6) {
          continue;
        }
        normal.normalize();
        const area = twiceArea * 0.5;

        let bestCluster = null;
        let bestDot = 0.92;
        clusters.forEach((cluster) => {
          const dot = Math.abs(normal.dot(cluster.normal));
          if (dot > bestDot) {
            bestDot = dot;
            bestCluster = cluster;
          }
        });

        if (!bestCluster) {
          clusters.push({
            normal: normal.clone(),
            weightedNormal: normal.clone().multiplyScalar(area),
            totalArea: area,
          });
          continue;
        }

        const alignedNormal = normal.dot(bestCluster.normal) >= 0 ? normal : normal.clone().negate();
        bestCluster.weightedNormal.addScaledVector(alignedNormal, area);
        bestCluster.totalArea += area;
        bestCluster.normal.copy(bestCluster.weightedNormal).normalize();
      }
    });

    return clusters
      .map((cluster) => ({
        normal: cluster.normal.clone().normalize(),
        totalArea: cluster.totalArea,
      }))
      .sort((left, right) => right.totalArea - left.totalArea);
  }

  orientAxisDeterministically(axis) {
    const normalized = axis.clone().normalize();
    const components = [Math.abs(normalized.x), Math.abs(normalized.y), Math.abs(normalized.z)];
    const dominantIndex = components.indexOf(Math.max(...components));
    if (normalized.getComponent(dominantIndex) < 0) {
      normalized.negate();
    }
    return normalized;
  }

  computeDominantFaceFrame(object3D) {
    const clusters = this.collectDominantFaceClusters(object3D);
    if (clusters.length < 2) {
      return null;
    }

    const primary = this.orientAxisDeterministically(clusters[0].normal);
    const secondaryCluster = clusters.find((cluster, index) => index > 0 && Math.abs(cluster.normal.dot(primary)) < 0.82 && cluster.totalArea >= clusters[0].totalArea * 0.08);
    if (!secondaryCluster) {
      return null;
    }

    const secondary = secondaryCluster.normal.clone().sub(primary.clone().multiplyScalar(secondaryCluster.normal.dot(primary)));
    if (secondary.lengthSq() < 1e-6) {
      return null;
    }
    secondary.normalize();
    const tertiary = new THREE.Vector3().crossVectors(primary, secondary).normalize();
    if (tertiary.lengthSq() < 1e-6) {
      return null;
    }

    const axes = [
      this.orientAxisDeterministically(primary),
      this.orientAxisDeterministically(secondary),
      this.orientAxisDeterministically(tertiary),
    ];
    if (new THREE.Vector3().crossVectors(axes[0], axes[1]).dot(axes[2]) < 0) {
      axes[2].negate();
    }

    const totalArea = clusters.reduce((sum, cluster) => sum + cluster.totalArea, 0);
    const confidence = totalArea > 0
      ? THREE.MathUtils.clamp(
        (clusters[0].totalArea / totalArea) * 0.55
        + (secondaryCluster.totalArea / totalArea) * 0.25
        + (1 - Math.abs(clusters[0].normal.dot(secondaryCluster.normal))) * 0.3,
        0,
        1
      )
      : 0;

    if (confidence < 0.42) {
      return null;
    }

    return {
      axes,
      values: [
        clusters[0].totalArea,
        secondaryCluster.totalArea,
        Math.max(totalArea - clusters[0].totalArea - secondaryCluster.totalArea, secondaryCluster.totalArea * 0.5),
      ],
      confidence,
      source: "dominant-face",
    };
  }

  buildPoseCandidateFromFrame(frame, baseQuaternion, upIndex, upSign, label) {
    const axes = frame.axes.map((axis) => axis.clone());
    const up = axes[upIndex].multiplyScalar(upSign).normalize();
    const remaining = [0, 1, 2]
      .filter((index) => index !== upIndex)
      .sort((left, right) => frame.values[right] - frame.values[left]);
    let forward = axes[remaining[0]].clone().normalize();
    const side = axes[remaining[1]].clone().normalize();
    let right = new THREE.Vector3().crossVectors(forward, up).normalize();
    if (right.dot(side) < 0) {
      forward.negate();
      right = new THREE.Vector3().crossVectors(forward, up).normalize();
    }
    forward = new THREE.Vector3().crossVectors(up, right).normalize();

    const basisMatrix = new THREE.Matrix4().makeBasis(right, up, forward);
    const basisQuaternion = new THREE.Quaternion().setFromRotationMatrix(basisMatrix);
    const deltaQuaternion = basisQuaternion.clone().invert();
    const candidateQuaternion = deltaQuaternion.multiply(baseQuaternion.clone());
    return { label, quaternion: candidateQuaternion };
  }

  getGenericPoseCandidates(object3D) {
    const baseQuaternion = object3D.quaternion.clone();
    const frame = this.computeDominantFaceFrame(object3D) || {
      ...this.computePrincipalAxesFrame(object3D),
      source: "pca",
      confidence: 0,
    };
    return [
      this.buildPoseCandidateFromFrame(frame, baseQuaternion, 0, 1, "+X up"),
      this.buildPoseCandidateFromFrame(frame, baseQuaternion, 0, -1, "-X up"),
      this.buildPoseCandidateFromFrame(frame, baseQuaternion, 1, 1, "+Y up"),
      this.buildPoseCandidateFromFrame(frame, baseQuaternion, 1, -1, "-Y up"),
      this.buildPoseCandidateFromFrame(frame, baseQuaternion, 2, 1, "+Z up"),
      this.buildPoseCandidateFromFrame(frame, baseQuaternion, 2, -1, "-Z up"),
    ].map((candidate) => ({
      ...candidate,
      basisSource: frame.source,
      basisConfidence: frame.confidence,
    }));
  }

  computeStructuralReadability(object3D) {
    const clusters = this.collectDominantFaceClusters(object3D, 800);
    if (!clusters.length) {
      return { alignment: 0, orthogonality: 0, coverage: 0 };
    }
    const totalArea = clusters.reduce((sum, cluster) => sum + cluster.totalArea, 0) || 1;
    const topClusters = clusters.slice(0, 3);
    let alignment = 0;
    let coverage = 0;
    topClusters.forEach((cluster) => {
      const axisAlignment = Math.max(Math.abs(cluster.normal.x), Math.abs(cluster.normal.y), Math.abs(cluster.normal.z));
      const weight = cluster.totalArea / totalArea;
      alignment += axisAlignment * weight;
      coverage += weight;
    });
    let orthogonality = 0;
    if (topClusters.length >= 2) {
      orthogonality = 1 - Math.abs(topClusters[0].normal.dot(topClusters[1].normal));
    }
    return { alignment, orthogonality, coverage };
  }

  evaluateGenericPoseCandidate(object3D, candidate, basePosition) {
    if (!object3D || !THREE) {
      return null;
    }
    object3D.position.copy(basePosition);
    object3D.quaternion.copy(candidate.quaternion);
    object3D.updateWorldMatrix(true, true);

    const initialBox = new THREE.Box3().setFromObject(object3D);
    if (initialBox.isEmpty()) {
      return null;
    }

    object3D.position.y -= initialBox.min.y;
    object3D.updateWorldMatrix(true, true);

    const groundedBox = new THREE.Box3().setFromObject(object3D);
    const size = groundedBox.getSize(new THREE.Vector3());
    const footprint = this.computeSupportFootprint(object3D, groundedBox);
    if (!footprint) {
      return {
        candidate,
        quaternion: candidate.quaternion.clone(),
        score: -1,
      };
    }

    const supportWidth = Math.max(footprint.maxX - footprint.minX, 0.001);
    const supportDepth = Math.max(footprint.maxZ - footprint.minZ, 0.001);
    const supportArea = supportWidth * supportDepth;
    const baseArea = Math.max(size.x * size.z, 0.001);
    const supportRatio = THREE.MathUtils.clamp(supportArea / baseArea, 0, 1.6);
    const center = groundedBox.getCenter(new THREE.Vector3());
    const centerOffset = Math.hypot(footprint.center.x - center.x, footprint.center.z - center.z);
    const footprintBalance = 1 - THREE.MathUtils.clamp(centerOffset / Math.max(Math.max(size.x, size.z), 0.001), 0, 1);
    const heightReadability = 1 - THREE.MathUtils.clamp(size.y / Math.max(size.x + size.z, 0.001), 0, 1);
    const silhouetteSpread = Math.min(size.x, size.z) / Math.max(Math.max(size.x, size.z), 0.001);
    const maxDimension = Math.max(size.x, size.y, size.z, 0.001);
    const horizontalOccupancy = THREE.MathUtils.clamp((size.x * size.z) / (maxDimension * maxDimension), 0, 1.2);
    const structural = this.computeStructuralReadability(object3D);
    const score = (structural.alignment * 2.0)
      + (structural.orthogonality * 1.15)
      + (structural.coverage * 0.9)
      + (supportRatio * 1.05)
      + (footprintBalance * 0.92)
      + (heightReadability * 0.95)
      + (silhouetteSpread * 0.55)
      + (horizontalOccupancy * 0.45);

    return {
      candidate,
      quaternion: candidate.quaternion.clone(),
      box: groundedBox.clone(),
      supportFootprint: footprint,
      structuralReadability: structural,
      score,
    };
  }

  normalizeRestingOrientation(object3D) {
    if (!object3D || !THREE) {
      return null;
    }

    const baseQuaternion = object3D.quaternion.clone();
    const basePosition = object3D.position.clone();
    const candidates = this.getGenericPoseCandidates(object3D);
    let best = null;

    for (const candidate of candidates) {
      const result = this.evaluateGenericPoseCandidate(object3D, candidate, basePosition);
      if (!result) {
        continue;
      }
      if (!best || result.score > best.score + 1e-6) {
        best = result;
      }
    }

    object3D.position.copy(basePosition);
    object3D.quaternion.copy(best?.quaternion || baseQuaternion);
    object3D.updateWorldMatrix(true, true);
    return best;
  }

  placeObjectOnStage(object3D) {
    if (!object3D || !THREE) {
      return null;
    }
    const initialBox = new THREE.Box3().setFromObject(object3D);
    if (initialBox.isEmpty()) {
      return null;
    }
    object3D.position.y -= initialBox.min.y;
    const groundedBox = new THREE.Box3().setFromObject(object3D);
    const supportFootprint = this.computeSupportFootprint(object3D, groundedBox);
    const fallbackCenter = groundedBox.getCenter(new THREE.Vector3());
    const contactCenter = supportFootprint?.center || fallbackCenter;
    object3D.position.x -= contactCenter.x;
    object3D.position.z -= contactCenter.z;

    const placedBox = new THREE.Box3().setFromObject(object3D);
    const placedSupportFootprint = this.computeSupportFootprint(object3D, placedBox);
    const settled = this.applyFinalSettlingPass(object3D, placedBox, placedSupportFootprint);
    const squared = this.applyConservativeLeveling(object3D, settled.box, settled.supportFootprint);
    this.updateContactShadow(squared.supportFootprint || squared.box, squared.box);
    return squared;
  }

  computeSupportFootprint(object3D, box = null) {
    if (!object3D || !THREE) {
      return null;
    }
    const measuredBox = box || new THREE.Box3().setFromObject(object3D);
    if (measuredBox.isEmpty()) {
      return null;
    }
    const size = measuredBox.getSize(new THREE.Vector3());
    const sliceHeight = THREE.MathUtils.clamp(size.y * 0.1, 0.025, 0.14);
    const supportCeiling = measuredBox.min.y + sliceHeight;
    const supportCandidates = [];
    const worldVertex = new THREE.Vector3();

    object3D.updateWorldMatrix(true, true);
    object3D.traverse((child) => {
      if (!child.isMesh || !child.geometry?.attributes?.position) {
        return;
      }
      const positions = child.geometry.attributes.position;
      const step = Math.max(1, Math.ceil(positions.count / 1500));
      for (let index = 0; index < positions.count; index += step) {
        worldVertex.fromBufferAttribute(positions, index).applyMatrix4(child.matrixWorld);
        if (worldVertex.y <= supportCeiling + 1e-4) {
          supportCandidates.push(worldVertex.clone());
        }
      }
    });

    if (!supportCandidates.length) {
      return null;
    }

    let candidateMinY = Infinity;
    supportCandidates.forEach((point) => {
      candidateMinY = Math.min(candidateMinY, point.y);
    });
    const dominantSupportCeiling = candidateMinY + Math.min(sliceHeight * 0.35, 0.018);
    let minX = Infinity;
    let maxX = -Infinity;
    let minZ = Infinity;
    let maxZ = -Infinity;
    let weightedX = 0;
    let weightedZ = 0;
    let weightedY = 0;
    let weightTotal = 0;
    let samples = 0;
    let minSampleY = Infinity;
    let maxSampleY = -Infinity;
    supportCandidates.forEach((point) => {
      if (point.y > dominantSupportCeiling + 1e-4) {
        return;
      }
      const normalizedHeight = Math.max(0, Math.min(1, (point.y - candidateMinY) / Math.max(dominantSupportCeiling - candidateMinY, 1e-4)));
      const weight = 1 - normalizedHeight * 0.82;
      minX = Math.min(minX, point.x);
      maxX = Math.max(maxX, point.x);
      minZ = Math.min(minZ, point.z);
      maxZ = Math.max(maxZ, point.z);
      minSampleY = Math.min(minSampleY, point.y);
      maxSampleY = Math.max(maxSampleY, point.y);
      weightedX += point.x * weight;
      weightedZ += point.z * weight;
      weightedY += point.y * weight;
      weightTotal += weight;
      samples += 1;
    });

    if (!samples || !Number.isFinite(minX) || !Number.isFinite(minZ) || !weightTotal) {
      return null;
    }

    return {
      center: new THREE.Vector3(weightedX / weightTotal, measuredBox.min.y, weightedZ / weightTotal),
      minX,
      maxX,
      minZ,
      maxZ,
      minSampleY,
      maxSampleY,
      meanSampleY: weightTotal ? (weightedY / weightTotal) : measuredBox.min.y,
      dominantSupportCeiling,
      samples,
    };
  }

  applyFinalSettlingPass(object3D, currentBox, currentSupportFootprint) {
    if (!object3D || !THREE) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }
    if (!currentSupportFootprint || !currentSupportFootprint.samples) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    const supportHeightSpread = Math.max(0, (currentSupportFootprint.maxSampleY ?? currentBox.min.y) - (currentSupportFootprint.minSampleY ?? currentBox.min.y));
    const supportMeanLift = Math.max(0, (currentSupportFootprint.meanSampleY ?? currentBox.min.y) - currentBox.min.y);
    const settleAmount = THREE.MathUtils.clamp((supportMeanLift * 0.6) + (supportHeightSpread * 0.2), 0, 0.014);
    if (settleAmount <= 1e-4) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    object3D.position.y -= settleAmount;
    object3D.updateWorldMatrix(true, true);
    const settledBox = new THREE.Box3().setFromObject(object3D);
    const settledSupportFootprint = this.computeSupportFootprint(object3D, settledBox);
    return { box: settledBox, supportFootprint: settledSupportFootprint };
  }

  detectDominantRestingSurface(object3D, currentBox) {
    if (!object3D || !THREE || !currentBox || currentBox.isEmpty()) {
      return null;
    }

    const size = currentBox.getSize(new THREE.Vector3());
    const bottomY = currentBox.min.y;
    const surfaceBand = Math.min(Math.max(size.y * 0.08, 0.012), 0.05);
    const triangleThreshold = bottomY + surfaceBand;
    const a = new THREE.Vector3();
    const b = new THREE.Vector3();
    const c = new THREE.Vector3();
    const edgeAB = new THREE.Vector3();
    const edgeAC = new THREE.Vector3();
    let weightedNormal = new THREE.Vector3();
    let weightedCenter = new THREE.Vector3();
    let totalWeight = 0;
    let matchedTriangles = 0;
    let maxTriangleArea = 0;

    object3D.updateWorldMatrix(true, true);
    object3D.traverse((child) => {
      if (!child.isMesh || !child.geometry?.attributes?.position) {
        return;
      }
      const position = child.geometry.attributes.position;
      const indexArray = child.geometry.index?.array || null;
      const triangleCount = indexArray ? Math.floor(indexArray.length / 3) : Math.floor(position.count / 3);
      const step = Math.max(1, Math.ceil(triangleCount / 700));
      for (let triangleIndex = 0; triangleIndex < triangleCount; triangleIndex += step) {
        const i0 = indexArray ? indexArray[triangleIndex * 3] : triangleIndex * 3;
        const i1 = indexArray ? indexArray[(triangleIndex * 3) + 1] : (triangleIndex * 3) + 1;
        const i2 = indexArray ? indexArray[(triangleIndex * 3) + 2] : (triangleIndex * 3) + 2;
        a.fromBufferAttribute(position, i0).applyMatrix4(child.matrixWorld);
        b.fromBufferAttribute(position, i1).applyMatrix4(child.matrixWorld);
        c.fromBufferAttribute(position, i2).applyMatrix4(child.matrixWorld);
        const triangleMinY = Math.min(a.y, b.y, c.y);
        const triangleAvgY = (a.y + b.y + c.y) / 3;
        if (triangleMinY > triangleThreshold || triangleAvgY > triangleThreshold + surfaceBand * 0.25) {
          continue;
        }

        edgeAB.subVectors(b, a);
        edgeAC.subVectors(c, a);
        const triangleNormal = new THREE.Vector3().crossVectors(edgeAB, edgeAC);
        const twiceArea = triangleNormal.length();
        if (twiceArea < 1e-6) {
          continue;
        }
        triangleNormal.normalize();
        const upness = Math.abs(triangleNormal.y);
        if (upness < 0.88) {
          continue;
        }
        const area = twiceArea * 0.5;
        const proximityWeight = 1 - THREE.MathUtils.clamp((triangleAvgY - bottomY) / Math.max(surfaceBand, 1e-4), 0, 1);
        const weight = area * upness * (0.65 + proximityWeight * 0.7);
        const triangleCenter = new THREE.Vector3(
          (a.x + b.x + c.x) / 3,
          (a.y + b.y + c.y) / 3,
          (a.z + b.z + c.z) / 3
        );
        weightedNormal.addScaledVector(triangleNormal, weight);
        weightedCenter.addScaledVector(triangleCenter, weight);
        totalWeight += weight;
        matchedTriangles += 1;
        maxTriangleArea = Math.max(maxTriangleArea, area);
      }
    });

    if (!matchedTriangles || totalWeight <= 1e-6 || weightedNormal.lengthSq() <= 1e-8) {
      return null;
    }

    const normal = weightedNormal.normalize();
    const center = weightedCenter.divideScalar(totalWeight);
    const confidence = Math.min(1, (matchedTriangles / 18) * 0.45 + (Math.abs(normal.y) * 0.4) + (Math.min(maxTriangleArea, 0.35) * 0.4));
    return {
      normal,
      center,
      confidence,
      matchedTriangles,
    };
  }

  applyConservativeLeveling(object3D, currentBox, currentSupportFootprint) {
    if (!object3D || !THREE || !currentBox || currentBox.isEmpty()) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    const surface = this.detectDominantRestingSurface(object3D, currentBox);
    if (!surface || surface.confidence < 0.74 || surface.matchedTriangles < 4) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    const planeNormal = surface.normal.clone();
    const worldUp = new THREE.Vector3(0, 1, 0);
    const tiltAxis = new THREE.Vector3().crossVectors(planeNormal, worldUp);
    const tiltMagnitude = tiltAxis.length();
    if (tiltMagnitude < 1e-4) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    const tiltAngle = Math.acos(THREE.MathUtils.clamp(planeNormal.dot(worldUp), -1, 1));
    const maxCorrectionAngle = 0.105;
    if (tiltAngle < 0.012 || tiltAngle > maxCorrectionAngle) {
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    tiltAxis.normalize();
    const correctionAngle = THREE.MathUtils.clamp(tiltAngle * 0.9, 0, maxCorrectionAngle);
    const correction = new THREE.Quaternion().setFromAxisAngle(tiltAxis, correctionAngle);
    const originalPosition = object3D.position.clone();
    const originalQuaternion = object3D.quaternion.clone();
    object3D.quaternion.premultiply(correction);
    object3D.updateWorldMatrix(true, true);

    const correctedBox = new THREE.Box3().setFromObject(object3D);
    object3D.position.y -= correctedBox.min.y;
    object3D.updateWorldMatrix(true, true);

    const groundedBox = new THREE.Box3().setFromObject(object3D);
    const supportFootprint = this.computeSupportFootprint(object3D, groundedBox);
    const fallbackCenter = groundedBox.getCenter(new THREE.Vector3());
    const contactCenter = supportFootprint?.center || fallbackCenter;
    object3D.position.x -= contactCenter.x;
    object3D.position.z -= contactCenter.z;
    object3D.updateWorldMatrix(true, true);

    const finalBox = new THREE.Box3().setFromObject(object3D);
    const finalSupportFootprint = this.computeSupportFootprint(object3D, finalBox);
    const originalSize = currentBox.getSize(new THREE.Vector3());
    const finalSize = finalBox.getSize(new THREE.Vector3());
    const originalFootprint = currentSupportFootprint
      ? Math.max((currentSupportFootprint.maxX - currentSupportFootprint.minX) * (currentSupportFootprint.maxZ - currentSupportFootprint.minZ), 0)
      : 0;
    const finalFootprint = finalSupportFootprint
      ? Math.max((finalSupportFootprint.maxX - finalSupportFootprint.minX) * (finalSupportFootprint.maxZ - finalSupportFootprint.minZ), 0)
      : 0;
    const originalBalance = currentSupportFootprint
      ? 1 - THREE.MathUtils.clamp(
        Math.hypot(
          currentSupportFootprint.center.x - currentBox.getCenter(new THREE.Vector3()).x,
          currentSupportFootprint.center.z - currentBox.getCenter(new THREE.Vector3()).z
        ) / Math.max(Math.max(originalSize.x, originalSize.z), 0.001),
        0,
        1
      )
      : 0;
    const finalBalance = finalSupportFootprint
      ? 1 - THREE.MathUtils.clamp(
        Math.hypot(
          finalSupportFootprint.center.x - finalBox.getCenter(new THREE.Vector3()).x,
          finalSupportFootprint.center.z - finalBox.getCenter(new THREE.Vector3()).z
        ) / Math.max(Math.max(finalSize.x, finalSize.z), 0.001),
        0,
        1
      )
      : 0;

    if (
      finalSize.y > originalSize.y * 1.08
      || finalBalance < originalBalance - 0.1
      || finalFootprint < originalFootprint * 0.78
    ) {
      object3D.position.copy(originalPosition);
      object3D.quaternion.copy(originalQuaternion);
      object3D.updateWorldMatrix(true, true);
      return { box: currentBox, supportFootprint: currentSupportFootprint };
    }

    return { box: finalBox, supportFootprint: finalSupportFootprint };
  }

  updateContactShadow(footprintOrBox, fullBox = null) {
    if (!this.contactShadow || !footprintOrBox) {
      return;
    }
    const isSupportFootprint = "samples" in footprintOrBox;
    const bounds = isSupportFootprint
      ? footprintOrBox
      : {
        minX: footprintOrBox.min.x,
        maxX: footprintOrBox.max.x,
        minZ: footprintOrBox.min.z,
        maxZ: footprintOrBox.max.z,
      };
    const box = fullBox || (!isSupportFootprint ? footprintOrBox : null);
    const baseFootprintX = Math.max(bounds.maxX - bounds.minX, 0.36);
    const baseFootprintZ = Math.max(bounds.maxZ - bounds.minZ, 0.36);
    const boxSize = box ? box.getSize(new THREE.Vector3()) : new THREE.Vector3(baseFootprintX, 0, baseFootprintZ);
    const footprintX = Math.max(baseFootprintX, boxSize.x * 0.14);
    const footprintZ = Math.max(baseFootprintZ, boxSize.z * 0.14);
    this.contactShadow.scale.set(footprintX * 0.44, footprintZ * 0.44, 1);
    this.contactShadow.material.opacity = THREE.MathUtils.clamp(0.1 + Math.min(footprintX, footprintZ) * 0.018, 0.1, 0.18);
    this.contactShadow.position.set((bounds.minX + bounds.maxX) / 2, 0.0018, (bounds.minZ + bounds.maxZ) / 2);
    this.contactShadow.visible = true;
  }

  getFramingProfile(previewKind, size) {
    const flatProfile = size.y <= Math.max(size.x, size.z) * 0.2;
    if (previewKind === "bracket" || previewKind === "clip" || previewKind === "cylinder") {
      return {
        direction: new THREE.Vector3(1.06, 0.6, 0.86),
        distanceMultiplier: 1.14,
        targetHeight: 0.35,
      };
    }
    if (previewKind === "panel" || flatProfile) {
      return {
        direction: new THREE.Vector3(0.3, 0.9, 1.12),
        distanceMultiplier: 1.1,
        targetHeight: 0.24,
      };
    }
    if (previewKind === "enclosure" || previewKind === "planter") {
      return {
        direction: new THREE.Vector3(1, 0.72, 1.04),
        distanceMultiplier: 1.18,
        targetHeight: 0.35,
      };
    }
    return {
      direction: new THREE.Vector3(0.96, 0.68, 1),
      distanceMultiplier: 1.16,
      targetHeight: 0.35,
    };
  }

  fitCameraToObject(object3D, previewKind = "block", placement = null) {
    if (!object3D || !this.camera || !this.controls || !THREE) {
      return;
    }
    const box = placement?.box || new THREE.Box3().setFromObject(object3D);
    if (box.isEmpty()) {
      return;
    }
    const size = box.getSize(new THREE.Vector3());
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    const aspect = this.camera.aspect || 1;
    const verticalFov = THREE.MathUtils.degToRad(this.camera.fov);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * aspect);
    const fitHeightDistance = (size.y / 2) / Math.tan(verticalFov / 2);
    const fitWidthDistance = (Math.max(size.x, size.z) / 2) / Math.tan(horizontalFov / 2);
    const profile = this.getFramingProfile(previewKind, size);
    const fitDistance = THREE.MathUtils.clamp(
      Math.max(fitHeightDistance, fitWidthDistance, sphere.radius * 1.34, 0.28) * profile.distanceMultiplier,
      1.6,
      22
    );
    const supportCenter = placement?.supportFootprint?.center || new THREE.Vector3(0, box.min.y, 0);
    const viewCenter = new THREE.Vector3(
      supportCenter.x * 0.3,
      box.max.y * profile.targetHeight,
      supportCenter.z * 0.3
    );
    const direction = profile.direction.clone().normalize();
    const offset = direction.multiplyScalar(fitDistance);
    this.camera.position.copy(viewCenter).add(offset);
    this.controls.target.copy(viewCenter);
    this.camera.near = Math.max(fitDistance / 100, 0.001);
    this.camera.far = Math.max(fitDistance * 20, 20);
    this.camera.updateProjectionMatrix();
    this.controls.update();
  }

  focusObject() {
    if (this.previewObject) {
      this.fitCameraToObject(this.previewObject);
    }
  }

  resetView() {
    if (!this.camera || !this.controls) {
      return;
    }
    this.camera.position.set(5.8, 4.6, 6.9);
    this.controls.target.set(0, 0.78, 0);
    this.controls.update();
    if (this.previewObject) {
      this.fitCameraToObject(this.previewObject);
    }
  }

  async tryLoadExternalPreview(previewModelPath, previewAssetVersion = "") {
    if (!GLTFLoader || !previewModelPath) {
      return null;
    }
    const previewUrl = withCacheKey(toFileUrl(previewModelPath) || previewModelPath, previewAssetVersion);
    if (!previewUrl || !/\.(glb|gltf)$/i.test(previewUrl)) {
      return null;
    }
    const loader = new GLTFLoader();
    return new Promise((resolve, reject) => {
      loader.load(
        previewUrl,
        (gltf) => resolve(gltf.scene),
        undefined,
        reject
      );
    });
  }

  async loadPreview({ promptText = "", plan = null, previewModelPath = "", previewAssetVersion = "", previewKey = "" }) {
    if (!this.initialized) {
      return;
    }
    if (previewKey && previewKey === this.lastPreviewKey) {
      return;
    }

    setViewerOverlay("loading", "Generating model", "Setting the current model in place.");
    this.clearPreview();

    let loadedObject = null;
    const previewKind = getPromptPreviewKind(promptText, plan);
    if (previewModelPath) {
      try {
        loadedObject = await this.tryLoadExternalPreview(previewModelPath, previewAssetVersion);
      } catch (error) {
        appendLog(`Preview asset load failed, falling back to procedural preview: ${error}`);
      }
    }

    this.previewObject = loadedObject || this.buildPreviewGroup({ promptText, plan });
    this.rootGroup.add(this.previewObject);
    this.normalizeRestingOrientation(this.previewObject, previewKind);
    const placement = this.placeObjectOnStage(this.previewObject);
    this.setRenderMode(this.renderMode);
    this.fitCameraToObject(this.previewObject, previewKind, placement);
    this.lastPreviewKey = previewKey;
    setViewerOverlay("ready", "Preview ready", "Review available.");
  }

  setError(message) {
    setViewerOverlay("error", "Viewer error", message);
  }

  setEmpty() {
    this.clearPreview();
    if (this.contactShadow) {
      this.contactShadow.visible = false;
    }
    this.lastPreviewKey = "";
    setViewerOverlay(
      "empty",
      "Ready for a model",
      "Generate a part to review it here."
    );
  }

  setLoading(message) {
    setViewerOverlay("loading", "Generating model", message);
  }
}

const viewer = new GeomancerViewer();

async function applyState(rawState) {
  const state = await resolveBridgeJson(rawState, "getInitialState/stateChanged");
  appendLog(`Debug: restored state applied -> status=${state.lastGenerationStatus || "idle"}, raw_status=${state.lastGenerationRawStatus || "none"}, family=${state.lastGenerationFamily || "none"}, generation_id=${state.generationId || "none"}, saved_models=${state.librarySummary?.saved_model_count || 0}`);
  updatePassiveShellState(state);
  if (!hasLoadedInitialState) {
    hasLoadedInitialState = true;
    resetActiveSession({
      reasonText: runtimeReady()
        ? (state.librarySummary?.saved_model_count
          ? `${state.librarySummary.saved_model_count} saved model(s) are available in the local library.`
          : "No active generation is loaded yet.")
        : (state.runtimeHealthMessage || "Finish local setup before using the main workspace."),
      clearPrompt: true,
    });
    promptInput.focus();
    return;
  }
  appendLog(`Passive backend refresh applied. Saved models: ${state.librarySummary?.saved_model_count || 0}`);
}

function setGenerating(isGenerating) {
  generateButton.disabled = isGenerating || !runtimeReady();
  generateButton.textContent = isGenerating ? "..." : "Go";
}

function connectBridge() {
  if (typeof qt === "undefined") {
    appendLog("Qt bridge unavailable. This UI is intended for the desktop shell.");
    return;
  }

  appendLog("[UI] WebChannel initialized");
  new QWebChannel(qt.webChannelTransport, (channel) => {
    bridge = channel.objects.geomancerBridge;
    appendLog("[UI] bridge object detected");
    bridge.stateChanged.connect((payload) => {
      void applyState(payload).catch((error) => {
        appendLog(`Failed to apply backend state: ${error}`);
      });
    });
    bridge.runtimeHealthChanged.connect((payload) => {
      void (async () => {
        const health = await resolveBridgeJson(payload, "runtimeHealthChanged");
        applyRuntimeGate({ runtimeHealth: health, setupFlow: runtimeSetupFlow });
      })().catch((error) => {
        appendLog(`Failed to apply runtime health: ${error}`);
      });
    });
    bridge.modelPullProgress.connect((payload) => {
      void (async () => {
        const event = await resolveBridgeJson(payload, "modelPullProgress");
        const completed = Number(event.completed || 0);
        const total = Number(event.total || 0);
        const percent = total > 0 ? Math.round((completed / total) * 100) : null;
        const suffix = percent === null ? "" : ` (${percent}%)`;
        appendLog(`AI setup: ${event.status || "working"}${suffix}`);
        setupStatusText.textContent = `Setting up local AI ${event.model || runtimeHealth?.ollamaModelName || ""}${suffix}`;
        replaceLastAssistantMessage(`Setting up local AI ${event.model || runtimeHealth?.ollamaModelName || "runtime"}${suffix}.`, {
          title: "System update",
        });
      })().catch((error) => {
        appendLog(`Failed to apply model pull progress: ${error}`);
      });
    });
    bridge.modelPullCompleted.connect((payload) => {
      void (async () => {
        const result = await resolveBridgeJson(payload, "modelPullCompleted");
        appendLog(`AI setup completed for ${result.pull_result?.model_name || "the configured model"}.`);
        addChatMessage("assistant", `Local AI is ready for ${result.pull_result?.model_name || "the configured model"}.`, {
          title: "System update",
        });
        if (result.runtime_health) {
          applyRuntimeGate({ runtimeHealth: result.runtime_health, setupFlow: runtimeSetupFlow });
        }
      })().catch((error) => {
        appendLog(`Failed to apply model pull completion: ${error}`);
      });
    });
    bridge.modelPullFailed.connect((payload) => {
      void (async () => {
        const result = await resolveBridgeJson(payload, "modelPullFailed");
        appendLog(result.message || "AI setup failed.");
        addChatMessage("assistant", result.message || "Local AI setup failed.", {
          title: "System update",
        });
      })().catch((error) => {
        appendLog(`Failed to apply model pull failure: ${error}`);
      });
    });
    bridge.logMessage.connect(appendLog);
    appendLog("[UI] generationCompleted signal connected");
    bridge.generationCompleted.connect((payload) => {
      void (async () => {
        try {
          appendLog("[UI] generationCompleted callback entered");
          appendLog(`[UI] raw payload received: ${typeof payload === "string" ? `${payload.slice(0, 280)}${payload.length > 280 ? "..." : ""}` : String(payload)}`);
          const result = await resolveBridgeJson(payload, "generationCompleted");
          appendLog("[UI] payload parsed successfully");
          appendLog(`[UI] terminal status resolved: status=${result.status || "none"}, generation_id=${result.generation_id || result.generationId || "none"}, request_text=${result.request_text || result.requestText || "none"}`);
          setGenerationInFlight(false);
          appendLog("[UI] generationInFlight cleared");
          await applyTerminalResult(result);
        } catch (error) {
          appendLog(`Failed to apply generation result: ${error}`);
          await handleTerminalFailure(`Desktop result handling failed: ${error}`);
        } finally {
          setGenerationInFlight(false);
          appendLog("[UI] generationInFlight cleared");
        }
      })();
    });
    appendLog("[UI] generationFailed signal connected");
    bridge.generationFailed.connect((message) => {
      appendLog(`[UI] generationFailed callback entered: ${message}`);
      if (!generationInFlight) {
        return;
      }
      void (async () => {
        try {
          await handleTerminalFailure(message, { rawStatus: "bridge_failure_signal", status: "error" });
        } finally {
          setGenerationInFlight(false);
        }
      })();
    });

    appendLog("Debug: requesting initial bridge state.");
    void applyState(bridge.getInitialState()).catch((error) => {
      appendLog(`Failed to load initial backend state: ${error}`);
    });
    appendLog("Desktop shell connected.");
  });
}

bindClick(setupDetectButton, async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    appendLog("Refreshing environment detection.");
    addChatMessage("assistant", "Checking this PC for local AI and Blender.", {
      title: "System update",
    });
    const health = await resolveBridgeJson(bridge.maybeDetectOrRepairEnvironment(), "maybeDetectOrRepairEnvironment");
    applyRuntimeGate({ runtimeHealth: health, setupFlow: runtimeSetupFlow });
  } catch (error) {
    appendLog(`Environment detection failed: ${error}`);
  }
});

bindClick(setupPullButton, async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  const modelName = runtimeHealth?.ollamaModelName || runtimeHealth?.recommendedModel || "";
  try {
    addChatMessage("assistant", `Starting local AI setup for ${modelName || "the configured model"}.`, {
      title: "System update",
    });
    const result = await resolveBridgeJson(bridge.startModelPull(modelName), "startModelPull");
    if (!result.started) {
      appendLog(result.message || "AI setup could not be started.");
      addChatMessage("assistant", result.message || "Local AI setup could not be started.", {
        title: "System update",
      });
      return;
    }
    appendLog(`Starting AI setup for ${result.model_name}.`);
  } catch (error) {
    appendLog(`Failed to start AI setup: ${error}`);
  }
});

bindClick(setupSmokeButton, async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    appendLog("Running setup smoke test.");
    addChatMessage("assistant", "Running a quick local system check.", {
      title: "System update",
    });
    const result = await resolveBridgeJson(bridge.runSetupSmokeTest(), "runSetupSmokeTest");
    appendLog(result.message || "Smoke test finished.");
    addChatMessage("assistant", result.message || "Quick local check finished.", {
      title: "System update",
    });
    if (result.runtime_health) {
      applyRuntimeGate({ runtimeHealth: result.runtime_health, setupFlow: runtimeSetupFlow });
    }
  } catch (error) {
    appendLog(`Smoke test failed: ${error}`);
  }
});

bindClick(setupRefreshButton, async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    appendLog("Refreshing system status.");
    addChatMessage("assistant", "Refreshing system status.", {
      title: "System update",
    });
    const health = await resolveBridgeJson(bridge.getRuntimeHealth(), "getRuntimeHealth");
    applyRuntimeGate({ runtimeHealth: health, setupFlow: runtimeSetupFlow });
    bridge.refreshState();
  } catch (error) {
    appendLog(`System refresh failed: ${error}`);
  }
});

bindClick(generateButton, () => {
  appendLog("[UI] generationStarted path entered");
  const promptText = promptInput.value.trim();
  if (!bridge) {
    appendLog("Debug: submit blocked -> bridge not ready.");
    appendLog("Desktop bridge is not ready.");
    return;
  }
  if (!promptText) {
    appendLog("Debug: submit blocked -> empty prompt.");
    appendLog("Enter a prompt before generating.");
    return;
  }
  if (!runtimeReady()) {
    appendLog("Debug: submit blocked -> runtime setup incomplete.");
    appendLog(runtimeHealth?.runtimeHealthMessage || "Complete local setup before generating.");
    return;
  }
  if (generationInFlight) {
    appendLog("Debug: submit blocked -> generation already in flight.");
    return;
  }

  appendLog("Debug: submit allowed.");
  setGenerationInFlight(true);
  appendLog(`Debug: prompt submit -> ${promptText}`);
  appendLog("Debug: generation start.");
  appendLog(`Prompt submitted: ${promptText}`);
  setSessionTitle(generateSessionTitle(promptText));
  addChatMessage("user", promptText);
  addChatMessage("assistant", "Understanding your request...");
  addChatMessage("assistant", "Preparing deterministic geometry...", {
    title: "Generation in progress",
    checklist: [
      "Understanding your request",
      "Classifying the geometry family",
      "Normalizing dimensions and features",
      "Preparing deterministic geometry",
      "Updating the preview",
    ],
  });
  activeSession = {
    ...createEmptySession(),
    requestText: promptText,
    promptText,
  };
  updateHistoryPanel({
    promptText,
    plan: null,
    validation: null,
    classification: null,
    resultStatus: "generating",
    message: "Interpreting the request, classifying the family, and preparing deterministic geometry.",
    previewStatus: "pending",
  });
  setGenerationStatusText("Generating...");
  setReadinessStateText("Generating the current model for review.");
  updateRightPanel(null, null, "generating");
  updateMetricsFromPlan(null, null, animatedStateLabel("Generating"), "generating");
  viewer.setLoading("Preparing the current model preview.");
  appendLog("Debug: bridge generateModel call start.");
  appendLog(`[UI] typeof bridge.generateModel = ${typeof bridge.generateModel}`);
  if (typeof bridge.generateModel !== "function") {
    appendLog("[UI] bridge.generateModel missing or not callable");
    void handleTerminalFailure("Desktop bridge entrypoint is unavailable.", {
      rawStatus: "bridge_entrypoint_missing",
      status: "error",
      requestText: promptText,
    }).finally(() => {
      setGenerationInFlight(false);
    });
    return;
  }
  try {
    bridge.generateModel(promptText);
  } catch (error) {
    appendLog(`[UI] bridge.generateModel call threw: ${error}`);
    void handleTerminalFailure(`Desktop bridge call failed: ${error}`, {
      rawStatus: "bridge_call_exception",
      status: "error",
      requestText: promptText,
    }).finally(() => {
      setGenerationInFlight(false);
    });
  }
});

bindClick(openBlenderButton, async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    const result = await resolveBridgeJson(bridge.openLatestInBlender(), "openLatestInBlender");
    appendLog(result.message);
  } catch (error) {
    appendLog(`Failed to launch Blender: ${error}`);
  }
});

bindClick(modelsGoWorkspace, () => setActiveTab("workspace"));
bindClick(modelsEmptyCta, () => setActiveTab("workspace"));

bindClick(modelsSelectionOpen, async () => {
  if (!bridge || !modelsSelectionOpen?.dataset.modelId) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    const result = await resolveBridgeJson(bridge.openSavedModelInBlender(modelsSelectionOpen.dataset.modelId), "openSavedModelInBlender");
    appendLog(result.message || "Saved model opened in Blender.");
  } catch (error) {
    appendLog(`Failed to open saved model in Blender: ${error}`);
  }
});

bindClick(modelsSelectionDelete, async () => {
  if (!bridge || !modelsSelectionDelete?.dataset.modelId) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  const model = currentSelectedSavedModel();
  if (!window.confirm(`Delete ${model?.name || "this saved model"} from the local library?`)) {
    return;
  }
  try {
    const result = await resolveBridgeJson(bridge.deleteSavedModel(modelsSelectionDelete.dataset.modelId), "deleteSavedModel");
    appendLog(result.message || "Saved model deleted.");
  } catch (error) {
    appendLog(`Failed to delete saved model: ${error}`);
  }
});

if (promptInput) {
  promptInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      generateButton.click();
    }
  });
}

bindClick(toolbeltImproveButton, () => {
  const currentPrompt = promptInput.value.trim();
  currentPromptSuggestion = buildPromptSuggestion(currentPrompt);
  promptImproverOriginal.textContent = currentPrompt || "No prompt entered yet.";
  promptImproverSuggestion.textContent = currentPromptSuggestion;
  setComposerQuickMenuOpen(false);
  setPromptImproverOpen(true);
});

bindClick(toolbeltSettingsButton, (event) => {
  event.stopPropagation();
  setComposerQuickMenuOpen(composerQuickMenu.hidden);
});

bindClick(quickClearConversationButton, () => {
  setComposerQuickMenuOpen(false);
  startNewChat();
});

bindClick(quickToggleAutoscrollButton, () => {
  autoScrollEnabled = !autoScrollEnabled;
  updateConversationMenuLabels();
  if (autoScrollEnabled) {
    scrollConversationToBottom();
  }
});

bindClick(quickToggleTimestampsButton, () => {
  timestampsEnabled = !timestampsEnabled;
  updateConversationMenuLabels();
  renderConversationThread();
});

bindClick(usePromptSuggestionButton, () => {
  promptInput.value = currentPromptSuggestion || buildPromptSuggestion(promptInput.value.trim());
  setPromptImproverOpen(false);
  promptInput.focus();
});

bindClick(keepOriginalPromptButton, () => {
  setPromptImproverOpen(false);
  promptInput.focus();
});

bindClick(closePromptImproverButton, () => setPromptImproverOpen(false));
bindClick(promptImproverBackdrop, () => setPromptImproverOpen(false));

if (conversationThread) {
  conversationThread.addEventListener("click", (event) => {
    const exampleButton = event.target.closest("[data-example-prompt]");
    if (!exampleButton) {
      return;
    }
    promptInput.value = exampleButton.dataset.examplePrompt || "";
    promptInput.focus();
  });
}

if (modelsSearchInput) {
  modelsSearchInput.addEventListener("input", (event) => {
    modelsSearchQuery = event.target.value || "";
    renderModelsGrid();
  });
}

if (modelsSortSelect) {
  modelsSortSelect.addEventListener("change", (event) => {
    modelsSortMode = event.target.value || "newest";
    renderModelsGrid();
  });
}

if (modelsFamilyFilters) {
  modelsFamilyFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-family-filter]");
    if (!button) {
      return;
    }
    activeModelFamilyFilter = button.dataset.familyFilter || "all";
    renderModelsGrid();
  });
}

if (modelsGrid) {
  modelsGrid.addEventListener("click", async (event) => {
    const selectButton = event.target.closest("[data-model-select]");
    if (selectButton) {
      selectedSavedModelId = selectButton.dataset.modelSelect || "";
      renderModelsGrid();
      return;
    }

    const deleteButton = event.target.closest("[data-model-delete]");
    if (!deleteButton) {
      return;
    }

    if (!bridge) {
      appendLog("Desktop bridge is not ready.");
      return;
    }

    const modelId = deleteButton.dataset.modelDelete || "";
    const model = getNormalizedSavedModels().find((entry) => entry.id === modelId);
    if (!window.confirm(`Delete ${model?.name || "this saved model"} from the local library?`)) {
      return;
    }

    try {
      const result = await resolveBridgeJson(bridge.deleteSavedModel(modelId), "deleteSavedModel");
      appendLog(result.message || "Saved model deleted.");
    } catch (error) {
      appendLog(`Failed to delete saved model: ${error}`);
    }
  });
}

if (modelsSidebarList) {
  modelsSidebarList.addEventListener("click", (event) => {
    const selectButton = event.target.closest("[data-model-select]");
    if (!selectButton) {
      return;
    }
    selectedSavedModelId = selectButton.dataset.modelSelect || "";
    renderModelsGrid();
  });
}

function startNewChat() {
  if (generationInFlight) {
    appendLog("Debug: new chat blocked -> generation already in flight.");
    return;
  }
  appendLog("New chat requested. Active session reset to idle.");
  resetActiveSession({
    reasonText: "New chat started. Submit a prompt to begin a fresh generation.",
    clearPrompt: true,
  });
}

bindClick(newConversationButton, startNewChat);
topnavTabs.forEach((button) => {
  button.addEventListener("click", () => {
    setActiveTab(button.dataset.tab || "workspace");
  });
});

bindClick(showLogsButton, () => setLogsModalOpen(true));
bindClick(closeLogsButton, () => setLogsModalOpen(false));
bindClick(logsBackdrop, () => setLogsModalOpen(false));

document.addEventListener("click", (event) => {
  if (!composerQuickMenu.hidden && !event.target.closest(".composer-toolbelt-group-right")) {
    setComposerQuickMenuOpen(false);
  }
});

async function bootstrap() {
  await viewer.init();
  if (viewer.initialized) {
    viewer.setEmpty();
  }
  setLogsModalOpen(false);
  setPromptImproverOpen(false);
  setComposerQuickMenuOpen(false);
  updateConversationMenuLabels();
  renderModelsGrid();
  setActiveTab("workspace");
  connectBridge();
}

void bootstrap();
