import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
intl_news_path = os.path.join(current_dir, f'../../../store_data/raw/crawling/general_news')

quarter_map = {
    'Q1': [1, 2, 3],
    'Q2': [4, 5, 6],
    'Q3': [7, 8, 9],
    'Q4': [10, 11, 12]
}

def intl_news_info(year:str, start_date:str, end_date:str) -> pd.DataFrame:
    '''
    ticker, year와 시작일, 종료일을 입력하면 그에 맞춰 df 반환
    단, start_date와 end_date는 YYYYMMDD 형식으로 입력

    ex. intl_news_info('2019', '20190101', '20191231)
    '''
    df_list = []
    items_list = []

    items_list_raw = os.listdir(intl_news_path)
    for item in items_list_raw:
        try:
            int(item[:4])
        except:
            if item != '.DS_Store':
                items_list.append(item)
            continue

    for item in items_list:
        target_news_path = os.path.join(intl_news_path, item, year)

        # 월별 폴더 가져오기
        month_list = [month for month in os.listdir(target_news_path) if month != '.DS_Store']

        # 각 월별 폴더의 첫 번째 CSV 읽기
        for month in month_list:
            csv_target_news_path = os.path.join(target_news_path, month)
            try:
                file_name = os.listdir(csv_target_news_path)[0]

                df = pd.read_csv(os.path.join(csv_target_news_path, file_name))
                df_list.append(df)
            except:
                continue

    # DataFrame들을 세로로 합치기
    merged_df = pd.concat(df_list, axis=0, ignore_index=True)

    # news_date를 datetime으로 변환 후 인덱스로 설정
    merged_df['news_date'] = pd.to_datetime(merged_df['news_date'])
    merged_df.set_index('news_date', inplace=True)

    # 날짜 범위를 datetime으로 변환
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # 시간순으로 정렬
    merged_df = merged_df.sort_index()

    # loc을 사용해 날짜 인덱스 슬라이싱
    result_df = merged_df.loc[start_date:end_date]

    return result_df