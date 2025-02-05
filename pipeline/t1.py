import pandas as pd
import json
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sub_func import *
from pipeline_utils import *

def extract_key_metrics(sector_info):
    """섹터 정보에서 Carhart 4 factor 관련 주요 지표 추출"""
    if sector_info is None:
        return None
    
    return {
        'market_beta': sector_info.get('market_beta', 0),
        'size_factor': sector_info.get('size_factor', 0),
        'value_factor': sector_info.get('value_factor', 0),
        'momentum_factor': sector_info.get('momentum_factor', 0)
    }

def extract_sentiment_score(df):
    """감성분석 결과를 numerical score로 변환"""
    def get_score(result):
        if isinstance(result, dict):
            # 딕셔너리에서 감성 결과 추출 (예: result.get('sentiment') 등)
            sentiment = result.get('sentiment', 'neutral')  # 적절한 키로 수정
        else:
            sentiment = result
            
        score_mapping = {
            'positive': 1.0,
            'neutral': 0.0,
            'negative': -1.0
        }
        return score_mapping.get(sentiment, 0.0)
    
    df['sentiment_score'] = df['SA_result'].apply(get_score)
    return df

def filter_by_percentile_and_label(df, label, percentile):
    """특정 감성의 상위/하위 percentile에 해당하는 뉴스 필터링"""
    if df.empty:
        return pd.DataFrame()
    
    # label에 따라 필터링
    if label == 'positive':
        filtered_df = df[df['SA_result'] == 'positive']
        return filtered_df.nlargest(int(len(filtered_df) * percentile/100), 'sentiment_score')
    else:  # negative
        filtered_df = df[df['SA_result'] == 'negative']
        return filtered_df.nsmallest(int(len(filtered_df) * percentile/100), 'sentiment_score')
    
def get_final_tickers(content):
    """content['portfolio']['corp_analysis_report']에서 invest가 True인 ticker 리스트 반환"""
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
    
def get_analyst_rp(agent_type, title):
    data = read_json(json_file_path)
    if agent_type in data and title in data[agent_type]:
        page_id = data[agent_type][title]
        content = get_all_text_from_page(page_id)
        return content
    else:
        return None
    
def get_current_portfolio(target_year, target_quarter):
    jsons_list = os.listdir(f'./pf_logs/{target_year}_{target_quarter}')
    not_init = any(filename.endswith('_weights.json') for filename in jsons_list)

    if not_init:
        target_pf = sorted(jsons_list)[-2]

        with open(f'./pf_logs/{target_year}_{target_quarter}/{target_pf}', 'r') as f:
            current_portfolio = json.load(f)
    else:
        with open(f'./pf_logs/{target_year}_{target_quarter}/{target_year}_{target_quarter}_init_pf.json', 'r') as f:
            current_portfolio = json.load(f)

    return current_portfolio

