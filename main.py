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
from tts.gpt_sovits_tts import GPTSoVITSTTS

class WednesdayRAGSystem:
    """Wednesday RAG 系統主類"""
    
    _instance = None  # 單例模式實例
    
    def __new__(cls):
        if cls._instance is None:
            print("🏗️ 創建新的 Wednesday RAG 系統實例...")
            cls._instance = super(WednesdayRAGSystem, cls).__new__(cls)
            # 在这里初始化基本属性
            cls._instance.loader = None
            cls._instance.retriever_instance = None
            cls._instance.llm_chain = None
            cls._instance.wednesday = None
            cls._instance.tts = None
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化方法不做任何事情，因为我们已经在 __new__ 中初始化了所有属性
        这样可以避免多次初始化的问题
        """
        pass
    
    def initialize(self, force_rebuild: bool = False):
        """
        初始化系統
        
        Args:
            force_rebuild: 是否強制重建向量資料庫
        """
        print("🖤 初始化 Wednesday RAG 系統...")
        
        # 如果已經初始化過，且不需要強制重建，則直接返回
        if self._initialized and not force_rebuild:
            print("✅ 系統已初始化")
            return
            
        # 1. 檢查向量檢索器是否已存在
        if self.retriever_instance is None or force_rebuild:
            print("🔍 初始化向量檢索器...")
            self.retriever_instance = VectorRetriever()
            
            # 2. 檢查是否需要載入或建立向量資料庫
            if os.path.exists(RAGConfig.VECTOR_DB_PERSIST_DIR) and not force_rebuild:
                print("💾 載入現有的向量資料庫...")
                retriever = self.retriever_instance.get_retriever()
            else:
                print("🔨 建立新的向量資料庫...")
                if not self.loader:
                    print("📚 初始化文檔載入器...")
                    self.loader = DocumentLoader()
                documents = self.loader.load_and_split()
                if not documents:
                    raise ValueError("無法載入文檔，請檢查 scripts 資料夾是否包含 PDF 檔案")
                retriever = self.retriever_instance.get_retriever(documents)
        else:
            retriever = self.retriever_instance.get_retriever()
        
        # 3. 初始化 LLM 鏈
        if self.llm_chain is None:
            print("🤖 初始化 LLM 鏈...")
            self.llm_chain = LLMChain(retriever)
        
        # 4. 初始化 Wednesday 聊天助手
        if self.wednesday is None:
            print("🕸️ 初始化 Wednesday 聊天助手...")
            self.wednesday = WednesdayChat(self.llm_chain)
        
        # 5. 初始化 TTS 系統
        if self.tts is None:
            print("🎙️ 初始化 TTS 系統...")
            self.tts = GPTSoVITSTTS()
        
        self._initialized = True
        print("✅ 系統初始化完成！")
    
    def chat(self, user_input: str, use_tts: bool = True) -> str:
        """
        與 Wednesday 聊天 (同步)
        
        Args:
            user_input: 用戶輸入
            use_tts: 是否使用語音合成
            
        Returns:
            str: Wednesday 的完整回覆
        """
        if not self._initialized:
            self.initialize()
        
        response = self.wednesday.chat(user_input)
        
        # 如果啟用 TTS，合成語音
        if use_tts and self.tts:
            try:
                audio_path = self.tts.synthesize(response)
                if audio_path:
                    print(f"🎙️ 已生成語音: {audio_path}")
                    self.tts.play_audio(audio_path)
            except Exception as e:
                print(f"❌ TTS 合成失敗: {e}")
        
        return response
    
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
        
        full_response = ""
        for chunk in self.wednesday.chat_stream(user_input):
            full_response += chunk
            yield chunk
        
        # 串流完成後，合成語音
        if self.tts:
            try:
                audio_path = self.tts.synthesize(full_response)
                if audio_path:
                    print(f"🎙️ 已生成語音: {audio_path}")
                    self.tts.play_audio(audio_path)
            except Exception as e:
                print(f"❌ TTS 合成失敗: {e}")

    def console_chat(self):
        """控制台聊天介面"""
        if not self._initialized:
            self.initialize()
        
        print("\n🦇 Wednesday 已準備就緒，開始聊天吧！")
        print("(輸入 'quit' 或 'exit' 結束對話)\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ['quit', 'exit']:
                    print("\n👋 Wednesday: 再會了...")
                    break
                if not user_input:
                    continue
                
                print("\nWednesday:", end=" ", flush=True)
                for chunk in self.chat(user_input):
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
    if len(sys.argv) > 1 and sys.argv[1] == "--rebuild":
        system.initialize(force_rebuild=True)
    else:
        system.initialize()
    
    system.console_chat()

if __name__ == "__main__":
    main()
