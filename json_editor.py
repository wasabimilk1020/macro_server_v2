import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel, QGroupBox
)
from PyQt5.QtCore import pyqtSlot
import utils

class JsonEditor(QWidget):
    def __init__(self, tab_name, tab_widget, tab_treeview_btn):
        super().__init__()
        self.tab_name = tab_name  # 탭 이름
        self.tab_widget = tab_widget
        self.tab_treeview_btn = tab_treeview_btn  # TabTreeview 객체 참조
        self.json_file = f"./json_files/PC_buttons/{tab_name}_btn.json"
        self.tables = {}  # 각 카테고리 테이블
        self.json_editor_layout = QVBoxLayout()

        # 초기화: 모든 탭 생성
        self.setup_tabs()

        # 저장 버튼
        self.save_button = QPushButton("Save Changes")
        self.save_button.setStyleSheet("background-color: green;")
        self.save_button.clicked.connect(self.save_json)  # 현재 탭만 저장
        self.json_editor_layout.addWidget(self.save_button)
        self.setLayout(self.json_editor_layout)
        
        # # 탭 변경 시그널 연결
        # self.tab_widget.currentChanged.connect(self.on_tab_changed)  # 탭 변경 이벤트 연결

    def setup_tabs(self):        
        try:
          tab_data = utils.load_json(self.json_file)
        except FileNotFoundError:
          print(f"{self.tab_name} JSON 파일이 없음")
          return
        except json.JSONDecodeError:
          print(f"{self.tab_name} JSON 파일의 형식이 잘못됨")
          return
        self.create_table(self.tab_name, tab_data)


    def create_table(self, tab_name, tab_data):
        """JSON 데이터를 기반으로 탭 생성."""
        table_layout = QVBoxLayout()

        for category, items in tab_data.items():
            group_box = QGroupBox(category)
            group_layout = QVBoxLayout()

            table = QTableWidget(len(items), 6)
            table.setHorizontalHeaderLabels(["Name", "X", "Y", "X 범위", "Y 범위", "충전석"])
            self.populate_table(table, items)
            self.tables[(tab_name, category)] = table

            # 열 크기 조정
            table.setColumnWidth(0, 70)  # Name
            table.setColumnWidth(1, 30)   # X
            table.setColumnWidth(2, 30)   # Y
            table.setColumnWidth(3, 45)   # X Range
            table.setColumnWidth(4, 45)   # Y Range
            table.setColumnWidth(5, 40)   # Delay

            group_layout.addWidget(table)

            btn_layout = QHBoxLayout()
            add_button = QPushButton("Add Row")
            add_button.clicked.connect(lambda _, c=category, t=tab_name: self.add_row(t, c))
            delete_button = QPushButton("Delete Row")
            delete_button.clicked.connect(lambda _, c=category, t=tab_name: self.delete_row(t, c))
            btn_layout.addWidget(add_button)
            btn_layout.addWidget(delete_button)
            group_layout.addLayout(btn_layout)

            group_box.setLayout(group_layout)
            table_layout.addWidget(group_box)

            # table.cellChanged.connect(self.on_cell_changed)
            table.itemChanged.connect(self.on_cell_changed)
            
        self.json_editor_layout.addLayout(table_layout)

    def on_cell_changed(self):
      self.save_button.setStyleSheet("background-color: red;")

    def populate_table(self, table, items):
        """테이블 데이터 채우기."""
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            table.setItem(row, 1, QTableWidgetItem(str(item.get("x", 0))))
            table.setItem(row, 2, QTableWidgetItem(str(item.get("y", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(item.get("xRange", 0))))
            table.setItem(row, 4, QTableWidgetItem(str(item.get("yRange", 0))))
            table.setItem(row, 5, QTableWidgetItem(str(item.get("charging", 0))))

    def add_row(self, tab_name, category):
        self.save_button.setStyleSheet("background-color: red;")
        """새 행 추가."""
        table = self.tables[(tab_name, category)]
        table.insertRow(table.rowCount())

    def delete_row(self, tab_name, category):
        self.save_button.setStyleSheet("background-color: red;")
        """선택된 행 삭제."""
        table = self.tables[(tab_name, category)]
        current_row = table.currentRow()
        if current_row != -1:
            table.removeRow(current_row)

    def update_tab_buttons(self, target_tab_name):
        """특정 탭의 버튼 레이아웃을 업데이트."""
        self.tab_treeview_btn
        if target_tab_name:
            self.tab_treeview_btn.load_buttons()
            print(f"Updated buttons for tab: {target_tab_name}")
        else:
            print(f"Tab {target_tab_name} does not exist.")

    def save_json(self):
        """특정 탭의 JSON 데이터를 저장."""
        json_file = self.json_file
        data_to_save = {}
        for (name, category), table in self.tables.items():
            if name != self.tab_name:
                continue
            data_to_save[category] = []
            for row in range(table.rowCount()):
                item = {
                    "name": table.item(row, 0).text() if table.item(row, 0) else "",
                    "x": int(table.item(row, 1).text()) if table.item(row, 1) else 0,
                    "y": int(table.item(row, 2).text()) if table.item(row, 2) else 0,
                    "xRange": int(table.item(row, 3).text()) if table.item(row, 3) else 0,
                    "yRange": int(table.item(row, 4).text()) if table.item(row, 4) else 0,
                    "charging": int(table.item(row, 5).text()) if table.item(row, 5) else 0,
                }
                data_to_save[category].append(item)
        try:
          utils.write_json(json_file, data_to_save)
        except FileNotFoundError:
          print(f"{self.tab_name} JSON 파일이 없음")
          return
        
        # with open(json_file, "w", encoding="utf-8") as f:
        #     json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        print(f"JSON file for tab {self.tab_name} saved successfully!")
        
        self.save_button.setStyleSheet("background-color: green;")
        # 저장 후 버튼 업데이트
        self.update_tab_buttons(self.tab_name)
