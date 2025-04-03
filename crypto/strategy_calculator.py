import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QComboBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from datetime import datetime


class TradingCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Profit Calculator")
        self.setFixedSize(450, 550)
        self.init_ui()
        self.set_dark_theme()

    def init_ui(self):
        layout = QGridLayout()

        labels = [
            "Current Price (USDT):",
            "Target Profit (%):",
            "Max Loss (%):",
            "Capital (USDT):",
            "Leverage (x):",
            "Position Type:"
        ]

        self.inputs = []

        for i, text in enumerate(labels[:-1]):
            label = QLabel(text)
            input_field = QLineEdit()
            layout.addWidget(label, i, 0)
            layout.addWidget(input_field, i, 1)
            self.inputs.append(input_field)

        # Position type dropdown
        self.position_type = QComboBox()
        self.position_type.addItems(["Long", "Short"])
        layout.addWidget(QLabel(labels[-1]), len(labels) - 1, 0)
        layout.addWidget(self.position_type, len(labels) - 1, 1)

        # Output labels
        self.output_labels = {
            "Take-Profit Price:": QLabel(""),
            "Stop-Loss Price:": QLabel(""),
            "Position Size:": QLabel(""),
            "Profit if Hit Target:": QLabel(""),
            "Loss if Hit Stop:": QLabel(""),
            "Liquidation Price:": QLabel("")
        }

        for i, (key, val) in enumerate(self.output_labels.items(), start=6):
            layout.addWidget(QLabel(key), i, 0)
            layout.addWidget(val, i, 1)

        # Buttons
        fetch_button = QPushButton("Fetch BTC Price")
        fetch_button.clicked.connect(self.fetch_btc_price)
        layout.addWidget(fetch_button, 12, 0, 1, 2)

        calc_button = QPushButton("Calculate")
        calc_button.clicked.connect(self.calculate)
        layout.addWidget(calc_button, 13, 0, 1, 2)

        export_button = QPushButton("Export to Text File")
        export_button.clicked.connect(self.export_results)
        layout.addWidget(export_button, 14, 0, 1, 2)

        theme_button = QPushButton("Toggle Light/Dark Theme")
        theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_button, 15, 0, 1, 2)

        self.setLayout(layout)

    def fetch_btc_price(self):
        try:
            response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
            price = float(response.json()['price'])
            self.inputs[0].setText(f"{price:.2f}")
        except Exception as e:
            self.inputs[0].setText("Error")

    def calculate(self):
        try:
            price = float(self.inputs[0].text())
            target_pct = float(self.inputs[1].text())
            loss_pct = float(self.inputs[2].text())
            capital = float(self.inputs[3].text())
            leverage = float(self.inputs[4].text())
            position = self.position_type.currentText()

            position_size = capital * leverage
            take_profit_price = price * (1 + target_pct / 100) if position == "Long" else price * (1 - target_pct / 100)
            stop_loss_price = price * (1 - loss_pct / 100) if position == "Long" else price * (1 + loss_pct / 100)
            profit = position_size * (target_pct / 100)
            loss = position_size * (loss_pct / 100)

            if position == "Long":
                liquidation_price = price * (1 - 1 / leverage)
            else:
                liquidation_price = price * (1 + 1 / leverage)

            self.output_labels["Take-Profit Price:"].setText(f"{take_profit_price:.2f} USDT")
            self.output_labels["Stop-Loss Price:"].setText(f"{stop_loss_price:.2f} USDT")
            self.output_labels["Position Size:"].setText(f"{position_size:.2f} USDT")
            self.output_labels["Profit if Hit Target:"].setText(f"{profit:.2f} USDT")
            self.output_labels["Loss if Hit Stop:"].setText(f"{loss:.2f} USDT")
            self.output_labels["Liquidation Price:"].setText(f"{liquidation_price:.2f} USDT")

        except ValueError:
            for val in self.output_labels.values():
                val.setText("Invalid input")

    def export_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Results",
                                                   f"trading_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                                   "Text Files (*.txt)")
        if file_name:
            with open(file_name, "w") as file:
                file.write("Trading Calculation Results:\n")
                for key, label in self.output_labels.items():
                    file.write(f"{key} {label.text()}\n")

    def set_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #ffffff;
                font-family: Arial;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton {
                background-color: #2d89ef;
                border: none;
                padding: 6px 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e5cb3;
            }
        """)
        self.theme = "dark"

    def set_light_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #000000;
                font-family: Arial;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d7;
                border: none;
                padding: 6px 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.theme = "light"

    def toggle_theme(self):
        if getattr(self, 'theme', 'dark') == 'dark':
            self.set_light_theme()
        else:
            self.set_dark_theme()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingCalculator()
    window.show()
    sys.exit(app.exec_())
