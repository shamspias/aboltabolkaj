import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QFormLayout, QGroupBox, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class CryptoTradeCalculator:
    """
    Encapsulates the calculation logic for crypto trades.
    """

    def __init__(self, investment, buy_price, sell_price, fee_percent=0.10):
        self.investment = investment
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.fee_percent = fee_percent

    def calculate(self):
        """
        Calculate and return trade details as a dictionary.
        """
        # Calculate how much coin is bought
        coin_amount = self.investment / self.buy_price

        # Calculate gross return from selling
        gross_return = coin_amount * self.sell_price

        # Calculate trading fees on both buy and sell
        buy_fee = self.investment * (self.fee_percent / 100)
        sell_fee = gross_return * (self.fee_percent / 100)
        total_fees = buy_fee + sell_fee

        # Net return and profit calculations
        net_return = gross_return - total_fees
        net_profit = net_return - self.investment
        percent_profit = (net_profit / self.investment) * 100

        return {
            "Investment (USDT)": round(self.investment, 2),
            "Buy Price (USD)": round(self.buy_price, 2),
            "Sell Price (USD)": round(self.sell_price, 2),
            "Coins Bought": round(coin_amount, 6),
            "Gross Return (USDT)": round(gross_return, 2),
            "Total Fees (USDT)": round(total_fees, 2),
            "Net Return (USDT)": round(net_return, 2),
            "Net Profit (USDT)": round(net_profit, 2),
            "Profit %": round(percent_profit, 2)
        }


class CalculatorApp(QWidget):
    """
    Main GUI application for iterative monthly crypto trade calculations.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monthly Crypto Trade Calculator")
        self.setGeometry(100, 100, 600, 500)

        # Track the current month and investment
        self.month_count = 0
        self.current_investment = None

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # Title label
        title_label = QLabel("Crypto Trade Calculator (Monthly Iterations)")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        # Input fields
        self.investment_input = QLineEdit()
        self.investment_input.setPlaceholderText("e.g., 1000")

        self.buy_price_input = QLineEdit()
        self.buy_price_input.setPlaceholderText("e.g., 86000")

        self.sell_price_input = QLineEdit()
        self.sell_price_input.setPlaceholderText("e.g., 94000")

        self.fee_input = QLineEdit()
        self.fee_input.setPlaceholderText("Default is 0.10 (%)")

        # Group box for inputs
        inputs_group = QGroupBox("Trade Inputs")
        inputs_layout = QFormLayout()
        inputs_layout.addRow(QLabel("Investment (USDT):"), self.investment_input)
        inputs_layout.addRow(QLabel("Buy Price (USD):"), self.buy_price_input)
        inputs_layout.addRow(QLabel("Sell Price (USD):"), self.sell_price_input)
        inputs_layout.addRow(QLabel("Fee Percent (%):"), self.fee_input)
        inputs_group.setLayout(inputs_layout)

        # Buttons
        self.calculate_button = QPushButton("Calculate Next Month")
        self.calculate_button.clicked.connect(self.calculate_next_month)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_calculator)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.calculate_button)
        button_layout.addWidget(self.reset_button)

        # Result display area
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(QFont("Courier", 10))

        # Group box for results
        results_group = QGroupBox("Calculation Results (Cumulative)")
        results_layout = QVBoxLayout()
        results_layout.addWidget(self.result_display)
        results_group.setLayout(results_layout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(inputs_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(results_group)

        self.setLayout(main_layout)

    def apply_styles(self):
        # A stylesheet with better contrast and a subtle gray background
        self.setStyleSheet("""
            QWidget {
                background-color: #F3F4F6; /* Light gray background */
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 14px;
                color: #333333; /* Default text color */
            }
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                top: 5px;
            }
            QLabel {
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:hover {
                border: 1px solid #999999;
            }
            QLineEdit:placeholderText {
                color: #777777;
            }
            QPushButton {
                background-color: #0078D7;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                margin: 10px 0;
            }
            QPushButton:hover {
                background-color: #005EA6;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
            }
        """)

    def calculate_next_month(self):
        """
        Each press simulates the next month:
        - Uses current investment if not the first month,
          or reads from user input for the first month.
        - Calculates net return.
        - Updates investment field to net return for the next iteration.
        - Appends results to the text area with a 'Month X' header.
        """
        try:
            # If first calculation, read investment from input field
            if self.month_count == 0:
                self.current_investment = float(self.investment_input.text())

            buy_price = float(self.buy_price_input.text())
            sell_price = float(self.sell_price_input.text())
            fee_text = self.fee_input.text().strip()
            fee_percent = float(fee_text) if fee_text else 0.10

            # Validate inputs
            if (self.current_investment is None or self.current_investment <= 0 or
                    buy_price <= 0 or sell_price <= 0 or fee_percent < 0):
                raise ValueError("All numeric inputs must be positive.")

            # Perform calculation
            calculator = CryptoTradeCalculator(self.current_investment, buy_price, sell_price, fee_percent)
            result = calculator.calculate()

            # Increment the month counter
            self.month_count += 1

            # Append result to the text display
            month_header = f"Month {self.month_count} Results:"
            result_text = "\n".join(f"{key}: {value}" for key, value in result.items())
            display_text = f"{month_header}\n{result_text}\n{'-' * 30}\n"
            self.result_display.append(display_text)

            # Update current investment to the net return for the next month
            new_investment = result["Net Return (USDT)"]
            self.current_investment = new_investment

            # Reflect the updated investment in the input field
            self.investment_input.setText(str(new_investment))

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {e}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {ex}")

    def reset_calculator(self):
        """
        Resets the month count, current investment, input fields,
        and the results display area.
        """
        self.month_count = 0
        self.current_investment = None
        self.investment_input.clear()
        self.buy_price_input.clear()
        self.sell_price_input.clear()
        self.fee_input.clear()
        self.result_display.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec_())
