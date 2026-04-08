let bridge = null;
let THREE = null;
let OrbitControls = null;
let GLTFLoader = null;

const promptInput = document.getElementById("prompt-input");
const generateButton = document.getElementById("generate-button");
const openBlenderButton = document.getElementById("open-blender-button");
const backendStatus = document.getElementById("backend-status");
const lastRunStatus = document.getElementById("last-run-status");
const systemAiStatus = document.getElementById("system-ai-status");
const systemBlenderStatus = document.getElementById("system-blender-status");
const scriptPath = document.getElementById("script-path");
const logOutput = document.getElementById("log-output");
const logsModal = document.getElementById("logs-modal");
const logsBackdrop = document.getElementById("logs-backdrop");
const showLogsButton = document.getElementById("show-logs-button");
const closeLogsButton = document.getElementById("close-logs-button");
const footerVersion = document.getElementById("footer-version");
const metricLength = document.getElementById("metric-length");
const metricWidth = document.getElementById("metric-width");
const metricHeight = document.getElementById("metric-height");
const metricVolume = document.getElementById("metric-volume");
const metricWall = document.getElementById("metric-wall");
const metricTriangles = document.getElementById("metric-triangles");
const metricQuality = document.getElementById("metric-quality");
const historyUserPrompt = document.getElementById("history-user-prompt");
const historyPlanState = document.getElementById("history-plan-state");
const historySummaryList = document.getElementById("history-summary-list");
const historyResultTitle = document.getElementById("history-result-title");
const historyResultText = document.getElementById("history-result-text");
const generationStatus = document.getElementById("generation-status");
const readinessState = document.getElementById("readiness-state");
const currentModelDimensions = document.getElementById("current-model-dimensions");
const currentModelShell = document.getElementById("current-model-shell");
const currentModelFeatures = document.getElementById("current-model-features");
const currentModelCutouts = document.getElementById("current-model-cutouts");
const setupWizard = document.getElementById("setup-wizard");
const setupStatusTitle = document.getElementById("setup-status-title");
const setupStatusText = document.getElementById("setup-status-text");
const setupSteps = document.getElementById("setup-steps");
const setupDetectButton = document.getElementById("setup-detect-button");
const setupPullButton = document.getElementById("setup-pull-button");
const setupSmokeButton = document.getElementById("setup-smoke-button");
const setupRefreshButton = document.getElementById("setup-refresh-button");
const setupHelpText = document.getElementById("setup-help-text");
const footerRuntimePrimary = document.getElementById("footer-runtime-primary");
const footerRuntimeSecondary = document.getElementById("footer-runtime-secondary");

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
const newConversationButton = document.getElementById("new-conversation-button");
const topnavTabs = Array.from(document.querySelectorAll(".topnav-tab"));
let generationInFlight = false;
let activeSession = createEmptySession();
let librarySummary = { saved_model_count: 0, recent_saved_models: [], project_count: 0, template_count: 0, templates: [] };
let hasLoadedInitialState = false;
let runtimeHealth = null;
let runtimeSetupFlow = [];

const TAB_INTENTS = {
  chat: "Active generation workspace",
  models: "Saved generated model library",
  projects: "Grouped model organization",
  templates: "Starter creations and capability examples",
};

