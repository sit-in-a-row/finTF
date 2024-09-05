import os
import time
import random
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .init_driver import init_driver

def date_to_sedaily_format(date: str) -> str:
    """YYYYMMDD 형식을 YYYY-MM-DD로 변환"""
    year = date[:4]
    month = date[4:6]
    day = date[6:8]
    return f'{year}-{month}-{day}'

def crawl_sedaily_news(keyword: str, start_date: str, end_date: str) -> pd.DataFrame:
    """주어진 키워드 (or 종목 코드), 시작일자, 종료일자를 기준으로 서울경제의 관련 뉴스를 크롤링하여 CSV로 저장"""
    
    # 주어진 키워드가 종목 코드인지 검증 (문자열을 int로 변환 가능하면 종목 코드로 판단)
    is_stock_code = False
    try:
        stock_code = int(keyword)
        is_stock_code = True
    except:
        is_stock_code = False

    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 저장 경로 부모 디렉토리의 절대 경로 생성
    if is_stock_code:
        save_path = os.path.join(current_dir, f'../../../store_data/raw/crawling/corp_rel_news/')
    else:
        save_path = os.path.join(current_dir, f'../../../store_data/raw/crawling/general_news/')
    
    # 날짜 형식 변환
    start_date_formatted = date_to_sedaily_format(start_date)
    end_date_formatted = date_to_sedaily_format(end_date)
    
    # 저장 경로 생성
    year = start_date[:4]
    month = start_date[4:6]

    print('확인용:', year, month)
    save_path = os.path.abspath(save_path)
    save_directory = os.path.join(save_path, keyword, year, month)
    os.makedirs(save_directory, exist_ok=True)

    # CSV 파일 경로 설정 (YYYY-MM-DD 형식을 YYYY.MM.DD로 변경)
    csv_file_name = f'{keyword}_{start_date_formatted.replace("-", ".")}_{end_date_formatted.replace("-", ".")}.csv'
    csv_file_path = os.path.join(save_directory, csv_file_name)
    print('확인용:', csv_file_path)

    # 파일이 이미 존재하는지 확인하고, 존재하면 건너뜀
    if os.path.exists(csv_file_path):
        print(f'{csv_file_path} 파일이 이미 존재합니다. 크롤링을 건너뜁니다.')
        return pd.read_csv(csv_file_path)
    else:
        print('파일이 없습니다. 크롤링을 진행합니다...')

    # 첫 번째 페이지 URL 설정
    url = f'https://www.sedaily.com/Search/?scText={keyword}&scPeriod=0&scArea=tc&scPeriodS={start_date_formatted}&scPeriodE={end_date_formatted}&scDetail=detail&Page=1'
    
    # WebDriver 초기화
    download_path = os.path.join(save_path)
    driver = init_driver(download_path)
    driver.get(url)
    
    # 페이지네이션의 전체 길이 확인
    news_data_form = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'NewsDataFrm'))
    )
    
    try:
        # pagination_parent 존재 여부를 확인
        try:
            pagination_parent = news_data_form.find_element(By.CLASS_NAME, 'page')
            pagination_list = pagination_parent.find_elements(By.TAG_NAME, 'li')
            
            if len(pagination_list) > 10:
                nnext_attribute = pagination_list[-1].find_element(By.TAG_NAME, 'a').get_attribute('href')
                total_length = int(nnext_attribute.split('&Page=')[-1])
            else:
                total_length = len(pagination_list)
        except:
            total_length = 1  # pagination_parent가 없을 경우 페이지는 1개로 간주
        
        # 결과를 저장할 리스트
        crawled_news_result = []
        current_pg_idx = 1
        
        # 페이지네이션을 순회하며 크롤링
        for i in range(total_length):
            print(f'{i + 1}/{total_length} 페이지 크롤링 중...')
            
            if i > 0:
                updated_url = f'https://www.sedaily.com/Search/?scText={keyword}&scPeriod=0&scArea=tc&scPeriodS={start_date_formatted}&scPeriodE={end_date_formatted}&scDetail=detail&Page={current_pg_idx}'
                driver.get(updated_url)
                news_data_form = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'NewsDataFrm'))
                )
            
            news_list = news_data_form.find_element(By.CLASS_NAME, 'sub_news_list')
            news_row = news_list.find_elements(By.TAG_NAME, 'li')
            
            for news_element in news_row:
                time.sleep(random.uniform(1, 3))
                news_title = news_element.find_element(By.CLASS_NAME, 'article_tit').text.strip()
                news_category = news_element.find_element(By.CLASS_NAME, 'sec').text.strip()
                news_date = news_element.find_element(By.CLASS_NAME, 'date').text.strip()
                sub_dict = {
                    'news_title': news_title,
                    'news_category': news_category,
                    'news_date': news_date
                }
                crawled_news_result.append(sub_dict)
            
            current_pg_idx += 1
        
        # 드라이버 종료
        driver.quit()
        
        # DataFrame으로 변환 및 CSV 저장
        df = pd.DataFrame(crawled_news_result)
        
        # 경로에 따라 파일을 저장
        df.to_csv(csv_file_path, index=False)
        
        print(f'크롤링 완료. {csv_file_path}에 저장되었습니다.')
        return df
    except Exception as e:
        print(f'오류 발생: {e}')
        driver.quit()
