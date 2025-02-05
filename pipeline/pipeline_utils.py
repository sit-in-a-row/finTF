import pandas as pd
import numpy as np
from sub_func import *

from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import GRU, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
import os
import joblib
from pykrx import stock

def get_final_tickers(content):
    """content['final_portfolio']['corp_analysis_report']에서 invest가 True인 ticker 리스트 반환"""
    corp_analysis_report = content.get('final_portfolio', {}).get('corp_analysis_report', {})
    
    # invest가 'True'인 ticker만 리스트로 추출
    invest_tickers = [ticker for ticker, data in corp_analysis_report.items() if data.get('invest') == 'True']
    
    return invest_tickers

def get_tickers_from_json(agent_type, title):
    data = read_json(json_file_path)
    if agent_type in data and title in data[agent_type]:
        page_id = data[agent_type][title]
        content = get_all_text_from_page(page_id)
        
    try:
        data = read_json(json_file_path)
        if agent_type in data and title in data[agent_type]:
            page_id = data[agent_type][title]
            content = eval(get_all_text_from_page(page_id))
            tickers = get_final_tickers(content)

            return tickers
        else:
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def predict_multiple_prices(tickers: list, start_date: str, end_date: str, price_data_dict=None) -> dict:
    predictions = {}
    
    if not os.path.exists('models'):
        os.makedirs('models')
    
    for ticker in tickers:
        try:
            data = load_stock_data(ticker, start_date, end_date)
            if data is None:
                continue
                
            # PER이 0인 경우 처리
            if np.all(data['PER'] == 0):
                print("[WARNING] PER이 모두 0입니다. 평균값으로 대체합니다.")
                data['PER'] = 15.0  # 일반적인 PER 평균값으로 대체
            
            # 스케일링
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data[['close', 'high', 'PER', 'foreign_holding']])
            data[['close', 'high', 'PER', 'foreign_holding']] = scaled_data
            
            # 시계열 데이터 준비
            window_size = 15
            X = []
            y = []
            for i in range(window_size, len(data)):
                X.append(data[['high', 'PER', 'foreign_holding']].values[i-window_size:i])
                y.append(data['close'].values[i])
            X = np.array(X)
            y = np.array(y)
            
            # 모델 학습
            model = create_and_train_model(X, y, ticker)
            
            # 예측 수행
            last_sequence = X[-1:]
            future_predictions = []
            current_sequence = last_sequence.copy()
            
            for _ in range(20):
                pred = model.predict(current_sequence, verbose=0)
                future_predictions.append(float(pred[0, 0]))
                
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1] = [pred[0, 0], data['PER'].iloc[-1], data['foreign_holding'].iloc[-1]]
            
            # 예측값 역변환
            future_predictions = np.array(future_predictions).reshape(-1, 1)
            future_predictions = np.concatenate([future_predictions, np.zeros((len(future_predictions), 3))], axis=1)
            future_predictions = scaler.inverse_transform(future_predictions)[:, 0]
            
            predictions[ticker] = {
                'current_price': float(scaler.inverse_transform([[data['close'].iloc[-1], 0, 0, 0]])[0, 0]),
                'predicted_prices': future_predictions.tolist(),
                'prediction_dates': pd.date_range(
                    start=pd.to_datetime(data['date'].iloc[-1]) + pd.Timedelta(days=1),
                    periods=20
                ).strftime('%Y-%m-%d').tolist()
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
    print(f"[DEBUG] 학습 데이터 통계:")
    print(f"X_train shape: {X_train.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"X_train 값 범위: {np.min(X_train)} ~ {np.max(X_train)}")
    print(f"y_train 값 범위: {np.min(y_train)} ~ {np.max(y_train)}")

    # 입력 데이터 검증
    if np.any(np.isnan(X_train)) or np.any(np.isinf(X_train)):
        raise ValueError("입력 데이터에 NaN 또는 무한값이 포함되어 있습니다.")

    if np.any(np.isnan(y_train)) or np.any(np.isinf(y_train)):
        raise ValueError("타겟 데이터에 NaN 또는 무한값이 포함되어 있습니다.")

    # 모델 구조
    model = Sequential([
        GRU(32, input_shape=(X_train.shape[1], X_train.shape[2])),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    
    # 컴파일
    optimizer = Adam(learning_rate=0.001)
    model.compile(
        optimizer=optimizer,
        loss='huber',
        metrics=['mae']
    )
    
    # 콜백
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.0001
        )
    ]
    
    # 학습
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=16,
        validation_split=0.2,
        callbacks=callbacks,
        verbose=1
    )
    
    # 학습 결과 검증
    print("\n[DEBUG] 모델 평가:")
    val_predictions = model.predict(X_train[-int(len(X_train)*0.2):])
    val_true = y_train[-int(len(y_train)*0.2):]
    mse = np.mean((val_predictions - val_true) ** 2)
    print(f"검증 세트 MSE: {mse}")
    
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
        if price_data is not None:
            print("[DEBUG] 기존 price_data 사용")  # 디버깅
            selected_data = pd.DataFrame()
            selected_data['close'] = price_data['Close']
            selected_data['high'] = price_data['High']
            selected_data['date'] = price_data.index
            selected_data = selected_data.reset_index(drop=True)
        else:
            print("[DEBUG] 새로운 데이터 로드 시도")  # 디버깅
            price_data = stock_price_info(ticker, start_date, end_date)
            
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
            print("\n[DEBUG] 외국인 보유 비중 데이터 로드 시도")
            foreign_data = stock.get_exhaustion_rates_of_foreign_investment(start_date, end_date, ticker)
            print(f"[DEBUG] 외국인 보유 비중 데이터 로드 성공")
            
            # 데이터 병합을 위해 인덱스 처리
            selected_data['date'] = pd.to_datetime(selected_data['date'])
            foreign_data = foreign_data.reset_index()
            foreign_data.columns = ['date' if col == '날짜' else col for col in foreign_data.columns]
            foreign_data['date'] = pd.to_datetime(foreign_data['date'])
            
            # 날짜 기준으로 데이터 병합
            selected_data = pd.merge(selected_data, 
                                   foreign_data[['date', '지분율']], 
                                   on='date', 
                                   how='left')
            selected_data = selected_data.rename(columns={'지분율': 'foreign_holding'})
            
            print("[DEBUG] 데이터 병합 완료")
        except Exception as e:
            print(f"[DEBUG] 외국인 보유 비중 로드 실패: {str(e)}")
            selected_data['foreign_holding'] = 0
            
        print(f"[DEBUG] 최종 데이터 shape: {selected_data.shape}")  # 디버깅
        return selected_data
        
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")
        print(f"[DEBUG] 오류 발생 위치 정보: {e.__traceback__.tb_lineno}")  # 디버깅
        return None
    
def get_kospi_open_days(start_date: str, end_date: str):
    """
    코스피 장이 열린 날짜(거래일)만 리스트로 반환
    :param start_date: 조회 시작 날짜 (YYYYMMDD)
    :param end_date: 조회 종료 날짜 (YYYYMMDD)
    :return: 거래일 리스트
    """
    # 코스피 전체 종목 중 아무 종목이나 하나 선택하여 거래일 조회
    sample_ticker = "005930"  # 삼성전자
    df = stock.get_market_ohlcv(start_date, end_date, sample_ticker)

    # 데이터프레임의 인덱스(날짜)를 리스트로 변환
    open_days = df.index.strftime("%Y%m%d").tolist()
    return open_days