# search_app.py
import sys
import logging
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QHBoxLayout, QMessageBox, QFileDialog, QProgressBar, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QComboBox, QCheckBox,
    QGridLayout, QSplitter, QShortcut, QFrame, QAction, QMenuBar
)
from PyQt5.QtCore import Qt, QThread, QUrl
from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QKeySequence
from worker import Worker
from gui_components import GuiLogHandler, MyLineEdit, MyTextEdit, CheckBoxHeader, CenteredCheckBoxDelegate
from utils import save_results_to_txt, generate_txt_content
from language_manager import LanguageManager  # 引入语言管理器

class SearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.language_manager = LanguageManager()
        self.thread = None
        self.saved_file = None
        self.all_results = []
        self.current_content = ""
        self.init_ui()

    def init_ui(self):
        """
        初始化用户界面。
        """
        label_font = QFont("微软雅黑", 12)
        input_font = QFont("微软雅黑", 12)
        button_font = QFont("微软雅黑", 12)
        status_font = QFont("微软雅黑", 10)
        table_font = QFont("微软雅黑", 10)
        log_font = QFont("Consolas", 10)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 创建菜单栏
        self.menu_bar = QMenuBar(self)
        language_menu_title = "Language" if self.language_manager.current_language == 'en' else "语言"
        language_menu = self.menu_bar.addMenu(language_menu_title)
        english_action = QAction("English", self)
        chinese_action = QAction("中文", self)
        language_menu.addAction(english_action)
        language_menu.addAction(chinese_action)
        english_action.triggered.connect(lambda: self.change_language('en'))
        chinese_action.triggered.connect(lambda: self.change_language('zh'))

        # 帮助菜单
        help_menu_title = self.language_manager.tr('help')
        help_menu = self.menu_bar.addMenu(help_menu_title)
        about_action = QAction(self.language_manager.tr('about'), self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(self.show_about_dialog)

        main_layout.setMenuBar(self.menu_bar)

        # 搜索设置分组框
        search_group = QGroupBox(self.language_manager.tr('search_settings'))
        search_group.setObjectName("search_group")
        search_layout = QGridLayout()
        search_layout.setSpacing(10)
        search_group.setLayout(search_layout)

        # 进阶模式复选框
        self.advanced_mode_checkbox = QCheckBox(self.language_manager.tr('advanced_mode'))
        self.advanced_mode_checkbox.setFont(label_font)
        self.advanced_mode_checkbox.setToolTip(self.language_manager.tr('advanced_mode'))
        self.advanced_mode_checkbox.stateChanged.connect(self.on_advanced_mode_changed)

        # 搜索引擎选择
        self.engine_label = QLabel(self.language_manager.tr('search_engine'))
        self.engine_label.setFont(label_font)
        self.engine_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.engine_combo = QComboBox()
        self.engine_combo.setFont(input_font)
        self.engines = {
            "Google": "Google",
            "Bing": "Bing",
            "百度": "百度"
        }
        for engine in self.engines.keys():
            self.engine_combo.addItem(engine)
        self.engine_combo.setCurrentText("Google")
        self.engine_combo.setToolTip(self.language_manager.tr('search_engine'))

        # 搜索结果数量
        self.result_num_label = QLabel(self.language_manager.tr('search_number'))
        self.result_num_label.setFont(label_font)
        self.result_num_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.decrement_button = QPushButton(self.language_manager.tr('decrement'))
        self.decrement_button.setFont(button_font)
        self.decrement_button.setFixedWidth(30)
        self.decrement_button.setStyleSheet("""
            QPushButton {
                background-color: #ff5722;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e64a19;
            }
            QPushButton:pressed {
                background-color: #d84315;
            }
        """)
        self.decrement_button.setToolTip(self.language_manager.tr('decrement'))
        self.decrement_button.clicked.connect(self.on_decrement)

        self.result_num_value = 5  # 默认5
        self.result_num_display = QLabel(str(self.result_num_value))
        self.result_num_display.setFont(input_font)
        self.result_num_display.setAlignment(Qt.AlignCenter)
        self.result_num_display.setFixedWidth(30)
        self.result_num_display.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: #f0f0f0;
            }
        """)

        self.increment_button = QPushButton(self.language_manager.tr('increment'))
        self.increment_button.setFont(button_font)
        self.increment_button.setFixedWidth(30)
        self.increment_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        """)
        self.increment_button.setToolTip(self.language_manager.tr('increment'))
        self.increment_button.clicked.connect(self.on_increment)

        # 布局搜索数量控件
        result_num_layout = QHBoxLayout()
        result_num_layout.addWidget(self.decrement_button)
        result_num_layout.addWidget(self.result_num_display)
        result_num_layout.addWidget(self.increment_button)
        result_num_layout.setSpacing(5)

        # 复制按钮
        self.copy_button = QPushButton(self.language_manager.tr('copy'))
        self.copy_button.setFont(button_font)
        self.copy_button.setFixedWidth(120)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #fb8c00;
            }
            QPushButton:pressed {
                background-color: #f57c00;
            }
        """)
        self.copy_button.setToolTip(self.language_manager.tr('copy'))
        self.copy_button.clicked.connect(self.on_copy_click)
        self.copy_button.setEnabled(False)

        # 清空按钮
        self.clear_button = QPushButton(self.language_manager.tr('clear'))
        self.clear_button.setFont(button_font)
        self.clear_button.setFixedWidth(80)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
        """)
        self.clear_button.setToolTip(self.language_manager.tr('clear'))
        self.clear_button.clicked.connect(self.on_clear_click)

        copy_and_clear_layout = QHBoxLayout()
        copy_and_clear_layout.addWidget(self.copy_button)
        copy_and_clear_layout.addWidget(self.clear_button)
        copy_and_clear_layout.setSpacing(10)

        search_num_layout = QHBoxLayout()
        search_num_layout.addWidget(self.result_num_label)
        search_num_layout.addLayout(result_num_layout)
        search_num_layout.addLayout(copy_and_clear_layout)
        search_num_layout.setSpacing(20)

        # 添加到搜索布局（第一行）
        search_layout.addWidget(self.advanced_mode_checkbox, 0, 0)
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(self.engine_label)
        engine_layout.addWidget(self.engine_combo)
        engine_layout.setSpacing(5)
        search_layout.addLayout(engine_layout, 0, 1)
        search_layout.addLayout(search_num_layout, 0, 2, 1, 2)

        # 普通模式搜索输入框
        self.search_label = QLabel(self.language_manager.tr('search_keywords'))
        self.search_label.setFont(label_font)
        self.search_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.search_input = MyLineEdit()
        self.search_input.setFont(input_font)
        self.search_input.setPlaceholderText(self.language_manager.tr('search_placeholder'))
        self.search_input.setToolTip(self.language_manager.tr('search_keywords'))

        # 进阶模式搜索输入框
        self.search_input_advanced = MyTextEdit()
        self.search_input_advanced.setFont(input_font)
        self.search_input_advanced.setPlaceholderText(self.language_manager.tr('search_placeholder_advanced'))
        self.search_input_advanced.setVisible(False)
        self.search_input_advanced.setToolTip(self.language_manager.tr('search_keywords'))

        # 自定义问题（仅进阶模式）
        self.question_label = QLabel(self.language_manager.tr('custom_question'))
        self.question_label.setFont(label_font)
        self.question_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.question_input = QTextEdit()
        self.question_input.setFont(input_font)
        self.question_input.setPlaceholderText(self.language_manager.tr('question_placeholder'))
        self.question_label.setVisible(False)
        self.question_input.setVisible(False)
        self.question_input.setToolTip(self.language_manager.tr('custom_question'))

        # 搜索按钮
        self.search_button = QPushButton(self.language_manager.tr('search'))
        self.search_button.setFont(button_font)
        self.search_button.setFixedWidth(120)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        self.search_button.setToolTip(self.language_manager.tr('search'))
        self.search_button.clicked.connect(self.on_search_click)

        # 中断按钮
        self.interrupt_button = QPushButton(self.language_manager.tr('interrupt'))
        self.interrupt_button.setFont(button_font)
        self.interrupt_button.setFixedWidth(120)
        self.interrupt_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.interrupt_button.setToolTip(self.language_manager.tr('interrupt'))
        self.interrupt_button.clicked.connect(self.on_interrupt_click)
        self.interrupt_button.setEnabled(False)

        self.search_input.returnPressed.connect(self.on_search_click)

        # 添加 Ctrl+C 快捷键
        self.interrupt_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.interrupt_shortcut.setContext(Qt.ApplicationShortcut)
        self.interrupt_shortcut.activated.connect(self.on_interrupt_click)

        # 保存按钮
        self.save_button = QPushButton(self.language_manager.tr('save_results'))
        self.save_button.setFont(button_font)
        self.save_button.setFixedWidth(120)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #095a9d;
            }
        """)
        self.save_button.setToolTip(self.language_manager.tr('save_results'))
        self.save_button.clicked.connect(self.on_save_click)
        self.save_button.setEnabled(False)

        # 打开结果按钮
        self.open_button = QPushButton(self.language_manager.tr('open_results'))
        self.open_button.setFont(button_font)
        self.open_button.setFixedWidth(120)
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
            QPushButton:pressed {
                background-color: #4a0072;
            }
        """)
        self.open_button.setToolTip(self.language_manager.tr('open_results'))
        self.open_button.clicked.connect(self.on_open_click)
        self.open_button.setEnabled(False)

        self.input_button_layout = QHBoxLayout()
        self.input_button_layout.addWidget(self.search_input)
        self.input_button_layout.addWidget(self.search_input_advanced)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.search_button)
        self.button_layout.addWidget(self.interrupt_button)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.open_button)

        self.input_button_layout.addLayout(self.button_layout)

        # 将搜索关键词和问题添加到布局
        search_layout.addWidget(self.search_label, 1, 0)
        search_layout.addLayout(self.input_button_layout, 1, 1, 1, 3)
        search_layout.addWidget(self.question_label, 2, 0)
        search_layout.addWidget(self.question_input, 2, 1, 1, 3)

        search_layout.setColumnStretch(0, 0)
        search_layout.setColumnStretch(1, 1)
        search_layout.setColumnStretch(2, 1)
        search_layout.setColumnStretch(3, 1)

        self.status_label = QLabel(self.language_manager.tr('status_waiting'))
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setStyleSheet("color: #555;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                background-color: #eee;
                height: 15px;
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 7px;
            }
        """)

        # 结果显示区
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels([
            self.language_manager.tr('copy'),
            "URL",
            "Title",
            "Snippet",
            "Content"
        ])

        self.checkbox_header = CheckBoxHeader()
        self.result_table.setHorizontalHeader(self.checkbox_header)
        self.checkbox_header.checkBoxClicked.connect(self.on_header_checkbox_clicked)

        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SingleSelection)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFont(table_font)
        self.result_table.setStyleSheet("""
            QTableWidget {
                background-color: #fff;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #d6d6d6;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
            }
        """)

        self.result_table.setColumnWidth(0, 40)
        self.result_table.setColumnWidth(1, 250)
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        for i in range(2, 5):
            self.result_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        self.result_table.setItemDelegateForColumn(0, CenteredCheckBoxDelegate())
        self.result_table.cellClicked.connect(self.on_result_cell_clicked)

        log_group = QGroupBox("日志" if self.language_manager.current_language == 'zh' else "Logs")
        log_group.setObjectName("log_group")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(log_font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.result_table)
        splitter.addWidget(log_group)
        splitter.setSizes([600, 300])

        main_layout.addWidget(search_group)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        self.setup_logging()

        self.setWindowTitle(self.language_manager.tr('window_title'))

        # 使用 __file__ 定位资源文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, 'resources', 'icon.png')
        print(f"尝试加载图标路径: {icon_path}")
        if not os.path.exists(icon_path):
            logging.error(f"图标文件不存在: {icon_path}")
            QMessageBox.critical(self, "错误", f"图标文件不存在: {icon_path}")
        else:
            try:
                self.setWindowIcon(QIcon(icon_path))
                logging.info(f"已设置窗口图标: {icon_path}")
                print(f"已设置窗口图标: {icon_path}")
            except Exception as e:
                logging.error(f"设置窗口图标时出错: {e}")
                QMessageBox.critical(self, "错误", f"设置窗口图标时出错: {e}")

    def setup_logging(self):
        gui_handler = GuiLogHandler(self.log_text)
        gui_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        logging.getLogger().addHandler(gui_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    def change_language(self, language_code):
        if language_code in ['en', 'zh']:
            if language_code == self.language_manager.current_language:
                return
            self.language_manager.set_language(language_code)
            logging.info(f"语言更改为: {'English' if language_code == 'en' else '中文'}")
            self.update_ui_texts()
        else:
            logging.warning(f"尝试设置未知语言: {language_code}")

    def update_ui_texts(self):
        self.setWindowTitle(self.language_manager.tr('window_title'))
        language_menu = self.menu_bar.actions()[0].menu()
        language_menu.setTitle("Language" if self.language_manager.current_language == 'en' else "语言")
        language_menu.actions()[0].setText("English" if self.language_manager.current_language == 'en' else "英文")
        language_menu.actions()[1].setText("中文" if self.language_manager.current_language == 'en' else "中文")

        help_menu = self.menu_bar.actions()[1].menu()
        help_menu.setTitle(self.language_manager.tr('help'))
        help_menu.actions()[0].setText(self.language_manager.tr('about'))

        search_group = self.findChild(QGroupBox, "search_group")
        if search_group:
            search_group.setTitle(self.language_manager.tr('search_settings'))

        self.advanced_mode_checkbox.setText(self.language_manager.tr('advanced_mode'))
        self.advanced_mode_checkbox.setToolTip(self.language_manager.tr('advanced_mode'))

        self.engine_label.setText(self.language_manager.tr('search_engine'))
        self.engine_combo.setToolTip(self.language_manager.tr('search_engine'))

        self.result_num_label.setText(self.language_manager.tr('search_number'))

        self.decrement_button.setText(self.language_manager.tr('decrement'))
        self.decrement_button.setToolTip(self.language_manager.tr('decrement'))
        self.increment_button.setText(self.language_manager.tr('increment'))
        self.increment_button.setToolTip(self.language_manager.tr('increment'))
        self.copy_button.setText(self.language_manager.tr('copy'))
        self.copy_button.setToolTip(self.language_manager.tr('copy'))
        self.clear_button.setText(self.language_manager.tr('clear'))
        self.clear_button.setToolTip(self.language_manager.tr('clear'))
        self.search_button.setText(self.language_manager.tr('search'))
        self.search_button.setToolTip(self.language_manager.tr('search'))
        self.interrupt_button.setText(self.language_manager.tr('interrupt'))
        self.interrupt_button.setToolTip(self.language_manager.tr('interrupt'))
        self.save_button.setText(self.language_manager.tr('save_results'))
        self.save_button.setToolTip(self.language_manager.tr('save_results'))
        self.open_button.setText(self.language_manager.tr('open_results'))
        self.open_button.setToolTip(self.language_manager.tr('open_results'))

        self.search_label.setText(self.language_manager.tr('search_keywords'))
        if self.advanced_mode_checkbox.isChecked():
            self.search_input_advanced.setPlaceholderText(self.language_manager.tr('search_placeholder_advanced'))
            self.search_input_advanced.setToolTip(self.language_manager.tr('search_keywords'))
        else:
            self.search_input.setPlaceholderText(self.language_manager.tr('search_placeholder'))
            self.search_input.setToolTip(self.language_manager.tr('search_keywords'))

        self.question_label.setText(self.language_manager.tr('custom_question'))
        self.question_input.setPlaceholderText(self.language_manager.tr('question_placeholder'))
        self.question_input.setToolTip(self.language_manager.tr('custom_question'))

        self.status_label.setText(self.language_manager.tr('status_waiting'))

        self.result_table.setHorizontalHeaderLabels([
            self.language_manager.tr('copy'),
            "URL",
            "Title",
            "Snippet",
            "Content"
        ])

        log_group = self.findChild(QGroupBox, "log_group")
        if log_group:
            log_group.setTitle("Logs" if self.language_manager.current_language == 'en' else "日志")

    def show_about_dialog(self):
        about_title = self.language_manager.tr('about_title')
        about_message = self.language_manager.tr('about_message')
        QMessageBox.about(self, about_title, about_message)

    def on_advanced_mode_changed(self, state):
        is_advanced = (state == Qt.Checked)
        logging.info(f"进阶模式 {'开启' if is_advanced else '关闭'}")
        if is_advanced:
            self.search_input.setVisible(False)
            self.search_input_advanced.setVisible(True)
            self.question_label.setVisible(True)
            self.question_input.setVisible(True)
            self.search_input_advanced.setFocus()
        else:
            self.search_input.setVisible(True)
            self.search_input_advanced.setVisible(False)
            self.question_label.setVisible(False)
            self.question_input.setVisible(False)
            self.search_input.setFocus()

    def on_increment(self):
        if self.result_num_value < 20:
            self.result_num_value += 1
            self.result_num_display.setText(str(self.result_num_value))
            logging.info(f"搜索数量增加到 {self.result_num_value}")

    def on_decrement(self):
        if self.result_num_value > 1:
            self.result_num_value -= 1
            self.result_num_display.setText(str(self.result_num_value))
            logging.info(f"搜索数量减少到 {self.result_num_value}")

    def on_clear_click(self):
        if self.advanced_mode_checkbox.isChecked():
            self.search_input_advanced.clear()
        else:
            self.search_input.clear()
        logging.info("已清空搜索关键词输入框。")

    def on_search_click(self):
        is_advanced = self.advanced_mode_checkbox.isChecked()
        if is_advanced:
            keywords_text = self.search_input_advanced.toPlainText().strip()
            if not keywords_text:
                QMessageBox.warning(self, self.language_manager.tr('input_error'), self.language_manager.tr('input_error_empty_keyword'))
                logging.warning("空关键词搜索（进阶模式）。")
                return
            queries = [line.strip() for line in keywords_text.splitlines() if line.strip()]
            if not queries:
                QMessageBox.warning(self, self.language_manager.tr('input_error'), self.language_manager.tr('input_error_empty_keyword'))
                logging.warning("空关键词搜索（进阶模式）。")
                return
            custom_question = self.question_input.toPlainText().strip()
            if not custom_question:
                QMessageBox.warning(self, self.language_manager.tr('input_error'), self.language_manager.tr('input_error_empty_question'))
                logging.warning("进阶模式下无自定义问题输入。")
                return
        else:
            query = self.search_input.text().strip()
            if not query:
                QMessageBox.warning(self, self.language_manager.tr('input_error'), self.language_manager.tr('input_error_empty_keyword'))
                logging.warning("空关键词搜索。")
                return
            queries = [query]
            custom_question = None

        num_results = self.result_num_value
        engine_display = self.engine_combo.currentText()
        engine = self.engines.get(engine_display, 'Google')
        logging.info(f"开始搜索，关键词: {queries}, 数量: {num_results}, 引擎: {engine}")

        self.search_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.interrupt_button.setEnabled(True)
        self.search_input.setEnabled(False)
        self.search_input_advanced.setEnabled(False)
        self.question_input.setEnabled(False)
        self.increment_button.setEnabled(False)
        self.decrement_button.setEnabled(False)
        self.engine_combo.setEnabled(False)

        self.result_table.setRowCount(0)
        self.status_label.setText(self.language_manager.tr('status_searching'))
        self.progress_bar.setVisible(True)

        self.thread = QThread()
        self.worker = Worker(queries, num_results, engine, custom_question)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_search_complete)
        self.worker.error.connect(self.on_search_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_interrupt_click(self):
        if self.thread and self.thread.isRunning():
            logging.info("用户中断搜索任务。")
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()
            self.interrupt_button.setEnabled(False)
            self.status_label.setText(self.language_manager.tr('interrupt_info_task_interrupted'))

            self.search_button.setEnabled(True)
            self.open_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.copy_button.setEnabled(False)
            self.search_input.setEnabled(True)
            self.search_input_advanced.setEnabled(True)
            self.question_input.setEnabled(True)
            self.increment_button.setEnabled(True)
            self.decrement_button.setEnabled(True)
            self.engine_combo.setEnabled(True)
        else:
            logging.warning("无正在运行的搜索任务可中断。")
            QMessageBox.information(self, self.language_manager.tr('input_error'), self.language_manager.tr('interrupt_info_no_task'))

    def on_search_complete(self, results, filename):
        self.progress_bar.setVisible(False)
        self.interrupt_button.setEnabled(False)
        if results:
            try:
                self.saved_file = filename
                self.all_results = results
                logging.info("搜索结果已成功获取。")
            except Exception as e:
                logging.error(f"保存文件时出错：{e}")
                QMessageBox.critical(self, self.language_manager.tr('save_failure'), f"{self.language_manager.tr('save_failure').format(e)}")
                self.status_label.setText(self.language_manager.tr('status_search_failed'))
                self.reset_ui_after_search_failure()
                return

            self.result_table.setRowCount(0)
            for idx, result in enumerate(results):
                self.result_table.insertRow(idx)
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Checked)

                url_item = QTableWidgetItem(result['link'])
                url_item.setFont(QFont("微软雅黑", 10))
                title_item = QTableWidgetItem(result['title'])
                title_item.setFont(QFont("微软雅黑", 10))
                snippet_item = QTableWidgetItem(result['snippet'])
                snippet_item.setFont(QFont("微软雅黑", 9))
                content_item = QTableWidgetItem(result['content'])
                content_item.setFont(QFont("微软雅黑", 9))

                self.result_table.setItem(idx, 0, checkbox_item)
                self.result_table.setItem(idx, 1, url_item)
                self.result_table.setItem(idx, 2, title_item)
                self.result_table.setItem(idx, 3, snippet_item)
                self.result_table.setItem(idx, 4, content_item)

            self.result_table.itemChanged.connect(self.on_checkbox_state_changed)
            self.update_saved_content()

            self.status_label.setText(self.language_manager.tr('status_search_complete'))
            self.save_button.setEnabled(True)
            self.open_button.setEnabled(True)
            self.copy_button.setEnabled(True)
            self.search_button.setEnabled(True)
            self.search_input.setEnabled(True)
            self.search_input_advanced.setEnabled(True)
            self.question_input.setEnabled(True)
            self.increment_button.setEnabled(True)
            self.decrement_button.setEnabled(True)
            self.engine_combo.setEnabled(True)

            if self.advanced_mode_checkbox.isChecked():
                self.search_input_advanced.setFocus()
            else:
                self.search_input.setFocus()

            logging.info("搜索完成，结果已展示。")
            self.copy_results_silently()

        else:
            self.result_table.setRowCount(0)
            self.status_label.setText(self.language_manager.tr('status_search_failed'))
            QMessageBox.information(self, self.language_manager.tr('input_error'), self.language_manager.tr('status_search_failed'))
            logging.info("搜索完成但无结果。")
            self.reset_ui_after_search_failure()

    def on_search_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.result_table.setRowCount(0)
        self.status_label.setText(self.language_manager.tr('status_search_failed'))
        QMessageBox.critical(self, self.language_manager.tr('input_error'), f"{self.language_manager.tr('status_search_failed')}\n{error_message}")
        logging.error(f"搜索错误：{error_message}")
        self.reset_ui_after_search_failure()

    def reset_ui_after_search_failure(self):
        self.search_button.setEnabled(True)
        self.open_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.search_input.setEnabled(True)
        self.search_input_advanced.setEnabled(True)
        self.question_input.setEnabled(True)
        self.increment_button.setEnabled(True)
        self.decrement_button.setEnabled(True)
        self.engine_combo.setEnabled(True)
        self.interrupt_button.setEnabled(False)

        if self.advanced_mode_checkbox.isChecked():
            self.search_input_advanced.setFocus()
        else:
            self.search_input.setFocus()

    def on_save_click(self):
        is_advanced = self.advanced_mode_checkbox.isChecked()
        if is_advanced:
            queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
            custom_question = self.question_input.toPlainText().strip()
        else:
            query = self.search_input.text().strip()
            queries = [query]
            custom_question = None

        if not queries:
            QMessageBox.warning(self, self.language_manager.tr('input_error'), self.language_manager.tr('save_error_no_keyword'))
            logging.warning("试图保存结果但无关键词。")
            return

        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        default_filename = os.path.join(downloads_path, "search_results.txt")
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.language_manager.tr('save_results'),
            default_filename,
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        if filename:
            logging.info(f"用户选择保存文件路径：{filename}")
            try:
                selected_results = self.get_selected_results()
                save_results_to_txt(
                    selected_results,
                    ', '.join(queries),
                    filename=filename,
                    engine=self.engine_combo.currentText(),
                    custom_question=custom_question,
                    language=self.language_manager.current_language
                )

                QMessageBox.information(self, self.language_manager.tr('save_success').format(filename), self.language_manager.tr('save_success').format(filename))
                logging.info(f"结果成功保存到 {filename}")
                self.saved_file = filename
                self.open_button.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, self.language_manager.tr('save_failure'), f"{self.language_manager.tr('save_failure').format(e)}")
                logging.error(f"保存文件时出错：{e}")

    def on_open_click(self):
        if self.saved_file and os.path.exists(self.saved_file):
            logging.info(f"打开文件：{self.saved_file}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.saved_file))
        else:
            QMessageBox.warning(self, self.language_manager.tr('input_error'), self.language_manager.tr('open_error_no_file'))
            logging.warning("尝试打开文件但不存在或未保存。")

    def on_copy_click(self):
        selected_results = self.get_selected_results()
        if selected_results:
            is_advanced = self.advanced_mode_checkbox.isChecked()
            if is_advanced:
                queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
                custom_question = self.question_input.toPlainText().strip()
            else:
                query = self.search_input.text().strip()
                queries = [query]
                custom_question = None

            try:
                content = generate_txt_content(
                    selected_results,
                    ', '.join(queries),
                    engine=self.engine_combo.currentText(),
                    custom_question=custom_question,
                    language=self.language_manager.current_language
                )
                clipboard = QApplication.clipboard()
                clipboard.setText(content)
                logging.info("选中内容已复制到剪贴板。")
                QMessageBox.information(self, self.language_manager.tr('copy_success'), self.language_manager.tr('copy_success'))
            except Exception as e:
                QMessageBox.warning(self, self.language_manager.tr('copy_failure').format(e), self.language_manager.tr('copy_failure').format(e))
                logging.error(f"复制出错：{e}")
        else:
            QMessageBox.warning(self, self.language_manager.tr('copy_failure_no_selection'), self.language_manager.tr('copy_failure_no_selection'))
            logging.warning("尝试复制但无选择内容。")

    def copy_results_silently(self):
        selected_results = self.get_selected_results()
        if selected_results:
            is_advanced = self.advanced_mode_checkbox.isChecked()
            if is_advanced:
                queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
                custom_question = self.question_input.toPlainText().strip()
            else:
                query = self.search_input.text().strip()
                queries = [query]
                custom_question = None

            try:
                content = generate_txt_content(
                    selected_results,
                    ', '.join(queries),
                    engine=self.engine_combo.currentText(),
                    custom_question=custom_question,
                    language=self.language_manager.current_language
                )
                clipboard = QApplication.clipboard()
                clipboard.setText(content)
                logging.info("选中内容已自动复制到剪贴板。")
            except Exception as e:
                logging.error(f"自动复制出错：{e}")
        else:
            logging.warning("自动复制时无选择内容。")

    def on_result_cell_clicked(self, row, column):
        if column == 1:  # URL列
            item = self.result_table.item(row, column)
            if item:
                url = item.text()
                logging.info(f"点击URL：{url}")
                QDesktopServices.openUrl(QUrl(url))
            else:
                logging.warning("点击的URL单元格为空。")

    def on_checkbox_state_changed(self, item):
        if item.column() == 0:
            self.update_saved_content()
            all_checked = True
            for row in range(self.result_table.rowCount()):
                checkbox_item = self.result_table.item(row, 0)
                if checkbox_item is None or checkbox_item.checkState() != Qt.Checked:
                    all_checked = False
                    break
            self.checkbox_header.isOn = all_checked
            self.checkbox_header.updateSection(0)

    def on_header_checkbox_clicked(self, checked):
        for row in range(self.result_table.rowCount()):
            checkbox_item = self.result_table.item(row, 0)
            if checkbox_item is not None:
                checkbox_item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def get_selected_results(self):
        selected_results = []
        for row in range(self.result_table.rowCount()):
            checkbox_item = self.result_table.item(row, 0)
            if checkbox_item is not None and checkbox_item.checkState() == Qt.Checked:
                title_item = self.result_table.item(row, 2)
                link_item = self.result_table.item(row, 1)
                snippet_item = self.result_table.item(row, 3)
                content_item = self.result_table.item(row, 4)
                if title_item and link_item and snippet_item and content_item:
                    result = {
                        'title': title_item.text(),
                        'link': link_item.text(),
                        'snippet': snippet_item.text(),
                        'content': content_item.text(),
                        'engine': self.engine_combo.currentText()
                    }
                    selected_results.append(result)
                else:
                    logging.warning(f"行 {row} 存在空数据项。")
        return selected_results

    def update_saved_content(self):
        selected_results = self.get_selected_results()
        is_advanced = self.advanced_mode_checkbox.isChecked()
        if is_advanced:
            queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
            custom_question = self.question_input.toPlainText().strip()
        else:
            query = self.search_input.text().strip()
            queries = [query]
            custom_question = None

        try:
            content = generate_txt_content(
                selected_results,
                ', '.join(queries),
                engine=self.engine_combo.currentText(),
                custom_question=custom_question,
                language=self.language_manager.current_language
            )
            self.current_content = content
        except Exception as e:
            logging.error(f"更新内容时出错：{e}")

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SearchApp()
    window.show()
    sys.exit(app.exec_())