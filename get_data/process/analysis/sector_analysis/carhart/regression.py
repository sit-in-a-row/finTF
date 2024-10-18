import pandas as pd
import statsmodels.api as sm

from functools import reduce

from .R_i_minus_R_f import get_R_i_minus_R_f
from .R_m_minus_R_f import get_R_m_minus_R_f

from .SMB import get_SMB
from .HML import get_HML
from .MOM import get_MOM

from .load_data import get_corp_OHLCV, get_bond, get_index_OHLCV

# Carhart 4 Factor 회귀 분석 함수
def run_carhart_regression(df):
    # 독립변수 (R_m - R_f, SMB, HML, MOM)
    X = df[['R_m - R_f', 'SMB', 'HML', 'MOM']]
    
    # 종속변수 (R_i - R_f)
    Y = df['R_i - R_f']
    
    # 상수항 추가
    X = sm.add_constant(X)
    
    # 회귀 모델 피팅
    model = sm.OLS(Y, X).fit()
    
    # 결과 출력
    print(model.summary())
    
    return model

def get_carhart_regression(ticker, market, year, quarter):
    '''
    ticker, market, year, quarter를 인자로 받아 OLS회귀분석 결과를 반환하는 함수
    만약 ticker가 숫자형태로 들어오면 개별 종목에 대해, 문자열 형태로 들어오면 index에 대해 분석
    '''
    try:
        int(ticker)
        stock_df = get_corp_OHLCV(ticker, year, quarter)
    except:
        stock_df = get_index_OHLCV(ticker, year, quarter)

    bond_df = get_bond(year, quarter)
    market_df = get_index_OHLCV(market, year, quarter)

    R_i_minus_R_f = get_R_i_minus_R_f(stock_df, bond_df)
    R_m_minus_R_f = get_R_m_minus_R_f(market_df, bond_df)
    SMB = get_SMB(year, quarter)
    HML = get_HML(year, quarter)
    MOM = get_MOM(ticker, year, quarter)

    R_i_minus_R_f.index = pd.to_datetime(R_i_minus_R_f.index)
    R_m_minus_R_f.index = pd.to_datetime(R_m_minus_R_f.index)
    SMB.index = pd.to_datetime(SMB.index)
    HML.index = pd.to_datetime(HML.index)
    MOM.index = pd.to_datetime(MOM.index)

    # 중복된 인덱스 제거 및 인덱스 정렬
    R_i_minus_R_f = R_i_minus_R_f[~R_i_minus_R_f.index.duplicated(keep='first')].sort_index()
    R_m_minus_R_f = R_m_minus_R_f[~R_m_minus_R_f.index.duplicated(keep='first')].sort_index()
    SMB = SMB[~SMB.index.duplicated(keep='first')].sort_index()
    HML = HML[~HML.index.duplicated(keep='first')].sort_index()
    MOM = MOM[~MOM.index.duplicated(keep='first')].sort_index()

    # 병합할 데이터프레임들을 리스트로 만듭니다.
    dfs = [R_i_minus_R_f, R_m_minus_R_f, SMB, HML, MOM]

    # reduce를 사용하여 리스트 내의 모든 데이터프레임을 병합합니다.
    final_df = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True), dfs)

    # 회귀 분석 실행
    regression_result = run_carhart_regression(final_df)

    return regression_result