import json
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
VIEWER_FRAMING_JS = ROOT / "desktop" / "ui" / "viewer_framing.js"


def run_viewer_framing_script(expression: str) -> dict:
    script = f"""
import {{ pathToFileURL }} from 'node:url';
const moduleUrl = pathToFileURL({json.dumps(str(VIEWER_FRAMING_JS))}).href;
const {{ computeViewerFrame }} = await import(moduleUrl);
const result = {expression};
console.log(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout.strip())


class ViewerFramingTests(unittest.TestCase):
    def test_small_object_frames_closer_than_a_larger_object(self):
        small = run_viewer_framing_script(
            "computeViewerFrame({ size: { x: 0.12, y: 0.04, z: 0.08 }, center: { x: 0, y: 0.02, z: 0 }, aspect: 1.4, fovDegrees: 42, previewKind: 'phone_stand' })"
        )
        large = run_viewer_framing_script(
            "computeViewerFrame({ size: { x: 1.2, y: 0.7, z: 2.0 }, center: { x: 0, y: 0.35, z: 0 }, aspect: 1.4, fovDegrees: 42, previewKind: 'enclosure' })"
        )

        self.assertGreater(small["distance"], 0.4)
        self.assertLess(small["distance"], large["distance"])
        self.assertAlmostEqual(small["target"]["x"], 0.0)
        self.assertAlmostEqual(small["target"]["y"], 0.02)
        self.assertAlmostEqual(small["target"]["z"], 0.0)
        self.assertLess(small["near"], small["far"])

    def test_frame_math_preserves_center_as_orbit_target(self):
        frame = run_viewer_framing_script(
            "computeViewerFrame({ size: { x: 0.8, y: 0.6, z: 0.5 }, center: { x: 1.5, y: 0.8, z: -0.4 }, aspect: 1.6, fovDegrees: 42, previewKind: 'bracket' })"
        )

        self.assertAlmostEqual(frame["target"]["x"], 1.5)
        self.assertAlmostEqual(frame["target"]["y"], 0.8)
        self.assertAlmostEqual(frame["target"]["z"], -0.4)
        self.assertGreater(frame["radius"], 0.0)
        self.assertGreater(frame["far"], frame["near"])


if __name__ == "__main__":
    unittest.main()
