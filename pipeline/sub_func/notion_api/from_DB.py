import requests
import os
import yaml

# 현재 파일의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))
# yaml 파일의 절대 경로 생성
yaml_path = os.path.join(current_dir, '../../../config/api_keys.yaml')

# YAML 파일 읽기
with open(yaml_path, "r") as file:
    config = yaml.safe_load(file)

NOTION_API_TOKEN = config['api_keys']['NOTION_API_TOKEN']
NOTION_API_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_all_text_from_page(page_id):
    """
    page_id 입력 시 해당 페이지 본문 내의 텍스트 블럭 반환
    """

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.json()}")
        response.raise_for_status()

    data = response.json()
    blocks = data.get("results", [])
    
    # 텍스트 블럭에서 텍스트만 추출
    texts = []
    for block in blocks:
        if block.get("type") == "paragraph":
            paragraph = block.get("paragraph", {})
            rich_texts = paragraph.get("rich_text", [])
            for rich_text in rich_texts:
                texts.append(rich_text.get("text", {}).get("content", ""))

    final_text = ""
    for t in texts:
        final_text += t

    return final_text

def get_all_page_ids_from_database(agent_type):
    """
    agent_type 입력 시 {'글 제목': 'page_id', ...} 형식으로 반환
    """

    database_id = config['DB_IDs'][agent_type]
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    titles_and_ids = {}
    has_more = True
    next_cursor = None

    while has_more:
        # 요청 데이터
        data = {"start_cursor": next_cursor} if next_cursor else {}
        response = requests.post(url, headers=HEADERS, json=data)
        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.json()}")
            response.raise_for_status()
        
        data = response.json()
        pages = data.get("results", [])

        for page in pages:
            # 'Title' 속성에서 제목 추출 (제목이 데이터베이스에 따라 다를 수 있음)
            properties = page.get("properties", {})
            title_property = properties.get("Title", {}) 
            title = ""
            if title_property.get("type") == "title":
                title_texts = title_property.get("title", [])
                if title_texts:
                    title = title_texts[0].get("text", {}).get("content", "")
            
            # 제목과 페이지 ID를 딕셔너리에 추가
            titles_and_ids[title] = page["id"]
        
        # 다음 페이지 처리
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)

    return titles_and_ids
