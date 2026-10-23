from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,QHBoxLayout, QPushButton, QLabel,QMainWindow,QGroupBox,QLineEdit,QGridLayout,QSpinBox,QSizePolicy, QMessageBox,QMenu
from PyQt5.QtGui import QPixmap,QMovie,QColor,QStandardItemModel,QIcon
import sys,json
from PyQt5.QtCore import Qt,QVariantAnimation, QTimer,QObject,pyqtSignal
import schedule
import  time
from datetime import timedelta
import utils

class SignalGenerator(QObject):
  user_signal_send_command_to_client= pyqtSignal(object,object)
  user_signal_start_animation = pyqtSignal(object,object)
  user_signal_setText_time_for_statusChk = pyqtSignal(object,object)

class GifViewer(QLabel):
  def __init__(self, gif_path):
    super().__init__()
    self.movie = QMovie(gif_path)
    self.setMovie(self.movie)
    # GIF 시작
    self.movie.start()
    # 초기 크기 설정 (작게 표시)
    self.setFixedSize(50, 30)
    self.setScaledContents(True)

  def enterEvent(self, event):
    """마우스가 위로 올려졌을 때 원본 크기로 변경"""
    self.setFixedSize(100, 30)
    super().enterEvent(event)

  def leaveEvent(self, event):
    """마우스가 나갔을 때 작은 크기로 변경"""
    self.setFixedSize(40, 30)
    super().leaveEvent(event)
  
