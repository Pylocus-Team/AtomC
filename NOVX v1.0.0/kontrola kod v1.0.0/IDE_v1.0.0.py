import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout,
    QWidget, QPushButton, QFileDialog, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class NovxIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVX IDE")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.filepath = None

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setStyleSheet("""
            background-color: #252526;
            color: white;
            border: none;
        """)

        self.output = QTextEdit()
        self.output.setFont(QFont("Consolas", 11))
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            background-color: #1e1e1e;
            color: #c586c0;
            border-top: 1px solid #333;
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        button_style = """
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
                padding: 4px 10px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """

        btn_new = QPushButton("New")
        btn_open = QPushButton("Open")
        btn_save = QPushButton("Save")

        for btn in [btn_new, btn_open, btn_save]:
            btn.setStyleSheet(button_style)
            btn.setFixedHeight(25)
            btn.setFixedWidth(70)

        btn_new.clicked.connect(self.new_file)
        btn_open.clicked.connect(self.open_file)
        btn_save.clicked.connect(self.save_file)

        button_layout.addStretch()
        button_layout.addWidget(btn_new)
        button_layout.addWidget(btn_open)
        button_layout.addWidget(btn_save)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.editor, stretch=8)
        main_layout.addWidget(self.output, stretch=2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def new_file(self):
        if self.editor.toPlainText().strip():
            choice = QMessageBox.question(self, "Save Changes?", "Do you want to save changes before creating new file?",
                                          QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if choice == QMessageBox.Yes:
                self.save_file()
            elif choice == QMessageBox.Cancel:
                return

        path, _ = QFileDialog.getSaveFileName(self, "Create New NOVX File", "", "NOVX Files (*#nx.txt)")
        if path:
            if not path.endswith("#nx.txt"):
                path += "#nx.txt"
            self.filepath = path
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("")
            self.editor.clear()
            self.output.append(f">> Created new file: {os.path.basename(self.filepath)}")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open NOVX File", "", "Text Files (*.txt *#nx.txt);;All Files (*)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setText(f.read())
            self.filepath = path
            self.output.append(f">> Opened: {os.path.basename(self.filepath)}")

    def save_file(self):
        if not self.filepath:
            path, _ = QFileDialog.getSaveFileName(self, "Save NOVX File", "", "NOVX Files (*#nx.txt)")
            if path:
                if not path.endswith("#nx.txt"):
                    path += "#nx.txt"
                self.filepath = path
        if self.filepath:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.output.append(f">> Saved: {os.path.basename(self.filepath)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NovxIDE()
    window.show()
    sys.exit(app.exec_())