class t1_analyst:
    """Investment report generation class with GPT integration"""
    
    MARKDOWN_INSTRUCTION = """
    응답은 반드시 markdown 문법에 따라 작성되어야 합니다.
    ** 보고서에는 반드시 주어진 정보에 대한 분석이 필요합니다 **
    """

    ANALYST_BASE_PROMPT = """
    당신은 증권회사에 고용된 {role}입니다.
    주식투자의 관점에서 주어진 정보들을 요약하고, 이에 대한 의견을 알려주세요.
    {additional_instructions}
    {markdown_instruction}
    """

    INDIVIDUAL_REPORT_SYSTEM = """증권사 애널리스트로서 종목 분석 보고서 작성
        # 필수 섹션
        1. 기업 개요
        - 사업 모델과 핵심 역량
        - 시장 포지셔닝

        2. 재무 분석
        - 핵심 재무지표 분석
        - 수익성/성장성 평가

        3. 섹터 분석
        - 산업 동향과 경쟁력
        - 기술적 분석 시사점

        4. 투자의견
        - 투자포인트 3개
        - 주요 리스크
        - 목표가 및 근거

        요구사항:
        - 구체적 데이터 기반
        - 명확한 투자 논리 제시
        """ + MARKDOWN_INSTRUCTION

    def __init__(self, today, tickers: list, year: str, quarter: str):
        self.tickers = tickers
        self.year = year
        self.quarter = quarter
        self.prompts = self._initialize_prompts()
        self.responses = {ticker: {} for ticker in tickers}
        self.individual_reports = {}
        self.start_date, self.end_date = self._get_date_range()
        self.today = today
        
    def generate_individual_report(self, ticker: str) -> str:
        """Generate a comprehensive report for a single stock"""
        print(f"\n=== {ticker} 분석 중... ===")

        # report_prompt를 빈 문자열로 초기화하여 예외 발생 시에도 접근 가능하게 만듦
        report_prompt = ""

        try:
            # Financial analysis
            financial_data = self.analyze_financial_data(ticker)

            # Sector and pattern analysis
            sector_analysis = self.analyze_sector_and_pattern(ticker)

            # News analysis with cross-year support
            try:
                start_year = self.start_date[:4]
                end_year = self.today[:4]

                if start_year == end_year:
                    # 같은 연도면 기존 방식대로 호출
                    news_data = corp_rel_news_info(ticker, self.year, self.start_date, self.today)
                else:
                    # 연도가 다르면 두 번 호출 후 합침
                    df1 = corp_rel_news_info(ticker, start_year, self.start_date, f"{start_year}1231")
                    df2 = corp_rel_news_info(ticker, end_year, f"{end_year}0101", self.today)

                    # 두 개의 DataFrame을 합치고 정렬
                    news_data = pd.concat([df1, df2], axis=0).sort_index() if df1 is not None and df2 is not None else None

                news_summary = self._process_news(news_data) if news_data is not None else {"Positive": [], "Negative": []}

            except FileNotFoundError:
                print(f"{ticker}의 뉴스 데이터가 없습니다. 분석을 계속합니다.")
                news_summary = {"Positive": [], "Negative": []}
            except Exception as e:
                print(f"{ticker}의 뉴스 처리 중 오류 발생: {e}. 분석을 계속합니다.")
                news_summary = {"Positive": [], "Negative": []}

            # Stock price data
            try:
                stock_price = stock_price_info(ticker, self.start_date, self.today)[['Close', 'RSI_14']]
                price_dict = stock_price.to_dict() if stock_price is not None and not stock_price.empty else None
            except Exception as e:
                print(f"{ticker}의 주가 정보 처리 중 오류 발생: {e}. 분석을 계속합니다.")
                price_dict = None

            # Combine all data for individual report
            report_prompt = "\n".join([
                f"재무제표 및 재무 비율 분석: {financial_data}",
                f"섹터 분석: {sector_analysis}",
                f"종목 관련 뉴스: {news_summary}",
                f"주가 정보: {price_dict}"
            ])

            # Generate individual report
            report = to_GPT(self.INDIVIDUAL_REPORT_SYSTEM, report_prompt)
            self.individual_reports[ticker] = report
            return report

        except Exception as e:
            print(f"{ticker} 분석 중 오류 발생: {e}")
            return None

    def _initialize_prompts(self) -> Dict[str, str]:
        """Initialize system prompts with templated format"""
        return {
            "financial_system": self.ANALYST_BASE_PROMPT.format(
                role="재무전문가",
                additional_instructions="보고서 근거 기반 의견 제시",
                markdown_instruction=self.MARKDOWN_INSTRUCTION
            ),
            "intl_macro_system": self.ANALYST_BASE_PROMPT.format(
                role="국제관계전문가",
                additional_instructions="국가별 금리, GDP, 인플레이션 등 거시경제 정보 분석",
                markdown_instruction=self.MARKDOWN_INSTRUCTION
            ),
            "sector_system": """증권사 경제전문가로서 투자 관점에서 정보 분석 및 의견 제시
                # 필수 포함 사항
                - 섹터별 성과와 동향 분석
                - 투자 매력도 평가 (근거 제시)
                - 차트 패턴 분석 및 기술적 시사점
                """ + self.MARKDOWN_INSTRUCTION,
            "final_system": """증권사 리서치센터장으로서 개별 애널리스트 보고서들을 종합하여 최종 투자전략 보고서 작성
                # 필수 섹션
                1. 거시경제 분석 요약
                - 글로벌 동향 핵심 포인트
                - 주요 리스크 요인

                2. 개별 종목 분석 종합
                - 각 종목 투자매력도 비교
                - 상대가치 평가

                3. 최종 포트폴리오 전략
                - 종목별 투자비중 추천과 근거
                - 위험관리 방안

                4. 핵심 결론
                - 최우선 투자 추천 종목
                - 중점 모니터링 요소

                작성 지침:
                - 개별 애널리스트 보고서의 분석을 비교/종합하여 결론 도출
                - 종목간 상대매력도를 구체적 근거와 함께 제시
                - 실행 가능한 투자전략 제안
                """ + self.MARKDOWN_INSTRUCTION
        }

    def _get_previous_quarter(self) -> tuple:
        """Get the previous quarter's year and quarter"""
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        prev_index = quarter_order.index(self.quarter) - 1  # 이전 분기 인덱스

        if prev_index < 0:  # 현재가 Q1이면 이전 해의 Q4로 이동
            prev_year = str(int(self.year) - 1)
            prev_quarter = 'Q4'
        else:
            prev_year = self.year
            prev_quarter = quarter_order[prev_index]

        return prev_year, prev_quarter

    def _get_date_range(self) -> tuple:
        """Get start and end dates for the previous quarter"""
        quarter_months = {
            'Q1': ('01', '03'),
            'Q2': ('04', '06'),
            'Q3': ('07', '09'),
            'Q4': ('10', '12')
        }

        # 이전 분기 계산
        prev_year, prev_quarter = self._get_previous_quarter()
        
        if prev_quarter in quarter_months:
            start_month, end_month = quarter_months[prev_quarter]
            start_date = f"{prev_year}{start_month}01"
            end_date = f"{prev_year}{end_month}{'30' if end_month in ['06', '09'] else '31'}"
            return start_date, end_date
        else:
            raise ValueError(f"Invalid quarter: {prev_quarter}")

    def analyze_financial_data(self, ticker: str) -> str:
        """Analyze financial statements and generate report"""
        try:
            fin_statement = get_raw_fin_statement_info(ticker, self.year, self.quarter)
            fin_statement_dict = fin_statement.T.to_dict() if fin_statement is not None else {}
        except Exception:
            fin_statement_dict = {}

        try:
            fin_ratio = fin_statement_info(ticker, self.year, self.quarter)
            fin_ratio_dict = fin_ratio.to_dict('records')[0] if fin_ratio is not None and not fin_ratio.empty else {}
        except Exception:
            fin_ratio_dict = {}

        try:
            fin_report = reports_info(ticker, self.year, self.quarter)
            report_content = fin_report['1. 요약재무정보.csv'][0][4:-4] if not fin_report.empty else "정보 없음"
        except Exception:
            report_content = "정보 없음"
        
        prompt_data = {
            "재무제표": fin_statement_dict,
            "주요 재무 비율": fin_ratio_dict,
            "재무보고서": report_content
        }
        
        financial_prompt = "\n".join(f"{k}: {v}" for k, v in prompt_data.items())
        report = to_GPT(self.prompts["financial_system"], financial_prompt)

        print('analyze_financial_data의 GPT 요청 결과:', report) # 디버깅용

        return report

    def analyze_international_macro(self) -> str:
        """Analyze international news and macroeconomic data with cross-year support"""

        # 뉴스의 경우 매일매일 업데이트 되기 때문에 그에 맞춰서 일별로 새로운 데이터 포함해서 생성하도록 함
        try:
            start_year = self.start_date[:4]
            end_year = self.today[:4]

            if start_year == end_year:
                # 같은 연도면 기존 방식대로 호출
                intl_news = intl_news_info(self.year, self.start_date, self.today)
            else:
                # 연도가 다르면 두 번 호출 후 합치기
                df1 = intl_news_info(start_year, self.start_date, f"{start_year}1231")
                df2 = intl_news_info(end_year, f"{end_year}0101", self.today)

                # 두 개의 DataFrame을 합치고 정렬
                intl_news = pd.concat([df1, df2], axis=0).sort_index()

            news_titles = list(intl_news['news_title']) if intl_news is not None and not intl_news.empty else []
        except Exception as e:
            print(f"국제 뉴스 데이터 처리 중 오류 발생: {e}")
            news_titles = []

        # 거시경제는 분기별이니까 그대로 직전 분기에 대한 정보만 사용
        try:
            macro_data = macro_econ_info(self.year, self.start_date, self.end_date)
        except Exception:
            macro_data = "거시경제 데이터 없음"

        self.prompts["intl_macro_prompt"] = "\n".join([
            f"국제 뉴스 헤드라인: {news_titles}",
            f"거시경제 관련 정보: {macro_data}"
        ])

        return to_GPT(self.prompts["intl_macro_system"], self.prompts["intl_macro_prompt"])

    def analyze_sector_and_pattern(self, ticker: str) -> str:
        """Analyze sector trends and chart patterns"""
        index_prices = {}
        try:
            sector_list = [s for s in os.listdir('../store_data/raw/market_data/sector') 
                          if '코스피' not in s]
        except Exception:
            sector_list = []
        
        # Collect sector data
        # for sector in sector_list:
        #     try:
        #         # 이것도 직전분기 시작일 ~ 당일까지의 데이터로
        #         index_price = index_price_info(sector, self.start_date, self.today)
        #         if index_price is not None and not index_price.empty:
        #             index_price = index_price[['Close', 'Transaction_Val', 'Market_Cap', 'RSI_14']]
        #             index_prices[sector] = index_price.T.to_dict()
        #     except Exception:
        #         continue
        
        # Collect sector analysis
        sector_infos = {}
        for sector in sector_list:
            try:
                # 이건 분기별로 유지
                sector_analysis = sector_analysis_info(sector, self.year, self.quarter)
                if sector_analysis is not None:
                    sector_infos[sector] = extract_key_metrics(sector_analysis)
            except Exception:
                continue

        # try:
        #     pattern_data = pattern_info(ticker, self.today)
        #     pattern_dict = pattern_data.to_dict('records') if pattern_data is not None and not pattern_data.empty else None
        # except Exception:
        #     pattern_dict = None
        
        self.prompts["sector_prompt"] = "\n".join([
            # f"섹터별 가격 정보: {index_prices}",
            f"섹터별 carhart 4 factor 분석: {sector_infos}",
            # f"차트 패턴 분석 결과: {pattern_dict}"
        ])
        
        response = to_GPT(self.prompts["sector_system"], self.prompts["sector_prompt"])

        print('analyze_sector_and_pattern의 GPT 요청 결과:', response) # 디버깅용

        return response

    def analyze_stocks(self):
        """Execute analysis for all stocks"""
        # Only analyze macro once
        macro_response = self.analyze_international_macro()
        self.responses["international_macro"] = macro_response
        
        # for ticker in self.tickers:
        #     print(f"\n=== {ticker} 분석 중... ===")
        #     try:
        #         self.responses[ticker].update({
        #             "financial": self.analyze_financial_data(ticker),
        #             # "sector_pattern_analysis": self.analyze_sector_and_pattern(ticker)
        #         })
        #     except Exception as e:
        #         print(f"{ticker} 분석 중 오류 발생: {e}")

    def generate_final_report(self) -> dict:
        try:
            # 종목들의 개별 보고서만 포함하기
            combined_prompt = []
            
            for ticker in self.tickers:
                if ticker not in self.individual_reports:
                    print(f"{ticker} 보고서 없음")
                    pass
                
                report = self.individual_reports.get(ticker)
                if report:
                    combined_prompt.append(f"\n=== {ticker} 종목 분석 ===")
                    report_content = report.get('choices', [{}])[0].get('message', {}).get('content', '') if isinstance(report, dict) else str(report)
                    combined_prompt.append(report_content)

            prompt = "\n".join(combined_prompt)

            # 최종 보고서 생성 요청
            final_response = to_GPT(self.prompts["final_system"], prompt)
            return final_response
        
        except Exception as e:
            print(f"generate_final_report에서 예외 발생: {e}")
            return {}

    def _process_news(self, corp_news_df) -> Dict[str, list]:
        """Process corporate news and extract sentiment"""
        news_summary = {'Positive': [], 'Negative': []}
        
        if corp_news_df is not None and not corp_news_df.empty:
            try:
                # 증권 카테고리 필터링
                corp_news_df = corp_news_df[corp_news_df['news_category'].str.contains('증권', na=False)]
                
                if not corp_news_df.empty:
                    # SA 결과 및 감성 점수 추출
                    corp_news_df['SA_result'] = corp_news_df['news_title'].apply(lambda x: 
                        get_SA_result(x) if pd.notna(x) else None)
                    
                    # None이나 NaN이 아닌 행만 감성 점수 추출
                    valid_news = corp_news_df.dropna(subset=['SA_result'])
                    if not valid_news.empty:
                        valid_news = extract_sentiment_score(valid_news)
                        
                        for sentiment in ['positive', 'negative']:
                            try:
                                news = filter_by_percentile_and_label(valid_news, sentiment, 20)
                                if not news.empty:
                                    news_summary[sentiment.capitalize()] = list(news['news_title'])
                            except Exception:
                                continue
            except Exception as e:
                print(f"뉴스 처리 중 오류 발생: {e}")
        
        return news_summary

    def _get_response_content(self, response: Dict) -> str:
        """GPT 응답에서 content 추출"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""
        
    def save_final_report(self, final_response: Dict) -> None:
        """최종 애널리스트 보고서 저장"""
        page_title = f"{self.today}_t_1_analyst_rp"
        content = self._get_response_content(final_response)
        
        print(f"{page_title} 보고서를 노션 DB에 저장합니다...")
        to_DB('t_1', page_title, f"{self.start_date}_{self.today}", content)

class t1_pf_manager:
    def __init__(self, today, analyst_report, tickers: list, year: str, quarter: str, target_year, target_quarter):
        self.tickers = tickers
        self.year = year
        self.quarter = quarter
        self.prompts = self._initialize_prompts()
        self.responses = {}
        self.report_data = {}
        self.analyst_report = analyst_report
        self.current_portfolio = None
        self.individual_reports = {}
        self.today = today
        self.target_year = target_year
        self.target_quarter = target_quarter
        
    def _initialize_prompts(self) -> Dict[str, str]:
        return {
            "individual_portfolio_system": """당신은 자산운용사의 포트폴리오 매니저입니다.
