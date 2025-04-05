import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt


class SliceCalculator:
    def __init__(self, img_width, img_height, slice_width, slice_height, overlap_percent):
        self.img_width = img_width
        self.img_height = img_height
        self.slice_width = slice_width
        self.slice_height = slice_height
        self.overlap_percent = overlap_percent / 100

    def calculate(self, horizontal=True, vertical=True):
        stride_w = self.slice_width * (1 - self.overlap_percent)
        stride_h = self.slice_height * (1 - self.overlap_percent)

        num_slices_horizontal = (
            int((self.img_width - self.slice_width) / stride_w) + 1 if horizontal else 1
        )
        num_slices_vertical = (
            int((self.img_height - self.slice_height) / stride_h) + 1 if vertical else 1
        )

        total_slices = num_slices_horizontal * num_slices_vertical

        return num_slices_horizontal, num_slices_vertical, total_slices


class SliceCalcApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Slice Calculator')
        self.setFixedWidth(400)

        layout = QVBoxLayout()

        # Inputs
        self.img_width_input = QLineEdit('13252')
        self.img_height_input = QLineEdit('4686')
        self.slice_width_input = QLineEdit('500')
        self.slice_height_input = QLineEdit('500')
        self.overlap_input = QLineEdit('10')

        layout.addLayout(self._create_input_layout('Image Width:', self.img_width_input))
        layout.addLayout(self._create_input_layout('Image Height:', self.img_height_input))
        layout.addLayout(self._create_input_layout('Slice Width:', self.slice_width_input))
        layout.addLayout(self._create_input_layout('Slice Height:', self.slice_height_input))
        layout.addLayout(self._create_input_layout('Overlap (%):', self.overlap_input))

        # Checkboxes for horizontal/vertical slices
        self.horizontal_checkbox = QCheckBox('Horizontal Slices')
        self.horizontal_checkbox.setChecked(True)
        self.vertical_checkbox = QCheckBox('Vertical Slices')
        self.vertical_checkbox.setChecked(True)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.horizontal_checkbox)
        checkbox_layout.addWidget(self.vertical_checkbox)
        layout.addLayout(checkbox_layout)

        # Calculate Button
        calc_btn = QPushButton('Calculate')
        calc_btn.clicked.connect(self.perform_calculation)
        layout.addWidget(calc_btn)

        self.result_label = QLabel('Enter values and click Calculate')
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def _create_input_layout(self, label_text, widget):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(120)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def perform_calculation(self):
        try:
            img_w = int(self.img_width_input.text())
            img_h = int(self.img_height_input.text())
            slice_w = int(self.slice_width_input.text())
            slice_h = int(self.slice_height_input.text())
            overlap = float(self.overlap_input.text())

            if not (0 <= overlap < 100):
                raise ValueError('Overlap percentage must be between 0 and 100.')

            horizontal = self.horizontal_checkbox.isChecked()
            vertical = self.vertical_checkbox.isChecked()

            calculator = SliceCalculator(img_w, img_h, slice_w, slice_h, overlap)
            hor_slices, ver_slices, total_slices = calculator.calculate(horizontal, vertical)

            self.result_label.setText(
                f'Horizontal slices: {hor_slices}\n'
                f'Vertical slices: {ver_slices}\n'
                f'Total slices: {total_slices}'
            )

        except ValueError as e:
            QMessageBox.warning(self, 'Input Error', str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SliceCalcApp()
    ex.show()
    sys.exit(app.exec_())
