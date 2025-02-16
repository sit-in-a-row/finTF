from fuzzywuzzy import process
import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = '../corp_code/corp_code.csv'

csv_path = os.path.join(current_dir, csv_path)

df = pd.read_csv(csv_path, index_col=0)
df_filtered = df[df["stock_code"].notna() & (df["stock_code"] != ' ')]

# 종목명 검색 (fuzzy matching 적용)
def get_stock_code_fuzzy(user_input, df=df_filtered, threshold=80):
    # corp_name 리스트 추출
    corp_names = df["corp_name"].dropna().tolist()

    # fuzzy 매칭 실행 (여러 개 중 가장 높은 점수의 종목 선택)
    best_match, score = process.extractOne(user_input, corp_names)

    # 스코어가 기준 이상일 경우 해당 종목의 ticker 반환
    if score >= threshold:
        matched_row = df[df["corp_name"] == best_match]
        return matched_row["stock_code"].values[0]  # ticker만 반환
    else:
        return None  # 매칭되는 종목이 없을 경우 None 반환


# # 실행
# result = find_stock_code_fuzzy(user_input_sample, df_filtered)[0]['stock_code']

# # 결과 확인
# print(result)