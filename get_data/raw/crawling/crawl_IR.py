import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from pykrx import stock
from .init_driver import init_driver

def get_latest_file(download_path):
    """Download path에서 가장 최근에 생성된 파일을 반환"""
    files = [f for f in os.listdir(download_path) if f.endswith(".pdf")]
    if not files:
        return None
    latest_file = max([os.path.join(download_path, f) for f in files], key=os.path.getctime)
    return latest_file

def get_ticker_by_name(stock_name: str) -> str:
    """입력된 종목 이름에 해당하는 티커를 반환"""
    try:
        tickers = stock.get_market_ticker_list()
        for ticker in tickers:
            ticker_name = stock.get_market_ticker_name(ticker)
            if ticker_name and ticker_name.strip() == stock_name.strip():
                return ticker
    except Exception as e:
        print(f"티커 조회 중 오류 발생: {stock_name}: {e}")
    return 'unknown'

def crawl_ir_pdfs():
    # 드라이버 초기화 및 URL 열기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, '../../../store_data/raw/crawling/IR_pdf_raw')
    download_path = os.path.abspath(save_path)

    # WebDriver 초기화
    driver = init_driver(download_path)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get('https://kind.krx.co.kr/corpgeneral/irschedule.do?method=searchIRScheduleMain&gubun=iRMaterials&marketType=2&kosdaqSegment=1')
        time.sleep(3)  # 페이지 로딩 대기
    except Exception as e:
        print(f"페이지 로드 중 오류 발생: {e}")
        driver.quit()

    # 페이지네이션 및 다운로드 루프
    for i in range(1, 9):
        try:
            to_KOSPI = driver.find_element(By.ID, 'rWertpapier')
            to_KOSPI.click()

            set_timespan_all = driver.find_element(By.CLASS_NAME, 'ord-07')
            set_timespan_all.click()

            select_element = driver.find_element(By.TAG_NAME, "select")
            select = Select(select_element)
            select.select_by_value("100")  # 100개씩 보기

            pagination_wrap = driver.find_element(By.CLASS_NAME, 'paging')
            pagination_list = pagination_wrap.find_elements(By.TAG_NAME, 'a')
            pagination_list[i + 1].click()

            confirm = driver.find_element(By.CLASS_NAME, 'search-btn')
            confirm.click()

            time.sleep(random.uniform(3, 6))

            section = driver.find_element(By.CLASS_NAME, 'scrarea')
            rows = section.find_elements(By.TAG_NAME, 'tr')

            for j in range(1, len(rows)):
                try:
                    row = rows[j]
                    row_tds = row.find_elements(By.TAG_NAME, 'td')

                    corp_name = row_tds[1].text.strip()
                    date = row_tds[2].text.strip()

                    btns = row_tds[-1].find_elements(By.TAG_NAME, 'a')
                    btn = btns[-1]

                    pdf_title = btn.get_attribute('onclick').split(',')[-3]
                    if 'eng' in pdf_title.lower() or '영문' in pdf_title:
                        continue  # 영문 보고서는 건너뜁니다

                    btn.click()
                    time.sleep(random.uniform(5, 8))

                    latest_file = get_latest_file(download_path)
                    if latest_file:
                        stock_code = get_ticker_by_name(corp_name.strip())
                        # print(corp_name.strip())
                        # print(stock_code)

                        to_YYYY_MM = f'{date[:4]}.{date[5:7]}'

                        new_dir_path = os.path.join(download_path, stock_code, to_YYYY_MM)
                        new_file_name = f"{stock_code}_{corp_name}_{date}_IR.pdf"

                        # if stock_code:
                        #     new_dir_path = os.path.join(download_path, stock_code, to_YYYY_MM)
                        #     new_file_name = f"{stock_code}_{corp_name}_{date}_IR.pdf"
                        # else:
                        #     new_dir_path = os.path.join(download_path, 'unknown', to_YYYY_MM)
                        #     new_file_name = f"unknown_{corp_name}_{date}_IR.pdf"

                        os.makedirs(new_dir_path, exist_ok=True)
                        new_file_path = os.path.join(new_dir_path, new_file_name)

                        print(new_file_path)

                        os.rename(latest_file, new_file_path)
                        print(f"Renamed {os.path.basename(latest_file)} to {new_file_name}")

                except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
                    print(f"{j}번째 row 처리 중 오류 발생: {e}")
                    continue
                except Exception as e:
                    print(f"파일 저장 중 오류 발생: {e}")
                    continue

        except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
            print(f"{i}번째 페이지 처리 중 오류 발생: {e}")
            continue
        except Exception as e:
            print(f"페이지 처리 중 예상치 못한 오류 발생: {e}")
            continue

    # 브라우저 종료
    driver.quit()