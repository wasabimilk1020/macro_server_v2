from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTabWidget,QTabBar,QHeaderView,QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor,QPixmap, QIcon
from tabTreeview_btn_img import TabTreeview_btn
from json_editor import JsonEditor
import json
import schedule
import re
import utils

class ImageViewer(QLabel):
  def __init__(self, image_path):
    super().__init__()
    self.path=image_path

  def set_pixmap(self):
    self.full_pixmap = QPixmap(self.path)  # 전체 이미지
    self.setPixmap(self.full_pixmap.copy(0, 0, 50, 30))  # 일부 이미지만 표시

  def enterEvent(self, event):
    """마우스가 들어왔을 때 전체 이미지를 표시"""
    self.setPixmap(self.full_pixmap.copy(0, 0, 100, 30))
    super().enterEvent(event)

  def leaveEvent(self, event):
    """마우스가 나갔을 때 이미지를 일부만 표시"""
    self.setPixmap(self.full_pixmap.copy(0, 0, 50, 30))
    super().leaveEvent(event)

# 탭 클래스
class TabContents(QWidget):
  def __init__(self,tab_name, tab_container, tab_contents,show_context_menu):
    super().__init__()
    self.tab_name = tab_name  # 탭 이름 설정
    self.tab_container = tab_container
    self.sio = None
    self.rowId={} #{"아이디":rowId}
    self.tab_contents=tab_contents  #TabTreeview_btn클래스에서 필요 한건데 실질적으로 index가 필요한거라 index를 넘겨주게 만들자
    self.show_context_menu=show_context_menu
    
  # QTreeWidget 생성
    self.tree_widget = QTreeWidget()
    self.tree_widget.setColumnCount(5)
    self.tree_widget.setHeaderLabels(["", "Name", "Status", "Log", "다이아"])
    self.tree_widget.setAlternatingRowColors(True)
    
    # 컬럼별 폭 수동 설정
    self.tree_widget.header().setSectionResizeMode(0, QHeaderView.Fixed)  # 첫 번째 컬럼 고정
    self.tree_widget.header().resizeSection(0, 45)  # 첫 번째 컬럼 폭
    self.tree_widget.header().resizeSection(1, 155)  # 두 번째 컬럼 폭
    self.tree_widget.header().resizeSection(2, 140)  # 세 번째 컬럼 폭
    self.tree_widget.header().resizeSection(3, 200)  # 네 번째 컬럼 폭
    self.tree_widget.header().resizeSection(4, 75)  # 다섯 번째 컬럼 폭
    # 체크박스 상태 변경 이벤트 연결
    self.tree_widget.itemChanged.connect(self.on_check_allOrnot)

  # 합산 결과 표시 라벨
    self.sum_label = QLabel("다이아 합계: 0")
    self.sum_label.setAlignment(Qt.AlignRight)
    
  # 버튼 및 이미지 레이아웃
    self.tabTreeview_btn_img = TabTreeview_btn(self.tab_name, self.tab_container, self.tab_contents, self.show_context_menu)
    self.json_editor = JsonEditor(self.tab_name, self.tab_container, self.tabTreeview_btn_img)

  # 레이아웃 설정
    #탭 영역은 왼쪽 트리뷰+버튼과 오른쪽 json_editor로 나뉘어짐
    self.tab_layout = QHBoxLayout()
    self.left_tab_layout = QVBoxLayout()  #트리뷰, sum_label, 버튼(안에 이미지 레이아웃)
    self.left_tab_layout.addWidget(self.tree_widget)
    self.left_tab_layout.addWidget(self.sum_label)
    self.left_tab_layout.addWidget(self.tabTreeview_btn_img)
    #이 레프트 탭 레이아웃도 어떤 클래스로 감싸서 하나의 위젯으로 만들 수 있을 것 같은데...
    self.tab_layout.addLayout(self.left_tab_layout)
    self.tab_layout.addWidget(self.json_editor)

    # #이미지 테스트용 데이터
    # for i in range(10):
    #   # self.tabTreeview_btn_img.image_layout("이해의시계", "00:00", "test.png", "test_gif.gif")  #git포함
    #   self.tabTreeview_btn_img.image_layout("이해의시계", "00:00", "test.png")  
      
    self.setLayout(self.tab_layout)

  def on_check_allOrnot(self, item, column):
    if column == 0:  # 체크박스 열만 처리
      total_items = self.tree_widget.topLevelItemCount()
      
      # 첫 번째 행 체크박스 상태 변경 시 전체 항목 체크/해제
      if item == self.tree_widget.topLevelItem(0):
        state = item.checkState(0)
        for i in range(1, total_items):
          child_item = self.tree_widget.topLevelItem(i)
          child_item.setCheckState(0, state)

  
