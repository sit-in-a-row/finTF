import time
import os
import re
import pandas as pd
import easyocr
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

curr_dir = os.path.dirname(os.path.abspath(__file__))
screenshot_dir = os.path.join(curr_dir, "screenshots")

# 스크린샷 디렉토리 없으면 생성
if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)

def init_driver(download_dir=curr_dir):
    """Chrome WebDriver 초기화"""
    service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")  # 최신 Chrome 버전 호환

    return webdriver.Chrome(service=service, options=chrome_options)


def click_button(driver, xpath, timeout=10):
    """버튼 클릭 함수"""
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        button.click()
        time.sleep(1)
        return True
    except TimeoutException:
        return False


def set_date_input(driver, start_xpath, end_xpath, start_date, end_date, time_start_xpath, time_end_xpath):
    """날짜 및 시간 입력 필드 설정 함수"""

    def update_input(xpath, date_value):
        """한 글자씩 날짜 입력"""
        try:
            date_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            date_element.click()
            date_element.send_keys(Keys.END)
            time.sleep(0.2)
            for _ in range(10):
                date_element.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)
            for char in date_value:
                date_element.send_keys(char)
                time.sleep(0.2)
        except TimeoutException:
            pass

    def select_time(xpath):
        """드롭다운에서 '00:00' 선택"""
        try:
            time_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            time_element.click()
            time_item = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'desktop_time_input_item_00:00'))
            )
            time_item.click()
        except TimeoutException:
            pass

    select_time(time_start_xpath)
    select_time(time_end_xpath)
    update_input(start_xpath, start_date)
    update_input(end_xpath, end_date)

def move_mouse_to_canvas(driver, canvas_xpath, additional):
    """
    `canvas` 요소의 왼쪽 상단 모서리로 마우스를 이동하는 함수
    """
    try:
        canvas_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, canvas_xpath))
        )

        # 캔버스 위치 및 크기 가져오기
        location = canvas_element.location
        size = canvas_element.size
        # print(f"📸 캔버스 위치: {location}, 크기: {size}")

        # 스크린샷에서 캔버스 영역만 크롭하기
        left = -1 * 1/2 * (size['width'])
        top = -1 * 1/2 * (size['height'])

        bar_count = 44

        interpolation = (size['width'] / bar_count) * additional

        actions = ActionChains(driver)
        actions.move_to_element_with_offset(canvas_element, left + interpolation, top)  # 왼쪽 위 (1,1)으로 이동
        actions.perform()

        # print("✅ 마우스 이동 완료: canvas 요소 왼쪽 위")
        time.sleep(0.3)  # UI 반영 대기

    except TimeoutException:
        print("❌ Canvas 요소를 찾을 수 없음")
        pass

def capture_canvas_screenshot(driver, canvas_xpath, i):
    """캔버스 요소의 스크린샷을 찍어 OCR 수행"""
    try:
        canvas_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, canvas_xpath))
        )
        screenshot_path = os.path.join(screenshot_dir, "full_screenshot.png")
        driver.save_screenshot(screenshot_path)

        location = canvas_element.location
        size = canvas_element.size
        image = Image.open(screenshot_path)
        left, top, right, bottom = location["x"] * 2, location["y"] * 2, location["x"] * 2 + size["width"] * 2, location["y"] * 2 + size["height"] * 2
        cropped_image = image.crop((left, top, right, bottom))
        cropped_screenshot_path = os.path.join(screenshot_dir, f"canvas_cropped_{i}.png")
        cropped_image.save(cropped_screenshot_path)

        return cropped_screenshot_path
    except Exception:
        return None

def extract_bottom_text_from_image(image_path):
    """OCR을 사용하여 캔버스 이미지에서 날짜 텍스트 추출"""
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)


def extract_valid_datetime(text):
    """OCR 결과에서 날짜를 감지하고 pandas datetime 형식으로 변환"""
    pattern = r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) .*?:00\b"
    cleaned_text = text.replace("\n", " ").replace("‘", "'").replace("’", "'").strip()
    matches = re.findall(pattern, cleaned_text)

    if not matches:
        return None

    normalized_dates = [re.sub(r"(\d{2}) (\d{2}:\d{2})$", r"'\1 \2", date) if "'" not in date else date for date in matches]
    df = pd.DataFrame(normalized_dates, columns=["Timestamp"])
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%a %d %b '%y %H:%M", errors='coerce')

     # 🔹 UTC → 한국 시간(KST, UTC+9) 변환
    df["Timestamp"] = df["Timestamp"] + pd.Timedelta(hours=9)

    return df


def extract_text_from_xpath(driver, xpath):
    """OHLC 데이터를 추출하여 딕셔너리 변환"""
    try:
        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
        extracted_text = element.text.strip().split("\n")

        if len(extracted_text) >= 8:
            return {"O": extracted_text[1], "H": extracted_text[3], "L": extracted_text[5], "C": extracted_text[7], "Change": extracted_text[8] if len(extracted_text) > 8 else None}
        return None
    except TimeoutException:
        return None


def scrape_tradingview_data(ticker, start_date, end_date, log=False):
    """TradingView에서 날짜별 OHLC 데이터를 스크래핑하고 DataFrame으로 변환"""
    driver = init_driver()
    driver.get(f"https://www.tradingview.com/chart/?symbol={ticker}")

    if log:
        print('TradingView 웹사이트에 접속 중...')

    click_button(driver, '''//*[@id="header-toolbar-intervals"]/button''')
    click_button(driver, "//div[@role='row' and @data-value='60']")
    click_button(driver, "/html/body/div[2]/div[5]/div[2]/div/div[2]/div/button")
    click_button(driver, '''//*[@id="CustomRange"]''')

    if log:
        print('날짜 입력 중...')

    set_date_input(
        driver,
        start_xpath='//*[@data-name="start-date-range"]',
        end_xpath='//*[@data-name="end-date-range"]',
        start_date=start_date,
        end_date=end_date,
        time_start_xpath='//*[@id="overlap-manager-root"]/div[2]/div/div[1]/div/div[3]/div/div/div[1]/div[2]/span/span[2]',
        time_end_xpath='//*[@id="overlap-manager-root"]/div[2]/div/div[1]/div/div[3]/div/div/div[2]/div[2]/span/span[2]'
    )

    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'submitButton-PhMf7PhQ'))).click()
    except TimeoutException:
        pass

    additional = 0
    data = []

    if log:
        print('데이터 수집 중...')

    for i in range(10):
        time.sleep(1)
        move_mouse_to_canvas(driver, '''/html/body/div[2]/div[5]/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/canvas[2]''', additional)

        screenshot_path = capture_canvas_screenshot(driver, '''/html/body/div[2]/div[5]/div[1]/div[1]/div/div[2]/div[2]/div[2]/div/canvas[2]''', i)
        extracted_text = extract_bottom_text_from_image(screenshot_path)
        valid_datetime = extract_valid_datetime(extracted_text)

        price_data = extract_text_from_xpath(driver, '''/html/body/div[2]/div[5]/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div[1]/div[1]/div[1]/div[2]/div''')

        if valid_datetime is not None and price_data is not None:
            data.append({**price_data, "Timestamp": valid_datetime["Timestamp"][0]})

        additional += 1

    df = pd.DataFrame(data)

    driver.quit()
    return df