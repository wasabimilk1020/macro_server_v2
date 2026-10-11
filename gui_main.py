import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGroupBox, QWidget,QPushButton,QMessageBox
from PyQt5.QtCore import Qt,QTimer
import tab
import schedule_table
from send_to_image import ImageAttachApp
from json_editor import JsonEditor
from schedule_manager import Scheduler

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("Lineage2M")
    self.setGeometry(1920, 800, 960, 1080)
    self.cleanup=None
    Scheduler()  #스케쥴러 실행 (이건 또 왜 여기서 호출할까??)

#---main_vbox top 
    #Account, Log, and json 위젯과 레이아웃
    self.main_top_groupBox = QGroupBox("Account and Log")
    self.main_top_widget_layout=QVBoxLayout()
    self.tab = tab.Tab(tab_count=8)
    self.main_top_widget_layout.addWidget(self.tab)
    self.main_top_groupBox.setLayout(self.main_top_widget_layout)

#---main_vbox bottom 
    self.main_bottom_hbox = QHBoxLayout()  # 메인 아래 레이아웃

    # 스케쥴 테이블 위젯과 레이아웃
    self.main_bottom_left_groupBox = QGroupBox("Schedule")
    self.main_bottom_left_groupBox.setMaximumHeight(290)
    self.schedule_layout = QVBoxLayout()
    self.schedule_table=schedule_table.ScheduleTable(self.tab)
    self.schedule_layout.addWidget(self.schedule_table)
    self.schedule_set_btn = QPushButton("스케줄 설정")
    self.schedule_set_btn.setFixedWidth(100)
    self.schedule_set_btn.clicked.connect(self.schedule_table.set_time)
    self.schedule_layout.addWidget(self.schedule_set_btn, alignment=Qt.AlignCenter)
    self.main_bottom_left_groupBox.setLayout(self.schedule_layout)
    self.main_bottom_hbox.addWidget(self.main_bottom_left_groupBox)

    #이미지 전송
    self.main_bottom_right_groupBox = QGroupBox("Image Transfer")
    self.send_to_image = ImageAttachApp()
    self.send_to_image_layout = QHBoxLayout()
    self.send_to_image_layout.addWidget(self.send_to_image)
    self.main_bottom_right_groupBox.setLayout(self.send_to_image_layout)
    self.main_bottom_hbox.addWidget(self.main_bottom_right_groupBox)
    
#---main_vbox 세팅
    self.main_widget = QWidget()
    self.main_vbox = QVBoxLayout()
    self.main_vbox.addWidget(self.main_top_groupBox)
    self.main_vbox.addLayout(self.main_bottom_hbox)
    self.main_widget.setLayout(self.main_vbox)
    self.setCentralWidget(self.main_widget)

  def setup_server(self, cleanup):
    self.cleanup=cleanup
    
  def closeEvent(self, event):  # Qt event handlers
    reply = QMessageBox.question(
      self, '확인', '서버가 실행 중입니다. 종료하시겠습니까?',
      QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )   
    if reply == QMessageBox.Yes:
      print("GUI 닫기: 서버 종료 중...")   
      QTimer.singleShot(0, self.cleanup)  #이벤트 루프에 방해 받지 않고 실행되게
      # 종료 허용
      event.accept()
      self.close()
    else:
      print("프로그램 종료 취소")
      event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

#이미지전송 해쉬 값도 같이 보내서 클라에서 확인하자 서버에서는 확인하지 말고 클라에서 확인해서 틀리면 로그 발생시키자
#이미지가 지금은 그냥 ui에서 커지는데 뭔가 말풍선 처럼 나와서 커지게 할 수 있을 것 같은데...