import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, '../../../store_data/process/analysis/chart_pattern_analysis/')

def pattern_info(ticker:str, date:str) -> pd.DataFrame:
    '''
    ticker와 date를 입력하면, date를 기준으로 70일 이전까지의 일봉 데이터 기반 차트패턴 분석 반환
    단, 입력된 날짜가 거래일이 아닌 경우 등 해당 일자가 없는 경우 가장 가까운 과거의 날짜로 반환

    ex) chart_pattern_analysis('005930', '20190501')

    	start_date	end_date	pattern	prob
    0	2019-01-17	2019-04-30	ascending_wedge	0.987465
    '''
    year = date[:4]
    month = date[4:6]
    day = date[6:]
    init_date = f'{year}.{month}.{day}'

    csv_folder_path = os.path.join(path, ticker, year, month)

    csv_list = os.listdir(csv_folder_path)

    end_date_list = []
    for csv in csv_list:
        end_date = csv.split('_')[1]
        end_date_list.append(end_date)

    if init_date in end_date_list:
        for csv in csv_list:
            if csv.split('_')[1] == init_date:
                csv_path = os.path.join(csv_folder_path, csv)
                print(csv_path)
                df = pd.read_csv(csv_path, index_col=0)
                return df
        
    else:
        flag = int(day)
        new_date = int(day)

        while True:
            if flag != 0:
                new_day = str(new_date - 1).zfill(2)
                new_date_temp = f'{year}.{month}.{new_day}'

                if new_date_temp in end_date_list:
                    for csv in csv_list:
                        if csv.split('_')[1] == new_date_temp:
                            csv_path = os.path.join(csv_folder_path, csv)
                            df = pd.read_csv(csv_path, index_col=0)
                            return df
                    break

                else:
                    flag = flag - 1
                    new_date = new_date - 1

            else:
                if month == '12':
                    csv_folder_path = os.path.join(path, ticker, str(int(year)-1), '12')
                    csv_folder_list = sorted(os.listdir(csv_folder_path))
                    print(csv_folder_list[-1])
                    df = pd.read_csv(os.path.join(csv_folder_path, csv_folder_list[-1]), index_col=0)
                    return df

                else:
                    csv_folder_path = os.path.join(path, ticker, year, str(int(month)-1).zfill(2))
                    csv_folder_list = sorted(os.listdir(csv_folder_path))
                    df = pd.read_csv(os.path.join(csv_folder_path, csv_folder_list[-1]), index_col=0)
                    return df

                break

            