function appendLog(message) {
  const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const line = `[${timestamp}] ${message}`;
  logOutput.textContent = `${logOutput.textContent}\n${line}`.trim();
  logOutput.scrollTop = logOutput.scrollHeight;
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

function wallMetricFromPlan(plan) {
  const features = plan?.features || {};
  const keys = ["wall_thickness_mm", "base_thickness_mm", "thickness_mm"];
  for (const key of keys) {
    if (typeof features[key] === "number") {
      return formatMm(features[key]);
    }
  }
  return "Unavailable";
}

function updateMetricsFromPlan(plan, validation, generationText) {
  const dims = plan?.dimensions || {};
  metricLength.textContent = formatMm(
    dims.length_mm || dims.width_mm || dims.base_length_mm || dims.large_diameter_mm || dims.outer_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null
  );
  metricWidth.textContent = formatMm(
    dims.width_mm || dims.depth_mm || dims.flange_width_mm || dims.small_diameter_mm || dims.clip_width_mm || dims.base_width_mm || null
  );
  metricHeight.textContent = formatMm(
    dims.height_mm || dims.vertical_height_mm || dims.length_mm || dims.base_height_mm || null
  );
  const volume = estimateVolumeCm3(plan);
  metricVolume.innerHTML = volume ? `Approx. ${Number(volume.toFixed(1)).toString()} cm&sup3;` : "Unavailable";
  metricWall.textContent = wallMetricFromPlan(plan);
  metricTriangles.textContent = "Not measured";
  metricQuality.textContent = validation?.warnings?.length ? "Needs review" : (plan ? "Structured" : "Review needed");
  generationStatus.textContent = generationText || "Ready";
}

function renderListRows(container, items, formatter, emptyText = "Unavailable") {
  if (!items.length) {
    container.innerHTML = `<div class="check-row"><span class="checkmark">&#9672;</span><span>${emptyText}</span></div>`;
    return;
  }
  container.innerHTML = items.map(formatter).join("");
}

function updateRightPanel(plan) {
  const dimensions = dimensionEntries(plan);
  renderListRows(
    currentModelDimensions,
    dimensions,
    ([label, value]) => `<div class="check-row"><span class="checkmark">&#9672;</span><span>${label}: ${formatMm(value)}</span></div>`,
    "Unavailable until a generation completes"
  );

  const shellItems = featureEntries(plan).filter(([key]) => key.includes("thickness") || key.includes("wall") || key.includes("base"));
  renderListRows(
    currentModelShell,
    shellItems,
    ([key, value]) => `<div class="check-row"><span class="checkmark">&#9672;</span><span>${prettifyKey(key)}: ${key.endsWith("_mm") ? formatMm(value) : formatTextValue(value)}</span></div>`,
    "No shell information yet"
  );

  const featureItems = featureEntries(plan).filter(([key]) => !key.includes("thickness") && !key.includes("wall") && !key.includes("base") && !key.includes("hole"));
  renderListRows(
    currentModelFeatures,
    featureItems,
    ([key, value]) => `<div class="check-row"><span class="checkmark">&#9672;</span><span>${prettifyKey(key)}: ${key.endsWith("_mm") ? formatMm(value) : formatTextValue(value)}</span></div>`,
    "No feature details yet"
  );

  const cutoutItems = featureEntries(plan).filter(([key]) => key.includes("hole") || key.includes("opening") || key.includes("cutout"));
  renderListRows(
    currentModelCutouts,
    cutoutItems,
    ([key, value]) => `<div class="check-row"><span class="checkmark">&#10003;</span><span>${prettifyKey(key)}: ${key.endsWith("_mm") ? formatMm(value) : formatTextValue(value)}</span></div>`,
    "No openings or holes recorded yet"
  );
}

function updateHistoryPanel({ promptText = "", plan = null, validation = null, classification = null, resultStatus = "", message = "", previewStatus = "" }) {
  historyUserPrompt.textContent = promptText || "No prompt yet. Describe a supported part to start a generation.";
  historyPlanState.textContent = validation?.summary
    || message
    || "Geomancer is waiting for a prompt.";

  const summaryLines = toSummaryLines(plan, validation, classification, resultStatus, previewStatus);
  historySummaryList.innerHTML = summaryLines.length
    ? summaryLines.map((item) => `<li>${item}</li>`).join("")
    : "<li>No geometry summary is available yet.</li>";

  historyResultTitle.textContent = resultStatus === "ready" ? "Latest result" : "Status";
  historyResultText.textContent = resultStatus === "ready"
    ? (validation?.summary || "Generation finished. Review the parsed dimensions and features before Blender handoff.")
    : (message || "Generation results will appear here.");
}

function applyBackendSnapshot({ promptText = "", plan = null, validation = null, classification = null, resultStatus = "", message = "", previewStatus = "", previewMessage = "" }) {
  updateHistoryPanel({ promptText, plan, validation, classification, resultStatus, message, previewStatus });
  updateRightPanel(plan);
  updateMetricsFromPlan(plan, validation, resultStatus === "ready" ? "Generation complete" : (resultStatus || "Ready"));
  readinessState.textContent = validation?.summary || message || previewMessage || "Review the current model here, then open it in Blender for local editing.";
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
      readinessState.textContent = terminalViewerMessage(result);
    }

    if (result.previewStatus === "error") {
      historyResultTitle.textContent = "Preview needs review";
      historyResultText.textContent = terminalViewerMessage(result);
      readinessState.textContent = terminalViewerMessage(result);
    }
    return;
  }

  generationStatus.textContent = terminalStatusLabel(result.status);
  historyResultTitle.textContent = terminalStatusLabel(result.status);
  historyResultText.textContent = terminalViewerMessage(result);
  readinessState.textContent = terminalViewerMessage(result);
  viewer.setError(terminalViewerMessage(result));
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
  historyUserPrompt.textContent = "No active prompt.";
  historyPlanState.textContent = reasonText;
  historySummaryList.innerHTML = [
    "No current generation",
    "Viewer is waiting for a model",
    "Prompt box is ready",
    `Saved models available: ${librarySummary.saved_model_count || 0}`,
  ].map((item) => `<li>${item}</li>`).join("");
  historyResultTitle.textContent = "Latest result";
  historyResultText.textContent = "Run a prompt to generate a model and fill the workspace with real dimensions and features.";
  updateRightPanel(null);
  updateMetricsFromPlan(null, null, "Idle");
  readinessState.textContent = "Submit a dimensional prompt to start a new local generation.";
}

