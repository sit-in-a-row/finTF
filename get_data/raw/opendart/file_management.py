import os
import pandas as pd
from .open_dart_api import get_sub_report, get_financial_statements
from .data_processing import get_index_dict, divide_statement_df

def sub_reports_to_csv(sub_report_dict, stock_code):
    '''
    csv 저장 경로 설정 및 저장
    '''
    try:
        # 현재 파일의 디렉토리 경로 가져오기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 저장 경로 부모 디렉토리의 절대 경로 생성
        store_path_parent = os.path.join(current_dir, f'../../../store_data/raw/opendart/store_reports/{stock_code}')

        index_dict = get_index_dict(sub_report_dict)
        sub_report_dict_keys_list = list(sub_report_dict.keys())
        index_dict_keys_list = list(index_dict.keys())

        for i in range(len(index_dict)):
            for j in range(len(index_dict_keys_list)):
                date = index_dict_keys_list[j]
                for k in range(len(index_dict[date])):
                    report_title = sub_report_dict_keys_list[index_dict[date][k]]
                    store_path = os.path.join(store_path_parent, f'{date}/{date}_{stock_code}_{report_title}.csv')

                    # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
                    os.makedirs(os.path.dirname(store_path), exist_ok=True)

                    temp_df = pd.DataFrame(
                        {'text': [sub_report_dict[report_title]]},
                        index=[report_title]
                    )
                    temp_df.to_csv(store_path, index=False)
        
        print('csv 저장 성공')
        return None
    except Exception as e:
        print(f'csv 저장 실패: {str(e)}')
        return None

def save_sub_reports(stock_code, target_business_year):
    '''
    보고서 저장 기능의 main함수
    '''
    try:
        # 현재 파일의 디렉토리 경로 가져오기
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 저장 경로 부모 디렉토리의 절대 경로 생성
        store_path_parent = os.path.join(current_dir, f'../../../store_data/raw/opendart/store_reports/{stock_code}')
        
        # 연도별 하위 폴더 확인 (3, 6, 9, 12월만)
        for month in [3, 6, 9, 12]:
            month_str = f'{target_business_year}.{str(month).zfill(2)}'  # YYYY.MM 형식
            month_folder_path = os.path.join(store_path_parent, month_str)

            # 해당 월의 폴더가 없으면 그 월의 보고서를 다운로드
            if not os.path.exists(month_folder_path):
                print(f'{month_folder_path} 폴더가 존재하지 않습니다. 해당 월의 보고서를 다운로드합니다.')
                
                # get_sub_report를 호출하여 보고서 다운로드
                sub_report_dict = get_sub_report(stock_code, target_business_year)
                sub_report_dict_keys_list = list(sub_report_dict.keys())

                for report_title in sub_report_dict_keys_list:
                    report_date = report_title.split(' ')[1][1:-1]
                    
                    # 보고서 날짜가 해당 월인 경우에만 저장
                    if report_date.startswith(f'{target_business_year}.{str(month).zfill(2)}'):
                        store_path = os.path.join(store_path_parent, f'{report_date}', f'{stock_code}_{report_title}.csv')

                        # 파일이 존재하는지 확인
                        if not os.path.exists(store_path):
                            os.makedirs(os.path.dirname(store_path), exist_ok=True)
                            temp_df = pd.DataFrame(
                                {'text': [sub_report_dict[report_title]]},
                                index=[report_title]
                            )
                            temp_df.to_csv(store_path, index=False)
                            print(f'{store_path} 저장에 성공했습니다.')
                        else:
                            print(f'{store_path} 파일이 이미 존재합니다. 저장을 건너뜁니다.')
            else:
                print(f'{month_folder_path} 폴더가 이미 존재합니다. 보고서 저장을 건너뜁니다.')

    except Exception as e:
        print(f'에러가 발생했습니다: {e}')

def save_financial_statement(stock_code, target_business_year):
    '''
    분할된 데이터프레임을 필요 경로에 저장하는 함수, main함수
    '''
    try:
        # 현재 파일의 디렉토리 경로 가져오기
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 저장 경로 부모 디렉토리의 절대 경로 생성
        store_path_parent = os.path.join(current_dir, f'../../../store_data/raw/opendart/store_financial_statement/{stock_code}')

        financial_statements = get_financial_statements(stock_code, target_business_year)
        df_list = divide_statement_df(financial_statements)
        print(f'조회한 {stock_code}의 {target_business_year}에 대한 재무제표의 개수', len(df_list))
        for i in range(len(df_list)):
            df_to_save = df_list[i]
            time_raw = list(df_to_save['rcept_no'])[0][0:9]
            year = time_raw[0:4]
            month = time_raw[4:6]
            folder_path = f'{year}.{month}'
            statement_title = f'{folder_path}_{stock_code}_재무제표 ({folder_path}).csv'
            store_path = os.path.join(store_path_parent, folder_path, statement_title)

            # 디렉토리 및 파일이 존재하는지 확인
            if not os.path.exists(store_path):
                os.makedirs(os.path.dirname(store_path), exist_ok=True)
                df_to_save.to_csv(store_path, index=False)
                print(f'{statement_title} 저장에 성공했습니다.')
            else:
                print(f'{statement_title} 파일이 이미 존재합니다. 저장을 건너뜁니다.')

        return None
    except Exception as e:
        print(f'재무제표 저장에 실패했습니다: {str(e)}')
        return None
