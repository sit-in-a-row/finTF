from sub_func import *

json_file_path = './notion_page_ids.json'
current_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_dir, json_file_path)

def gen_trader(today, base_year, base_quarter):
    data = read_json(json_file_path)

    t_1_trader_report = get_all_text_from_page(data['t_1'][f"{today}_t_1_trader_report"])
    t_2_t_4_trader_log = get_all_text_from_page(data['t_2'][f"{today}_t_2_t_4_trader_log"])

    system_prompt = """
        당신은 한국 주식 시장 트레이더입니다.
        이전 t1, t2, t4의 트레이더 output을 참조해서 당일 거래 성과 보고서를 작성하세요.
        당일 거래 내역을 리뷰하고 거래에 개선해야 할 점을 작성하세요.
    """

    prompt = f"""
        아래는 당일 주식시장 거래시간 전과 거래시간 때 생성된 주식 트레이더의 레포트와 로그입니다.
        레포트와 로그를 사용해 당일거래성과 보고서를 작성하세요.
        당일거래에 개선할 점 또한 보고서에 포함하세요. 개선할 점을 구체적으로 알려주세요.

        주식시장 거래시간 전 레포트:
        {t_1_trader_report}

        주식시장 거래시간 중 로그:
        {t_2_t_4_trader_log}

        보고서를 Markdown 형식으로 작성하세요.
        보고서는 반드시 주어진 정보에 대한 분석이 필요합니다.
        """

    response = to_GPT(system_prompt, prompt)
    trader_report = response["choices"][0]["message"]["content"]
    print("\nGenerated Trade Report:", trader_report)  # 최종 출력 확인

    to_DB('t_5', f"{today}_t_5_trader_report", f"{base_quarter}_{base_year}", str(trader_report))
    
    return trader_report

def gen_portfolio(today, base_year, base_quarter):
    data = read_json(json_file_path)

    t_1_analyst_report = get_all_text_from_page(data['t_1'][f"{today}_t_1_analyst_rp"])
    t_1_pf_manager_report = get_all_text_from_page(data['t_1'][f"{today}_t_1_portfolio_report"])
    t_5_trader_report = get_all_text_from_page(data['t_5'][f"{today}_t_5_trader_report"])

    system_prompt = """
        당신은 주식 포트폴리오를 분석하는 금용 포트폴리오 매니저입니다.
        주식시장 거래시간 이후, 포트폴리오 성과 및 리스크 분석을 하고 주식시장 거래시간 전 포트폴리오와 비교를 합니다. 
    """

    prompt = f"""
    주식시장 거래시간 이후, 포트폴리오 성과 및 리스크 분석을 하고 주식시장 거래시간 전 포트폴리오와 비교를 합니다. 
    주식시장 거래시간 이후 트레이터 레포트와 애널리스트 레포트와 주식시장 거래시간 전 애널리스트 레포트를 참조해 현재 포트폴리오 성과 및 리스크 분석을 합니다.
    주식시장 거래시간 전 포트폴리오와 비교를 해서 전략이 잘 들어맞았는지 평가를 합니다.
    만약, 잘 맞지 않았다면 이에 대한 개선방안을 제안합니다.
    또한, 레포트에 주식시장 거래시간 전 포트폴리오와 주식시장 거래시간 마감 후 변동된 포트폴리오를 기재합니다.

    --트레이더 레포트--
    {t_5_trader_report}

    
    --애널리스트 레포트--
    {t_1_analyst_report}


    --주식시장 거래시간 전 포트폴리오 레포트--
    {t_1_pf_manager_report}
    

    보고서를 Markdown 형식으로 작성하세요.
    보고서는 반드시 주어진 정보에 대한 분석이 필요합니다.
    """

    response = to_GPT(system_prompt, prompt)
    portfolio_report = response["choices"][0]["message"]["content"]
    print("\nGenerated Portfolio Report:", portfolio_report)

    to_DB('t_5', f"{today}_t_5_portfolio_report", f"{base_quarter}_{base_year}", str(portfolio_report))

    return portfolio_report

def t_5_main(today, base_year, base_quarter):
    gen_trader(today, base_year, base_quarter)
    gen_portfolio(today, base_year, base_quarter)