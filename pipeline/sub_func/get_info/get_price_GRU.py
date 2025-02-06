import pandas as pd
import numpy as np
from sub_func import *

from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import GRU, Dense
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
import os
import joblib
from pykrx import stock

def predict_multiple_prices(tickers: list, start_date: str, end_date: str, price_data_dict=None) -> dict:
    """
    여러 종목의 가격을 예측하는 함수
    
    Args:
        tickers (list): 종목 코드 리스트
        start_date (str): 예측 시작일 (YYYYMMDD)
        end_date (str): 예측 종료일 (YYYYMMDD)
    
    Returns:
        dict: 각 종목별 예측 결과
    """
    predictions = {}
    
    for ticker in tickers:
        try:
            print(f"[DEBUG] predict_multiple_prices 시작 - ticker: {ticker}")
            print(f"[DEBUG] 날짜 범위: {start_date} ~ {end_date}")
            
            # 직접 stock_price_info 테스트
            test_data = st.stock_price_info(ticker, start_date, end_date)
            print(f"[DEBUG] stock_price_info 테스트 결과: {test_data is not None}")
            if test_data is not None:
                print(f"[DEBUG] 데이터 샘플:\n{test_data.head()}")
            
            data = load_stock_data(ticker, start_date, end_date)
            print(f"[DEBUG] load_stock_data 결과: {data is not None}")
            
            if data is None:
                print(f"{ticker} 데이터 로드 실패")
                continue
                
            # 스케일러 로드 또는 새로 생성
            if os.path.exists(SCALER_PATH):
                scaler = joblib.load(SCALER_PATH)
            else:
                scaler = MinMaxScaler()
                data[['close', 'high', 'PER', 'foreign_holding']] = scaler.fit_transform(
                    data[['close', 'high', 'PER', 'foreign_holding']]
                )
                joblib.dump(scaler, SCALER_PATH)
            
            # 시계열 데이터 준비
            window_size = 15
            X = []
            for i in range(window_size, len(data)):
                X.append(data[['high', 'PER', 'foreign_holding']].values[i-window_size:i])
            X = np.array(X)
            
            # 모델 로드 또는 새로 생성
            if os.path.exists(MODEL_PATH):
                model = load_model(MODEL_PATH)
            else:
                model = create_and_train_model(X, data['close'].values[window_size:], ticker)
            
            # 다음 분기 예측
            future_predictions = []
            last_sequence = X[-1:]
            
            # 다음 20일 예측
            for _ in range(20):
                next_pred = model.predict(last_sequence)
                future_predictions.append(next_pred[0, 0])
                
                last_sequence = np.roll(last_sequence, -1, axis=1)
                last_sequence[0, -1] = next_pred
            
            # 예측값 역변환
            future_predictions = np.array(future_predictions).reshape(-1, 1)
            future_predictions = scaler.inverse_transform(
                np.concatenate((future_predictions, np.zeros((future_predictions.shape[0], 3))), axis=1)
            )[:, 0]
            
            # 결과 저장
            predictions[ticker] = {
                'current_price': data['close'].iloc[-1],
                'predicted_prices': future_predictions.tolist(),
                'prediction_dates': pd.date_range(
                    start=data.iloc[-1]['date'] + pd.Timedelta(days=1), 
                    periods=20
                ).strftime('%Y-%m-%d').tolist(),
                'confidence_level': calculate_confidence_level(model, X, data['close'].values[window_size:])
            }
            
        except Exception as e:
            print(f"{ticker} 예측 중 오류 발생: {str(e)}")
            predictions[ticker] = None
    
    return predictions

def predict_price(ticker: str, start_date: str = None, end_date: str = None) -> dict:
    """
    GRU 모델을 사용하여 주가를 예측하는 함수
    
    Args:
        ticker (str): 주식 종목 코드
        start_date (str): 예측 시작일 (YYYYMMDD 형식)
        end_date (str): 예측 종료일 (YYYYMMDD 형식)
    
    Returns:
        dict: 예측 결과를 담은 딕셔너리
    """
    try:
        # 모델 및 스케일러 경로 설정
        MODEL_PATH = f'models/{ticker}_gru_model.h5'
        SCALER_PATH = f'models/{ticker}_scaler.pkl'
        
        # 데이터 로드 
        data = load_stock_data(ticker, start_date, end_date)  
        
        # 데이터 전처리
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date')
        
        # 저장된 스케일러 로드 또는 새로 생성
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
        else:
            scaler = MinMaxScaler()
            data[['close', 'high', 'PER', 'foreign_holding']] = scaler.fit_transform(
                data[['close', 'high', 'PER', 'foreign_holding']]
            )
            joblib.dump(scaler, SCALER_PATH)
        
        # 시계열 데이터 준비
        window_size = 15
        X = []
        for i in range(window_size, len(data)):
            X.append(data[['high', 'PER', 'foreign_holding']].values[i-window_size:i])
        X = np.array(X)
        
        # 모델 로드 또는 새로 생성
        if os.path.exists(MODEL_PATH):
            model = load_model(MODEL_PATH)
        else:
            model = create_and_train_model(X, data['close'].values[window_size:], ticker)
        
        # 다음 분기 예측
        future_predictions = []
        last_sequence = X[-1:]
        
        # 다음 20일(약 한 달) 예측
        for _ in range(20):
            next_pred = model.predict(last_sequence)
            future_predictions.append(next_pred[0, 0])
            
            # 다음 예측을 위한 시퀀스 업데이트
            last_sequence = np.roll(last_sequence, -1, axis=1)
            last_sequence[0, -1] = next_pred
        
        # 예측값 역변환
        future_predictions = np.array(future_predictions).reshape(-1, 1)
        future_predictions = scaler.inverse_transform(
            np.concatenate((future_predictions, np.zeros((future_predictions.shape[0], 3))), axis=1)
        )[:, 0]
        
        # 결과 정리
        result = {
            'current_price': data['close'].iloc[-1],
            'predicted_prices': future_predictions.tolist(),
            'prediction_dates': pd.date_range(
                start=data['date'].iloc[-1] + pd.Timedelta(days=1), 
                periods=20
            ).strftime('%Y-%m-%d').tolist(),
            'confidence_level': calculate_confidence_level(model, X, data['close'].values[window_size:])
        }
        
        return result
        
    except Exception as e:
        print(f"예측 중 오류 발생: {str(e)}")
        return None

