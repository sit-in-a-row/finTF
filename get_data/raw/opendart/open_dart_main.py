from .file_management import save_financial_statement, save_sub_reports

def get_financial_info(stock_code:str, target_business_year:str):
    '''
    Opendart 관련 기능의 최종 main 함수.
    재무제표 및 공시 보고서를 모두 가져와 저장
    '''
    save_financial_statement(stock_code, target_business_year)
    save_sub_reports(stock_code, target_business_year)