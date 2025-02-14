import os
# import pandas as pd
import sqlite3
import json
import numpy as np
import faiss
import torch
from pathlib import Path
from tqdm import tqdm
import logging
from typing import List, Tuple, Dict, Any
import gc
from contextlib import contextmanager
from transformers import AutoTokenizer, AutoModel
import pdfplumber

os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# @contextmanager
# def get_db_connection(db_file):
#     conn = sqlite3.connect(db_file)
#     try:
#         yield conn
#     finally:
#         conn.close()

class DocumentProcessor:
    def __init__(self, db_file="csv_text_cache.db", faiss_index_file="faiss_crawling.bin", batch_size=1000):
        """초기화 및 모델 로드"""
        self.db_file = db_file
        self.faiss_index_file = faiss_index_file
        self.batch_size = batch_size
        self.faiss_index = None
        
        # BERT 모델 초기화 시 메모리 설정
        torch.backends.cudnn.benchmark = False  # 메모리 사용량 최적화
        
        # 모델 로드
        self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.model = AutoModel.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        
        if torch.cuda.is_available() and not sys.platform.startswith('darwin'):
            self.model = self.model.cuda()
        else:
            self.model = self.model.cpu()
            # CPU 모드에서 메모리 최적화
            torch.set_num_threads(4)  # CPU 스레드 수 제한
        
        self.model.eval()
        
        # self._initialize_db()

    # def _initialize_db(self):
    #     """SQLite 데이터베이스 및 테이블 초기화"""
    #     with get_db_connection(self.db_file) as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("""
    #         CREATE TABLE IF NOT EXISTS csv_data (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             text TEXT,
    #             file_name TEXT
    #         )
    #         """)
    #         conn.commit()
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        logger.info("start")
        # 더 작은 배치 크기로 나누어 처리
        batch_size = 16  # 배치 크기를 64에서 16으로 줄임
        embeddings_list = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            inputs = self.tokenizer(
                batch_texts, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512, 
                padding=True
            )
            logger.info(f"Processing batch {i//batch_size + 1}")
            
            # CPU 사용 시 메모리 최적화
            if not torch.cuda.is_available() or sys.platform.startswith('darwin'):
                inputs = {k: v.cpu() for k, v in inputs.items()}
                # 메모리 사용량 로깅
                logger.info(f"Current memory usage: {torch.cuda.memory_allocated() if torch.cuda.is_available() else 'CPU mode'}")
                
                with torch.no_grad():
                    try:
                        outputs = self.model(**inputs)
                        batch_embeddings = outputs.last_hidden_state.mean(dim=1)
                        # 즉시 numpy로 변환하여 메모리 해제
                        batch_embeddings = batch_embeddings.cpu().numpy().astype(np.float32)
                        embeddings_list.append(batch_embeddings)
                    except RuntimeError as e:
                        logger.error(f"Error processing batch: {e}")
                        # 메모리 해제
                        del inputs
                        torch.cuda.empty_cache() if torch.cuda.is_available() else gc.collect()
                        continue
                
                # 메모리 정리
                del inputs
                torch.cuda.empty_cache() if torch.cuda.is_available() else gc.collect()
        
        # 모든 배치의 임베딩을 합침
        final_embeddings = np.vstack(embeddings_list)
        return np.ascontiguousarray(final_embeddings)


    def process_embeddings_in_batches(self, texts: List[str], embedding_file: str) -> np.ndarray:
        """기존 방식: 배치 단위로 임베딩을 처리하여 npy 파일로 저장 (참고용)"""
        if os.path.exists(embedding_file):
            logger.info(f"Loading existing embeddings from {embedding_file}")
            return np.load(embedding_file)

        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        embeddings_list = []

        for i in tqdm(range(0, len(texts), self.batch_size), total=total_batches):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self.get_embeddings(batch_texts)
            embeddings_list.append(batch_embeddings)
            
            if i % (self.batch_size * 10) == 0:
                gc.collect()

        final_embeddings = np.vstack(embeddings_list)
        np.save(embedding_file, final_embeddings)
        
        del embeddings_list
        gc.collect()
        
        return final_embeddings

    def extract_text_from_pdfs(self, pdf_root: str) -> Dict[str, List[Dict[str, Any]]]:
        pdf_data = {}  # 초기화
        pdf_root_path = Path(pdf_root)
        
        logger.info(f"PDF root path: {pdf_root_path}")
        
        if not pdf_root_path.exists():
            logger.warning(f"PDF root directory not found: {pdf_root}")
            return pdf_data  # 빈 딕셔너리 반환

        for company_folder in tqdm(list(pdf_root_path.iterdir()), desc="Processing companies"):
            if not company_folder.is_dir():
                continue

            company_code = company_folder.name
            pdf_data[company_code] = []
            
            pdf_files = list(company_folder.rglob("*.pdf")) + list(company_folder.rglob("*.PDF"))
            
            for pdf_file in pdf_files:
                try:
                    text = self._extract_pdf_text(pdf_file)
                    if text:
                        pdf_data[company_code].append({
                            "file": str(pdf_file),
                            "text": text
                        })
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_file}: {str(e)}")

        return pdf_data  # 반드시 pdf_data 반환

    def _extract_pdf_text(self, pdf_file: Path) -> str:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_file}: {e}")
            return ""  # 빈 문자열 반환

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """텍스트를 청크로 분할"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_length += len(word) + 1
            if current_length > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    # def process_csv_files(self, csv_folders: List[str]) -> Tuple[List[str], List[str]]:
    #     """CSV 파일 처리 및 데이터 저장"""
    #     if self._check_existing_data():
    #         logger.info("Loading cached CSV data from SQLite...")
    #         return self._load_csv_from_sqlite()

    #     logger.info("Processing CSV files from scratch...")
    #     csv_texts = []
    #     csv_file_names = []

    #     for folder in csv_folders:
    #         folder_path = Path(folder)
    #         if not folder_path.exists():
    #             logger.warning(f"Folder not found: {folder}")
    #             continue

    #         for file_path in tqdm(folder_path.rglob("*.csv"), desc=f"Processing {folder}"):
    #             try:
    #                 for chunk in pd.read_csv(file_path, encoding="utf-8", chunksize=1000):
    #                     text_data = chunk.select_dtypes(include=["object"]).astype(str)
    #                     for row in text_data.itertuples(index=False, name=None):
    #                         text = " ".join(str(x) for x in row if pd.notna(x))
    #                         csv_texts.append(text)
    #                         csv_file_names.append(str(file_path))

    #                         if len(csv_texts) >= self.batch_size:
    #                             self._save_to_db(csv_texts, csv_file_names)
    #                             csv_texts, csv_file_names = [], []
    #                             gc.collect()
    #             except Exception as e:
    #                 logger.error(f"Error processing {file_path}: {str(e)}")

    #     if csv_texts:
    #         self._save_to_db(csv_texts, csv_file_names)

    #     return self._load_csv_from_sqlite()

    # def _check_existing_data(self) -> bool:
    #     """SQLite DB에 데이터가 있는지 확인"""
    #     with get_db_connection(self.db_file) as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT COUNT(*) FROM csv_data")
    #         count = cursor.fetchone()[0]
    #     return count > 0

    # def _save_to_db(self, texts: List[str], file_names: List[str]):
    #     """데이터를 SQLite DB에 저장"""
    #     with get_db_connection(self.db_file) as conn:
    #         cursor = conn.cursor()
    #         cursor.executemany(
    #             "INSERT INTO csv_data (text, file_name) VALUES (?, ?)", 
    #             zip(texts, file_names)
    #         )
    #         conn.commit()

    # def _load_csv_from_sqlite(self) -> Tuple[List[str], List[str]]:
    #     """SQLite에서 저장된 CSV 데이터를 불러오기"""
    #     with get_db_connection(self.db_file) as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT text, file_name FROM csv_data")
    #         rows = cursor.fetchall()
        
    #     if not rows:
    #         return [], []
        
    #     csv_texts, csv_file_names = zip(*rows)
    #     return list(csv_texts), list(csv_file_names)

    def create_faiss_index_incrementally(self, pdf_chunks: List[str]) -> faiss.Index:
        """PDF 청크들의 임베딩을 계산하여 FAISS 인덱스 생성"""
        total_texts = len(pdf_chunks)
        logger.info(f"Total PDF chunks to index: {total_texts}")
        
        index = None
        total_batches = (total_texts + self.batch_size - 1) // self.batch_size

        for i in tqdm(range(0, total_texts, self.batch_size), total=total_batches, desc="Indexing batches"):
            batch_texts = pdf_chunks[i:i + self.batch_size]
            logger.info("임베딩 시작")
            batch_embeddings = self.get_embeddings(batch_texts)
            logger.info(f"Batch {i//self.batch_size+1}/{total_batches}: shape {batch_embeddings.shape}, dtype {batch_embeddings.dtype}")
            if index is None:
                embedding_dim = batch_embeddings.shape[1]
                index = faiss.IndexFlatL2(embedding_dim)
            index.add(batch_embeddings)
            logger.info(f"Indexed batch {i // self.batch_size + 1}/{total_batches}")
            gc.collect()

        
        if self.faiss_index_file:
            faiss.write_index(index, self.faiss_index_file)
            logger.info("FAISS index saved successfully")
        return index

    def load_faiss_index(self):
        """FAISS 인덱스 로드"""
        if os.path.exists(self.faiss_index_file):
            logger.info("Loading FAISS index from file...")
            self.faiss_index = faiss.read_index(self.faiss_index_file)
        else:
            logger.warning("No FAISS index found. Run create_faiss_index_incrementally() first.")

def main():
    # 설정
    pdf_root = "/Users/gamjawon/finTF/store_data/raw/crawling/IR_pdf_raw"
    # csv_root_folders = [
    #     "/Users/gamjawon/finTF/store_data/raw/crawling/corp_rel_news",
    #     "/Users/gamjawon/finTF/store_data/raw/crawling/general_news",
    #     "/Users/gamjawon/finTF/store_data/raw/FRED",
    #     "/Users/gamjawon/finTF/store_data/raw/market_data",
    #     "/Users/gamjawon/finTF/store_data/raw/opendart"
    # ]
    
    # 프로세서 초기화
    processor = DocumentProcessor(batch_size=64)
    
    # PDF 처리
    logger.info("Starting PDF processing...")
    pdf_text_data = processor.extract_text_from_pdfs(pdf_root)
    logger.info(f"Completed PDF extraction: {len(pdf_text_data)} companies processed")
    
    # # CSV 처리
    # logger.info("Starting CSV processing...")
    # csv_texts, csv_file_names = processor.process_csv_files(csv_root_folders)
    # logger.info(f"Completed CSV processing: {len(csv_texts)} entries extracted")
    
    # PDF 청크 생성
    pdf_chunks = []
    pdf_file_names = []
    logger.info("Processing PDF chunks...")
    for company_code, docs in pdf_text_data.items():
        for doc in docs:
            chunks = processor.chunk_text(doc["text"])
            pdf_chunks.extend(chunks)
            pdf_file_names.extend([doc["file"]] * len(chunks))
    logger.info(f"Created {len(pdf_chunks)} PDF chunks")
    
    # 디버깅: pdf_chunks의 내용을 일부 출력 (예: 처음 20개)
    logger.info("디버깅: PDF 청크 내용 미리보기")
    for idx, chunk in enumerate(pdf_chunks[:20]):  # 처음 20개의 청크만 확인
        # 청크가 비어있다면 그 사실도 로깅
        if not chunk.strip():
            logger.info(f"Chunk {idx}: [EMPTY]")
        else:
            preview = chunk[:200].replace("\n", " ")
            logger.info(f"Chunk {idx}: 길이={len(chunk)}; 미리보기='{preview}'")
    
    index_path = "faiss_crawling.bin"  # 필요하다면 절대 경로 사용

    if not os.path.exists(index_path) or os.path.getsize(index_path) < 100:
        print("Index file does not exist or is too small. Recreating the index...")
        index = processor.create_faiss_index_incrementally(pdf_chunks)
    else:
        index = faiss.read_index(index_path)
        if index is None:
            raise ValueError("Failed to load FAISS index from file. The file might be corrupted.")
        print("Total vectors in the index:", index.ntotal)
    
    # 메모리 정리
    # del csv_texts
    del pdf_chunks
    gc.collect()

    logger.info("Processing completed successfully")

if __name__ == "__main__":
    main()
