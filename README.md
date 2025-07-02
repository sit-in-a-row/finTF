# finTF

주식 시장 분석과 포트폴리오 생성을 지원하기 위한 데이터 수집 및 파이프라인 코드 모음입니다. 
한국 주식 시장을 기반으로 다양한 경제 지표와 뉴스, 기업 공시 자료를 자동으로 수집하여 GPT 기반 분석에 활용합니다.

## 주요 구성

- **get_data/** : 원시 데이터를 수집하는 스크립트 모음
  - `raw/` 폴더에서 FRED, OpenDART, KRX 등 여러 소스의 데이터를 받아 저장합니다.
  - `raw_main.py`의 `update_all_raw_info()` 함수를 호출하면 전반적인 데이터 업데이트 과정을 실행할 수 있습니다.
- **store_data/** : 수집한 원본 자료와 가공된 데이터를 저장하는 위치
- **pipeline/** : GPT 및 통계 모델을 활용한 포트폴리오 생성 파이프라인
  - `pf_selection.py`와 `sub_func/` 하위 모듈은 섹터 선정과 종목 분석을 진행합니다.
  - `t1.py`, `t2_t4.py`, `t5.py` 등은 보고서 작성과 트레이딩 전략 생성을 담당합니다.
  - `chatbot/` 디렉터리에는 FAISS 기반 RAG 챗봇 구현이 포함되어 있습니다.
- **demoday/** : 결과를 시각화하기 위한 간단한 웹 페이지 자료
- **analyze_portfolio.py** : 샤프 지수, VaR 등의 지표로 포트폴리오를 평가하는 예제 스크립트
- **config/** : API 키를 보관하는 `api_keys.yaml` 예시 파일이 있습니다. 개인 키로 수정하여 사용하세요.

## 환경 설정

Python 3.8 이상의 환경을 권장합니다. 다음과 같은 주요 패키지가 필요합니다.

```
pandas, numpy, yfinance, matplotlib, pykrx, openai, tensorflow, torch,
selenium, faiss-cpu, easyocr
```

가상환경을 만든 뒤 위 패키지들을 설치하여 사용하세요.

## 기본 사용법

1. `config/api_keys.yaml` 파일에 본인의 OpenDART, FRED, OpenAI API 키를 입력합니다.
2. 필요한 원시 데이터를 수집하려면 `python get_data/get_data_raw.py`를 실행합니다.
3. 파이프라인을 통해 포트폴리오 분석을 수행하려면 `pipeline/` 하위 모듈을 실행합니다. 예를 들어 `t1.py` 는 GPT를 이용한 종목 분석 보고서를 생성합니다.
4. `demoday/` 폴더의 웹 리소스를 통해 결과를 시각적으로 확인할 수 있습니다.

세부적인 사용 절차는 각 스크립트의 주석을 참고해 주세요.
