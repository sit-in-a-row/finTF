import os
import json
from .utils import get_model_summary_dict, load_json

def sector_analysis_info(sector, year, quarter):
    '''
    산업군, 연도, 분기를 입력하면 해당하는 Carhart 4 factor 분석 정보를 반환
    단, sector 자리에 종목의 ticker를 입력해도 무방함.

    ex. get_sector_analysis_info('금융업', '2019', 'Q1')

    가능한 산업군은 다음과 같음:
    ====================================================================
    '코스피 200 정보기술', '금융업', '코스피 200 중소형주', '증권', '코스피 200 중공업', 
    '코스피 200 금융', '운수창고업', '코스피 중형주', '코스피 200 생활소비재', '코스피 200 비중상한 30%', 
    '코스피 200 산업재', '코스피 100', '보험', '섬유의복', '코스피 200 건설', '코스피 대형주', '화학', 
    '코스피 200 커뮤니케이션서비스', '유통업', '제조업', '코스피 200 비중상한 25%', '코스피', '코스피 200', 
    '코스피200제외 코스피지수', '코스피 200 경기소비재', '코스피 50', '전기가스업', '코스피 200 TOP 10', 
    '코스피 소형주', '음식료품', '전기전자', '철강금속', '코스피 200 초대형제외 지수', '비금속광물', '의료정밀', 
    '기계', '통신업', '종이목재', '운수장비', '코스피 200 비중상한 20%', '의약품', '서비스업', '코스피 200 헬스케어', '건설업'
    '''

    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, f'../../store_data/process/analysis/index_analysis/{year}/{quarter}/코스피_carhart_results.json')

    dict_temp = load_json(path)

    try:
        if sector in list(dict_temp.keys()):
            dict_temp[sector] = get_model_summary_dict(dict_temp[sector])
            return dict_temp[sector]
        else:
            print(f'{sector}의 {year} {quarter} 산업군 분석 정보를 찾았으나 dict로 변환하는 과정에서 오류가 발생했습니다.')
    except Exception as e:
        print(f'{sector}의 {year} {quarter} 산업군 분석 정보를 찾을 수 없습니다! | {e}')
        return None