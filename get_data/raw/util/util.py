from pykrx import stock
from datetime import datetime, timedelta

def get_quarterly_market_ticker_list(start_date, end_date):
	'''
	start_date와 end_date를 기준으로, 각 연도를 4분할하여 분기별로 상장사 리스트 반환
	'''

	# start_date와 end_date 사이의 각 분기별 날짜를 반환해주는 함수
	def get_quarter_dates(start_date, end_date):
		# 날짜 문자열을 datetime 객체로 변환
		start_date = datetime.strptime(start_date, '%Y%m%d')
		end_date = datetime.strptime(end_date, '%Y%m%d')

		# 분기별 시작 날짜와 종료 날짜 계산
		quarter_dates = []
		
		# start_date가 속한 분기의 시작 날짜 계산
		year = start_date.year
		quarter_start_month = ((start_date.month - 1) // 3) * 3 + 1
		first_quarter_start = datetime(year, quarter_start_month, 1)
		
		# 첫 분기 시작 날짜가 start_date 이전이라면, 다음 분기로 이동
		if first_quarter_start < start_date:
			quarter_start_month += 3
			if quarter_start_month > 12:
				quarter_start_month = 1
				year += 1
			first_quarter_start = datetime(year, quarter_start_month, 1)
		
		# 분기별로 시작일과 종료일을 리스트에 추가
		current_date = first_quarter_start
		while current_date <= end_date:
			quarter_start = current_date
			# 다음 분기 시작 날짜를 계산하기 위해 3개월 더함
			quarter_end_month = quarter_start.month + 2
			if quarter_end_month > 12:
				quarter_end_month -= 12
				quarter_end_year = quarter_start.year + 1
			else:
				quarter_end_year = quarter_start.year
			
			# 분기 종료일은 해당 분기의 마지막 날 (31, 30, 30, 31 일)
			quarter_end = datetime(quarter_end_year, quarter_end_month, 1) + timedelta(days=32)
			quarter_end = quarter_end.replace(day=1) - timedelta(days=1)
			
			# 종료일이 end_date를 초과하면 end_date로 설정
			if quarter_end > end_date:
				quarter_end = end_date
			
			# 리스트에 추가
			quarter_dates.append([quarter_start.strftime('%Y%m%d'), quarter_end.strftime('%Y%m%d')])
			
			# 다음 분기로 이동
			quarter_start_month = current_date.month + 3
			year = current_date.year
			if quarter_start_month > 12:
				quarter_start_month -= 12
				year += 1
			current_date = datetime(year, quarter_start_month, 1)
		
		return quarter_dates

	# target_date에 대해 상장사 리스트 조회 후 딕셔너리 반환하는 함수
	def get_target_date_market_list(target_date:str):
		# 각 분기별로 코스피 내 상장된 종목 딕셔너리로 생성
		target_date = '20200101'
		stock_dict = {}
		for ticker in stock.get_market_ticker_list(date=target_date):
				corp_name = stock.get_market_ticker_name(ticker)
				stock_dict[ticker] = corp_name
		
		return stock_dict

	quarterly_market_ticker_dict = {}

	target_date_list = get_quarter_dates(start_date, end_date)

	print('target_date_list', target_date_list)

	for i in range(len(target_date_list)):
		target_date = target_date_list[i]

		print(target_date)
		quarter_start_date = target_date[0]
		quarter_end_date = target_date[-1]

		# print('quarter_start_date', quarter_start_date)
		# print('quarter_end_date', quarter_end_date)

		year = quarter_start_date[:4]
		which_quarter = ''
		
		# print(quarter_start_date[4:6])
		
		if quarter_start_date[4:6] == '01':
			which_quarter = '1Q'
		elif quarter_start_date[4:6] == '04':
			which_quarter = '2Q'
		elif quarter_start_date[4:6] == '07':
			which_quarter = '3Q'
		elif quarter_start_date[4:6] == '10':
			which_quarter = '4Q'

		market_list_dict = get_target_date_market_list(quarter_end_date)

		print('key:', f'{year}_{which_quarter}')

		quarterly_market_ticker_dict[f'{year}_{which_quarter}'] = {
			'start_date': quarter_start_date,
			'end_date': quarter_end_date,
			'market_list': market_list_dict
		}

	return quarterly_market_ticker_dict