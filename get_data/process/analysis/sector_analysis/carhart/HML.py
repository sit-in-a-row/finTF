from .load_data import get_corp_OHLCV
import os
import pandas as pd

no_fin_statement_list = []
no_csv_list = []
no_market_cap_list = []

# 파일 경로 및 분기별 월 설정
def get_financial_statement_path(base_path, ticker, year, quarter):
    """분기에 따라 파일 경로를 생성"""    
    existing_statement_list = os.listdir(os.path.join(base_path, ticker))
    print("existing_statement_list: ", existing_statement_list)
    
    target_year_list = []
    for existing_statement in existing_statement_list:
        if year in existing_statement:
            target_year_list.append(existing_statement)
        elif str(int(year)+1) in existing_statement_list:
            target_year_list.append(existing_statement)

    for target_year in target_year_list:
        temp_df_path = os.path.join(base_path, ticker, target_year, f"{target_year}_{ticker}_재무제표 ({target_year}).csv")
        temp_df = pd.read_csv(temp_df_path)
        test_row = temp_df.iloc[0]

        if quarter == 'Q1':
            if str(test_row['reprt_code']) == '11013' and str(test_row['bsns_year']) == year:
                return temp_df_path
            # else:
            #     print(f'{quarter}에 맞는 재무제표를 찾을 수 없습니다. reprt_code: {test_row["reprt_code"]} | bsns_year: {test_row["bsns_year"]}')

        elif quarter == 'Q2':
            if str(test_row['reprt_code']) == '11012' and str(test_row['bsns_year']) == year:
                return temp_df_path
            # else:
            #     print(f'{quarter}에 맞는 재무제표를 찾을 수 없습니다. reprt_code: {test_row["reprt_code"]} | bsns_year: {test_row["bsns_year"]}')

        elif quarter == 'Q3':
            if str(test_row['reprt_code']) == '11014' and str(test_row['bsns_year']) == year:
                return temp_df_path
            # else:
            #     print(f'{quarter}에 맞는 재무제표를 찾을 수 없습니다. reprt_code: {test_row["reprt_code"]} | bsns_year: {test_row["bsns_year"]}')

        elif quarter == 'Q4':
            if str(test_row['reprt_code']) == '11011' and str(test_row['bsns_year']) == year:
                return temp_df_path
            # else:
            #     print(f'{quarter}에 맞는 재무제표를 찾을 수 없습니다. reprt_code: {test_row["reprt_code"]} | bsns_year: {test_row["bsns_year"]}')
        else:
            print(f'조건에 맞는 재무제표를 찾을 수 없습니다. | quarter: {quarter}')
            return None

        
    
    # # ticker 폴더 내 파일 경로 설정
    # return os.path.join(base_path, ticker, f'{year}.{month}')


# 자산총계 추출
def extract_assets_from_csv(df):
    """CSV 파일에서 자산총계(thstrm_amount)를 추출"""
    # assets_row = df[df['account_id'] == 'ifrs-full_EquityAndLiabilities']
    # assets_row = df[df['account_id'] == 'ifrs-full_Equity']
    assets_row = df[df['account_nm'] == '자본총계']
    if not assets_row.empty:
        return assets_row.iloc[0]['thstrm_amount']
    return None

# 자산총계 수집 함수
def collect_assets(base_path, tickers, year, quarter):
    asset_dict = {}
    asset_dict['no_statement'] = []
    asset_dict['processing_error'] = []
    
    for ticker in tickers:
        df_path = get_financial_statement_path(base_path, ticker, year, quarter)

        try:
            if df_path:
                # CSV 파일 읽기
                df = pd.read_csv(df_path)
                
                # 자산총계 추출 및 저장
                thstrm_amount = extract_assets_from_csv(df)
                if thstrm_amount:
                    asset_dict[ticker] = thstrm_amount
                else:
                    print(f'{ticker}의 재무제표가 존재하지만 자산총계 관련 내용이 없습니다.')
            else:
                print(f'df_path가 None입니다. (HML.py, collect_assets())')
        
        except FileNotFoundError:
            print(f'{ticker}에 해당하는 {year}년 {quarter}분기 재무제표가 없습니다.')
            asset_dict['no_statement'].append(ticker)
        except Exception as e:
            print(f'{ticker}의 재무제표를 처리하는 중 오류 발생: {e}')
            asset_dict['processing_error'].append(ticker)
    
    return asset_dict

def load_stock_market_cap(ticker, year, quarter):
    base_path = f'../store_data/raw/market_data/market_cap/{year}/{ticker}/{quarter}_{ticker}_market_cap.csv'
    df = pd.read_csv(base_path)

    df_columns = ['Date', 'Market_Cap', 'Volume', 'Transaction_Val', 'Num_Stock']
    df.columns = df_columns

    df.set_index('Date', inplace=True)

    return df

def get_BM_ratio(ticker, year, quarter, asset_dict):
    try:
        book_value = asset_dict[ticker]
        ticker_market_cap = load_stock_market_cap(ticker, year, quarter)
        # print('ticker_market_cap: ', ticker_market_cap)
        ticker_market_cap = ticker_market_cap['Market_Cap'] / book_value
        return ticker_market_cap
    
    except KeyError:
        no_fin_statement_list.append(ticker)
        # print(f'{ticker}에 해당하는 재무제표 정보를 찾을 수 없습니다.')
        return None
    
