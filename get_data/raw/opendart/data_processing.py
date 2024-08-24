def get_index_dict(sub_report_dict):
    '''
    보고서 머리글에 있는 날짜 형식을 추출해서, 동일한 날짜에 해당하는 인덱스값을 같은 키로 묶어서 반환
    '''
    try:
        sub_report_dict_keys_list = list(sub_report_dict.keys())
        index_dict = {}
        for i in range(len(sub_report_dict_keys_list)):
            date = sub_report_dict_keys_list[i].split(' | ')[0].split(' ')[1][1:-1]
            if date in index_dict:  # date가 이미 index_dict에 존재하는지 확인
                sub_list = index_dict[date]
                sub_list.append(i)
            else:
                index_dict[date] = [i]  # date가 없으면 새로운 리스트 생성
        print('index_dict 생성 성공')
        return index_dict
    except Exception as e:
        print(f'index_dict 생성 실패 {str(e)}')
        return None
    
def divide_statement_df(financial_statements):
    '''
    하나의 business year 안에 있는 n개의 보고서를 n개의 데이터프레임으로 분할하는 함수
    '''
    try:
        # rcept_no 값들을 리스트로 추출
        rcept_no_list = list(set(financial_statements['rcept_no']))

        df_list = []
        # 각 rcept_no에 대해 데이터프레임 필터링 후 리스트에 추가
        for rcept_no in rcept_no_list:
            filtered_df = financial_statements[financial_statements['rcept_no'] == rcept_no]
            df_list.append(filtered_df)

        print('재무제표 필터링 성공')
        return df_list
    except Exception as e:
        print(f'재무제표 필터링 실패 {str(e)}')
        return None