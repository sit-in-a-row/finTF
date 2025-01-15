from .notion_utils import *
from .json_logging import add_id_to_json
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
# yaml 파일의 절대 경로 생성
yaml_path = os.path.join(current_dir, '../../../config/api_keys.yaml')

# YAML 파일 읽기
with open(yaml_path, "r") as file:
    config = yaml.safe_load(file)

def to_DB(agent_type, title, period, paragraph):
    """
    Notion DB에 페이지 만들고 본문 내용 추가하는 함수.

    agent_type: pf_selection_agent, t_1, t_2, ... t_5
    title: DB 내에 추가될 페이지의 제목
    period: 해당 페이지의 내용이 해당되는 시기
    paragraph: 페이지 내에 들어갈 본문
    """
    try:
        database_id = config['DB_IDs'][agent_type]

        # 1. 데이터베이스에 페이지 생성
        new_page = create_page_in_database(
            database_id=database_id,
            title=title,
            period=period
        )
        print(f"페이지 생성 완료: {new_page['id']}")

        # 2. 페이지 안에 텍스트 블럭 추가
        page_id = new_page["id"]
        add_text_to_page(page_id, paragraph)
        add_id_to_json(agent_type, title, page_id)

        print("텍스트 블럭 추가 완료")
    except Exception as e:
        print(f"오류 발생: {e}")    