class Tab(QWidget): #Tab과 TabContents를 분리해야되나 굳이? Tab클래스 내에서 다 하면 안되나?
  def __init__(self, tab_count):
    super().__init__()
    self.tab_container = QTabWidget()
    self.tab_layout = QVBoxLayout()
    self.sio = None
    self.nameList=[]
    self.character_list=None
    
    # --- 탭 추가 ---
    self.tab_contents = {}  # 탭 객체 딕트 {"PC01":탭 객체}
    self.create_tabs(tab_count, self.tab_container)
    self.tab_layout.addWidget(self.tab_container)
    self.setLayout(self.tab_layout)
    self.image_widgets={}

  def setup_character_list(self, PC_id):
    pass
    # self.character_list=character_list
    # self.tab_contents[PC_id].tabTreeview_btn_img.setup_character_list(character_list)  #버튼 클래스 초기화

  def create_tabs(self, tab_count, tab_container):  
    for i in range(1, tab_count + 1):
      tab_name = f"PC{i:02d}"
      tab = TabContents(tab_name, tab_container, self.tab_contents, self.show_context_menu)
      tab_container.addTab(tab, QIcon("./emoji/red_circle.png"), tab_name)
      self.tab_contents[tab_name] = tab
  
  def addLog(self, log, name, time, flag, PC_id):
    if PC_id not in self.tab_contents:
      print(f"없는 PC_id: {PC_id}")
      return
    #self.tab_contents[PC_id].rowId[name] 이 부분이 반복되니까 변수 담아서 처리하자 
    #플래그가 0이면 에러 1이면 상태 메세지로 처리하자
    if flag==0:
      if(name in self.tab_contents[PC_id].rowId):  
        self.tab_contents[PC_id].rowId[name].setText(3,"O")
        self.tab_contents[PC_id].rowId[name].setTextAlignment(2,Qt.AlignHCenter)
        self.tab_contents[PC_id].rowId[name].addChild(QTreeWidgetItem(self.tab_contents[PC_id].rowId[name],["","",time,log]))  
        # 특정 탭 이름만 빨간색으로 변경
        tab_index = self.tab_container.indexOf(self.tab_contents[PC_id])  # 현재 탭의 인덱스 가져오기
        if tab_index != -1:  # 유효한 인덱스라면
          self.tab_container.tabBar().setTabTextColor(tab_index, QColor("red"))
      else:
        print("없는 아이디")
    elif flag==1:
      if(name in self.tab_contents[PC_id].rowId):  
        self.tab_contents[PC_id].rowId[name].setText(2,time)
        self.tab_contents[PC_id].rowId[name].setText(3,log)
        self.tab_contents[PC_id].rowId[name].setTextAlignment(2,Qt.AlignHCenter)
      else:
        print("없는 아이디")

  def set_account(self, PC_id,character_list):
    self.name_list=character_list.keys()
    
    # 기존 rowId 데이터를 모두 제거
    self.tab_contents[PC_id].rowId.clear()
    self.tab_contents[PC_id].tree_widget.clear()  

    if self.name_list==[]:  # 빈 딕셔너리일 경우
      print("name_list가 비어 있음")
    else:
      # 첫 번째 열 첫 번째 행에 전체 체크박스 추가
      header_item = QTreeWidgetItem([""])
      header_item.setFlags(header_item.flags() | Qt.ItemIsUserCheckable)
      header_item.setCheckState(0, Qt.Checked)
      self.tab_contents[PC_id].tree_widget.addTopLevelItem(header_item)
      # 데이터 추가
      for index, name in enumerate(self.name_list):
        self.tab_contents[PC_id].rowId[name] = QTreeWidgetItem(["", f"{index+1}. {name}"])
        self.tab_contents[PC_id].rowId[name].setFlags(self.tab_contents[PC_id].rowId[name].flags() | Qt.ItemIsUserCheckable)
        self.tab_contents[PC_id].rowId[name].setCheckState(0, Qt.Checked)
        self.tab_contents[PC_id].tree_widget.addTopLevelItem(self.tab_contents[PC_id].rowId[name])

    tab_index = self.tab_container.indexOf(self.tab_contents[PC_id])  # 현재 탭의 인덱스 가져오기
    if tab_index != -1:  # 유효한 인덱스라면
      self.tab_container.tabBar().setTabTextColor(tab_index, QColor("black"))

    self.tab_contents[PC_id].tabTreeview_btn_img.setup_character_list_and_rowId(character_list, self.tab_contents[PC_id].rowId, header_item)
  
  def client_status_label(self, status, PC_id):
    self.tab_contents[PC_id].tabTreeview_btn_img.client_status.setText(status)
    tab_index = self.tab_container.indexOf(self.tab_contents[PC_id])  # 현재 탭의 인덱스 가져오기

    if status=="Client Status:ON":
      self.tab_contents[PC_id].tabTreeview_btn_img.client_status.setStyleSheet("color: green;")
      if tab_index != -1:  # 유효한 인덱스라면
        self.tab_container.setTabIcon(tab_index, QIcon("./emoji/green_circle.png"))
    else:
      self.tab_contents[PC_id].tabTreeview_btn_img.client_status.setStyleSheet("color: red;")
      if tab_index != -1:  # 유효한 인덱스라면
        self.tab_container.setTabIcon(tab_index, QIcon("./emoji/red_circle.png"))
  
  #---컨텍스트 메뉴 (버튼 오른쪽 클릭 메뉴 및 동작)
  def show_context_menu(self, position):
    clicked_button = self.sender()  # 이벤트를 보낸 버튼
    button_name=clicked_button.text()
    
    if not clicked_button:  # 버튼이 없으면 종료 (버튼이 없을 일이 있나? 뭐지 이거)
      return
    
    # QMenu 생성
    menu = QMenu(self)
    # 메뉴 항목 추가
    action1 = menu.addAction(f"{button_name} 실행")

    # 클릭된 버튼의 위치를 전역 좌표로 변환
    global_position = clicked_button.mapToGlobal(position)  #오른쪽 클릭 했을 때 메뉴가 나오는 마우스 좌표

    # 메뉴 실행
    action = menu.exec_(global_position)

    # 선택된 항목 확인
    if action == action1:
      for computer_id in self.tab_contents.keys():
        if button_name == "OFF":
          self.tab_contents[computer_id].tabTreeview_btn_img.checkStatusRun(True)
        elif button_name =="ON":
          self.tab_contents[computer_id].tabTreeview_btn_img.checkStatusRun(False)
        else:
          self.tab_contents[computer_id].tabTreeview_btn_img.send_command_to_client()   
  
  def stop_animation(self,btn_name,computer_id):
    button_name=btn_name
    #가끔 여기서 KeyError: 'status_check_button'
    # 작업 완료 시 애니메이션 중지 및 버튼 복원
    if button_name in self.tab_contents[computer_id].tabTreeview_btn_img.animations:
      animation =  self.tab_contents[computer_id].tabTreeview_btn_img.animations.pop(button_name)  # 애니메이션 제거
      animation.stop()
    # print("last_clicked_button: ",self.tab_contents[computer_id].tabTreeview_btn_img.last_clicked_button)
    self.tab_contents[computer_id].tabTreeview_btn_img.last_clicked_button[button_name].setStyleSheet("background-color: none;")
    self.tab_contents[computer_id].tabTreeview_btn_img.last_clicked_button[button_name].setEnabled(True)

  #---이미지 섹션
  # def image_layout(self, character_name, time, image_path, gif_path): #일단 gif는 보류
  # def image_layout(self, _character_name, time, image_path, computer_id):
  #   # 수직 레이아웃 생성
  #   image_vertical_box = QVBoxLayout()
  #   character_name = _character_name.split(maxsplit=1)[1]

  #   if character_name in self.image_widgets:
  #     self.image_widgets[character_name][0].setText(character_name)
  #     self.image_widgets[character_name][1].setText(time)
  #     self.image_widgets[character_name][2].set_pixmap()
  #   else: 
  #     self.image_widgets[character_name]=[]
  #     # 캐릭터 이름 QLabel
  #     name_label = QLabel(character_name)      
  #     image_vertical_box.addWidget(name_label)
  #     self.image_widgets[character_name].append(name_label)

  #     # 시간 QLabel
  #     time_label = QLabel(time)
  #     image_vertical_box.addWidget(time_label)
  #     self.image_widgets[character_name].append(time_label)

  #     # 이미지 뷰어
  #     image_viewer = ImageViewer(image_path)
  #     image_viewer.set_pixmap()
  #     image_vertical_box.addWidget(image_viewer)
  #     self.image_widgets[character_name].append(image_viewer)
  #     self.tab_contents[computer_id].tabTreeview_btn_img.image_main_layout.addLayout(image_vertical_box)
   
  def image_layout(self, _character_name, time, image_path, computer_id):
    # 수직 레이아웃 생성
    image_vertical_box = QVBoxLayout()

    # 앞부분 "리니지2M l " 같은 패턴을 제거 (없어도 그대로 반환 → 안전)
    character_name = re.sub(r"^리니지2M\s*l\s*", "", _character_name).strip()

    # 혹시나 완전 빈 문자열이면 원본 그대로 사용
    if not character_name:
        character_name = _character_name

    if character_name in self.image_widgets:
        self.image_widgets[character_name][0].setText(character_name)
        self.image_widgets[character_name][1].setText(time)
        self.image_widgets[character_name][2].set_pixmap()
    else:
        self.image_widgets[character_name] = []

        # 캐릭터 이름 QLabel
        name_label = QLabel(character_name)
        image_vertical_box.addWidget(name_label)
        self.image_widgets[character_name].append(name_label)

        # 시간 QLabel
        time_label = QLabel(time)
        image_vertical_box.addWidget(time_label)
        self.image_widgets[character_name].append(time_label)

        # 이미지 뷰어
        image_viewer = ImageViewer(image_path)
        image_viewer.set_pixmap()
        image_vertical_box.addWidget(image_viewer)
        self.image_widgets[character_name].append(image_viewer)

        self.tab_contents[computer_id].tabTreeview_btn_img.image_main_layout.addLayout(image_vertical_box)

  def diamond_update_sum(self, data, computer_id, name):
    """다이아 컬럼의 숫자 합계 업데이트"""
    diamond=data
    PC_id=computer_id
    character_name=name
    
    self.tab_contents[PC_id].rowId[character_name].setText(4,diamond)
    total = 0
    for i in range(1, self.tab_contents[PC_id].tree_widget.topLevelItemCount()):
      item = self.tab_contents[PC_id].tree_widget.topLevelItem(i)
      try:
        total += int(item.text(4))
      except ValueError:
        pass  # 숫자가 아니면 무시
    self.tab_contents[PC_id].sum_label.setText(f"다이아 합계: {total}")


