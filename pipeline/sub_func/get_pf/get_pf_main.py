from ..get_info import reports_info

from .get_pf_utils import *
import os
from transformers import AutoModel, AutoTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch

model = AutoModel.from_pretrained("monologg/kobert")
tokenizer = AutoTokenizer.from_pretrained("monologg/kobert", trust_remote_code=True)

# 현재 파일의 디렉터리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
ticker_path = os.path.abspath(os.path.join(current_dir, "../../../store_data/raw/opendart/store_reports"))

def get_pf(target_year:str, target_quarter:str, target_sector:list):
    """
    target_year: 훑어볼 정보들의 연도
    target_quarter: 훑어볼 정보들의 분기
    target_sector: pf_selection_agent가 선택한 섹터들 (리스트 형식으로)
    """

    print('='*50)
    print("포트폴리오 구성 시작...")
    print('='*50)
    # 데이터 로드 및 분석 초기화
    tickers = [ticker for ticker in os.listdir(ticker_path) if ticker != '.DS_Store']
    topic_matrix = {}

    # 분석 실행
    for i, ticker in enumerate(tickers):
        
        print('-'*50)
        print(f"({i+1}/{len(tickers)})")
        try:
            analysis_result = {}

            temp_report = reports_info(ticker, target_year, target_quarter)['II. 사업의 내용.csv'][0]
            print(len(temp_report))
            
            processed_report = preprocess_text(temp_report)

            # TF-IDF 분석
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([processed_report] + target_sector)
            cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

            # KoBERT 분석
            report_vector = embed_text_bert(processed_report, tokenizer, model)
            keyword_vectors = {keyword: embed_text_bert(keyword, tokenizer, model) for keyword in target_sector}

            for sector, tfidf_score in zip(target_sector, cosine_similarities):
                bert_similarity = torch.nn.functional.cosine_similarity(report_vector, keyword_vectors[sector]).item()
                analysis_result[sector] = (tfidf_score + bert_similarity) / 2  # TF-IDF와 BERT 유사도의 평균

            topic_matrix[ticker] = analysis_result
        except Exception as e:
            print(f"{ticker}에 해당하는 정보가 없습니다. | {e}")


    # 함수 실행 및 결과
    result = get_top_n_stocks_by_keyword(topic_matrix, n=10)

    return result