해당 종목에 대한 애널리스트 리서치 보고서를 검토하여 포트폴리오 운용 전략을 제시하세요.

# 1. 종목 현황
- 현재 비중과 추이
- 주요 위험/수익 지표
- 투자 성과 분석

# 2. 투자 전략
- 적정 비중과 근거
- 핵심 매력도/리스크
- 비중 조정 방향

# 3. 리스크 관리
- 손절/이익실현 기준
- 주요 모니터링 지표

응답은 markdown 형식으로 작성""",

            "final_portfolio_system": """당신은 자산운용사의 수석 포트폴리오 매니저입니다.
개별 종목 포트폴리오 보고서들을 종합하여 전체 포트폴리오 최종 운용 전략을 제시하세요.

# 1. 포트폴리오 종합 현황
- 전체 구성과 섹터 비중
- 종목별 성과 비교
- 핵심 위험/수익 특성

# 2. 전략적 자산배분
- 섹터별 비중 전략
- 종목간 상대매력도
- 전체 위험분산 방안

# 3. 최종 포트폴리오 조정안
- 종목별 비중 조정 방향
- 편입/편출 검토
- 우선순위와 실행계획

# 4. 종합 리스크 관리
- 포트폴리오 전체 관점
- 개별종목 리스크 통합 관리
- 주요 모니터링 지표

