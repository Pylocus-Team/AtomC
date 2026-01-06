import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class NovxSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Define highlighting rules
        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setColor(QColor(86, 156, 214))  # Blue
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ['def', 'class', 'if', 'else', 'elif', 'while', 'for', 'return',
                    'import', 'from', 'try', 'except', 'finally', 'with', 'as',
                    'and', 'or', 'not', 'in', 'is', 'lambda', 'global', 'nonlocal']

        for keyword in keywords:
            pattern = QRegExp(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setColor(QColor(206, 145, 120))  # Orange
        self.highlighting_rules.append((QRegExp(r'".*"'), string_format))
        self.highlighting_rules.append((QRegExp(r"'.*'"), string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setColor(QColor(106, 153, 85))  # Green
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp(r'#.*'), comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setColor(QColor(181, 206, 168))  # Light green
        self.highlighting_rules.append((QRegExp(r'\b[0-9]+\.?[0-9]*\b'), number_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setColor(QColor(220, 220, 170))  # Yellow
        self.highlighting_rules.append((QRegExp(r'\b[A-Za-z_][A-Za-z0-9_]*(?=\()'), function_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class ProjectTreeWidget(QTreeWidget):
    fileOpened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemDoubleClicked.connect(self.open_file)

    def load_project(self, project_path):
        self.clear()
        self.project_path = project_path
        root_item = QTreeWidgetItem(self)
        root_item.setText(0, os.path.basename(project_path))
        root_item.setData(0, Qt.UserRole, project_path)
        root_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
        self.load_directory(project_path, root_item)
        self.expandItem(root_item)

    def load_directory(self, path, parent_item):
        try:
            for item_name in sorted(os.listdir(path)):
                item_path = os.path.join(path, item_name)
                item = QTreeWidgetItem(parent_item)
                item.setText(0, item_name)
                item.setData(0, Qt.UserRole, item_path)

                if os.path.isdir(item_path):
                    item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                    self.load_directory(item_path, item)
                else:
                    if item_name.endswith('.nx'):
                        item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                        item.setForeground(0, QColor(86, 156, 214))
                    else:
                        item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
        except PermissionError:
            pass

    def open_file(self, item):
        file_path = item.data(0, Qt.UserRole)
        if os.path.isfile(file_path):
            self.fileOpened.emit(file_path)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            menu = QMenu()

            if os.path.isdir(item.data(0, Qt.UserRole)):
                new_file_action = menu.addAction("New Novx File")
                new_folder_action = menu.addAction("New Folder")
                menu.addSeparator()
                new_file_action.triggered.connect(lambda: self.create_new_file(item))
                new_folder_action.triggered.connect(lambda: self.create_new_folder(item))

            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")

            rename_action.triggered.connect(lambda: self.rename_item(item))
            delete_action.triggered.connect(lambda: self.delete_item(item))

            menu.exec_(self.mapToGlobal(position))

    def create_new_file(self, parent_item):
        parent_path = parent_item.data(0, Qt.UserRole)
        name, ok = QInputDialog.getText(self, 'New File', 'Enter file name:')
        if ok and name:
            if not name.endswith('.nx'):
                name += '.nx'
            file_path = os.path.join(parent_path, name)
            try:
                with open(file_path, 'w') as f:
                    f.write('# New Novx file\n')
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not create file: {str(e)}')

    def create_new_folder(self, parent_item):
        parent_path = parent_item.data(0, Qt.UserRole)
        name, ok = QInputDialog.getText(self, 'New Folder', 'Enter folder name:')
        if ok and name:
            folder_path = os.path.join(parent_path, name)
            try:
                os.makedirs(folder_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not create folder: {str(e)}')

    def rename_item(self, item):
        old_path = item.data(0, Qt.UserRole)
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, 'Rename', 'Enter new name:', text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not rename: {str(e)}')

    def delete_item(self, item):
        file_path = item.data(0, Qt.UserRole)
        reply = QMessageBox.question(self, 'Delete', f'Are you sure you want to delete {os.path.basename(file_path)}?')
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not delete: {str(e)}')

    def refresh_tree(self):
        if hasattr(self, 'project_path'):
            self.load_project(self.project_path)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        self.highlighter = NovxSyntaxHighlighter(self.document())

        # Set font
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)

        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Set colors for dark theme
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                selection-background-color: #264f78;
            }
        """)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(255, 255, 255, 20)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(60, 60, 60))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(0, int(top), self.line_number_area.width(), self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class EditorTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.open_files = {}

    def open_file(self, file_path):
        if file_path in self.open_files:
            # File already open, just switch to it
            self.setCurrentIndex(self.open_files[file_path]['index'])
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            editor = CodeEditor()
            editor.setPlainText(content)

            file_name = os.path.basename(file_path)
            index = self.addTab(editor, file_name)
            self.setCurrentIndex(index)

            self.open_files[file_path] = {
                'index': index,
                'editor': editor,
                'modified': False
            }

            # Connect text changed signal
            editor.textChanged.connect(lambda: self.mark_modified(file_path))

        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not open file: {str(e)}')

    def mark_modified(self, file_path):
        if file_path in self.open_files:
            file_info = self.open_files[file_path]
            if not file_info['modified']:
                file_info['modified'] = True
                file_name = os.path.basename(file_path)
                self.setTabText(file_info['index'], f"{file_name} *")

    def save_current_file(self):
        current_index = self.currentIndex()
        if current_index == -1:
            return

        # Find file path by index
        file_path = None
        for path, info in self.open_files.items():
            if info['index'] == current_index:
                file_path = path
                break

        if file_path:
            try:
                editor = self.open_files[file_path]['editor']
                content = editor.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Mark as saved
                self.open_files[file_path]['modified'] = False
                file_name = os.path.basename(file_path)
                self.setTabText(current_index, file_name)

            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not save file: {str(e)}')

    def close_tab(self, index):
        # Find file path by index
        file_path = None
        for path, info in self.open_files.items():
            if info['index'] == index:
                file_path = path
                break

        if file_path:
            if self.open_files[file_path]['modified']:
                reply = QMessageBox.question(self, 'Unsaved Changes',
                                             f'Save changes to {os.path.basename(file_path)}?',
                                             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    self.save_current_file()
                elif reply == QMessageBox.Cancel:
                    return

            # Update indices for other open files
            for path, info in self.open_files.items():
                if info['index'] > index:
                    info['index'] -= 1

            del self.open_files[file_path]

        self.removeTab(index)


class TerminalWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self.append("Novx Terminal Ready...")

        # Dark theme
        self.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #ffffff;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)


class NovxIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_project = None
        self.settings_file = "novx_settings.json"
        self.settings = self.load_settings()

        self.init_ui()
        self.apply_dark_theme()

        # Restore window state
        if 'window_geometry' in self.settings:
            self.restoreGeometry(QByteArray.fromBase64(self.settings['window_geometry'].encode()))
        else:
            self.resize(1200, 800)
            self.center_window()

    def init_ui(self):
        self.setWindowTitle("Novx IDE")
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        # Central widget with splitters
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel (Project tree)
        self.project_tree = ProjectTreeWidget()
        self.project_tree.fileOpened.connect(self.open_file)

        # Right panel (Editor + Terminal)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Editor tabs
        self.editor_tabs = EditorTabWidget()

        # Terminal
        self.terminal = TerminalWidget()

        right_layout.addWidget(self.editor_tabs, 3)
        right_layout.addWidget(self.terminal, 1)

        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.project_tree)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([250, 950])

        main_layout.addWidget(main_splitter)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar().showMessage("Ready")

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        new_project_action = QAction('New Project', self)
        new_project_action.setShortcut('Ctrl+Shift+N')
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction('Open Project', self)
        open_project_action.setShortcut('Ctrl+Shift+O')
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        file_menu.addSeparator()

        new_file_action = QAction('New File', self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)

        open_file_action = QAction('Open File', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_file_action)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu('Edit')

        find_action = QAction('Find', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.find_dialog)
        edit_menu.addAction(find_action)

        replace_action = QAction('Replace', self)
        replace_action.setShortcut('Ctrl+H')
        replace_action.triggered.connect(self.replace_dialog)
        edit_menu.addAction(replace_action)

        # Run menu
        run_menu = menubar.addMenu('Run')

        run_action = QAction('Run Novx File', self)
        run_action.setShortcut('F5')
        run_action.triggered.connect(self.run_current_file)
        run_menu.addAction(run_action)

        # View menu
        view_menu = menubar.addMenu('View')

        toggle_terminal_action = QAction('Toggle Terminal', self)
        toggle_terminal_action.setShortcut('Ctrl+`')
        toggle_terminal_action.triggered.connect(self.toggle_terminal)
        view_menu.addAction(toggle_terminal_action)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3c3c3c;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #3c3c3c;
            }
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                alternate-background-color: #252526;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
            }
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)

    def center_window(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def new_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_path:
            self.current_project = project_path
            self.project_tree.load_project(project_path)
            self.setWindowTitle(f"Novx IDE - {os.path.basename(project_path)}")
            self.settings['last_project'] = project_path
            self.save_settings()

    def open_project(self):
        self.new_project()  # Same as new project for now

    def new_file(self):
        if not self.current_project:
            QMessageBox.warning(self, 'No Project', 'Please open or create a project first.')
            return

        file_name, ok = QInputDialog.getText(self, 'New File', 'Enter file name:')
        if ok and file_name:
            if not file_name.endswith('.nx'):
                file_name += '.nx'
            file_path = os.path.join(self.current_project, file_name)
            try:
                with open(file_path, 'w') as f:
                    f.write('# New Novx file\n')
                self.project_tree.refresh_tree()
                self.open_file(file_path)
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not create file: {str(e)}')

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Novx Files (*.nx);;All Files (*)")
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path):
        self.editor_tabs.open_file(file_path)
        self.statusBar().showMessage(f"Opened: {os.path.basename(file_path)}")

    def save_file(self):
        self.editor_tabs.save_current_file()
        self.statusBar().showMessage("File saved")

    def find_dialog(self):
        current_editor = self.editor_tabs.currentWidget()
        if current_editor:
            text, ok = QInputDialog.getText(self, 'Find', 'Enter search text:')
            if ok and text:
                cursor = current_editor.textCursor()
                found = current_editor.find(text)
                if not found:
                    QMessageBox.information(self, 'Find', 'Text not found.')

    def replace_dialog(self):
        current_editor = self.editor_tabs.currentWidget()
        if current_editor:
            dialog = QDialog(self)
            dialog.setWindowTitle('Find and Replace')
            layout = QVBoxLayout()

            find_layout = QHBoxLayout()
            find_layout.addWidget(QLabel('Find:'))
            find_input = QLineEdit()
            find_layout.addWidget(find_input)
            layout.addLayout(find_layout)

            replace_layout = QHBoxLayout()
            replace_layout.addWidget(QLabel('Replace:'))
            replace_input = QLineEdit()
            replace_layout.addWidget(replace_input)
            layout.addLayout(replace_layout)

            button_layout = QHBoxLayout()
            replace_btn = QPushButton('Replace All')
            cancel_btn = QPushButton('Cancel')
            button_layout.addWidget(replace_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)

            def replace_all():
                find_text = find_input.text()
                replace_text = replace_input.text()
                if find_text:
                    content = current_editor.toPlainText()
                    new_content = content.replace(find_text, replace_text)
                    current_editor.setPlainText(new_content)
                dialog.close()

            replace_btn.clicked.connect(replace_all)
            cancel_btn.clicked.connect(dialog.close)

            dialog.setLayout(layout)
            dialog.exec_()

    def run_current_file(self):
        current_index = self.editor_tabs.currentIndex()
        if current_index == -1:
            QMessageBox.warning(self, 'No File', 'No file is currently open.')
            return

        # Find current file path
        file_path = None
        for path, info in self.editor_tabs.open_files.items():
            if info['index'] == current_index:
                file_path = path
                break

        if file_path and file_path.endswith('.nx'):
            self.terminal.append(f"\n> Running {os.path.basename(file_path)}")
            self.terminal.append("Note: SWC compiler not yet implemented.")
            self.terminal.append("This will execute the Novx file when SWC is ready.")
        else:
            QMessageBox.warning(self, 'Invalid File', 'Please select a .nx file to run.')

    def toggle_terminal(self):
        if self.terminal.isVisible():
            self.terminal.hide()
        else:
            self.terminal.show()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_settings(self):
        self.settings['window_geometry'] = self.saveGeometry().toBase64().data().decode()
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def closeEvent(self, event):
        # Check for unsaved files
        unsaved_files = []
        for path, info in self.editor_tabs.open_files.items():
            if info['modified']:
                unsaved_files.append(os.path.basename(path))

        if unsaved_files:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         f'Save changes to {", ".join(unsaved_files)}?',
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                # Save all modified files
                for _ in range(self.editor_tabs.count()):
                    self.editor_tabs.save_current_file()

        self.save_settings()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look

    # Set application properties
    app.setApplicationName("Novx IDE")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Novx")

    window = NovxIDE()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()