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
        coin_amount = self.investment / self.buy_price
        gross_return = coin_amount * self.sell_price

        buy_fee = self.investment * (self.fee_percent / 100)
        sell_fee = gross_return * (self.fee_percent / 100)
        total_fees = buy_fee + sell_fee

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
        self.setGeometry(100, 100, 680, 600)

        # Track the current month, cumulative additional investment, and additional cost
        self.month_count = 0
        self.additional_investment_count = 0
        self.additional_cost_count = 0
        self.current_investment = None

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # 1. Title
        title_label = QLabel("Crypto Trade Calculator (Monthly Iterations)")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        # 2. Inputs Group Box
        self.investment_input = QLineEdit()
        self.investment_input.setPlaceholderText("e.g., 1000")

        self.buy_price_input = QLineEdit()
        self.buy_price_input.setPlaceholderText("e.g., 86000")

        self.sell_price_input = QLineEdit()
        self.sell_price_input.setPlaceholderText("e.g., 94000")

        self.fee_input = QLineEdit()
        self.fee_input.setPlaceholderText("Default is 0.10 (%)")

        self.additional_investment_input = QLineEdit()
        self.additional_investment_input.setPlaceholderText("Add extra funds each month (e.g., 200)")

        self.additional_cost_input = QLineEdit()
        self.additional_cost_input.setPlaceholderText("Monthly cost (e.g., 50)")

        inputs_group = QGroupBox("Trade Inputs")
        inputs_layout = QFormLayout()
        inputs_layout.addRow(QLabel("Investment (USDT):"), self.investment_input)
        inputs_layout.addRow(QLabel("Buy Price (USD):"), self.buy_price_input)
        inputs_layout.addRow(QLabel("Sell Price (USD):"), self.sell_price_input)
        inputs_layout.addRow(QLabel("Fee Percent (%):"), self.fee_input)
        inputs_layout.addRow(QLabel("Additional Investment (USDT):"), self.additional_investment_input)
        inputs_layout.addRow(QLabel("Additional Cost (USDT):"), self.additional_cost_input)
        inputs_group.setLayout(inputs_layout)

        # 3. Buttons
        self.calculate_button = QPushButton("Calculate Next Month")
        self.calculate_button.clicked.connect(self.calculate_next_month)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_calculator)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.calculate_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()

        # 4. Statistics Group Box
        self.month_label = QLabel("0")
        self.additional_investment_label = QLabel("0")
        self.additional_cost_label = QLabel("0")

        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()
        stats_layout.addRow(QLabel("Month Count:"), self.month_label)
        stats_layout.addRow(QLabel("A. Investment Count:"), self.additional_investment_label)
        stats_layout.addRow(QLabel("A. Cost Count:"), self.additional_cost_label)
        stats_group.setLayout(stats_layout)

        # 5. Results Group Box
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(QFont("Courier", 10))

        results_group = QGroupBox("Calculation Results (Cumulative)")
        results_layout = QVBoxLayout()
        results_layout.addWidget(self.result_display)
        results_group.setLayout(results_layout)

        # 6. Main Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(inputs_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(stats_group)
        main_layout.addWidget(results_group)

        self.setLayout(main_layout)

    def apply_styles(self):
        """
        Stylesheet for a cleaner, modern look.
        """
        self.setStyleSheet("""
            QWidget {
                background-color: #F3F4F6; /* Light gray background */
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 14px;
                color: #333333;
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
                margin: 10px;
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
        1. If first month, read investment from the input field.
        2. Add 'Additional Investment' to current investment.
        3. Perform calculation.
        4. Subtract 'Additional Cost' from the net return.
        5. Update counters and display results.
        6. Set the base investment for the next month.
        """
        try:
            # For the first calculation, read the initial investment
            if self.month_count == 0:
                self.current_investment = float(self.investment_input.text())

            buy_price = float(self.buy_price_input.text())
            sell_price = float(self.sell_price_input.text())
            fee_text = self.fee_input.text().strip()
            fee_percent = float(fee_text) if fee_text else 0.10

            # Parse additional investment and cost
            add_invest_text = self.additional_investment_input.text().strip()
            additional_investment = float(add_invest_text) if add_invest_text else 0.0

            add_cost_text = self.additional_cost_input.text().strip()
            additional_cost = float(add_cost_text) if add_cost_text else 0.0

            # Validate inputs
            if (self.current_investment is None or self.current_investment < 0 or
                    buy_price <= 0 or sell_price <= 0 or fee_percent < 0 or
                    additional_investment < 0 or additional_cost < 0):
                raise ValueError("All numeric inputs must be non-negative (and buy/sell > 0).")

            # Add the additional investment for this month
            self.current_investment += additional_investment

            # Perform the trade calculation
            calculator = CryptoTradeCalculator(self.current_investment, buy_price, sell_price, fee_percent)
            result = calculator.calculate()

            # Increment counters
            self.month_count += 1
            self.month_label.setText(str(self.month_count))

            self.additional_investment_count += additional_investment
            self.additional_investment_label.setText(str(self.additional_investment_count))

            self.additional_cost_count += additional_cost
            self.additional_cost_label.setText(str(self.additional_cost_count))

            # Append results to the display
            month_header = f"Month {self.month_count} Results:"
            result_text = "\n".join(f"{key}: {value}" for key, value in result.items())
            display_text = f"{month_header}\n{result_text}\n{'-' * 40}\n"
            self.result_display.append(display_text)

            # Update current investment for next month by subtracting the additional cost
            new_investment = result["Net Return (USDT)"] - additional_cost
            self.current_investment = new_investment
            self.investment_input.setText(str(new_investment))

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {e}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {ex}")

    def reset_calculator(self):
        """
        Resets all counters, investment values, and clears input/output fields.
        """
        self.month_count = 0
        self.additional_investment_count = 0
        self.additional_cost_count = 0
        self.current_investment = None

        self.investment_input.clear()
        self.buy_price_input.clear()
        self.sell_price_input.clear()
        self.fee_input.clear()
        self.additional_investment_input.clear()
        self.additional_cost_input.clear()
        self.result_display.clear()

        self.month_label.setText("0")
        self.additional_investment_label.setText("0")
        self.additional_cost_label.setText("0")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorApp()
    window.show()
    sys.exit(app.exec_())
