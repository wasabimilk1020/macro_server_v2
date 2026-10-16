from PyQt5.QtWidgets import QTableWidget,QHeaderView,QVBoxLayout,QTableWidgetItem,QWidget
from PyQt5.QtCore import Qt,pyqtSignal,QObject
import random
import schedule

class SignalGenerator(QObject):
  user_signal_schedule_send_command_to_client = pyqtSignal(object, object)
  
class ScheduleTable(QWidget):
  def __init__(self,tab_tree_view):
    super().__init__()
    self.tables=[]  #테이블 객체
    self.tab_tree_view=tab_tree_view
    self.scheduled_buttons = {}  # 헤더 제목과 버튼 객체 매핑
    self.signal_generator = SignalGenerator()
    for computer_id in self.tab_tree_view.tab_contents.keys():
      # print("computer_id",computer_id)
      self.signal_generator.user_signal_schedule_send_command_to_client.connect(self.tab_tree_view.tab_contents[computer_id].tabTreeview_btn_img.send_command_to_client)
    
    # 메인 레이아웃
    layout = QVBoxLayout()
    # 테이블 헤더 설정
    self.table_titles = [
        ["모닝","오전 우편", "오후 우편", "저녁 우편", "밤 우편"],
        ["파괴된성채","격전의섬"]
        # ["파괴된성채", "크루마탑", "안타라스","시즌패스", "격전의섬"]
    ]
    # 두 개의 테이블 생성
    for titles in self.table_titles:
      table = self.create_table(titles)
      self.tables.append(table)
      layout.addWidget(table)
    self.setLayout(layout)
      
  def create_table(self, titles):
    table = QTableWidget(1, 5)  # 1행 5열 테이블 생성
    table.setHorizontalHeaderLabels(titles)  # 열 제목 설정
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) #수평헤더고 크기가 위젯에 맞춰짐
    table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch) #수직헤더고 크기가 위젯에 맞춰짐
    
    return table
    
  def set_data(self): #데이터를 이 함수를 이용해 세팅해줘야 한다
    pass

  def set_schedule_with_button(self, header_title):
    button = self.scheduled_buttons.get(header_title)
    if button:
      self.signal_generator.user_signal_schedule_send_command_to_client.emit(button, header_title)

  #여기 for루프가 너무 많은대...??
  # 스케줄 설정 함수
  def setup_schedule(self, schedule_time, table_headers):
    for table_index, times in enumerate(schedule_time):
      headers = table_headers[table_index]
      for idx, scheduled_time in enumerate(times):
        header_title = headers[idx].split()[-1]  # 현재 컬럼의 헤더 제목
        # 버튼 객체 미리 찾기
        for computer_id in self.tab_tree_view.tab_contents.keys():
          for button_group_list in self.tab_tree_view.tab_contents[computer_id].tabTreeview_btn_img.buttonsFromJson.values():
            for button_dict in button_group_list:
              if button_dict["name"]==header_title:
                button=button_dict["btn_widget"]

          if button:
            self.scheduled_buttons[header_title] = button
            schedule.every().day.at(scheduled_time).do(self.set_schedule_with_button, header_title).tag('routine')
            break
    
  def set_time(self): 
    schedule_time=[]  #[['09:37', '10:43', '14:40', '18:44', '22:19'], ['13:43', '15:37', '16:44', '21:40', '23:44']]
    schedule.clear(tag='routine')
    hours_list=[
        ["09","10","14","18","22"],
        ["13", "19"] #파괴, 격섬
        # ["13","15","16","21","23"] #파괴, 크루마, 안타, 시즌패스, 격섬
      ]
    
    minutes_list=[]
    for i in range(5):
      minutes_list.append(str(random.randint(10, 50))) 
    
    for idx, table in enumerate(self.tables):
      hours=hours_list[idx]
      time_list=[]
      for column, hour in enumerate(hours):  
        minutes=random.choice(minutes_list)
        time=f"{hour}:{minutes}"
        schedule_time_widget=QTableWidgetItem(time)
        schedule_time_widget.setTextAlignment(Qt.AlignCenter)
        table.setItem(0, column, schedule_time_widget)
        time_list.append(time)
      schedule_time.append(time_list)
    self.setup_schedule(schedule_time, self.table_titles)

    
#시간이 되면 contextmenu가 실행되야 한다.

     
  # schedule.every().day.at(setTimePostbox[1]).do(schedulePostBox,1).tag('routine')