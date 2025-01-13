from ..get_info import *
from .pf_utils import *

PRINT_EXCEPTION = False
current_dir = os.path.dirname(os.path.abspath(__file__))

def get_current_quarter_pf(curr_year, curr_quarter, n):
    """
    curr_year: 투자가 진행될 시점의 연도
    curr_quarter: 투자가 진행될 시점의 분기
    n: 포트폴리오 내 종목의 개수
    """

    # 날짜 계산
    if curr_quarter == 'Q1':
        target_year = f"{int(curr_year)-1}"
        target_quarter = "Q4"

        start_date = f"{int(target_year)-1}{target_quarter}"
        end_date = f"{target_year}{target_quarter}"
    else:
        target_year = curr_year
        quarter_num = curr_quarter[-1]
        target_quarter = f"Q{int(quarter_num)-1}"

        start_date = f"{int(target_year)-1}{target_quarter}"
        end_date = f"{target_year}{target_quarter}"

    # 분석 데이터 로드
    analysis_path = f'../../../store_data/process/analysis/index_analysis/{target_year}/{target_quarter}/코스피_carhart_results.json'
    analysis_path = os.path.join(current_dir, analysis_path)
    
    anal_temp = load_json(analysis_path)

    anal_temp_dict = {}

    # Carhart 분석 결과를 dict형식으로 변환
    for ticker in anal_temp:
        try:
            to_dict = get_model_summary_dict(anal_temp[ticker])
            anal_temp_dict[ticker] = to_dict
        except Exception as e:
            if PRINT_EXCEPTION:
                print(f"{ticker}에서 오류 발생: {e}")

    # 종목 필터링에 활용할 초기 하이퍼파라미터
    adj_R_squared_value = 0.5
    const_P_t_value = 0.05
    const_coef_value = 0

    carhart_filtered = {}

    # 필터링 루프
    for ticker in anal_temp_dict:
        try:
            int(ticker)
            carhart_result = anal_temp_dict[ticker]

            adj_R_squared = carhart_result.get('Adj. R-squared', 0)
            const_P_t = carhart_result.get('const_result', {}).get('const_P_t', 1)
            const_coef = carhart_result.get('const_result', {}).get('const_coef', -1)

            if adj_R_squared > adj_R_squared_value and const_P_t < const_P_t_value and const_coef > const_coef_value:
                carhart_filtered[ticker] = carhart_result
        except Exception as e:
            if PRINT_EXCEPTION:
                print(f"{ticker}에서 오류 발생: {e}")

    # 조건 완화 루프
    while len(carhart_filtered) < n:
        adj_R_squared_value -= 0.05
        const_P_t_value += 0.01
        const_coef_value -= 0.01

        for ticker in anal_temp_dict:
            if ticker in carhart_filtered:
                continue

            try:
                int(ticker)
                carhart_result = anal_temp_dict[ticker]

                adj_R_squared = carhart_result.get('Adj. R-squared', 0)
                const_P_t = carhart_result.get('const_result', {}).get('const_P_t', 1)
                const_coef = carhart_result.get('const_result', {}).get('const_coef', -1)

                if adj_R_squared > adj_R_squared_value and const_P_t < const_P_t_value and const_coef > const_coef_value:
                    carhart_filtered[ticker] = carhart_result
            except Exception as e:
                if PRINT_EXCEPTION:
                    print(f"{ticker}에서 오류 발생: {e}")

    # 필터링된 종목 리스트
    target_tickers = list(carhart_filtered.keys())[:n]

    # 데이터 수집 및 포트폴리오 최적화
    price_data = get_stock_data(target_tickers, start_date, end_date)
    returns_data = calculate_returns(price_data)

    expected_returns = returns_data.mean().values
    cov_matrix = returns_data.cov().values

    optimal_weights = optimize_portfolio(expected_returns, cov_matrix)

    # 결과 데이터프레임 생성
    portfolio_weights = pd.DataFrame({
        'Ticker': target_tickers,
        'Weight': optimal_weights
    })

    return portfolio_weights
