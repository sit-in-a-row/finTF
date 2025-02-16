import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def init_driver(download_dir=os.getcwd()):
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
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def parse_complex_table(html_content):
    """
    복수의 헤더 행을 가진 테이블을 파싱합니다.
    각 열의 최종 헤더를 구성한 후, 첫 번째 셀을 행 key로, 나머지 셀들을 헤더와 매핑하여 dict로 반환합니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        return None

    thead = table.find('thead')
    header_rows = thead.find_all('tr')
    # 첫 번째 행의 각 셀의 colspan을 고려하여 전체 열 수 계산
    total_cols = 0
    for cell in header_rows[0].find_all(['th', 'td']):
        colspan = int(cell.get('colspan', '1'))
        total_cols += colspan

    # 헤더 정보를 저장할 2차원 그리드 생성
    grid = [['' for _ in range(total_cols)] for _ in range(len(header_rows))]
    for r, row in enumerate(header_rows):
        cells = row.find_all(['th', 'td'])
        col = 0
        for cell in cells:
            # 이미 값이 채워진 칸은 건너뛰기
            while col < total_cols and grid[r][col]:
                col += 1
            colspan = int(cell.get('colspan', '1'))
            rowspan = int(cell.get('rowspan', '1'))
            text = cell.get_text(separator=" ", strip=True)
            for i in range(r, r + rowspan):
                for j in range(col, col + colspan):
                    grid[i][j] = text
            col += colspan

    # 세로로 헤더를 결합하여 최종 헤더 리스트 생성
    final_headers = []
    for j in range(total_cols):
        header_parts = []
        for i in range(len(header_rows)):
            if grid[i][j] and grid[i][j] not in header_parts:
                header_parts.append(grid[i][j])
        final_headers.append(" ".join(header_parts).strip())

    tbody = table.find('tbody')
    data = {}
    for row in tbody.find_all('tr'):
        cells = row.find_all(['th', 'td'])
        if not cells:
            continue
        row_key = cells[0].get_text(separator=" ", strip=True)
        row_values = [cell.get_text(separator=" ", strip=True) for cell in cells[1:]]
        # zip만 사용하면 열 개수가 달라도 매핑되므로, 헤더와 값의 개수를 맞춰줍니다.
        row_dict = {header: value for header, value in zip(final_headers[1:], row_values)}
        data[row_key] = row_dict
    return data

def parse_simple_table(html_content):
    """
    단일 헤더 행을 가진 테이블을 파싱합니다.
    첫 번째 셀을 key로, 나머지 셀들을 헤더와 매핑하여 dict로 반환합니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        return None

    header_row = table.find('thead').find('tr')
    headers = [cell.get_text(separator=" ", strip=True) for cell in header_row.find_all(['th', 'td'])]
    tbody = table.find('tbody')
    data = {}
    for row in tbody.find_all('tr'):
        cells = row.find_all(['th', 'td'])
        if not cells:
            continue
        key = cells[0].get_text(separator=" ", strip=True)
        values = [cell.get_text(separator=" ", strip=True) for cell in cells[1:]]
        row_dict = {h: v for h, v in zip(headers[1:], values)}
        data[key] = row_dict
    return data

