"""
資料載入與文本分割處理
負責從各種格式載入文檔並進行分割
"""
import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config import RAGConfig

class DocumentLoader:
    """文檔載入器"""
    
    def __init__(self, scripts_dir: str = None):
        self.scripts_dir = scripts_dir or RAGConfig.SCRIPTS_DIR
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAGConfig.CHUNK_SIZE,
            chunk_overlap=RAGConfig.CHUNK_OVERLAP,
            add_start_index=True
        )
    
    def load_pdf_documents(self) -> List[Document]:
        """
        載入指定目錄下的所有 PDF 文件
        
        Returns:
            List[Document]: 載入的文檔列表
        """
        all_docs = []
        
        if not os.path.isdir(self.scripts_dir):
            print(f"找不到 {self.scripts_dir} 資料夾")
            return all_docs
        
        # 列出所有 PDF 檔案
        pdf_files = [f for f in os.listdir(self.scripts_dir) if f.endswith(".pdf")]
        print(f"找到 {len(pdf_files)} 個 PDF 檔案")
        
        # 載入每個 PDF 檔案
        for filename in pdf_files:
            print(f"載入檔案: {filename}")
            file_path = os.path.join(self.scripts_dir, filename)
            
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                all_docs.extend(docs)
                print(f"成功載入 {len(docs)} 頁")
            except Exception as e:
                print(f"載入 {filename} 時發生錯誤: {e}")
            
            print()
        
        print(f"總文件頁數: {len(all_docs)}")
        return all_docs
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        將文檔分割成較小的塊
        
        Args:
            documents: 原始文檔列表
            
        Returns:
            List[Document]: 分割後的文檔塊
        """
        if not documents:
            print("沒有文檔需要分割")
            return []
        
        all_splits = self.text_splitter.split_documents(documents)
        print(f"文件總共切成 {len(all_splits)} 等分")
        
        return all_splits
    
    def load_and_split(self) -> List[Document]:
        """
        載入並分割文檔的完整流程
        
        Returns:
            List[Document]: 分割後的文檔塊
        """
        # 載入文檔
        documents = self.load_pdf_documents()
        
        if not documents:
            return []
        
        # 分割文檔
        splits = self.split_documents(documents)
        
        # 顯示第一個文檔的部分內容作為示例
        if documents:
            print("第一頁內容前 100 字：", documents[0].page_content[:100])
        
        return splits

if __name__ == "__main__":
    # 測試載入器
    loader = DocumentLoader()
    splits = loader.load_and_split()
    
    # 顯示分割結果的 metadata
    if splits:
        print("\n分割後的文檔 metadata:")
        for i, split in enumerate(splits[:5]):  # 只顯示前5個
            print(f"分割 {i}: {split.metadata}")
