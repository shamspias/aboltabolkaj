import sys
import requests
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QGridLayout, QFileDialog, QComboBox, QMessageBox
)


class TradingCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Profit Calculator")
        self.setFixedSize(450, 600)
        # Track current theme
        self.theme = "dark"
        # Initialize UI
        self.init_ui()
        # Start with dark theme
        self.apply_dark_theme()

    def init_ui(self):
        """Create all UI elements and arrange them in a grid layout."""
        main_layout = QGridLayout()

        # Input fields: 7 lines (6 QLineEdits + 1 QComboBox)
        labels = [
            "Current Price (USDT):",
            "Target Profit (%):",
            "Max Loss (%):",
            "Capital (USDT):",
            "Leverage (x):",
            "Platform Fee (round trip %):",
            "Position Type:"
        ]

        self.inputs = []

        # Create QLineEdits for the first 6 items
        for i, label_text in enumerate(labels[:-1]):
            label = QLabel(label_text)
            input_field = QLineEdit()
            main_layout.addWidget(label, i, 0)
            main_layout.addWidget(input_field, i, 1)
            self.inputs.append(input_field)

        # Create a QComboBox for position (Long/Short)
        self.position_type = QComboBox()
        self.position_type.addItems(["Long", "Short"])
        main_layout.addWidget(QLabel(labels[-1]), len(labels) - 1, 0)
        main_layout.addWidget(self.position_type, len(labels) - 1, 1)

        # Output labels
        self.output_labels = {
            "Take-Profit Price:": QLabel(),
            "Stop-Loss Price:": QLabel(),
            "Position Size:": QLabel(),
            "Profit if Hit Target (After Fee):": QLabel(),
            "Loss if Hit Stop (After Fee):": QLabel(),
            "Liquidation Price:": QLabel()
        }

        row_offset = 7
        for i, (key, lbl) in enumerate(self.output_labels.items()):
            main_layout.addWidget(QLabel(key), row_offset + i, 0)
            main_layout.addWidget(lbl, row_offset + i, 1)

        # Buttons (Fetch Price, Calculate, Export, Theme Toggle)
        btn_fetch = QPushButton("Fetch BTC Price")
        btn_fetch.clicked.connect(self.fetch_btc_price)
        main_layout.addWidget(btn_fetch, row_offset + len(self.output_labels), 0, 1, 2)

        btn_calculate = QPushButton("Calculate")
        btn_calculate.clicked.connect(self.calculate)
        main_layout.addWidget(btn_calculate, row_offset + len(self.output_labels) + 1, 0, 1, 2)

        btn_export = QPushButton("Export to Text File")
        btn_export.clicked.connect(self.export_results)
        main_layout.addWidget(btn_export, row_offset + len(self.output_labels) + 2, 0, 1, 2)

        btn_theme = QPushButton("Toggle Light/Dark Theme")
        btn_theme.clicked.connect(self.toggle_theme)
        main_layout.addWidget(btn_theme, row_offset + len(self.output_labels) + 3, 0, 1, 2)

        self.setLayout(main_layout)

    def fetch_btc_price(self):
        """Fetch the latest BTC/USDT price from Binance API and populate the Current Price field."""
        try:
            response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
            response.raise_for_status()
            price_data = response.json()
            price = float(price_data["price"])
            self.inputs[0].setText(f"{price:.2f}")
        except Exception:
            # If there's any error, show 'Error' in the field
            self.inputs[0].setText("Error")

    def calculate(self):
        """Perform all trading calculations (TP, SL, Liq Price, fees, etc.) and update the output labels."""
        try:
            # Unpack input fields
            price = float(self.inputs[0].text())
            target_pct = float(self.inputs[1].text())
            loss_pct = float(self.inputs[2].text())
            capital = float(self.inputs[3].text())
            leverage = float(self.inputs[4].text())
            fee_pct = float(self.inputs[5].text())  # round trip fee in %
            position = self.position_type.currentText()

            if leverage <= 0:
                leverage = 1

            # Core calculations
            position_size = capital * leverage

            if position == "Long":
                take_profit_price = price * (1 + target_pct / 100)
                stop_loss_price = price * (1 - loss_pct / 100)
                liquidation_price = price * (1 - 1 / leverage)
            else:
                take_profit_price = price * (1 - target_pct / 100)
                stop_loss_price = price * (1 + loss_pct / 100)
                liquidation_price = price * (1 + 1 / leverage)

            # Gross PnL (before fees)
            gross_profit = position_size * (target_pct / 100)
            gross_loss = position_size * (loss_pct / 100)

            # Net PnL after fees
            #   - We'll assume fee_pct is total round-trip % on the notional (position_size).
            fee_cost = position_size * (fee_pct / 100)
            net_profit = gross_profit - fee_cost
            net_loss = gross_loss + fee_cost

            # Check stop-loss validity:
            # For a Long, we must have stop_loss_price > liquidation_price
            # For a Short, we must have stop_loss_price < liquidation_price
            if position == "Long" and stop_loss_price <= liquidation_price:
                self.show_error_message(
                    "Invalid Stop-Loss",
                    "Stop-loss is at or below liquidation price!\n"
                    "Increase your max loss percentage or reduce leverage."
                )
                return
            elif position == "Short" and stop_loss_price >= liquidation_price:
                self.show_error_message(
                    "Invalid Stop-Loss",
                    "Stop-loss is at or above liquidation price!\n"
                    "Increase your max loss percentage or reduce leverage."
                )
                return

            # If stop-loss is valid, update output fields
            self.output_labels["Take-Profit Price:"].setText(f"{take_profit_price:.2f} USDT")
            self.output_labels["Stop-Loss Price:"].setText(f"{stop_loss_price:.2f} USDT")
            self.output_labels["Position Size:"].setText(f"{position_size:.2f} USDT")
            self.output_labels["Profit if Hit Target (After Fee):"].setText(f"{net_profit:.2f} USDT")
            self.output_labels["Loss if Hit Stop (After Fee):"].setText(f"{net_loss:.2f} USDT")
            self.output_labels["Liquidation Price:"].setText(f"{liquidation_price:.2f} USDT")

        except ValueError:
            # If any field is invalid, set outputs to 'Invalid input'
            for lbl in self.output_labels.values():
                lbl.setText("Invalid input")

    def export_results(self):
        """Export the current output results to a text file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            f"trading_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if file_name:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write("Trading Calculation Results:\n")
                for key, label in self.output_labels.items():
                    file.write(f"{key} {label.text()}\n")

    def toggle_theme(self):
        """Switch between dark and light themes."""
        if self.theme == "dark":
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply a sleek dark theme using style sheets."""
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

    def apply_light_theme(self):
        """Apply a clean light theme."""
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

    def show_error_message(self, title: str, message: str):
        """Display a modal error dialog with a given title and message."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingCalculator()
    window.show()
    sys.exit(app.exec_())
