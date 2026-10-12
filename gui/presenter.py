from core.processor import Processor
from gui.main_window import MainWindow


class StickerPresenter:
    def __init__(self, view: MainWindow, processor: Processor):
        self.view = view
        self.processor = processor

    def export(self, destination, file_format, elements):
        """Apply a current panel snapshot before exporting."""
        panel = self.view.output_settings
        output = panel.get_output_data()
        self.processor.set_output_data(
            output.width, output.height, output.dpi, output.unit, output.color,
        )
        # Keep dieline and bleed DPI in sync with the output.
        self.processor.set_output_dpi(output.dpi)
        return self.processor.export_all(
            destination, file_format, elements, resize=panel.resize.isChecked(),
        )