function resetActiveSession(options = {}) {
  const { reasonText = "Start a new generation when ready.", clearPrompt = true } = options;
  activeSession = createEmptySession();
  setGenerationInFlight(false);
  if (clearPrompt) {
    promptInput.value = "";
  }
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
    readinessState.textContent = normalizedHealth.runtimeHealthMessage || "Finish local setup before generating.";
    generationStatus.textContent = "Setup required";
  }

  backendStatus.textContent = ready ? "Ready" : sentenceCaseStatus(normalizedHealth.runtimeHealthStatus || "setup_required");
  systemAiStatus.textContent = aiReady ? "Ready" : (normalizedHealth.ollamaInstalled ? "Setup needed" : "Not ready");
  systemBlenderStatus.textContent = blenderReady ? "Detected" : "Not configured";
  footerRuntimePrimary.textContent = aiReady
    ? `AI ready: ${normalizedHealth.ollamaModelName || normalizedHealth.recommendedModel || "configured"}`
    : (normalizedHealth.ollamaInstalled ? "AI setup in progress" : "AI not set up");
  footerRuntimeSecondary.textContent = blenderReady
    ? (ready ? "Blender ready for handoff" : "Blender detected")
    : "Blender not configured";
}

function updatePassiveShellState(state) {
  librarySummary = state.librarySummary || librarySummary;
  lastRunStatus.textContent = sentenceCaseStatus(state.lastRunStatus || "Idle");
  scriptPath.textContent = state.generatedScriptPath || "Unavailable";
  footerVersion.textContent = `v${state.version}`;
  applyRuntimeGate(state);
}

function setActiveTab(tabName) {
  topnavTabs.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === tabName);
  });
  appendLog(`Tab selected: ${tabName} -> ${TAB_INTENTS[tabName] || "Unknown role"}`);
}

