import json
import logging

def load_json(json_file):
  with open(json_file, "r", encoding="utf-8") as f:
    return json.load(f)
 
def write_json(json_file, data):
  with open(json_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

# 로그 설정 (프로그램 시작 시 한 번만 실행)
logging.basicConfig(
  filename="server.log",
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s",
  encoding="utf-8"
)

 