작성 지침:
- 개별 보고서들의 분석을 통합하여 결론 도출
- 종목간 상대가치 고려한 전략 수립
- 구체적 실행방안 제시

*** Weight를 작성할 때에는, 반드시 포트폴리오 내 모든 종목의 가중치 합이 1이 되도록 작성해야 합니다. ***

응답은 markdown 형식으로 작성""",
            "individual_portfolio_prompt": "",
            "final_portfolio_prompt": ""
        }
        
    def generate_individual_report(self, ticker: str, analyst_report: str, portfolio: Dict) -> Dict:
        """개별 종목 포트폴리오 보고서 생성"""
        prompt = f"종목코드: {ticker}\n"
        prompt += f"현재 포트폴리오 구성: {portfolio}\n"
        prompt += f"애널리스트 보고서: {analyst_report}\n\n"
        prompt += "응답 형식:\n\n"
        prompt += "1. 투자 전략 및 분석 보고서 (Markdown 형식)\n"
        prompt += "2. 포트폴리오 내 적정 비중 (JSON 형식: {'ticker': 'weight'})"

        response = to_GPT(self.prompts["individual_portfolio_system"], prompt)

        # 응답에서 내용 추출
        report_text = self._get_response_content(response)

        # JSON 형식의 비중 정보 추출
        weight_info = self._extract_weight_info(response)

        self.individual_reports[ticker] = {
            "report": report_text,
            "weight": weight_info
        }
        return self.individual_reports[ticker]

    def _extract_weight_info(self, response: Dict) -> Dict:
        """GPT 응답에서 비중 정보를 추출하는 메서드"""
        try:
            content = response["choices"][0]["message"]["content"]
            match = re.search(r'({.*?})', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))  # JSON 변환
        except (KeyError, IndexError, json.JSONDecodeError):
            return {}
        return {}

        
    def set_current_portfolio(self, portfolio: Dict) -> None:
        """현재 포트폴리오 설정"""
        self.current_portfolio = portfolio
        
    def generate_final_report(self) -> Dict:
        """최종 포트폴리오 매니저 보고서 생성"""
        if not self.individual_reports:
            raise ValueError("Individual reports must be generated first")

        combined_prompt = []
        final_weights = {}

        for ticker in self.tickers:
            if ticker in self.individual_reports:
                combined_prompt.append(f"\n=== {ticker} 포트폴리오 보고서 ===")
                combined_prompt.append(self.individual_reports[ticker]["report"])
                
                # 종목별 비중 저장
                final_weights[ticker] = self.individual_reports[ticker]["weight"].get(ticker, "N/A")

        self.prompts["final_portfolio_prompt"] = "\n".join(combined_prompt)
        final_response = to_GPT(self.prompts["final_portfolio_system"], self.prompts["final_portfolio_prompt"])

        return {
            "final_report": self._get_response_content(final_response),
            "final_weights": final_weights
        }

    def _get_response_content(self, response: Dict) -> str:
        """GPT 응답에서 content 추출"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def save_final_report(self, final_response: Dict) -> None:
        """최종 포트폴리오 매니저 보고서 저장"""
        page_title = f"{self.today}_t_1_portfolio_report"
        content = final_response["final_report"]
        weights = final_response["final_weights"]

        print(f"{page_title} 보고서를 노션 DB에 저장합니다...")

        # 노션 DB 저장
        to_DB('t_1', page_title, f"{self.quarter}_{self.year}", content)
        to_DB('t_1', f"{self.today}_portfolio_weights", f"{self.quarter}_{self.year}", json.dumps(weights, indent=2))

        # JSON 파일 저장할 디렉토리 경로
        log_dir = f"./pf_logs/{self.target_year}_{self.target_quarter}"
        os.makedirs(log_dir, exist_ok=True)  # 디렉토리 없으면 생성

        # 파일 경로
        file_path = os.path.join(log_dir, f"{self.today}_portfolio_weights.json")

        # JSON 파일 저장
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=2, ensure_ascii=False)

        print(f"포트폴리오 비중 데이터가 {file_path}에 저장되었습니다.")

