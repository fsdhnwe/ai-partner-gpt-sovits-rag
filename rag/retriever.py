"""
向量檢索器
負責文本嵌入、向量資料庫建立和相似性搜尋
"""
import os
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever

from config import RAGConfig

class VectorRetriever:
    """向量檢索器"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or RAGConfig.VECTOR_DB_PERSIST_DIR
        self.embeddings = HuggingFaceEmbeddings(
            model_name=RAGConfig.EMBEDDING_MODEL
        )
        self.vector_store: Optional[Chroma] = None
        self.retriever: Optional[BaseRetriever] = None
    
    def create_vector_store(self, documents: List[Document], force_recreate: bool = False) -> Chroma:
        """
        建立向量資料庫
        
        Args:
            documents: 文檔列表
            force_recreate: 是否強制重新建立
            
        Returns:
            Chroma: 向量資料庫實例
        """
        # 檢查是否已存在持久化的向量資料庫
        if os.path.exists(self.persist_directory) and not force_recreate:
            print(f"載入現有向量資料庫: {self.persist_directory}")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name=RAGConfig.COLLECTION_NAME
            )
        else:
            print("建立新的向量資料庫...")
            # 確保目錄存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 建立向量資料庫
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name=RAGConfig.COLLECTION_NAME
            )
            print(f"向量資料庫已保存至: {self.persist_directory}")
        
        return self.vector_store
    
    def get_retriever(self, documents: List[Document] = None) -> BaseRetriever:
        """
        取得檢索器
        
        Args:
            documents: 如果向量資料庫不存在，用這些文檔建立
            
        Returns:
            BaseRetriever: 檢索器實例
        """
        if self.vector_store is None:
            if documents:
                self.create_vector_store(documents)
            else:
                # 嘗試載入現有的向量資料庫
                if os.path.exists(self.persist_directory):
                    self.vector_store = Chroma(
                        persist_directory=self.persist_directory,
                        embedding_function=self.embeddings,
                        collection_name=RAGConfig.COLLECTION_NAME
                    )
                else:
                    raise ValueError("向量資料庫不存在，且未提供文檔來建立新的資料庫")
        
        self.retriever = self.vector_store.as_retriever(
            search_type=RAGConfig.SEARCH_TYPE,
            search_kwargs={"k": RAGConfig.SEARCH_K}
        )
        
        return self.retriever
    
    def test_retrieval(self, query: str, documents: List[Document] = None) -> List[Document]:
        """
        測試檢索功能
        
        Args:
            query: 查詢文本
            documents: 如果需要建立向量資料庫的文檔
            
        Returns:
            List[Document]: 檢索到的文檔
        """
        retriever = self.get_retriever(documents)
        retrieved_docs = retriever.invoke(query)
        
        print(f"檢索到的文件數量: {len(retrieved_docs)}")
        
        # 印出檢索文件的 metadata
        for i, doc in enumerate(retrieved_docs):
            print(f"檢索結果 {i}: {doc.metadata}")
            print(f"內容片段: {doc.page_content[:200]}...")
            print()
        
        return retrieved_docs

def format_docs(docs: List[Document]) -> str:
    """
    格式化檢索到的文檔內容
    
    Args:
        docs: 文檔列表
        
    Returns:
        str: 格式化後的文本
    """
    return "\n\n".join(doc.page_content for doc in docs)

if __name__ == "__main__":
    # 測試檢索器
    from rag.loader import DocumentLoader
    
    # 載入文檔
    loader = DocumentLoader()
    documents = loader.load_and_split()
    
    if documents:
        # 建立檢索器
        retriever = VectorRetriever()
        
        # 測試檢索
        test_query = "一年365天,你最喜歡哪一天?"
        retrieved_docs = retriever.test_retrieval(test_query, documents)
    else:
        print("沒有找到文檔，請確保 scripts 資料夾中有 PDF 檔案")
