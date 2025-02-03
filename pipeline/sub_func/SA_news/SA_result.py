from transformers import BertTokenizer, BertForSequenceClassification
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd
import os

# 모델과 토크나이저 로드
tokenizer = BertTokenizer.from_pretrained("snunlp/KR-FinBert-SC", local_files_only=False, use_safetensors=False)
model = BertForSequenceClassification.from_pretrained("snunlp/KR-FinBert-SC", local_files_only=False, use_safetensors=False)
labels = ["negative", "neutral", "positive"]

def get_SA_result(target_text):
    SA_result_dict = {}

    # 입력 텍스트 토크나이즈 (max_length 설정)
    inputs = tokenizer(target_text, return_tensors="pt", truncation=True, padding=True, max_length=512)

    # 모델로 예측
    with torch.no_grad():
        outputs = model(**inputs)

    # 출력 값 확인 (로짓)
    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=-1)

    # 클래스 레이블
    predicted_label = labels[predicted_class.item()]
    SA_result_dict['label'] = predicted_label

    # 예측 확률 출력
    probabilities = torch.softmax(logits, dim=-1)
    predicted_probability = probabilities[0][predicted_class].item()
    SA_result_dict['prob'] = predicted_probability

    return SA_result_dict