#---이 파일의 메인 클래스
class TabTreeview_btn(QWidget):
  def __init__(self,tab_name, tab_widget, tab_contents):
  # def __init__(self, parent_tab, tab_name, tab_widget, tab_content):
    super().__init__()
    self.tab_name=tab_name
    self.sio=None
    self.pcList=None
    self.tab_widget=tab_widget
    self.tab_contents=tab_contents
    # self.tab_content=tab_content
    # self.parent_tab=parent_tab
    self.last_clicked_button={}
    self.character_list=None
    self.rowId={}
    self.header_item=None
    self.run_btn_cnt=0
    self.signal_generator = SignalGenerator()
    self.signal_generator.user_signal_start_animation.connect(self.start_animation)
    self.signal_generator.user_signal_send_command_to_client.connect(self.send_command_to_client)
    self.signal_generator.user_signal_setText_time_for_statusChk.connect(self.setText_time_for_statusChk)
    self.buttonsFromJson={} #json 버튼 데이터
    self.animations = {}  #애니메이션 객체를 위한 딕트
    
    self.run_btn = QPushButton("OFF")
    self.status_check_label = QLabel("Status Check:")
    self.run_btn.setContextMenuPolicy(Qt.CustomContextMenu) # 컨텍스트 메뉴 활성화 (우클릭 이벤트)
    self.run_btn.customContextMenuRequested.connect(self.show_context_menu)
    # self.run_btn.customContextMenuRequested.connect(self.parent_tab.show_context_menu)
    self.run_btn.setFixedSize(100, 22)
    self.run_btn.setCheckable(True)
    self.run_btn.toggled.connect(self.checkStatusRun)
  
    self.client_status_horizontal=QHBoxLayout()
    self.client_status_horizontal.setAlignment(Qt.AlignLeft)
    self.client_status_horizontal.addWidget(self.status_check_label)
    self.client_status_horizontal.addWidget(self.run_btn)

    #reset and Set Account buttons
    self.reset_button = QPushButton("reset")
    self.reset_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    self.reset_button.setShortcut("F1")
    self.reset_button.setToolTip("단축키(F1)")
    self.reset_button.clicked.connect(self.reset_status_and_log)
    self.set_account_btn=QPushButton("Set Account")
    self.set_account_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    self.set_account_btn.clicked.connect(self.set_account_fct)

    self.status_reset_btn_layout = QHBoxLayout()  #status 라벨과 reset 버튼 메인 레이아웃
    self.status_reset_btn_layout.addLayout(self.client_status_horizontal)
    self.status_reset_btn_layout.addWidget(self.set_account_btn)
    self.status_reset_btn_layout.addWidget(self.reset_button)

    #버튼 그룹박스 위젯에 각각 grid layout 세팅
    self.dungeon_grid_layout = QGridLayout()
    self.routine_grid_layout = QGridLayout()
    self.setting_grid_layout = QGridLayout()
    self.dungeon_group_btn_layout=QGroupBox("던전")
    self.dungeon_group_btn_layout.setLayout(self.dungeon_grid_layout)
    self.routine_group_btn_layout=QGroupBox("루틴")
    self.routine_group_btn_layout.setLayout(self.routine_grid_layout)
    self.setting_group_btn_layout=QGroupBox("세팅")
    self.setting_group_btn_layout.setLayout(self.setting_grid_layout)

    #메인 레이아웃에 세팅
    self.tabContents_layout=QVBoxLayout() #여기서는 이게 main layout이다. 이게 main gui에서 원하는 곳에 위치하면된다
    self.tabContents_layout.addLayout(self.status_reset_btn_layout)
    self.tabContents_layout.addWidget(self.dungeon_group_btn_layout)
    self.tabContents_layout.addWidget(self.routine_group_btn_layout)
    self.tabContents_layout.addWidget(self.setting_group_btn_layout)

    self.image_main_layout=QHBoxLayout()  #이미지 레이아웃
    self.tabContents_layout.addLayout(self.image_main_layout)

    self.setLayout(self.tabContents_layout) 
    self.load_buttons()  #default button 생성

  def setup_data(self, pcList, sio):
    self.pcList=pcList
    self.sio=sio
  
  def setup_character_list_and_rowId(self, character_list, rowid, header_item):
    self.character_list=character_list
    self.rowId=rowid
    self.header_item=header_item

  def setText_time_for_statusChk(self,row,message):
    if self.header_item is None:
      print("header_item이 None입니다. setText 실행 불가")
      return

    self.header_item.setText(row,message)
    self.header_item.setTextAlignment(row,Qt.AlignHCenter)

  def set_schedule_chkStatus(self, clicked_button, button_name, decomposeItem_button, client_tag, schedule_min):
    self.run_btn_cnt+=1
    self.last_clicked_button[button_name]=clicked_button
    button=decomposeItem_button
    sid=self.pcList[self.tab_name]

    job=schedule.get_jobs(client_tag)
    new_time = job[0].next_run + timedelta(minutes=schedule_min)

    if self.run_btn_cnt==3:
      self.signal_generator.user_signal_setText_time_for_statusChk.emit(3, new_time.strftime('%H:%M:%S'))
      self.signal_generator.user_signal_send_command_to_client.emit(button, "아이템분해")
      self.run_btn_cnt=0
    elif self.run_btn_cnt==2:
      self.signal_generator.user_signal_setText_time_for_statusChk.emit(3, f"아이템분해: {new_time.strftime('%H:%M:%S')}")
      self.sio.emit('button_schedule', {"status_check_button":[1,1,1,1,1],"character_list":{}}, to=sid)
      self.signal_generator.user_signal_start_animation.emit(clicked_button, button_name)  #(button_name="OFF")
    else:
      self.signal_generator.user_signal_setText_time_for_statusChk.emit(3, new_time.strftime('%H:%M:%S'))
      self.sio.emit('button_schedule', {"status_check_button":[1,1,1,1,1],"character_list":{}}, to=sid)
      self.signal_generator.user_signal_start_animation.emit(clicked_button, button_name)  #(button_name="OFF")

  def checkStatusRun(self, checked):
    clicked_button=self.run_btn
    button_name="status_check_button"
    client_tag= f"chkStatusSchedule_{self.tab_name}"
    tab_index = self.tab_widget.indexOf(self.tab_contents[self.tab_name])  # 현재 탭의 인덱스 가져오기
    # tab_index = self.tab_widget.indexOf(self.tab_content)  # 현재 탭의 인덱스 가져오기
    schedule_min=30

    for config in self.buttonsFromJson["루틴"]: #아이템분해 버튼이 반드시 루틴 그룹에 있어야함
      if config["name"] == "아이템분해":
        decomposeItem_button = config["btn_widget"]
        break

    if checked:
      self.run_btn.setText("ON")
      if tab_index != -1:  # 유효한 인덱스라면
        self.tab_widget.setTabText(tab_index, f"✅ {self.tab_name}")
      schedule.clear(client_tag)
      schedule.every(schedule_min).minutes.do(self.set_schedule_chkStatus, clicked_button, button_name, decomposeItem_button, client_tag, schedule_min).tag(client_tag)
      job=schedule.get_jobs(client_tag)
      self.setText_time_for_statusChk(2,"statusChk time:")
      self.setText_time_for_statusChk(3,job[0].next_run.strftime('%H:%M:%S'))
    else:
      self.run_btn.setText("OFF")
      if tab_index != -1:  # 유효한 인덱스라면
        self.tab_widget.setTabText(tab_index, f"❌ {self.tab_name}")
      schedule.clear(client_tag)
      self.setText_time_for_statusChk(2,"")
      self.setText_time_for_statusChk(3,"")
    
  def load_buttons(self):
    try:
      self.buttonsFromJson = utils.load_json(f"./json_files/PC_buttons/{self.tab_name}_btn.json")
    except FileNotFoundError:
      print(f"{self.tab_name} JSON 파일이 없음")
      return
    except json.JSONDecodeError:
      print(f"{self.tab_name} JSON 파일의 형식이 잘못됨")
      return
    
    for groupBox_name, json_button_configs in self.buttonsFromJson.items():
      if groupBox_name == "던전":
        self.create_button(self.dungeon_grid_layout, json_button_configs)
      elif groupBox_name == "루틴":
        self.create_button(self.routine_grid_layout, json_button_configs)
      elif groupBox_name == "세팅":
        self.create_button(self.setting_grid_layout, json_button_configs)
 
  def create_button(self, grid_layout, button_configs):
      #button_configs=[{버튼속성},{버튼속성}]
      while grid_layout.count():  # GridLayout의 모든 위젯 제거
          item = grid_layout.takeAt(0)
          widget = item.widget()
          if widget:
              widget.deleteLater()  # 위젯 메모리에서 삭제

      for i, button_config in enumerate(button_configs):
        button_name = button_config["name"]
        
        #버튼 위젯 생성 및 그리드 레이아웃에 배치
        qpush_btn = QPushButton(button_name)
        button_config["btn_widget"]=qpush_btn #위젯을 button_config에 할당 
        row = i // 6
        col = i % 6
        grid_layout.addWidget(qpush_btn, row, col)
  
        # 컨텍스트 메뉴 활성화 (우클릭 이벤트)
        qpush_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        qpush_btn.customContextMenuRequested.connect(self.show_context_menu)
        # qpush_btn.customContextMenuRequested.connect(self.parent_tab.show_context_menu)
  
        #버튼 클릭 시 동작
        qpush_btn.clicked.connect(
          lambda checked=False, btn=qpush_btn, name=button_name:
            self.send_command_to_client(btn, name)
        )

  #왼쪽 버튼 클릭 시 이벤트 핸들러  
  def send_command_to_client(self, btn_widget, btn_name):
    #이게 현재는 재시작 윈도우즈 스케쥴러에 예약하는거네
    #이것도 시간 설정을 하드 코딩 하지 말고 gui에서 예약 할 수 있게 바꿔야 하는대...
    if btn_name == "재시작": 
      sid = self.pcList.get(self.tab_name)
      if not sid:
          print("에러: 해당 클라이언트의 sid를 찾을 수 없습니다.")
          return
      # 부모를 명확히 지정 (현재 활성화된 윈도우)
      parent_window = QApplication.instance().activeWindow()
      # 비동기 메시지 박스를 안전하게 실행
      msg_box = QMessageBox(parent_window)
      msg_box.setWindowTitle("확인")
      msg_box.setText("컴퓨터 재시작 예약 하시겠습니까?")
      msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
      msg_box.setDefaultButton(QMessageBox.No)
      # 메시지 박스가 닫힐 때 후속 동작 실행
      def on_messagebox_closed(result):
        if result == QMessageBox.Yes:
          try:
            self.sio.emit('reboot_computer', {"days":"WED","time":"07:00"}, to=sid) #"days":"WED","time":"07:00" 이렇게 하드코딩하면 안된다. 임시
          except Exception as e:
            print(f"소켓 오류 발생: {e}")  # 네트워크 오류 발생 시 로그 출력
      msg_box.buttonClicked.connect(lambda btn_widget: on_messagebox_closed(msg_box.standardButton(btn_widget)))
      msg_box.open()  # exec_() 대신 open() 사용 (비동기 실행)
      return
    elif btn_name == "게임실행":
      sid = self.pcList.get(self.tab_name)
      if not sid:
          print("에러: 해당 클라이언트의 sid를 찾을 수 없습니다.")
          return
      self.sio.emit('game_start', {}, to=sid)
      return
    elif btn_name == "CODE":
      sid = self.pcList.get(self.tab_name)
      if not sid:
          print("에러: 해당 클라이언트의 sid를 찾을 수 없습니다.")
          return
      self.sio.emit('update_code', {}, to=sid)
      return
    else:
      emit_data=self.generate_button_data(btn_name,self.buttonsFromJson)
      
      self.last_clicked_button[btn_name]=btn_widget

      if emit_data is not None:
        if self.pcList is not None and self.sio is not None:
          sid=self.pcList[self.tab_name]
          #emit_data={"버튼이름":[데이터],"character_list":[{"아이디1":핸들 값1,"아이디2":핸들 값2}]}
          self.sio.emit('button_schedule', emit_data, to=sid)
          self.start_animation(btn_widget, btn_name) #애니메이션 추가
        else:
          print("set account 필요함")
    #버튼 이름에 따라 뭔가 역할을 나누지 말고 여기서는 그냥 버튼 데이터만 보내면 수행처리는 클라이언트에서 
    #하도록 하는게 뭔가 더 일관성 있어 보이긴하네...

  def generate_button_data(self, button_name,buttonsFromJson):
    emit_data={}
    selected_characters={}
    for group_configs in buttonsFromJson.values():
      for config in group_configs:
          if config["name"] == button_name:
            data_list = [
              config["x"],
              config["y"],
              config["xRange"],
              config["yRange"],
              config["charging"]
            ]
   
    emit_data[button_name]=data_list
    
    if self.rowId !={}:
      for name,rowid in self.rowId.items():  #수행할 캐릭터 데이터
        check_state=rowid.checkState(0) #컬럼 0을 가리킴 즉, 체크박스 상태
        if check_state== Qt.Checked:  #체크 된 아이디만 실행
          handle=self.character_list[name]
          selected_characters[name]=handle
          # self.last_clicked_button[button_name]=button
      emit_data["character_list"]=selected_characters
      #emit_data={"버튼이름":[데이터],"character_list":{"아이디1":핸들 값1,"아이디2":핸들 값2}}
      return emit_data
    else:
      print("어카운트 접속하지 않음")

