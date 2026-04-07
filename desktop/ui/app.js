let bridge = null;
let THREE = null;
let OrbitControls = null;
let GLTFLoader = null;

const promptInput = document.getElementById("prompt-input");
const generateButton = document.getElementById("generate-button");
const openBlenderButton = document.getElementById("open-blender-button");
const backendStatus = document.getElementById("backend-status");
const lastRunStatus = document.getElementById("last-run-status");
const scriptPath = document.getElementById("script-path");
const logOutput = document.getElementById("log-output");
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

function appendLog(message) {
  const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const line = `[${timestamp}] ${message}`;
  logOutput.textContent = `${logOutput.textContent}\n${line}`.trim();
  logOutput.scrollTop = logOutput.scrollHeight;
}

function formatMm(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "Unavailable";
  }
  return `${Number(value.toFixed(2)).toString()} mm`;
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
  metricVolume.innerHTML = volume ? `${Number(volume.toFixed(1)).toString()} cm&sup3;` : "Unavailable";
  metricWall.textContent = wallMetricFromPlan(plan);
  metricTriangles.textContent = "Unavailable";
  metricQuality.textContent = validation?.warnings?.length ? "Review" : "Alpha";
  generationStatus.textContent = generationText || "Ready";
}

function renderListRows(container, items, formatter) {
  if (!items.length) {
    container.innerHTML = '<div class="check-row"><span class="checkmark">&#9672;</span><span>Unavailable</span></div>';
    return;
  }
  container.innerHTML = items.map(formatter).join("");
}

function updateRightPanel(plan) {
  const dimensions = dimensionEntries(plan);
  renderListRows(
    currentModelDimensions,
    dimensions,
    ([label, value]) => `<div class="check-row"><span class="checkmark">&#9672;</span><span>${label}: ${formatMm(value)}</span></div>`
  );

  const shellItems = featureEntries(plan).filter(([key]) => key.includes("thickness") || key.includes("wall") || key.includes("base"));
  renderListRows(
    currentModelShell,
    shellItems,
    ([key, value]) => `<div class="check-row"><span class="checkmark">&#9672;</span><span>${prettifyKey(key)}: ${key.endsWith("_mm") ? formatMm(value) : formatTextValue(value)}</span></div>`
  );

  const featureItems = featureEntries(plan).filter(([key]) => !key.includes("thickness") && !key.includes("wall") && !key.includes("base") && !key.includes("hole"));
  renderListRows(
    currentModelFeatures,
    featureItems,
    ([key, value]) => `<div class="check-row"><span class="checkmark">&#9672;</span><span>${prettifyKey(key)}: ${key.endsWith("_mm") ? formatMm(value) : formatTextValue(value)}</span></div>`
  );

  const cutoutItems = featureEntries(plan).filter(([key]) => key.includes("hole") || key.includes("opening") || key.includes("cutout"));
  renderListRows(
    currentModelCutouts,
    cutoutItems,
    ([key, value]) => `<div class="check-row"><span class="checkmark">&#10003;</span><span>${prettifyKey(key)}: ${key.endsWith("_mm") ? formatMm(value) : formatTextValue(value)}</span></div>`
  );
}

function updateHistoryPanel({ promptText = "", plan = null, validation = null, classification = null, resultStatus = "", message = "", previewStatus = "" }) {
  historyUserPrompt.textContent = promptText || "No prompt submitted yet.";
  historyPlanState.textContent = validation?.summary
    || message
    || "Waiting for a backend generation result.";

  const summaryLines = toSummaryLines(plan, validation, classification, resultStatus, previewStatus);
  historySummaryList.innerHTML = summaryLines.length
    ? summaryLines.map((item) => `<li>${item}</li>`).join("")
    : "<li>No normalized backend summary available yet.</li>";

  historyResultTitle.textContent = resultStatus === "ready" ? "Generation succeeded" : "Generation state";
  historyResultText.textContent = resultStatus === "ready"
    ? (validation?.summary || "Model script generated successfully.")
    : (message || "Waiting for a completed generation result.");
}

