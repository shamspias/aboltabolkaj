import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout
)


class TradingCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Profit Calculator")
        self.setFixedSize(400, 400)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # Input labels and fields
        labels = [
            "Current Price (USDT):",
            "Target Profit (%):",
            "Max Loss (%):",
            "Capital (USDT):",
            "Leverage (x):"
        ]
        self.inputs = []

        for i, text in enumerate(labels):
            label = QLabel(text)
            input_field = QLineEdit()
            layout.addWidget(label, i, 0)
            layout.addWidget(input_field, i, 1)
            self.inputs.append(input_field)

        # Output labels
        self.output_labels = {
            "Take-Profit Price:": QLabel(""),
            "Stop-Loss Price:": QLabel(""),
            "Position Size:": QLabel(""),
            "Profit if Hit Target:": QLabel(""),
            "Loss if Hit Stop:": QLabel("")
        }

        for i, (key, val) in enumerate(self.output_labels.items(), start=6):
            layout.addWidget(QLabel(key), i, 0)
            layout.addWidget(val, i, 1)

        # Calculate button
        calc_button = QPushButton("Calculate")
        calc_button.clicked.connect(self.calculate)
        layout.addWidget(calc_button, 11, 0, 1, 2)

        self.setLayout(layout)

    def calculate(self):
        try:
            price = float(self.inputs[0].text())
            target_pct = float(self.inputs[1].text())
            loss_pct = float(self.inputs[2].text())
            capital = float(self.inputs[3].text())
            leverage = float(self.inputs[4].text())

            position_size = capital * leverage
            take_profit_price = price * (1 + target_pct / 100)
            stop_loss_price = price * (1 - loss_pct / 100)

            profit = position_size * (target_pct / 100)
            loss = position_size * (loss_pct / 100)

            self.output_labels["Take-Profit Price:"].setText(f"{take_profit_price:.2f} USDT")
            self.output_labels["Stop-Loss Price:"].setText(f"{stop_loss_price:.2f} USDT")
            self.output_labels["Position Size:"].setText(f"{position_size:.2f} USDT")
            self.output_labels["Profit if Hit Target:"].setText(f"{profit:.2f} USDT")
            self.output_labels["Loss if Hit Stop:"].setText(f"{loss:.2f} USDT")

        except ValueError:
            for val in self.output_labels.values():
                val.setText("Invalid input")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingCalculator()
    window.show()
    sys.exit(app.exec_())
