import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "desktop" / "ui" / "app.js"


class ViewerOrientationTests(unittest.TestCase):
    def test_preview_load_does_not_apply_extra_orientation_correction(self):
        source = APP_JS.read_text(encoding="utf-8")
        self.assertIn("this.previewObject = loadedObject;", source)
        self.assertNotIn("this.normalizeRestingOrientation(this.previewObject", source)