function applyBackendSnapshot({ promptText = "", plan = null, validation = null, classification = null, resultStatus = "", message = "", previewStatus = "", previewMessage = "" }) {
  updateHistoryPanel({ promptText, plan, validation, classification, resultStatus, message, previewStatus });
  updateRightPanel(plan);
  updateMetricsFromPlan(plan, validation, resultStatus === "ready" ? "Generation complete" : (resultStatus || "Ready"));
  readinessState.textContent = validation?.summary || message || previewMessage || "Ready for export and Blender handoff.";
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

function getPromptPreviewKind(promptText = "", plan = null) {
  if (plan?.family) {
    if (plan.family === "enclosure" || plan.family === "housing_shell") {
      return "enclosure";
    }
    if (plan.family === "bracket") {
      return "bracket";
    }
    if (plan.family === "gear") {
      return "gear";
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
  if (normalized.includes("gear")) {
    return "gear";
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
    this.animationFrame = 0;
    this.resizeObserver = null;
    this.lastPreviewKey = "";
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
    this.scene.fog = new THREE.Fog(0xf4f6f6, 10, 24);

    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200);
    this.camera.position.set(5.6, 4.4, 6.8);

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
    this.controls.target.set(0, 0.6, 0);

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

    const floorPlane = new THREE.Mesh(
      new THREE.CircleGeometry(6.8, 64),
      new THREE.ShadowMaterial({ color: 0x79848a, opacity: 0.12 })
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = -0.65;
    floorPlane.receiveShadow = true;
    this.rootGroup.add(floorPlane);

    const grid = new THREE.GridHelper(12, 24, 0xd4dbdd, 0xe7ecec);
    grid.position.y = -0.64;
    grid.material.opacity = 0.48;
    grid.material.transparent = true;
    this.rootGroup.add(grid);

    const axes = new THREE.AxesHelper(1.5);
    axes.position.set(-4.6, -0.62, 4.2);
    this.rootGroup.add(axes);

    this.bindControls();
    this.setInteractionMode("orbit");
    this.setRenderMode("solid");
    this.resize();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(viewerRenderSurface);
    this.initialized = true;
    this.animate();
    setViewerOverlay(
      "empty",
      "Viewer ready",
      "Generate a model to preview it here. Future backend preview assets will load into this same viewer."
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
    if (this.previewObject) {
      this.previewObject.rotation.y += 0.0025;
    }
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
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

  createGearShape(teeth = 18, outerRadius = 1.45, innerRadius = 1.15) {
    const shape = new THREE.Shape();
    const points = [];
    const total = teeth * 2;
    for (let index = 0; index < total; index += 1) {
      const angle = (index / total) * Math.PI * 2;
      const radius = index % 2 === 0 ? outerRadius : innerRadius;
      points.push(new THREE.Vector2(Math.cos(angle) * radius, Math.sin(angle) * radius));
    }
    shape.moveTo(points[0].x, points[0].y);
    points.slice(1).forEach((point) => shape.lineTo(point.x, point.y));
    shape.closePath();

    const hole = new THREE.Path();
    hole.absellipse(0, 0, 0.42, 0.42, 0, Math.PI * 2, false, 0);
    shape.holes.push(hole);
    return shape;
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
    } else if (previewKind === "gear") {
      const gear = new THREE.Mesh(
        new THREE.ExtrudeGeometry(this.createGearShape(), { depth: 0.48, bevelEnabled: false }),
        this.createMaterial(0xf2f4f5)
      );
      gear.geometry.center();
      gear.rotation.x = Math.PI / 2;
      gear.castShadow = true;
      group.add(gear);
      group.rotation.x = -0.42;
      group.rotation.y = 0.4;
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

  fitCameraToObject(object3D) {
    if (!object3D || !this.camera || !this.controls || !THREE) {
      return;
    }
    const box = new THREE.Box3().setFromObject(object3D);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z, 1);
    const distance = maxDimension * 2.25;
    this.camera.position.set(center.x + distance, center.y + distance * 0.72, center.z + distance);
    this.controls.target.copy(center);
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
    this.camera.position.set(5.6, 4.4, 6.8);
    this.controls.target.set(0, 0.6, 0);
    this.controls.update();
    if (this.previewObject) {
      this.fitCameraToObject(this.previewObject);
    }
  }

  async tryLoadExternalPreview(previewModelPath) {
    if (!GLTFLoader || !previewModelPath) {
      return null;
    }
    const previewUrl = toFileUrl(previewModelPath) || previewModelPath;
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

  async loadPreview({ promptText = "", plan = null, previewModelPath = "", previewKey = "" }) {
    if (!this.initialized) {
      return;
    }
    if (previewKey && previewKey === this.lastPreviewKey) {
      return;
    }

    setViewerOverlay("loading", "Loading preview", "Preparing the viewer scene for the current model.");
    this.clearPreview();

    let loadedObject = null;
    if (previewModelPath) {
      try {
        loadedObject = await this.tryLoadExternalPreview(previewModelPath);
      } catch (error) {
        appendLog(`Preview asset load failed, falling back to procedural preview: ${error}`);
      }
    }

    this.previewObject = loadedObject || this.buildPreviewGroup({ promptText, plan });
    this.rootGroup.add(this.previewObject);
    this.setRenderMode(this.renderMode);
    this.fitCameraToObject(this.previewObject);
    this.lastPreviewKey = previewKey;
    setViewerOverlay("ready", "", "");
  }

  setError(message) {
    setViewerOverlay("error", "Viewer error", message);
  }

  setEmpty() {
    this.clearPreview();
    this.lastPreviewKey = "";
    setViewerOverlay(
      "empty",
      "No preview yet",
      "Submit a prompt to generate a model preview. The alpha viewer will render a preview here when data is available."
    );
  }

  setLoading(message) {
    setViewerOverlay("loading", "Generating preview", message);
  }
}

const viewer = new GeomancerViewer();

function applyState(rawState) {
  const state = JSON.parse(rawState);
  backendStatus.textContent = `${state.appName} v${state.version}`;
  lastRunStatus.textContent = state.lastRunStatus || "Idle";
  scriptPath.textContent = state.generatedScriptPath || "Unavailable";
  footerVersion.textContent = `v${state.version}`;
  generationStatus.textContent = state.lastGenerationStatus || state.lastRunStatus || "Ready for preview";

  applyBackendSnapshot({
    promptText: state.lastUserRequest || "",
    plan: state.lastPlan || null,
    validation: state.lastValidation || null,
    classification: state.lastClassification || null,
    resultStatus: state.lastGenerationStatus || "",
    message: state.lastGenerationMessage || "",
    previewStatus: state.previewExportStatus || "",
    previewMessage: state.previewExportMessage || "",
  });

  if (state.lastUserRequest && viewer.initialized && !viewer.previewObject) {
    void viewer.loadPreview({
      promptText: state.lastUserRequest,
      plan: state.lastPlan || null,
      previewModelPath: state.previewModelPath || "",
      previewKey: `${state.generatedScriptPath || state.lastUserRequest}-${state.lastGenerationTimestamp || "initial"}`,
    });
  }
}

function setGenerating(isGenerating) {
  generateButton.disabled = isGenerating;
  generateButton.textContent = isGenerating ? "..." : "->";
}

function connectBridge() {
  if (typeof qt === "undefined") {
    appendLog("Qt bridge unavailable. This UI is intended for the desktop shell.");
    return;
  }

  new QWebChannel(qt.webChannelTransport, (channel) => {
    bridge = channel.objects.geomancerBridge;
    bridge.stateChanged.connect(applyState);
    bridge.logMessage.connect(appendLog);
    bridge.generationCompleted.connect((payload) => {
      const result = JSON.parse(payload);
      appendLog(`Generation finished with status: ${result.status}`);
      setGenerating(false);
      applyBackendSnapshot({
        promptText: promptInput.value.trim(),
        plan: result.plan || null,
        validation: result.validation || null,
        classification: result.classification || null,
        resultStatus: result.status || "",
        message: result.message || "",
        previewStatus: result.preview_export_status || "",
        previewMessage: result.preview_export_message || "",
      });

      if (result.status === "ready") {
        void viewer.loadPreview({
          promptText: promptInput.value.trim(),
          plan: result.plan || null,
          previewModelPath: result.preview_model_path || result.previewModelPath || "",
          previewKey: `${result.script_path || promptInput.value.trim()}-${Date.now()}`,
        });
      } else {
        viewer.setError(result.message || "The generated result could not be previewed.");
      }
    });
    bridge.generationFailed.connect((message) => {
      appendLog(`Generation failed: ${message}`);
      historyResultTitle.textContent = "Generation failed";
      historyResultText.textContent = message;
      generationStatus.textContent = "Generation failed";
      readinessState.textContent = "Resolve the prompt or runtime issue before export.";
      viewer.setError(message);
      setGenerating(false);
    });

    applyState(bridge.getInitialState());
    appendLog("Desktop shell connected.");
  });
}

generateButton.addEventListener("click", () => {
  const promptText = promptInput.value.trim();
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  if (!promptText) {
    appendLog("Enter a prompt before generating.");
    return;
  }

  setGenerating(true);
  appendLog(`Prompt submitted: ${promptText}`);
  updateHistoryPanel({
    promptText,
    plan: null,
    validation: null,
    classification: null,
    resultStatus: "generating",
    message: "Planning request, classifying family, normalizing parameters, and preparing deterministic generation.",
    previewStatus: "pending",
  });
  generationStatus.textContent = "Generating...";
  readinessState.textContent = "Waiting for generation before export or Blender handoff.";
  updateRightPanel(null);
  updateMetricsFromPlan(null, null, "Generating...");
  historySummaryList.innerHTML = [
    "Prompt received",
    "Family classification pending",
    "Normalized parameters pending",
    "Viewer update pending",
  ].map((item) => `<li>${item}</li>`).join("");
  viewer.setLoading("Waiting for generation output before previewing the current model.");
  bridge.generateModel(promptText);
});

openBlenderButton.addEventListener("click", () => {
  if (!bridge) {
    appendLog("Desktop bridge is not ready.");
    return;
  }
  const result = JSON.parse(bridge.openLatestInBlender());
  appendLog(result.message);
});

promptInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    generateButton.click();
  }
});

async function bootstrap() {
  await viewer.init();
  if (viewer.initialized) {
    viewer.setEmpty();
  }
  connectBridge();
}

void bootstrap();