#---버튼 애니메이션 기능
  def start_animation(self,btn, btn_name):
    button=btn
    button_name=btn_name

    # 버튼 클릭 비활성화 (중복 클릭 방지)
    button.setEnabled(False)
    
    # 애니메이션 생성
    animation = QVariantAnimation(
         self,
         startValue=QColor(255, 255, 255),  # 흰색 (원래 상태)
        endValue=QColor(128, 0, 128),  # 보라색
     )
    animation.setDuration(2000)  # 1초 동안 실행
    animation.valueChanged.connect(lambda color: button.setStyleSheet(f"background-color: {color.name()};")) 
    animation.setLoopCount(-1)  # 무한 반복
    animation.start()
   
    self.animations[button_name] = animation # 애니메이션 저장
    
  #트리뷰 Status and Log 초기화 핸들러
  def reset_status_and_log(self):
    for row_id in self.rowId.values():
      row_id.setText(2,"")
      row_id.setText(3,"")
      row_id.takeChildren()
      # 특정 탭 이름만 빨간색으로 변경
      tab_index = self.tab_widget.indexOf(self.tab_contents[self.tab_name])  # 현재 탭의 인덱스 가져오기
      # tab_index = self.tab_widget.indexOf(self.tab_content)  # 현재 탭의 인덱스 가져오기
      row_id.setCheckState(0,Qt.Checked)
      if tab_index != -1:  # 유효한 인덱스라면
        self.tab_widget.tabBar().setTabTextColor(tab_index, QColor("black"))
  
  def set_account_fct(self):
    pc_name=self.tab_name
    if self.pcList is not None:
      sid=self.pcList.get(pc_name)
      self.sio.emit("reqAccount","어카운트 정보 요청!",to=sid)
    else:
      print("클라이언트가 연결되지 않았습니다.")

  #---컨텍스트 메뉴 (버튼 오른쪽 클릭 메뉴 및 동작)
  def show_context_menu(self, position):
    clicked_button = self.sender()  # 이벤트를 보낸 버튼
    if not clicked_button:  
        return
    button_name=clicked_button.text()
    
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
          for button_group_list in self.tab_contents[computer_id].tabTreeview_btn_img.buttonsFromJson.values():
            for button_dict in button_group_list:
              if button_dict["name"]==button_name:
                button=button_dict["btn_widget"]
          self.tab_contents[computer_id].tabTreeview_btn_img.send_command_to_client(button, button_name)    


