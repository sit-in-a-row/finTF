import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import json
import logging

#to_GPT 함수 임포트
import sys
sys.path.append('.')
from pipeline.sub_func.to_gpt import to_GPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, model_name="jhgan/ko-sroberta-multitask", 
             index_path="/Users/gamjawon/finTF/faiss_crawling.bin", 
             doc_store_path="/Users/gamjawon/finTF/doc_store.json"):
        print("초기화 시작")
        self.device = torch.device("cpu")
        
        print("토크나이저 로딩")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        print("모델 로딩")
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to("cpu")
        self.model.eval()
        
        print("FAISS 인덱스 로딩")
        try:
            self.index = faiss.read_index(index_path)
            print(f"FAISS 인덱스 크기: {self.index.ntotal}")
        except Exception as e:
            print(f"FAISS 로딩 오류: {e}")
            raise
        
        print("문서 저장소 로딩")
        with open(doc_store_path, "r", encoding="utf-8") as f:
            self.doc_store = json.load(f)
        
        self.system_prompt = "You are a helpful Stock Market Analyst"

    @torch.no_grad()
    def get_embedding(self, text: str) -> np.ndarray:
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :].numpy()
            return embeddings
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            raise

    def search_documents(self, query: str, top_k: int = 5):
        print("임베딩 시작")
        query_embedding = self.get_embedding(query)
        
        print("FAISS 검색 시작")
        try:
            distances, indices = self.index.search(query_embedding, top_k)
            print(f"검색된 인덱스: {indices}")
        except Exception as e:
            print(f"FAISS 검색 오류: {e}")
            return []
        
        retrieved_docs = []
        for idx in indices[0]:
            if idx < len(self.doc_store):
                retrieved_docs.append(self.doc_store[idx])
        
        return retrieved_docs

    def generate_answer(self, query: str):
        """RAG 기반 응답 생성"""
        retrieved_docs = self.search_documents(query, top_k=5)
        
        if not retrieved_docs:
            return "관련 문서를 찾을 수 없습니다."
        
        context = "\n".join(retrieved_docs)
        
        # LLM에 전달할 프롬프트 생성
        prompt = f"질문: {query}\n\n참고 자료:\n{context}\n\n답변:"
        
        # to_GPT 함수를 이용하여 OpenAI API 호출
        response_dict = to_GPT(self.system_prompt, prompt)
        
        # OpenAI API의 응답 형식에 따라 답변 텍스트 추출
        # 예시: Chat API의 경우 response_dict['choices'][0]['message']['content'] 형태일 수 있음
        answer = response_dict.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not answer:
            answer = "응답 생성에 실패했습니다."
            
        return answer

def main():
    rag = RAGSystem()
    
    while True:
        query = input("\n질문을 입력하세요 (종료하려면 'exit' 입력): ")
        if query.lower() == "exit":
            break
        
        answer = rag.generate_answer(query)
        print(f"\nAI 응답: {answer}")

if __name__ == "__main__":
    main()