class t1_trader:
    def __init__(self, today, tickers: list, year: str, quarter: str):
        self.tickers = tickers
        self.year = year
        self.quarter = quarter
        self.prompts = self._initialize_prompts()
        self.individual_reports = {}
        self.responses = {ticker: {} for ticker in tickers}
        self.report_data = {}
        self.start_date, self.end_date = self._get_date_range()
        self.today = today
        self.price_data = {}
        self.analyst_reports = {}
        self.pm_reports = {}
        self.price_predictions = {}
        
    def _initialize_prompts(self) -> Dict[str, str]:
        """프롬프트 초기화"""
        return {
            "individual_trader_system": """당신은 증권사의 트레이더입니다. 해당 종목의 데이터와 보고서를 분석하여 구체적인 매매 전략을 제시하세요.

# 종목 기본 분석
- 현재가 동향과 기술적 신호
- 예측가격 분석
- 거래량 특징

# 매매 전략
- 매매 방향과 근거
- 진입/청산 가격대
- 리스크 관리 전략

모든 분석은 제공된 데이터에 기반하여 작성하세요.
응답은 markdown 형식으로 작성""",

            "final_trader_system": """당신은 증권사의 수석 트레이더입니다. 개별 종목 트레이딩 보고서들을 종합하여 최종 매매 전략을 제시하세요.

# 시장 종합 분석
- 주요 매매 환경
- 전반적 매매 전략

# 우선 매매 종목
- 상위 5-7개 종목 선정과 근거
- 구체적 매매 전략
- 핵심 리스크 관리

# 기타 종목 전략
- 실제 매수/매도 대상 종목 분석
- 종목별 구체적 진입/청산 전략
- 종목별 리스크 관리 방안

작성 지침:
- 개별 보고서 분석 통합
- 우선순위 기반 전략 수립
- 구체적 실행 방안 제시
- 가정이나 예시가 아닌 실제 종목과 데이터 기반 분석 필수
- 각 종목별 현재 시장 상황과 기업 실적 반영

응답은 markdown 형식으로 작성""",
            "individual_trader_prompt": "",
            "final_trader_prompt": ""
        }
    
    def _get_previous_quarter(self) -> tuple:
        """Get the previous quarter's year and quarter"""
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        prev_index = quarter_order.index(self.quarter) - 1  # 이전 분기 인덱스

        if prev_index < 0:  # 현재가 Q1이면 이전 해의 Q4로 이동
            prev_year = str(int(self.year) - 1)
            prev_quarter = 'Q4'
        else:
            prev_year = self.year
            prev_quarter = quarter_order[prev_index]

        return prev_year, prev_quarter


    def _get_date_range(self) -> tuple:
        """Get start and end dates for the previous quarter"""
        quarter_months = {
            'Q1': ('01', '03'),
            'Q2': ('04', '06'),
            'Q3': ('07', '09'),
            'Q4': ('10', '12')
        }

        # 이전 분기 계산
        prev_year, prev_quarter = self._get_previous_quarter()
        
        if prev_quarter in quarter_months:
            start_month, end_month = quarter_months[prev_quarter]
            start_date = f"{prev_year}{start_month}01"
            end_date = f"{prev_year}{end_month}{'30' if end_month in ['06', '09'] else '31'}"
            return start_date, end_date
        else:
            raise ValueError(f"Invalid quarter: {prev_quarter}")

    def set_price_data(self) -> None:
        """주가 데이터 설정"""
        try:
            for ticker in self.tickers:
                self.price_data[ticker] = stock_price_info(ticker, self.start_date, self.today)
        except Exception as e:
            print(f"가격 데이터 설정 중 오류 발생: {str(e)}")


    def set_analyst_report(self, report: str) -> None:
        """애널리스트 보고서 설정"""
        self.analyst_report = report

    def set_pm_report(self, report: str) -> None:
        """포트폴리오 매니저 보고서 설정"""
        self.pm_report = report

    def get_price_prediction(self) -> None:
        """GRU 모델을 사용한 가격 예측"""
        try:
            self.price_predictions = predict_multiple_prices(
                self.tickers,
                self.start_date,
                self.end_date
            )
        except Exception as e:
            print(f"가격 예측 모델 실행 중 오류 발생: {str(e)}")
    
    def generate_individual_report(self, ticker: str) -> str:
        """개별 종목 트레이더 보고서 생성"""
        price_data = self.price_data.get(ticker, {})
        if hasattr(price_data, 'to_dict'):
            price_data = price_data.to_dict()
            
        prompt = f"종목코드: {ticker}\n"
        prompt += f"가격 데이터: {price_data}\n"
        prompt += f"가격 예측: {self.price_predictions.get(ticker, {})}\n"
        prompt += f"애널리스트 보고서: {self.analyst_reports.get(ticker, '정보 없음')}\n"
        prompt += f"PM 보고서: {self.pm_reports.get(ticker, '정보 없음')}"

        response = to_GPT(self.prompts["individual_trader_system"], prompt)
        self.individual_reports[ticker] = response
        return response

    def generate_final_report(self) -> str:
        """최종 트레이더 보고서 생성"""
        if not self.individual_reports:
            raise ValueError("Individual reports must be generated first")
        
        combined_prompt = []
        for ticker in self.tickers:
            if ticker in self.individual_reports:
                combined_prompt.append(f"\n=== {ticker} 트레이딩 보고서 ===")
                combined_prompt.append(self._get_response_content(self.individual_reports[ticker]))
        
        self.prompts["final_trader_prompt"] = "\n".join(combined_prompt)
        final_response = to_GPT(self.prompts["final_trader_system"], 
                              self.prompts["final_trader_prompt"])
        return final_response
    
    def _get_response_content(self, response: Dict) -> str:
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def save_final_report(self, final_response: Dict) -> None:
        page_title = f"{self.today}_t_1_trader_report"
        content = self._get_response_content(final_response)
        
        print(f"{page_title} 보고서를 노션 DB에 저장합니다...")
        to_DB('t_1', page_title, f"{self.quarter}_{self.year}", content)

