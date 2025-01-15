import json
import os

# 현재 파일의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))
# JSON 파일 경로
json_file_path = os.path.join(current_dir, "../../notion_page_ids.json")

# JSON 파일 열기 및 읽기
def read_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        # 파일이 없으면 빈 딕셔너리를 반환
        return {}

# JSON 파일 수정
def write_json(file_path, new_data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(new_data, file, ensure_ascii=False, indent=4)

def add_id_to_json(agent_type, title, id):
    """
    api를 통해 생성한 보고서 등의 page_id를 json에 저장

    agent_type: 'pf_selection_agent', 't_1', 't_2', ... 't_5' 중 하나
    title: 생성한 페이지의 제목
    id: 생성한 페이지의 id
    """
    data = read_json(json_file_path)
    data[agent_type][title] = id
    write_json(json_file_path, data)