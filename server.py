from gevent import monkey, pywsgi, spawn, sleep,lock
# monkey.patch_all()
from PyQt5.QtCore import QTimer,pyqtSignal,QObject
from PyQt5.QtWidgets import QApplication
from socketio import Server, WSGIApp
import datetime
from urllib.parse import parse_qs
import sys
from gui_main import MainWindow
import json
import base64
import os
import utils

class SignalGenerator(QObject):
  log = pyqtSignal(object, object, object, object, object)
  set_account = pyqtSignal(object,object)
  user_signal_client_status_label = pyqtSignal(object,object)
  user_signal_stop_animation = pyqtSignal(object,object)
  user_signal_captured_img = pyqtSignal(object,object,object,object)
  user_signal_diamond = pyqtSignal(object, object, object)
  # user_signal_statusChk = pyqtSignal(object)


class WebSocketServer:
  def __init__(self, host='127.0.0.1', port=4000, main_window=None):
    self.host=host
    self.port=port
    self.sio = Server(async_mode='gevent')
    socketApp = WSGIApp(self.sio)
    self.server = pywsgi.WSGIServer((self.host, self.port), socketApp)
    self.pcList = {}  # 클라이언트 리스트 {"PC01": sid}
    self.sid_to_pc = {} #{"sid":"PC01"}
    self.cleanup_done=False #정리 작업을 위한 플래그
    self.cleanup_lock=lock.Semaphore()
    self.greenlet=None  #greenlet 저장용
    self.main_window=main_window
    self.signal_generator = SignalGenerator()  # SignalGenerator를 속성으로 생성 
    self.signal_generator.set_account.connect(main_window.tab.set_account)
    self.signal_generator.log.connect(main_window.tab.addLog)
    self.signal_generator.user_signal_client_status_label.connect(main_window.tab.client_status_label)
    self.signal_generator.user_signal_stop_animation.connect(main_window.tab.stop_animation)
    self.signal_generator.user_signal_captured_img.connect(main_window.tab.image_layout)
    self.signal_generator.user_signal_diamond.connect(main_window.tab.diamond_update_sum)
    # self.signal_generator.user_signal_statusChk.connect(main_window.tab.diamond_update_sum)
    print("signal 연결 당시 tab:", id(main_window.tab))

    # 이벤트 핸들러 등록
    self.sio.on('connect', self.connect)
    self.sio.on('disconnect', self.disconnect)
    self.sio.on('ping', self.handle_ping)
    self.sio.on("revAccount", self.revAccount)
    self.sio.on("logEvent", self.logEvent)
    self.sio.on("stop_animation", self.stop_animation)
    self.sio.on("captured_image", self.captured_image)
    self.sio.on("get_diamond", self.get_diamond)
  
  def connect(self, sid, environ):
    try:
      query_string = environ.get("QUERY_STRING")
      query_params = parse_qs(query_string)
      computer_id = query_params["computer_id"][0]  # "PC01"

      self.pcList[computer_id] = sid  #클라이언트 리스트 생성
      self.sid_to_pc[sid] = computer_id
      utils.logging.info(f"connect 성공: {computer_id} (sid={sid})")

      self.sio.emit("reqAccount","어카운트 정보 요청!",to=sid)
      utils.logging.info("reqAccount 전송 완료")

      #아래 Client Status:ON이라는게 그냥 클라이언트가 접속 했는지 안했는지를 나타내는건가? 
      #만약 그렇다면 어차피 탭에 색으로 표시되기 때문에 없애버리자.
      self.signal_generator.user_signal_client_status_label.emit("ON",computer_id)
      utils.logging.info("상태 라벨 변경 요청 완료")
      utils.logging.info(
            f"tab_contents 키 확인: {computer_id in main_window.tab.tab_contents}"
        )
      main_window.tab.tab_contents[computer_id].tabTreeview_btn_img.setup_data(self.pcList, self.sio)  #버튼 클래스 pcList setup
      utils.logging.info("setup_data 완료")
      main_window.send_to_image.setup_data(self.sio)
      utils.logging.info("send_to_image setup_data 완료")
    except:
      utils.logging.exception(
          f"connect 오류: computer_id={computer_id if 'computer_id' in locals() else 'unknown'}, sid={sid}"
        )
      
  def disconnect(self, sid):
    print("클라이언트 연결 끊김")
    computer_id=self.sid_to_pc[sid]
    self.signal_generator.user_signal_client_status_label.emit("OFF",computer_id)

  def handle_ping(self, sid, data):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self.sio.emit('pong', {"time": f"{current_time}"}, to=sid)
  
  #Set Account 버튼으로 캐릭터리스트를 갱신함
  def revAccount(self, sid, data):
    computer_id=self.sid_to_pc[sid]
    if computer_id is None:
      utils.logging.warning("등록되지 않은 SID: %s", sid)
      return
    character_list=data  #{"아이디":핸들 값...}
    self.signal_generator.set_account.emit(computer_id,character_list)
    
  def logEvent(self, sid, data):
    #[log_message, id, flag]
    log_message=data[0]
    character_name=data[1]
    flag=data[2]
    computer_id=self.sid_to_pc[sid]
    
    #현재 시간
    now = datetime.datetime.now()
    nowDatetime=now.strftime('%Y-%m-%d %H:%M')
    self.signal_generator.log.emit(log_message,character_name, nowDatetime, flag, computer_id)

  def stop_animation(self, sid, btn_name):
    button_name=btn_name
    computer_id=self.sid_to_pc[sid]
    self.signal_generator.user_signal_stop_animation.emit(button_name, computer_id)
  
  def captured_image(self, sid, data):
    id=data[0]
    current_time=data[1]
    img=data[2]
    computer_id=self.sid_to_pc[sid]
    image_data = base64.b64decode(img)
    # 파일로 저장
    with open(f"./image_files/{id}.png", "wb") as f:
      f.write(image_data)
    self.signal_generator.user_signal_captured_img.emit(id, current_time, f"./image_files/{id}.png", computer_id)
    
  def get_diamond(self, sid, data):
    diamond=data[0]
    character_name=data[1]
    computer_id=self.sid_to_pc[sid]
    self.signal_generator.user_signal_diamond.emit(diamond, computer_id, character_name)

  def cleanup(self):
    with self.cleanup_lock:  # Lock으로 보호 (메인스레드와 그린렛이 동시 접근)
      if self.cleanup_done:
        return
      self.cleanup_done = True  # Cleanup 시작
      print("Cleanup 시작")
      try:
        # 클라이언트 종료 및 서버 종료 로직
        for pc, sid in list(self.pcList.items()):
          print(f"Disconnecting client: {pc}")
          try:
            self.sio.disconnect(sid)
          except Exception as e:
            print(f"Error disconnecting client {sid}: {e}")

        if self.server.started:
          try:
            self.server.stop()
            print("서버가 정상적으로 종료되었습니다.")
          except Exception as e:
            print(f"서버 종료 중 오류 발생: {e}")

        if self.greenlet and not self.greenlet.dead:
          try:
            self.greenlet.kill()
            print("Greenlet이 종료되었습니다.")
          except Exception as e:
            print(f"Greenlet 종료 중 오류 발생: {e}")
      except Exception as e:
            print(f"Cleanup 중 예외 발생: {e}")

  def runServer(self, server):  # 서버 실행을 위한 함수
    try:
      print("서버 실행")
      server.serve_forever()  # 서버 실행
    except Exception as e:
        print(f"Server error: {e}")
    finally:
      self.cleanup()  # Gevent Lock을 사용해 안전하게 Cleanup