def create_and_train_model(X_train, y_train, ticker):
    """GRU 모델 생성 및 학습"""
    model = Sequential([
        GRU(50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
        GRU(50, return_sequences=True),
        GRU(50),
        Dense(1)
    ])
    
    model.compile(optimizer=Adam(), loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=50, batch_size=64, validation_split=0.2)
    
    # 모델 저장
    model.save(f'models/{ticker}_gru_model.h5')
    
    return model

def calculate_confidence_level(model, X, y_true):
    """예측 신뢰도 계산"""
    y_pred = model.predict(X)
    mse = np.mean((y_pred - y_true.reshape(-1, 1)) ** 2)
    confidence = np.exp(-mse)  # 0~1 사이의 값으로 변환
    return float(confidence)

def load_stock_data(ticker: str, start_date: str, end_date: str, price_data=None) -> pd.DataFrame:
    """
    주식 데이터를 로드하는 함수
    price_data: TraderReportGenerator에서 이미 로드된 가격 데이터
    """
    print("로드 데이터 함수 시작")
    try:
        print(f"[DEBUG] 데이터 로드 시작 - ticker: {ticker}, start_date: {start_date}, end_date: {end_date}")  # 디버깅
        
        if price_data is not None:
            print("[DEBUG] 기존 price_data 사용")  # 디버깅
            selected_data = pd.DataFrame()
            selected_data['close'] = price_data['Close']
            selected_data['high'] = price_data['High']
            selected_data['date'] = price_data.index
            selected_data = selected_data.reset_index(drop=True)
        else:
            print("[DEBUG] 새로운 데이터 로드 시도")  # 디버깅
            price_data = st.stock_price_info(ticker, start_date, end_date)
            print(f"[DEBUG] stock_price_info 결과: {price_data is not None}")  # 디버깅
            
            if price_data is None:
                print(f"Warning: 가격 데이터를 가져올 수 없습니다: {ticker}")
                return None
            
            selected_data = pd.DataFrame()
            selected_data['close'] = price_data['Close']
            selected_data['high'] = price_data['High']
            selected_data['date'] = price_data.index
            selected_data = selected_data.reset_index(drop=True)
            
        # 연도와 분기 추출
        year = start_date[:4]
        month = start_date[4:6]
        print(f"[DEBUG] 연도: {year}, 월: {month}")  # 디버깅
        
        # 분기 매핑
        quarter_map = {
            'Q1': ['01', '02', '03'],
            'Q2': ['04', '05', '06'],
            'Q3': ['07', '08', '09'],
            'Q4': ['10', '11', '12']
        }
        
        quarter = next(q for q, months in quarter_map.items() if month in months)
        print(f"[DEBUG] 매핑된 분기: {quarter}")  # 디버깅
        
        # PER 데이터 가져오기
        fin_data = fin_statement_info(ticker, year, quarter)
        print(f"[DEBUG] 재무제표 데이터 로드: {fin_data is not None}")  # 디버깅
        
        if fin_data is not None:
            per_value = fin_data['PER'].iloc[0]
        else:
            per_value = None
            
        # PER 컬럼 추가
        selected_data['PER'] = per_value
        
        # 외국인 보유 비중 추가
        try:
            print("[DEBUG] 외국인 보유 비중 데이터 로드 시도")  # 디버깅
            selected_data['foreign_holding'] = stock.get_exhaustion_rates_of_foreign_investment(start_date, end_date, ticker)
        except Exception as e:
            print(f"[DEBUG] 외국인 보유 비중 로드 실패: {str(e)}")  # 디버깅
            selected_data['foreign_holding'] = 0
            
        print(f"[DEBUG] 최종 데이터 shape: {selected_data.shape}")  # 디버깅
        return selected_data
        
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")
        print(f"[DEBUG] 오류 발생 위치 정보: {e.__traceback__.tb_lineno}")  # 디버깅
        return None