import requests
import yaml
import os

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

def create_page_in_database(database_id, title, period):
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Title": {
                "title": [
                    {"text": {"content": title}}
                ]
            },
            "Period": {
                "rich_text": [
                    {"text": {"content": period}}
                ]
            }
        }
    }

    response = requests.post(NOTION_API_URL, headers=HEADERS, json=data)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.json()}")
    response.raise_for_status()
    return response.json()

def add_text_to_page(page_id, text):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    # 텍스트를 2000자 단위로 분할
    chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": chunk}}
                ]
            }
        }
        for chunk in chunks
    ]

    # 요청 데이터 생성
    data = {"children": children}

    # API 요청
    response = requests.patch(url, headers=HEADERS, json=data)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.json()}")
        response.raise_for_status()
    return response.json()