def get_HML(year, quarter):
    save_path = f'./factor_data/HML/{year}'

    try:
        df_path = os.path.join(save_path, f'{quarter}_HML.csv')
        BM_df = pd.read_csv(df_path, index_col='Date')
        print(f'{year}_{quarter}에 대한 HML파일이 존재합니다. 해당 데이터를 로드합니다...')
        return BM_df

    except:
        print(f'{year}_{quarter}에 대한 HML파일이 없습니다. 해당 데이터를 생성합니다...')
        base_path = f'../store_data/raw/opendart/store_financial_statement'
        market_cap_path = f'../store_data/raw/market_data/market_cap/{year}'
        tickers = os.listdir(base_path)
        market_cap_tickers = os.listdir(market_cap_path)

        asset_dict = collect_assets(base_path, tickers, year, quarter)
        BM_data = []

        for ticker in tickers:
            if ticker in market_cap_tickers:
                try:
                    df_test = get_BM_ratio(ticker, year, quarter, asset_dict)
                    # print('df_test:', df_test)
                    if df_test is not None:
                        BM_data.append(df_test.rename(ticker))  # ticker 이름으로 열을 추가
                except FileNotFoundError:
                    no_csv_list.append(ticker)
            else:
                no_market_cap_list.append(ticker)

        # print('BM_data:', BM_data)
        BM_df = pd.concat(BM_data, axis=1)  # 열들을 한 번에 병합

        high_bm_avg_list = []
        low_bm_avg_list = []

        for i in range(len(BM_df.index)):
            daily_BM_df = BM_df.iloc[i]
            high_bm = daily_BM_df[daily_BM_df >= daily_BM_df.quantile(0.7)].index
            low_bm = daily_BM_df[daily_BM_df <= daily_BM_df.quantile(0.3)].index

            sum_high_bm_return = 0
            sum_low_bm_return = 0
            count_high_bm = 0
            count_low_bm = 0

            # high_bm 그룹에 대해 수익률 계산
            for ticker in high_bm:
                try:
                    return_data = get_corp_OHLCV(ticker, year, quarter).iloc[i]['Return']
                    sum_high_bm_return += return_data
                    count_high_bm += 1
                except:
                    # 해당 날짜의 가격 정보가 없으면 0을 추가
                    print(f'{BM_df.index[i]}, {year}, {quarter}에 대해 {ticker}의 가격정보를 찾을 수 없습니다.')
            
            # low_bm 그룹에 대해 수익률 계산
            for ticker in low_bm:
                try:
                    return_data = get_corp_OHLCV(ticker, year, quarter).iloc[i]['Return']
                    sum_low_bm_return += return_data
                    count_low_bm += 1
                except:
                    # 해당 날짜의 가격 정보가 없으면 0을 추가
                    print(f'{BM_df.index[i]}, {year}, {quarter}에 대해 {ticker}의 가격정보를 찾을 수 없습니다.')
            
            # 평균을 계산할 때 데이터가 있으면 그 수익률의 합을 나누고, 없으면 0으로 처리
            if count_high_bm > 0:
                high_bm_avg_list.append(sum_high_bm_return / count_high_bm)
            else:
                high_bm_avg_list.append(0)  # 데이터가 없을 경우 0으로 처리

            if count_low_bm > 0:
                low_bm_avg_list.append(sum_low_bm_return / count_low_bm)
            else:
                low_bm_avg_list.append(0)  # 데이터가 없을 경우 0으로 처리


        if len(no_csv_list) > 0:
            print(f'다음 종목에 대해 요구되는 csv 파일을 찾을 수 없습니다: {no_csv_list}')
        
        if len(no_market_cap_list) > 0:
            print(f'다음 종목에 대해 시총 정보를 찾을 수 없습니다: {no_market_cap_list}')

        if len(no_fin_statement_list) > 0:
            print(f'다음 종목에 대해 재무제표를 찾을 수 없습니다: {no_fin_statement_list}')

        BM_df['high_bm'] = high_bm_avg_list
        BM_df['low_bm'] = low_bm_avg_list
        BM_df['HML'] = BM_df['high_bm'] - BM_df['low_bm']

        os.makedirs(save_path, exist_ok=True)
        df_path = os.path.join(save_path, f'{quarter}_HML.csv')
        BM_df = BM_df['HML']
        BM_df.to_csv(df_path, index=True)

        return BM_df

# =========================================================================== #

def get_HML_tickers(year, quarter):

    base_path = f'../store_data/raw/opendart/store_financial_statement'
    market_cap_path = f'../store_data/raw/market_data/market_cap/{year}'
    tickers = os.listdir(base_path)
    market_cap_tickers = os.listdir(market_cap_path)

    asset_dict = collect_assets(base_path, tickers, year, quarter)
    BM_data = []

    for ticker in tickers:
        if ticker in market_cap_tickers:
            try:
                df_test = get_BM_ratio(ticker, year, quarter, asset_dict)
                # print('df_test:', df_test)
                if df_test is not None:
                    BM_data.append(df_test.rename(ticker))  # ticker 이름으로 열을 추가
            except FileNotFoundError:
                no_csv_list.append(ticker)
        else:
            no_market_cap_list.append(ticker)

    BM_df = pd.concat(BM_data, axis=1)  # 열들을 한 번에 병합

    high_bm_ticker_list = []
    low_bm_ticker_list = []

    for i in range(len(BM_df.index)):
        daily_BM_df = BM_df.iloc[i]
        high_bm = list(daily_BM_df[daily_BM_df >= daily_BM_df.quantile(0.7)].index)
        low_bm = list(daily_BM_df[daily_BM_df <= daily_BM_df.quantile(0.3)].index)

        for ticker_high in high_bm:
            if ticker_high not in high_bm_ticker_list:
                high_bm_ticker_list.append(ticker_high)
        
        for ticker_low in low_bm:
            if ticker_low not in low_bm_ticker_list:
                low_bm_ticker_list.append(ticker_low)

    return {
        'high_ticker': high_bm_ticker_list,
        'low_ticker': low_bm_ticker_list
    }
