import re
from konlpy.tag import Okt

def preprocess_text(text):

    text = re.sub(r'[^\w\s]', '', text)  # 특수문자 제거
    okt = Okt()
    nouns = okt.nouns(text)  # 명사 추출
    return ' '.join(nouns)

def embed_text_bert(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)

# 각 키워드별 상위 10개 종목 추출 함수
def get_top_n_stocks_by_keyword(topic_matrix, n=10):
    import pandas as pd

    # topic_matrix를 DataFrame으로 변환
    df = pd.DataFrame.from_dict(topic_matrix, orient='index')

    # 결과를 저장할 딕셔너리
    top_n_by_keyword = {}

    # 각 키워드별로 상위 n개 종목 추출
    for keyword in df.columns:
        top_n_by_keyword[keyword] = (
            df[keyword]
            .sort_values(ascending=False)  # 점수를 기준으로 내림차순 정렬
            .head(n)  # 상위 n개 선택
            .to_dict()  # 딕셔너리 형태로 변환
        )

    return top_n_by_keyword