# class GuiHandler:
#   def __init__(self, main_window):
#     self.main_window = main_window

#   def handle_cleanup(self):
#     if self.main_window.ws_server:
#       self.main_window.ws_server.cleanup()
if __name__ == "__main__":
  app = QApplication(sys.argv)
  main_window = MainWindow()
  ws_server=WebSocketServer('192.168.50.29', 5000, main_window)
  #웹 소켓 connet에서 발생하는 tab를 위해 main_window를 ws_server에 전달
  #즉, gui변경이 웹 소켓에서 발생해야되는 상황.


  # 서버 실행 (Greenlet 스레드:gevent wsgi에 있는 스레드)
  ws_server.greenlet = spawn(ws_server.runServer, ws_server.server)  

  main_window.setup_server(ws_server.cleanup) 
  main_window.show()

  # PyQt 타이머로 gevent 이벤트 루프 실행
  timer = QTimer()
  timer.timeout.connect(lambda: sleep(0.1))  # gevent 루프 실행
  timer.start(100)  # 100ms마다 실행

  sys.exit(app.exec_())


#--구조
#
#--해결해야 할 것들
#1. gui와 서버를 확실히 분리하자
#2. 나머지는 어떻게 할 지 생각해보자.
#3. 클라이언트 접속은 탭에서 색으로 확인 할 수 있는대 가끔 접속은 됬는대 어카운트가 안오는 경우가 있음 어카운트 정보도 표시되게 만들자.
#4. 애니메이션에 아직도 문제가 있내. 스케쥴로 우편 실행 될때 다 안되고 한군대만 효과가 나오네. 스케쥴 전부 그런가 우편만 그런가??
#5. tabTreeview_btn에 tab_contents를 self로 보내는것 주석 처리로 완성해놨으니 주석 풀고 테스트. 문제가 show_context_menu때문에 안되는거였네...모든 클라에 어떻게 접근할까 이 방법 말고.
#6. #4번과 연관된건대 애니메이션이 어떻게 시작하고 스탑되는지 살펴보자. 스케쥴 시 왜 하나만 애니메이션이 동작하는지 자체는 이해했음. 위젯을 하나만 전달해주고 있음.
#7. #4, #6 스케쥴 테이블에서 list로 위젯을 보내는거까지는 맞는대. 이때 현재 send_command_to_client에서 인자로 list도 받게 하고 if문 분기를 하나더 만들어서 처리 할까
#아니면 아예 스케쥴 command 함수를 따로 만드는가 나을까? ssend_scheduled_command_to_client 이런 식으로. 음..chatgpt읽어 보니까 이 방법이 나은것 같다.