function setViewerOverlay(mode, title, text) {
  viewerOverlay.classList.toggle("is-visible", mode !== "ready");
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
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.rootGroup = null;
    this.previewObject = null;
    this.contactShadow = null;
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
    this.controls.minDistance = 1.2;
    this.controls.maxDistance = 30;
    this.controls.target.set(0, 0.78, 0);

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

    const axes = new THREE.AxesHelper(1.35);
    axes.position.set(-4.95, 0.03, 4.55);
    this.rootGroup.add(axes);

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
    viewerModeSolid.addEventListener("click", () => this.setRenderMode("solid"));
    viewerModeWireframe.addEventListener("click", () => this.setRenderMode("wireframe"));
    viewerToolOrbit.addEventListener("click", () => this.setInteractionMode("orbit"));
    viewerToolPan.addEventListener("click", () => this.setInteractionMode("pan"));
    viewerToolZoom.addEventListener("click", () => this.setInteractionMode("zoom"));
    viewerFocusButton.addEventListener("click", () => this.focusObject());
    viewerResetButton.addEventListener("click", () => this.resetView());
  }

  animate() {
    this.animationFrame = window.requestAnimationFrame(() => this.animate());
    if (this.controls) {
      this.controls.update();
    }
    this.updateAxisIndicator();
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
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
    if (!viewerAxisScene || !this.camera || !THREE) {
      return;
    }
    const quaternion = this.camera.quaternion.clone().invert();
    const directions = [
      { selector: ".axis-x", vector: new THREE.Vector3(1, 0, 0) },
      { selector: ".axis-y", vector: new THREE.Vector3(0, 1, 0) },
      { selector: ".axis-z", vector: new THREE.Vector3(0, 0, 1) },
    ];
    directions.forEach(({ selector, vector }) => {
      const axis = viewerAxisScene.querySelector(selector);
      if (!axis) {
        return;
      }
      const projected = vector.clone().applyQuaternion(quaternion);
      const angle = Math.atan2(projected.y, projected.x);
      const depthWeight = (projected.z + 1) / 2;
      const length = 18 + depthWeight * 10;
      axis.style.transform = `rotate(${angle}rad) scaleX(${length / 30})`;
      axis.style.opacity = `${0.38 + depthWeight * 0.58}`;
      axis.style.zIndex = `${Math.round(depthWeight * 10)}`;
    });
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

  buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, upIndex, upSign, label) {
    const axes = principalFrame.axes.map((axis) => axis.clone());
    const up = axes[upIndex].multiplyScalar(upSign).normalize();
    const remaining = [0, 1, 2]
      .filter((index) => index !== upIndex)
      .sort((left, right) => principalFrame.values[right] - principalFrame.values[left]);
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
    const principalFrame = this.computePrincipalAxesFrame(object3D);
    return [
      this.buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, 0, 1, "+X up"),
      this.buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, 0, -1, "-X up"),
      this.buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, 1, 1, "+Y up"),
      this.buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, 1, -1, "-Y up"),
      this.buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, 2, 1, "+Z up"),
      this.buildPoseCandidateFromPrincipalFrame(principalFrame, baseQuaternion, 2, -1, "-Z up"),
    ];
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
    const score = (supportRatio * 1.8)
      + (footprintBalance * 1.2)
      + (heightReadability * 0.95)
      + (silhouetteSpread * 0.55)
      + (horizontalOccupancy * 0.45);

    return {
      candidate,
      quaternion: candidate.quaternion.clone(),
      box: groundedBox.clone(),
      supportFootprint: footprint,
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
    this.updateContactShadow(placedSupportFootprint || placedBox, placedBox);
    return { box: placedBox, supportFootprint: placedSupportFootprint };
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
    const sliceHeight = THREE.MathUtils.clamp(size.y * 0.14, 0.05, 0.24);
    const supportCeiling = measuredBox.min.y + sliceHeight;
    let minX = Infinity;
    let maxX = -Infinity;
    let minZ = Infinity;
    let maxZ = -Infinity;
    let weightedX = 0;
    let weightedZ = 0;
    let weightTotal = 0;
    let samples = 0;
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
        if (worldVertex.y > supportCeiling + 1e-4) {
          continue;
        }
        const normalizedHeight = Math.max(0, Math.min(1, (worldVertex.y - measuredBox.min.y) / sliceHeight));
        const weight = 1 - normalizedHeight * 0.72;
        minX = Math.min(minX, worldVertex.x);
        maxX = Math.max(maxX, worldVertex.x);
        minZ = Math.min(minZ, worldVertex.z);
        maxZ = Math.max(maxZ, worldVertex.z);
        weightedX += worldVertex.x * weight;
        weightedZ += worldVertex.z * weight;
        weightTotal += weight;
        samples += 1;
      }
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
      samples,
    };
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
    const footprintX = Math.max(baseFootprintX, boxSize.x * 0.16);
    const footprintZ = Math.max(baseFootprintZ, boxSize.z * 0.16);
    this.contactShadow.scale.set(footprintX * 0.5, footprintZ * 0.5, 1);
    this.contactShadow.material.opacity = THREE.MathUtils.clamp(0.085 + Math.min(footprintX, footprintZ) * 0.02, 0.085, 0.17);
    this.contactShadow.position.set((bounds.minX + bounds.maxX) / 2, 0.0025, (bounds.minZ + bounds.maxZ) / 2);
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

    setViewerOverlay("loading", "Building preview", "Setting the current model in place.");
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
    setViewerOverlay("ready", "", "");
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
      })().catch((error) => {
        appendLog(`Failed to apply model pull progress: ${error}`);
      });
    });
    bridge.modelPullCompleted.connect((payload) => {
      void (async () => {
        const result = await resolveBridgeJson(payload, "modelPullCompleted");
        appendLog(`AI setup completed for ${result.pull_result?.model_name || "the configured model"}.`);
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

setupDetectButton.addEventListener("click", async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    appendLog("Refreshing environment detection.");
    const health = await resolveBridgeJson(bridge.maybeDetectOrRepairEnvironment(), "maybeDetectOrRepairEnvironment");
    applyRuntimeGate({ runtimeHealth: health, setupFlow: runtimeSetupFlow });
  } catch (error) {
    appendLog(`Environment detection failed: ${error}`);
  }
});

setupPullButton.addEventListener("click", async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  const modelName = runtimeHealth?.ollamaModelName || runtimeHealth?.recommendedModel || "";
  try {
    const result = await resolveBridgeJson(bridge.startModelPull(modelName), "startModelPull");
    if (!result.started) {
      appendLog(result.message || "AI setup could not be started.");
      return;
    }
    appendLog(`Starting AI setup for ${result.model_name}.`);
  } catch (error) {
    appendLog(`Failed to start AI setup: ${error}`);
  }
});

setupSmokeButton.addEventListener("click", async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    appendLog("Running setup smoke test.");
    const result = await resolveBridgeJson(bridge.runSetupSmokeTest(), "runSetupSmokeTest");
    appendLog(result.message || "Smoke test finished.");
    if (result.runtime_health) {
      applyRuntimeGate({ runtimeHealth: result.runtime_health, setupFlow: runtimeSetupFlow });
    }
  } catch (error) {
    appendLog(`Smoke test failed: ${error}`);
  }
});

