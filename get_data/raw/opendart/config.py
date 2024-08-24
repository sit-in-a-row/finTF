import os
import yaml

def get_api_key():
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # yaml 파일의 절대 경로 생성
    yaml_path = os.path.join(current_dir, '../../../config/api_keys.yaml')

    # YAML 파일 읽기
    with open(yaml_path, "r") as file:
        config = yaml.safe_load(file)

    # 필요한 값 가져오기
    api_key = config['api_keys']['open_dart']

    return api_key