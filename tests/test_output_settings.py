import os
import unittest
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication

from core.output_setting import MAX_OUTPUT_DIMENSION_PX, UnitType
from gui.main_window import MainWindow
from gui.presenter import StickerPresenter
from gui.widgets.output_setting import OutputSettingPanel
from utils.units import px_to_mm


class OutputSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.panel = OutputSettingPanel()
        self.addCleanup(self.panel.close)

    def test_resize_retains_dimensions(self):
        self.assertFalse(self.panel.width.isEnabled())
        self.assertFalse(self.panel.height.isEnabled())
        self.panel.resize.setChecked(True)
        self.panel.width.setValue(3000)
        self.panel.height.setValue(1500)
        self.panel.resize.setChecked(False)
        self.panel.unit.setCurrentIndex(self.panel.unit.findData(UnitType.MM))
        self.assertEqual(self.panel.width.value(), 254)
        self.panel.resize.setChecked(True)
        self.assertTrue(self.panel.width.isEnabled())
        self.assertTrue(self.panel.height.isEnabled())
        self.assertEqual(self.panel.get_output_data().get_size_px(), (3000, 1500))

    def test_unit_and_dpi_changes_do_not_drift(self):
        self.panel.width.setValue(3000)
        self.panel.height.setValue(1739)
        for _ in range(5):
            for dpi in (72, 144, 300, 350, 600):
                self.panel.resolution.setCurrentIndex(self.panel.resolution.findData(dpi))
                self.panel.unit.setCurrentIndex(self.panel.unit.findData(UnitType.MM))
                self.assertAlmostEqual(self.panel.width.value(), px_to_mm(3000, dpi), places=6)
                self.assertEqual(self.panel.width.decimals(), 6)
                self.panel.unit.setCurrentIndex(self.panel.unit.findData(UnitType.PX))
                self.assertEqual(self.panel.width.decimals(), 0)
                self.assertEqual(self.panel.width.value(), 3000)
                self.assertEqual(self.panel.get_output_data().get_size_px(), (3000, 1739))

    def test_fractional_mm_and_typed_bounds(self):
        self.panel.resize.setChecked(True)
        self.panel.unit.setCurrentIndex(self.panel.unit.findData(UnitType.MM))
        self.panel.width.setValue(12.345)
        self.assertEqual(self.panel.get_output_data().width, 146)
        for dpi in (72, 144, 300, 350, 600):
            self.panel.resolution.setCurrentIndex(self.panel.resolution.findData(dpi))
            for text, expected in [('0.000001', 1), ('99999999', MAX_OUTPUT_DIMENSION_PX)]:
                for field, attribute in [(self.panel.width, 'width'), (self.panel.height, 'height')]:
                    if expected == 1:
                        field.lineEdit().setText(text)
                        field.interpretText()
                    else:
                        field.setValue(float(text))
                    self.assertEqual(getattr(self.panel.get_output_data(), attribute), expected)
        self.panel.unit.setCurrentIndex(self.panel.unit.findData(UnitType.PX))
        self.assertEqual(self.panel.width.minimum(), 1)
        self.assertEqual(self.panel.width.maximum(), MAX_OUTPUT_DIMENSION_PX)

    def test_one_notification_and_independent_snapshot(self):
        changes = []
        self.panel.settings_changed.connect(lambda output, resize: changes.append((output, resize)))
        self.panel.width.setValue(3000)
        snapshot = changes[-1][0]
        for action in [
            lambda: self.panel.unit.setCurrentIndex(1),
            lambda: self.panel.resolution.setCurrentIndex(4),
            lambda: self.panel.resize.setChecked(True),
            lambda: self.panel.height.setValue(25.4),
        ]:
            before = len(changes)
            action()
            self.assertEqual(len(changes), before + 1)
        self.assertEqual(snapshot.get_size_px(), (3000, 1))
        self.assertIsInstance(snapshot.width, int)

    def test_presenter_applies_snapshot_and_resize(self):
        window = MainWindow()
        self.addCleanup(window.close)
        processor = Mock()
        presenter = StickerPresenter(window, processor)
        window.output_settings.width.setValue(3000)
        for resize in (False, True):
            window.output_settings.resize.setChecked(resize)
            presenter.export('destination', 'format', {'base'})
            processor.set_output_data.assert_called_with(3000, 1, 300, UnitType.PX, window.output_settings.get_output_data().color)
            processor.set_output_dpi.assert_called_with(300)
            processor.export_all.assert_called_with('destination', 'format', {'base'}, resize=resize)


if __name__ == '__main__':
    unittest.main()