setupRefreshButton.addEventListener("click", async () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  try {
    appendLog("Refreshing system status.");
    const health = await resolveBridgeJson(bridge.getRuntimeHealth(), "getRuntimeHealth");
    applyRuntimeGate({ runtimeHealth: health, setupFlow: runtimeSetupFlow });
    bridge.refreshState();
  } catch (error) {
    appendLog(`System refresh failed: ${error}`);
  }
});

generateButton.addEventListener("click", () => {
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
  generationStatus.textContent = "Generating...";
  readinessState.textContent = "Generating the current model for review.";
  updateRightPanel(null);
  updateMetricsFromPlan(null, null, "Generating...");
  historySummaryList.innerHTML = [
    "Prompt received",
    "Family selection in progress",
    "Dimensions and features pending",
    "Viewer update pending",
  ].map((item) => `<li>${item}</li>`).join("");
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

openBlenderButton.addEventListener("click", async () => {
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

promptInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    generateButton.click();
  }
});

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

newConversationButton.addEventListener("click", startNewChat);
topnavTabs.forEach((button) => {
  button.addEventListener("click", () => {
    setActiveTab(button.dataset.tab || "chat");
  });
});

showLogsButton.addEventListener("click", () => setLogsModalOpen(true));
closeLogsButton.addEventListener("click", () => setLogsModalOpen(false));
logsBackdrop.addEventListener("click", () => setLogsModalOpen(false));

async function bootstrap() {
  await viewer.init();
  if (viewer.initialized) {
    viewer.setEmpty();
  }
  setLogsModalOpen(false);
  setActiveTab("chat");
  connectBridge();
}

void bootstrap();
