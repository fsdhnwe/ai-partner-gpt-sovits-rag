"""
主控制器
整合 RAG、TTS、UI 功能的入口點
"""
import os
import sys
from typing import Optional

# 添加專案路徑到 Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.loader import DocumentLoader
from rag.retriever import VectorRetriever
from rag.llm_chain import LLMChain, WednesdayChat
from config import RAGConfig

class WednesdayRAGSystem:
    """Wednesday RAG 系統主類"""
    
    def __init__(self):
        self.loader: Optional[DocumentLoader] = None
        self.retriever_instance: Optional[VectorRetriever] = None
        self.llm_chain: Optional[LLMChain] = None
        self.wednesday: Optional[WednesdayChat] = None
        self._initialized = False
    
    def initialize(self, force_rebuild: bool = False):
        """
        初始化系統
        
        Args:
            force_rebuild: 是否強制重建向量資料庫
        """
        print("🖤 初始化 Wednesday RAG 系統...")
        
        # 1. 初始化文檔載入器
        print("📚 初始化文檔載入器...")
        self.loader = DocumentLoader()
        
        # 2. 初始化向量檢索器
        print("🔍 初始化向量檢索器...")
        self.retriever_instance = VectorRetriever()
        
        # 3. 檢查是否需要載入或建立向量資料庫
        if os.path.exists(RAGConfig.VECTOR_DB_PERSIST_DIR) and not force_rebuild:
            print("💾 載入現有的向量資料庫...")
            retriever = self.retriever_instance.get_retriever()
        else:
            print("🔨 建立新的向量資料庫...")
            documents = self.loader.load_and_split()
            if not documents:
                raise ValueError("無法載入文檔，請檢查 scripts 資料夾是否包含 PDF 檔案")
            retriever = self.retriever_instance.get_retriever(documents)
        
        # 4. 初始化 LLM 鏈
        print("🤖 初始化 LLM 鏈...")
        self.llm_chain = LLMChain(retriever)
        
        # 5. 初始化 Wednesday 聊天助手
        print("🕸️ 初始化 Wednesday 聊天助手...")
        self.wednesday = WednesdayChat(self.llm_chain)
        
        self._initialized = True
        print("✅ 系統初始化完成！")
    
    def chat(self, user_input: str) -> str:
        """
        與 Wednesday 聊天 (同步)
        
        Args:
            user_input: 用戶輸入
            
        Returns:
            str: Wednesday 的完整回覆
        """
        if not self._initialized:
            self.initialize()
        
        return self.wednesday.chat(user_input)
    
    def chat_stream(self, user_input: str):
        """
        與 Wednesday 聊天 (串流)
        
        Args:
            user_input: 用戶輸入
            
        Yields:
            str: Wednesday 回覆的片段
        """
        if not self._initialized:
            self.initialize()
        
        for chunk in self.wednesday.chat_stream(user_input):
            yield chunk
    
    def console_chat(self):
        """控制台聊天介面"""
        if not self._initialized:
            self.initialize()
        
        print("\n" + "="*50)
        print("🖤 Wednesday Addams RAG 聊天系統")
        print("輸入 'quit' 或 'exit' 離開")
        print("輸入 'rebuild' 重建向量資料庫")
        print("="*50 + "\n")
        
        while True:
            try:
                user_input = input("👤 你: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("🕷️ Wednesday: 再見了，無聊的人類。")
                    break
                
                if user_input.lower() == 'rebuild':
                    print("🔨 重建向量資料庫...")
                    self.initialize(force_rebuild=True)
                    continue
                
                if not user_input:
                    continue
                
                print("🕸️ Wednesday: ", end="", flush=True)
                
                # 串流輸出回答
                for chunk in self.chat_stream(user_input):
                    print(chunk, end="", flush=True)
                print("\n")
                
            except KeyboardInterrupt:
                print("\n🕷️ Wednesday: 被打斷了...再見。")
                break
            except Exception as e:
                print(f"\n❌ 發生錯誤: {e}")

def main():
    """主函數"""
    # 創建 Wednesday RAG 系統
    system = WednesdayRAGSystem()
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            # 只初始化系統
            system.initialize()
            
        elif command == "rebuild":
            # 重建向量資料庫
            system.initialize(force_rebuild=True)
            
        elif command == "chat":
            # 啟動控制台聊天
            system.console_chat()
            
        elif command == "test":
            # 測試系統
            system.initialize()
            test_question = "你最喜歡什麼季節？"
            print(f"測試問題: {test_question}")
            print("Wednesday 的回答:")
            for chunk in system.chat_stream(test_question):
                print(chunk, end="", flush=True)
            print()
            
        else:
            print(f"未知的命令: {command}")
            print("可用命令: init, rebuild, chat, test")
    else:
        # 預設啟動控制台聊天
        system.console_chat()

if __name__ == "__main__":
    main()
