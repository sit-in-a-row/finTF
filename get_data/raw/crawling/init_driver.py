import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# def init_driver(headless=False, download_dir=os.getcwd()):
def init_driver(download_dir=os.getcwd()):
    service = Service(ChromeDriverManager().install())
    chrome_options = Options()

    # if headless:
    #     chrome_options.add_argument("--headless")

    # 기본 다운로드 경로 설정
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,  # 다운로드 시 자동으로 처리
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True  # PDF 파일을 자동으로 다운로드하도록 설정
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver