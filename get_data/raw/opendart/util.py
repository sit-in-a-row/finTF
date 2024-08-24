from bs4 import BeautifulSoup
import re

def cleanse_text(response):
    '''
    과도한 줄바꿈을 클렌징해주는 코드 (줄바꿈이 연속될 시, 줄바꿈을 1개로 제한)
    '''
    try:
        # 연속된 줄바꿈을 하나의 줄바꿈으로 바꾸기
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        cleaned_text = re.sub(r'\n+', '\n', text)

        print('텍스트 클렌징 성공')
        return cleaned_text
    except Exception as e:
        print(f'텍스트 클렌징 실패 {str(e)}')
        return None
