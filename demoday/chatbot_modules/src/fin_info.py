import requests
from bs4 import BeautifulSoup

def get_fin_info_from_naver(ticker):

    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # HTML 요청
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # class="aside_invest_info" 선택
        aside_info = soup.find("div", class_="aside_invest_info")

        if aside_info:
            data = {}

            try:
                # 시가총액
                market_cap = aside_info.select_one("#_market_sum")
                data["시가총액"] = market_cap.text.strip().replace('\n', '').replace('\t', '') + "억원" if market_cap else None

                # 시가총액 순위
                market_rank = aside_info.select_one("table:first-of-type tr:nth-of-type(2) em")
                data["시가총액 순위"] = f"코스피 {market_rank.text.strip()}위" if market_rank else None

                # 상장주식수
                shares_outstanding = aside_info.select_one("table:first-of-type tr:nth-of-type(3) em")
                data["상장주식수"] = shares_outstanding.text.strip() if shares_outstanding else None

                # 액면가 및 매매단위
                face_value = aside_info.select("table:first-of-type tr:nth-of-type(4) em")
                if len(face_value) == 2:
                    data["액면가 | 매매단위"] = f"{face_value[0].text.strip()}원 | {face_value[1].text.strip()}주"

                # 외국인한도주식수(A)
                foreign_limit = aside_info.select_one("table:nth-of-type(2) tr:nth-of-type(1) em")
                data["외국인한도주식수(A)"] = foreign_limit.text.strip() if foreign_limit else None

                # 외국인보유주식수(B)
                foreign_owned = aside_info.select_one("table:nth-of-type(2) tr:nth-of-type(2) em")
                data["외국인보유주식수(B)"] = foreign_owned.text.strip() if foreign_owned else None

                # 외국인 소진율(B/A)
                foreign_ratio = aside_info.select_one("table:nth-of-type(2) tr.strong td em")
                data["외국인 소진율(B/A)"] = foreign_ratio.text.strip() + "%" if foreign_ratio else None

                # 투자의견 & 목표주가
                investment_opinion = aside_info.select_one("table:nth-of-type(3) tr:first-of-type td em")
                target_price = aside_info.select_one("table:nth-of-type(3) tr:first-of-type td em:nth-of-type(2)")
                if investment_opinion and target_price:
                    data["투자의견 | 목표주가"] = f"{investment_opinion.text.strip()}매수 | {target_price.text.strip()}"

                # 52주 최고/최저
                highest_52w = aside_info.select_one("table:nth-of-type(3) tr:nth-of-type(2) em:first-of-type")
                lowest_52w = aside_info.select_one("table:nth-of-type(3) tr:nth-of-type(2) em:nth-of-type(2)")
                if highest_52w and lowest_52w:
                    data["52주 최고 | 최저"] = f"{highest_52w.text.strip()} | {lowest_52w.text.strip()}"

                # PER & EPS
                per = aside_info.select_one("#_per")
                eps = aside_info.select_one("#_eps")
                data["PER | EPS (2024.09)"] = f"{per.text.strip()}배 | {eps.text.strip()}원" if per and eps else None

                # 추정 PER & EPS
                est_per = aside_info.select_one("#_cns_per")
                est_eps = aside_info.select_one("#_cns_eps")
                data["추정 PER | EPS"] = f"{est_per.text.strip()}배 | {est_eps.text.strip()}원" if est_per and est_eps else None

                # PBR & BPS
                pbr = aside_info.select_one("#_pbr")
                bps = aside_info.select_one("table.per_table tr:nth-of-type(3) td em:nth-of-type(2)")
                data["PBR | BPS (2024.09)"] = f"{pbr.text.strip()}배 | {bps.text.strip()}원" if pbr and bps else None

                # 배당수익률
                dividend_yield = aside_info.select_one("#_dvr")
                data["배당수익률 (2024.12)"] = dividend_yield.text.strip() + "%" if dividend_yield else None

                # 동일업종 PER
                industry_per = aside_info.select_one("table:nth-of-type(5) tr.strong td em")
                data["동일업종 PER"] = industry_per.text.strip() + "배" if industry_per else None

                # 동일업종 등락률
                industry_change = aside_info.select_one("table:nth-of-type(5) tr:nth-of-type(2) td em")
                data["동일업종 등락률"] = industry_change.text.strip() if industry_change else None

            except Exception as e:
                print(f"오류 발생: {e}")

            return data

        else:
            print("해당 정보를 찾을 수 없습니다.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None
