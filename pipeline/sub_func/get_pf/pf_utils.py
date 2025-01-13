from ..get_info import stock_price_info

import pandas as pd
import numpy as np
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler

# 데이터 가져오기 함수 (사용자가 제공한 함수)
def get_stock_data(tickers, start_date, end_date):
    data = {}
    for ticker in tickers:
        df = stock_price_info(ticker, start_date, end_date)  # 제공된 함수 사용
        if df is not None and 'Close' in df.columns:
            data[ticker] = df['Close']
        else:
            data[ticker] = np.nan  # 결측값 처리
    df_result = pd.DataFrame(data)
    return df_result.dropna(how='all')  # 모든 값이 NaN인 열 제거

# 수익률 계산 함수
def calculate_returns(price_data):
    # 결측값을 선형 보간 후 수익률 계산
    price_data = price_data.interpolate(method='linear')
    returns = price_data.pct_change().dropna()
    return returns 

# 공분산 행렬 정규화 함수
def normalize_cov_matrix(cov_matrix):
    """
    공분산 행렬을 정규화합니다.
    Args:
        cov_matrix (np.ndarray): 공분산 행렬
    Returns:
        np.ndarray: 정규화된 공분산 행렬
    """
    diag = np.sqrt(np.diag(cov_matrix))
    normalized_cov_matrix = cov_matrix / np.outer(diag, diag)
    return np.nan_to_num(normalized_cov_matrix)

# 수익률 데이터 정규화 함수
def standardize_returns(returns_data):
    """
    수익률 데이터를 정규화합니다.
    Args:
        returns_data (pd.DataFrame or np.ndarray): 수익률 데이터
    Returns:
        pd.DataFrame: 정규화된 수익률 데이터
    """
    scaler = StandardScaler()
    if isinstance(returns_data, pd.DataFrame):
        standardized_data = scaler.fit_transform(returns_data)
        return pd.DataFrame(standardized_data, columns=returns_data.columns, index=returns_data.index)
    elif isinstance(returns_data, np.ndarray):
        standardized_data = scaler.fit_transform(returns_data)
        return standardized_data  # numpy.ndarray 반환
    else:
        raise ValueError("returns_data는 DataFrame 또는 numpy.ndarray 여야 합니다.")

# 포트폴리오 위험 계산 함수
def portfolio_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

# 샤프 비율 최대화를 위한 최적화 함수
def optimize_portfolio(expected_returns, returns_data, risk_free_rate=0.0):
    """
    공분산 행렬을 정규화하여 포트폴리오를 최적화합니다.
    Args:
        expected_returns (np.ndarray): 기대수익률 벡터
        returns_data (pd.DataFrame): 수익률 데이터
        risk_free_rate (float): 무위험 수익률
    Returns:
        np.ndarray: 최적 가중치
    """
    # 수익률 데이터 정규화
    standardized_returns = standardize_returns(returns_data)
    
    # 정규화된 공분산 행렬 계산
    cov_matrix = np.cov(standardized_returns, rowvar=False)
    normalized_cov_matrix = normalize_cov_matrix(cov_matrix)

    # 초기 값 및 제약 조건
    n = len(expected_returns)
    init_guess = np.ones(n) / n  # 초기 가중치
    bounds = [(0.05, 0.2) for _ in range(n)]  # 가중치 범위 설정 (5% ~ 20%)
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})  # 가중치 합 = 1

    # 샤프 비율 최대화를 위한 최적화
    result = minimize(
        lambda w: -((np.dot(w, expected_returns) - risk_free_rate) / portfolio_volatility(w, normalized_cov_matrix)),
        init_guess, bounds=bounds, constraints=constraints
    )

    if result.success:
        return result.x
    else:
        raise ValueError("최적화 실패: 결과를 확인하세요.")