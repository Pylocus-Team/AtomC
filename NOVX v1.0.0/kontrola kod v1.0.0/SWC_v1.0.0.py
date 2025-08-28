import sys
import re
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel, QInputDialog
)
import time

class SWC(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVX – System Working Compiler (SWC)")
        self.setGeometry(100, 100, 700, 500)

        self.current_file = ""
        self.commands = self.load_commands()
        self.variables = {}
        self.bindings = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.path_label = QLabel("Trenutni projekt: (ništa nije učitano)")
        self.output_terminal = QTextEdit()
        self.output_terminal.setReadOnly(True)

        self.open_button = QPushButton("Otvori projekt")
        self.run_button = QPushButton("Pokreni kod")

        self.open_button.clicked.connect(self.open_file)
        self.run_button.clicked.connect(self.run_code)

        layout.addWidget(self.open_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.path_label)
        layout.addWidget(self.output_terminal)

        self.setLayout(layout)

    def load_commands(self):
        try:
            with open("commands_v1.0.0.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.output_terminal.append(f"Greška pri učitavanju commands.json: {e}")
            return {}

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Otvori .txt fajl",
            "",
            "Tekstualne datoteke (*.txt)"
        )
        if file_path:
            self.current_file = file_path
            self.path_label.setText(f"Trenutni projekt: {file_path}")

    def run_code(self):
        self.output_terminal.clear()
        self.variables.clear()
        self.bindings.clear()

        if not self.current_file:
            self.output_terminal.append("Greška. (Nema fajla)")
            return

        try:
            with open(self.current_file, "r", encoding="utf-8") as f:
                code = f.read()
        except:
            self.output_terminal.append("Greška. (Ne mogu otvoriti fajl)")
            return

        lines = self.preprocess_code(code)

        try:
            self.execute_lines(lines)
        except Exception as e:
            self.output_terminal.append(f"Greška. (Exception: {e})")

    def preprocess_code(self, code):
        code_lines = code.splitlines()
        processed = []
        for line in code_lines:
            line = line.strip()
            if line and not line.startswith("??"):
                processed.append(line)
        return processed

    def execute_lines(self, lines):
        for line in lines:
            if line.startswith("shout:"):
                m = re.match(r'shout:\s*"(.+)"', line)
                if m:
                    self.output_terminal.append(m.group(1))
                else:
                    self.output_terminal.append(self.commands["shout:"]["error"])

            elif line.startswith("echo!"):
                m = re.match(r"echo!\s*@([a-zA-Z_][a-zA-Z0-9_]*)", line)
                if m and m.group(1) in self.variables:
                    self.output_terminal.append(str(self.variables[m.group(1)]))
                else:
                    self.output_terminal.append(self.commands["echo!"]["error"])

            elif line.startswith("do:"):
                m = re.match(r"do:\s*@([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)", line)
                if not m:
                    self.output_terminal.append(self.commands["do:"]["error"])
                    continue
                var, expr = m.group(1), m.group(2)
                try:
                    expr = re.sub(r"@([a-zA-Z_][a-zA-Z0-9_]*)", lambda x: str(self.variables.get(x.group(1), "0")), expr)
                    self.variables[var] = eval(expr)
                except:
                    self.output_terminal.append(self.commands["do:"]["error"])

            elif line.strip() == "cut>":
                self.output_terminal.append("Program prekinut.")
                sys.exit(0)

            elif line.strip() == "purge!":
                self.output_terminal.clear()

            else:
                self.output_terminal.append(f"Nepoznata komanda: {line}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SWC()
    window.show()
    sys.exit(app.exec_())