today = '20230101'

# JSON 파일 경로
json_file_path = "./notion_page_ids.json"

# # 조회할 정보들의 기준 연도
# base_year = "2022"
# base_quarter = "Q4"

# # 현재 시기 (투자를 진행할 현재 시점)
# target_year = '2023'
# target_quarter = 'Q1'

# # 'pf_selection_agent'에서 종목 코드 가져오기
# tickers = get_tickers_from_json('pf_selection_agent', f'{target_year}_{target_quarter}_init_pf')

# 한번 실행에 약 40분 (26개 종목 기준) 소요, 150만토큰 소모
def t1_analyst_main(today, tickers, base_year, base_quarter):

    # 분석기 객체 생성
    analyzer = t1_analyst(today, tickers, base_year, base_quarter)

    print('[t1_analyst] === 종목별 분석 시작 ===')
    # 분석 실행
    analyzer.analyze_stocks()

    # 개별 보고서 생성 
    for ticker in tickers:
        analyzer.generate_individual_report(ticker)

    print('[t1_analyst] === 최종 보고서 생성 ===')
    # 최종 보고서 생성
    final_report = analyzer.generate_final_report()

    # 노션에 저장
    analyzer.save_final_report(final_report)

def t1_pf_manager_main(today, tickers, base_year, base_quarter, target_year, target_quarter):
    analyst_report = get_analyst_rp('t_1', f'{today}_t_1_analyst_rp')

    # 2. 종합 포트폴리오 매니저 보고서 생성
    print('[t1_pf_manager] === 종합 포트폴리오 매니저 보고서 생성 ===')
    portfolio_manager = t1_pf_manager(today, analyst_report, tickers, base_year, base_quarter, target_year, target_quarter)

    # 각 종목별 포트폴리오 보고서 생성
    for ticker in tickers:
        current_portfolio = portfolio_manager.set_current_portfolio(get_current_portfolio(target_year, target_quarter))# 현재 포트폴리오 정보 가져오기
        portfolio_manager.generate_individual_report(ticker, analyst_report, current_portfolio)
        print(f"{ticker} 포폴 매니저 보고서 추출 완료")
        
    print('[t1_pf_manager] === 최종 보고서 생성 ===')
    # 보고서 생성
    portfolio_report = portfolio_manager.generate_final_report()

    # 보고서 출력
    print("\n=== 포트폴리오 매니저 종합 보고서 ===")
    print(portfolio_report)
    print("=== 보고서 끝 ===")

    # 보고서 저장
    portfolio_manager.save_final_report(portfolio_report)

# 한번 실행에 약 10분 (26개 종목 기준) 소요
def t1_trader_main(today, tickers, base_year, base_quarter):
    trader = t1_trader(today, tickers, base_year, base_quarter)

    print('[t1_trader] === 종목별 트레이더 보고서 생성 ===')
    # 필요한 데이터 설정
    trader.set_price_data()
    trader.get_price_prediction()

    # 각 종목별 트레이더 보고서 생성
    for ticker in tickers:
        trader.generate_individual_report(ticker)
        print(f"{ticker} 트레이더 보고서 추출 완료")

    # 최종 트레이더 보고서 생성
    print('[t1_trader] === 최종 보고서 생성 ===')
    final_report = trader.generate_final_report()
    trader.save_final_report(final_report)