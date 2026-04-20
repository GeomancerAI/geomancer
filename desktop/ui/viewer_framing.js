const FRAMING_PROFILES = Object.freeze({
  enclosure: { direction: [1.0, 0.72, 1.04], multiplier: 1.16 },
  planter: { direction: [1.0, 0.72, 1.04], multiplier: 1.14 },
  bracket: { direction: [1.06, 0.6, 0.86], multiplier: 1.08 },
  clip: { direction: [1.06, 0.6, 0.86], multiplier: 1.1 },
  cylinder: { direction: [0.96, 0.68, 1.0], multiplier: 1.08 },
  panel: { direction: [0.42, 0.98, 1.08], multiplier: 1.14 },
  sphere: { direction: [0.92, 0.76, 0.96], multiplier: 1.08 },
  block: { direction: [0.96, 0.68, 1.0], multiplier: 1.1 },
});

function toFiniteNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function normalizeDirection(direction, fallback = [1, 0.7, 1]) {
  const x = toFiniteNumber(direction?.[0], fallback[0]);
  const y = toFiniteNumber(direction?.[1], fallback[1]);
  const z = toFiniteNumber(direction?.[2], fallback[2]);
  const length = Math.hypot(x, y, z);
  if (!Number.isFinite(length) || length <= 1e-6) {
    return { x: fallback[0], y: fallback[1], z: fallback[2] };
  }
  return { x: x / length, y: y / length, z: z / length };
}

function getProfile(previewKind = "block") {
  return FRAMING_PROFILES[previewKind] || FRAMING_PROFILES.block;
}

export function computeViewerFrame({
  size = {},
  center = {},
  aspect = 1,
  fovDegrees = 42,
  previewKind = "block",
} = {}) {
  const width = Math.max(toFiniteNumber(size.x, 0), 0.001);
  const height = Math.max(toFiniteNumber(size.y, 0), 0.001);
  const depth = Math.max(toFiniteNumber(size.z, 0), 0.001);
  const safeAspect = Math.max(toFiniteNumber(aspect, 1), 0.1);
  const vfov = (Math.max(toFiniteNumber(fovDegrees, 42), 5) * Math.PI) / 180;
  const hfov = 2 * Math.atan(Math.tan(vfov / 2) * safeAspect);
  const radius = Math.max(Math.hypot(width, height, depth) / 2, width * 0.5, height * 0.5, depth * 0.5, 0.02);
  const fitHeightDistance = height / (2 * Math.tan(vfov / 2));
  const fitWidthDistance = Math.max(width, depth) / (2 * Math.tan(hfov / 2));
  const fitSphereDistance = radius / Math.sin(vfov / 2);
  const profile = getProfile(previewKind);
  const distance = clamp(
    Math.max(fitHeightDistance, fitWidthDistance, fitSphereDistance, radius * 2.2, 0.25) * profile.multiplier,
    0.45,
    24
  );

  return {
    distance,
    direction: normalizeDirection(profile.direction),
    target: {
      x: toFiniteNumber(center.x, 0),
      y: toFiniteNumber(center.y, 0),
      z: toFiniteNumber(center.z, 0),
    },
    near: Math.max(distance / 220, 0.001),
    far: Math.max(distance * 14, 20),
    fitHeightDistance,
    fitWidthDistance,
    fitSphereDistance,
    radius,
    size: { x: width, y: height, z: depth },
  };
}