def parse_earning_table(html_content):
    """
    어닝서프라이즈 테이블(4번째 테이블)은 구조가 다소 복잡하므로,
    tbody의 첫 행(날짜 헤더)을 기준으로 이후 행들을 그룹별로 파싱하여 dict로 반환합니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        return None

    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    if not rows or len(rows) < 2:
        return None

    # 첫 번째 행: 날짜 헤더 (예: [재무연월, 2024/09, 2024/12])
    header_cells = rows[0].find_all(['th', 'td'])
    headers = [cell.get_text(separator=" ", strip=True) for cell in header_cells]
    # 날짜는 두 번째, 세 번째 셀 (첫 셀이 '재무연월')
    if len(headers) >= 3:
        date1, date2 = headers[1], headers[2]
    else:
        date1, date2 = "날짜1", "날짜2"

    data = {}
    i = 1  # 두 번째 행부터 처리
    while i < len(rows):
        row = rows[i]
        # 마지막 행: 잠정치발표(예정)일/회계기준 (th에 colspan 속성이 있음)
        ths = row.find_all('th')
        if ths and ths[0].has_attr('colspan'):
            key = ths[0].get_text(separator=" ", strip=True)
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 3:
                val1 = cells[1].get_text(separator=" ", strip=True)
                val2 = cells[2].get_text(separator=" ", strip=True)
                data[key] = {date1: val1, date2: val2}
            i += 1
            continue

        # 새 그룹 시작: 해당 행의 첫 th에 "ext-tit" 클래스가 있으면 그룹의 시작
        group_th = row.find('th', class_="ext-tit")
        if group_th:
            group_name = group_th.get_text(separator=" ", strip=True)
            group_data = {}
            # 첫 번째 행의 두 번째 셀: 서브카테고리 (예: "컨센서스")
            sub_ths = row.find_all('th')
            if len(sub_ths) >= 2:
                subcat = sub_ths[1].get_text(separator=" ", strip=True)
                tds = row.find_all('td')
                if len(tds) >= 2:
                    group_data[subcat] = {date1: tds[0].get_text(separator=" ", strip=True),
                                            date2: tds[1].get_text(separator=" ", strip=True)}
            i += 1
            # 그룹은 일반적으로 4개 행(컨센서스, 잠정치, Surprise, 전년동기대비) + 1 ext0(전분기대비)로 구성됨
            count = 1
            while i < len(rows) and count < 5:
                r = rows[i]
                # ext0 행이면 (전분기대비)
                if "ext0" in r.get("class", []):
                    cells = r.find_all(['th', 'td'])
                    if len(cells) >= 3:
                        subcat = cells[1].get_text(separator=" ", strip=True)
                        tds = r.find_all('td')
                        if len(tds) >= 2:
                            group_data[subcat] = {date1: tds[0].get_text(separator=" ", strip=True),
                                                    date2: tds[1].get_text(separator=" ", strip=True)}
                    i += 1
                    break
                else:
                    cells = r.find_all(['th', 'td'])
                    if len(cells) >= 3:
                        # 일반 행: 첫 셀(서브카테고리)와 td 값들
                        subcat = cells[0].get_text(separator=" ", strip=True)
                        tds = r.find_all('td')
                        if len(tds) >= 2:
                            group_data[subcat] = {date1: tds[0].get_text(separator=" ", strip=True),
                                                    date2: tds[1].get_text(separator=" ", strip=True)}
                    i += 1
                    count += 1
            data[group_name] = group_data
        else:
            i += 1

    return data

def crawl_naver_dynamic(url):
    driver = init_driver()
    try:
        driver.get(url)
        # iframe 전환 (XPath는 동일)
        iframe_xpath = "/html/body/div[3]/div[2]/div[2]/div[1]/div[2]/iframe"
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath))
        )

        # 첫 번째 테이블 (복합 헤더 테이블)
        table1_xpath = "/html/body/div/form/div[1]/div/div[2]/div[3]/div/div/div[14]/table[2]"
        table1_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, table1_xpath))
        )
        html_table1 = table1_element.get_attribute("outerHTML")
        table1_dict = parse_complex_table(html_table1)

        # 두 번째 테이블 (복합 헤더 테이블)
        table2_xpath = "/html/body/div/form/div[1]/div/div[2]/div[3]/div/div/div[24]/table"
        table2_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, table2_xpath))
        )
        html_table2 = table2_element.get_attribute("outerHTML")
        table2_dict = parse_complex_table(html_table2)

        # 세 번째 테이블 (단일 헤더 테이블)
        table3_xpath = "/html/body/div/form/div[1]/div/div[2]/div[3]/div/div/div[7]/table"
        table3_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, table3_xpath))
        )
        html_table3 = table3_element.get_attribute("outerHTML")
        table3_dict = parse_simple_table(html_table3)

        # 네 번째 테이블 (어닝서프라이즈, 구조가 특수함)
        table4_xpath = "/html/body/div/form/div[1]/div/div[2]/div[3]/div/div/div[8]/table"
        table4_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, table4_xpath))
        )
        html_table4 = table4_element.get_attribute("outerHTML")
        table4_dict = parse_earning_table(html_table4)

        # 네 개의 dict를 튜플로 반환
        return (table1_dict, table2_dict, table3_dict, table4_dict)
    except Exception as e:
        print("크롤링 중 오류 발생:", e)
        return None
    finally:
        driver.quit()

def get_fin_statement_naver(ticker):
    url = f"https://finance.naver.com/item/coinfo.naver?code={ticker}&target=finsum_more"
    result = crawl_naver_dynamic(url)
    return str(result)