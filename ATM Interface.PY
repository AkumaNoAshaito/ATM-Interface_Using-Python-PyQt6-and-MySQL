from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QDialog, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt
import mysql.connector
import sys

class Account:
    def __init__(self, user_id, pin, balance=0):
        self.user_id = user_id
        self.pin = pin
        self.balance = balance
    def log_transaction(self, transaction_type, amount):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s)"
            values = (self.user_id, transaction_type, amount)
            print("Executing query:", query)  
            print("With values:", values)  
            cursor.execute(query, values)
            conn.commit()
            print("Transaction successfully committed!")  
            cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 1;")
            print("Last inserted transaction:", cursor.fetchone())
            conn.close()
        except Exception as e:
            print("Error logging transaction:", e)  


    @staticmethod
    def get_db_connection():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Your Password",
            database="atm_db"
        )

    @classmethod
    def load_account(cls, user_id):
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, pin, balance FROM accounts WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return cls(result[0], result[1], result[2])
        return None

    def save_account(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (user_id, pin, balance) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE balance=%s",
                       (self.user_id, self.pin, self.balance, self.balance))
        conn.commit()
        conn.close()

    def check_pin(self, pin):
        return self.pin == pin

    def deposit(self, amount):
        self.balance += amount
        self.update_balance()
        self.log_transaction("Deposit", amount)
        return f"Balance: ₹{self.balance:.2f}"


    def withdraw(self, amount):
        if amount > self.balance:
            return 'Insufficient balance'
        self.balance -= amount
        self.update_balance()
        self.log_transaction("Withdraw", amount)
        return f"Balance: ₹{self.balance:.2f}"


    def update_balance(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = %s WHERE user_id = %s", (self.balance, self.user_id))
        conn.commit()
        conn.close()

    def get_transaction_history(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type, amount, timestamp FROM transactions WHERE user_id = %s ORDER BY timestamp DESC",
                       (self.user_id,))
        transactions = cursor.fetchall()
        conn.close()
        return transactions if transactions else 'No transactions available'

    def transfer(self, target_account, amount):
        if amount > self.balance:
            return 'Insufficient balance'
        self.withdraw(amount)
        target_account.deposit(amount)
        self.log_transaction("Transfer to " + target_account.user_id, amount)
        target_account.log_transaction("Transfer from " + self.user_id, amount)
        return f"Balance: ₹{self.balance:.2f}"


class ATMApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_account = None
        self.menu = None  
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("BMS Bank ATM")
        self.setGeometry(500, 200, 400, 300)
        self.setStyleSheet("background-color: #090979;")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Welcome to the BMS Bank ATM System", self)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff2400;")
        layout.addWidget(self.label)

        self.access_button = self.create_button("Access Account")
        self.access_button.clicked.connect(self.access_account)
        layout.addWidget(self.access_button)

        self.create_account_button = self.create_button("Create Account")
        self.create_account_button.clicked.connect(self.create_account)
        layout.addWidget(self.create_account_button)

        self.quit_button = self.create_button("Quit")
        self.quit_button.clicked.connect(self.close)
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

    def create_button(self, text):
        button = QPushButton(text, self)
        button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border-radius: 10px; 
                padding: 10px; 
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #dd4909;
            }
        """)
        return button

    def access_account(self):
        user_id, ok1 = self.get_input("Enter your Account Number")
        pin, ok2 = self.get_input("Enter your PIN", hide=True)
        if ok1 and ok2:
            self.current_account = Account.load_account(user_id)
            if self.current_account and self.current_account.check_pin(pin):
                QMessageBox.information(self, "Success", "Login Successful!")
                self.show_account_menu()
            else:
                QMessageBox.warning(self, "Error", "Invalid Account Number or PIN.")

    def create_account(self):
        user_id, ok1 = self.get_input("Enter new Account Number")
        pin, ok2 = self.get_input("Enter new PIN", hide=True)
        balance, ok3 = self.get_input("Enter initial deposit (optional, default is 0):")
        balance = float(balance) if balance and balance.isdigit() else 0
        if ok1 and ok2 and ok3:
            account = Account(user_id, pin, balance)
            account.save_account()
            QMessageBox.information(self, "Success", "Account created successfully!")

    def show_account_menu(self):
        self.menu = QWidget()
        self.menu.setWindowTitle("Account Menu")
        self.menu.setGeometry(500, 200, 400, 300)
        layout = QVBoxLayout()
        buttons = {
                "Transaction History": self.view_transaction_history,
                "Withdraw": self.withdraw_amount,
                "Deposit": self.deposit_amount,
                "Transfer": self.transfer_amount,
                "Balance Inquiry": self.check_balance,  
                "Quit": self.menu.close }
        for text, func in buttons.items():
            button = self.create_button(text)
            button.clicked.connect(func)
            layout.addWidget(button)
            self.menu.setLayout(layout)
            self.menu.setStyleSheet("background-color: #2403f9;")
            self.menu.show()


    def view_transaction_history(self):
        history = self.current_account.get_transaction_history()
        QMessageBox.information(self, "Transaction History", str(history))

    def withdraw_amount(self):
        amount, ok = self.get_input("Enter amount to withdraw:")
        if ok and amount.isdigit():
            result = self.current_account.withdraw(float(amount))
            QMessageBox.information(self, "Withdraw", str(result))

    def deposit_amount(self):
        amount, ok = self.get_input("Enter amount to deposit:")
        if ok and amount.isdigit():
            result = self.current_account.deposit(float(amount))
            QMessageBox.information(self, "Deposit", str(result))

    def check_balance(self):
        balance = self.current_account.balance
        QMessageBox.information(self, "Balance Inquiry", f"Your current balance is: {balance}")


    def transfer_amount(self):
        target_id, ok1 = self.get_input("Enter target Account Number:")
        target_account = Account.load_account(target_id)
        if ok1 and target_account:
            amount, ok2 = self.get_input("Enter amount to transfer:")
            if ok2 and amount.isdigit():
                amount = float(amount)
                result = self.current_account.transfer(target_account, amount)
                if isinstance(result, str):  
                    QMessageBox.warning(self, "Transfer Failed", result)
                else:
                    QMessageBox.information(self, "Transfer Successful",f"₹{amount:.2f} has been successfully transferred to {target_id}.")


    def get_input(self, text, hide=False):
        return QInputDialog.getText(self, "Input", text, QLineEdit.EchoMode.Password if hide else QLineEdit.EchoMode.Normal)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ATMApp()
    window.show()
    sys.exit(app.exec())
    app = QApplication(sys.argv)
    window = ATMApp()
    window.show()
    sys.exit(app.exec())