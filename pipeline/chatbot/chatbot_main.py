import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel, pipeline
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, model_name="snunlp/KR-FinBert-SC", index_path="faiss_crawling.bin", doc_store_path="doc_store.json"):
        """RAG 시스템 초기화"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 임베딩 모델 로드
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        # FAISS 벡터 DB 로드
        self.index = faiss.read_index(index_path)
        
        # 문서 저장소 로드
        with open(doc_store_path, "r", encoding="utf-8") as f:
            self.doc_store = json.load(f)
        
        # LLM 초기화 (GPT-40 mini)
        self.llm = pipeline("text-generation", model="gpt-40-mini")

    @torch.no_grad()
    def get_embedding(self, text: str) -> np.ndarray:
        """입력된 텍스트의 임베딩 벡터 생성"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(self.device)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state[:, 0, :].cpu().numpy()

    def search_documents(self, query: str, top_k: int = 5):
        """사용자 질문과 가장 유사한 문서를 검색"""
        query_embedding = self.get_embedding(query)
        
        # FAISS에서 유사한 문서 검색
        distances, indices = self.index.search(query_embedding, top_k)
        
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
        
        # LLM에 질문 및 문맥 전달
        prompt = f"질문: {query}\n\n참고 자료:\n{context}\n\n답변:"
        response = self.llm(prompt, max_length=200)[0]["generated_text"]
        
        return response

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
