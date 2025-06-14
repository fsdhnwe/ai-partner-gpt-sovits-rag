"""
LLM 鏈處理
負責問答生成和回覆鏈的建立
"""
from typing import Iterator, Optional
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import BaseRetriever
from langchain.prompts import ChatPromptTemplate

from config import LLMConfig, CharacterConfig

def format_docs(docs):
    """將檢索到的文件格式化為字串"""
    return "\n\n".join(doc.page_content for doc in docs)

class LLMChain:
    """LLM 問答鏈"""
    
    def __init__(self, retriever: BaseRetriever):
        self.retriever = retriever
        self.llm = self._setup_llm()
        self.prompt = self._setup_prompt()
        self.rag_chain = self._build_rag_chain()
    
    def _setup_llm(self):
        """設置 LLM 模型"""
        if LLMConfig.ACTIVE_LLM == "groq":
            print("使用 Groq 模型")
            return ChatOpenAI(
                model=LLMConfig.GROQ_MODEL,
                openai_api_base=LLMConfig.GROQ_BASE_URL,
                openai_api_key=LLMConfig.GROQ_API_KEY
            )
        elif LLMConfig.ACTIVE_LLM == "ollama":
            print("使用 Ollama 模型")
            return ChatOllama(
                model=LLMConfig.OLLAMA_MODEL,
                base_url=LLMConfig.OLLAMA_BASE_URL
            )
        else:
            raise ValueError(f"不支援的 LLM 類型: {LLMConfig.ACTIVE_LLM}")
    
    def _setup_prompt(self):
        """設置 Prompt 模板"""
        try:
            # 從 hub 載入預設的 RAG prompt
            prompt = hub.pull("rlm/rag-prompt").partial(
                system_message=CharacterConfig.SYSTEM_MESSAGE
            )
            return prompt
        except Exception as e:
            print(f"無法從 hub 載入 prompt，使用預設模板: {e}")
            # 備用的 prompt 模板
            return ChatPromptTemplate.from_messages([
                ("system", CharacterConfig.SYSTEM_MESSAGE),
                ("human", """基於以下上下文回答問題：

上下文：
{context}

問題：{question}

回答：""")
            ])
    
    def _build_rag_chain(self):
        """建立 RAG 鏈"""
        return (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def ask(self, question: str) -> str:
        """
        同步問答
        
        Args:
            question: 問題文本
            
        Returns:
            str: 完整回答
        """
        try:
            response = self.rag_chain.invoke(question)
            return response
        except Exception as e:
            return f"發生錯誤: {e}"
    
    def ask_stream(self, question: str) -> Iterator[str]:
        """
        串流問答
        
        Args:
            question: 問題文本
            
        Yields:
            str: 回答片段
        """
        try:
            for chunk in self.rag_chain.stream(question):
                yield chunk
        except Exception as e:
            yield f"發生錯誤: {e}"
    
    def ask_with_context_display(self, question: str) -> tuple[str, list]:
        """
        問答並返回使用的上下文
        
        Args:
            question: 問題文本
            
        Returns:
            tuple: (回答, 檢索到的文檔列表)
        """
        try:
            # 先獲取檢索到的文檔
            retrieved_docs = self.retriever.invoke(question)
            
            # 生成回答
            response = self.rag_chain.invoke(question)
            
            return response, retrieved_docs
        except Exception as e:
            return f"發生錯誤: {e}", []

class WednesdayChat:
    """Wednesday Addams 聊天助手（支持 TTS）"""
    
    def __init__(self, llm_chain: LLMChain, enable_tts: bool = True):
        self.llm_chain = llm_chain
        self.enable_tts = enable_tts
        
        # 初始化 TTS（如果啟用）
        if self.enable_tts:
            try:
                from tts.gpt_sovits_tts import GPTSoVITSTTS
                self.tts = GPTSoVITSTTS()
                print("✅ TTS 功能已啟用")
            except Exception as e:
                print(f"⚠️  TTS 初始化失敗，僅使用文本模式: {e}")
                self.tts = None
                self.enable_tts = False
        else:
            self.tts = None
    
    def chat(self, user_input: str, with_audio: bool = None) -> tuple[str, Optional[str]]:
        """
        與 Wednesday 聊天
        
        Args:
            user_input: 用戶輸入
            with_audio: 是否生成音頻（None 則使用初始化設定）
            
        Returns:
            tuple: (文本回覆, 音頻檔案路徑或None)
        """
        # 構建完整的問題
        full_question = (
            "請以 Wednesday Addams 的口吻，用第一人稱直接和我說話且使用繁體中文，"
            f"回答我下面的問題：{user_input}"
        )
        
        # 獲取文本回覆
        text_response = self.llm_chain.ask(full_question)
        
        # 生成音頻（如果需要）
        audio_path = None
        if (with_audio is True) or (with_audio is None and self.enable_tts and self.tts):
            try:
                print("🔊 正在生成語音...")
                audio_path = self.tts.synthesize_from_response(text_response)
                if audio_path:
                    print(f"✅ 語音生成完成: {audio_path}")
                else:
                    print("⚠️  語音生成失敗")
            except Exception as e:
                print(f"❌ 語音生成錯誤: {e}")
        
        return text_response, audio_path
    
    def chat_stream(self, user_input: str) -> Iterator[str]:
        """
        與 Wednesday 串流聊天（僅文本）
        
        Args:
            user_input: 用戶輸入
            
        Yields:
            str: Wednesday 回覆的片段
        """
        # 構建完整的問題
        full_question = (
            "請以 Wednesday Addams 的口吻，用第一人稱直接和我說話且使用繁體中文，"
            f"回答我下面的問題：{user_input}"
        )
        
        for chunk in self.llm_chain.ask_stream(full_question):
            yield chunk
    
    def chat_stream_with_tts(self, user_input: str) -> tuple[Iterator[str], str]:
        """
        串流聊天並在結束後生成音頻
        
        Args:
            user_input: 用戶輸入
            
        Returns:
            tuple: (文本串流迭代器, 最終完整回覆)
        """
        # 收集完整回覆
        full_response = ""
        
        def response_generator():
            nonlocal full_response
            for chunk in self.chat_stream(user_input):
                full_response += chunk
                yield chunk
        
        # 返回生成器和計劃在後續執行的 TTS
        return response_generator(), full_response
    
    def generate_audio_for_text(self, text: str) -> Optional[str]:
        """
        為指定文本生成音頻
        
        Args:
            text: 要轉換的文本
            
        Returns:
            str: 音頻檔案路徑或None
        """
        if not self.tts:
            print("❌ TTS 未啟用")
            return None
        
        try:
            return self.tts.synthesize_from_response(text)
        except Exception as e:
            print(f"❌ 音頻生成失敗: {e}")
            return None
    
    def play_audio(self, audio_path: str):
        """
        播放音頻檔案
        
        Args:
            audio_path: 音頻檔案路徑
        """
        if self.tts:
            self.tts.play_audio(audio_path)
        else:
            print("❌ TTS 未啟用，無法播放音頻")
    
    def toggle_tts(self, enabled: bool):
        """
        切換 TTS 功能
        
        Args:
            enabled: 是否啟用 TTS
        """
        if enabled and not self.tts:
            try:
                from tts.gpt_sovits_tts import GPTSoVITSTTS
                self.tts = GPTSoVITSTTS()
                self.enable_tts = True
                print("✅ TTS 功能已啟用")
            except Exception as e:
                print(f"❌ TTS 啟用失敗: {e}")
        elif not enabled:
            self.enable_tts = False
            print("⚠️  TTS 功能已停用")

if __name__ == "__main__":
    # 測試 LLM 鏈
    from rag.loader import DocumentLoader
    from rag.retriever import VectorRetriever
    
    # 載入文檔並建立檢索器
    loader = DocumentLoader()
    documents = loader.load_and_split()
    
    if documents:
        retriever_instance = VectorRetriever()
        retriever = retriever_instance.get_retriever(documents)
        
        # 建立 LLM 鏈
        llm_chain = LLMChain(retriever)
        
        # 建立 Wednesday 聊天助手
        wednesday = WednesdayChat(llm_chain)
        
        # 測試聊天
        test_question = "你最喜歡什麼顏色？"
        print(f"問題: {test_question}")
        print("Wednesday 的回答:")
        
        # 串流回答
        for chunk in wednesday.chat_stream(test_question):
            print(chunk, end="", flush=True)
        print()
    else:
        print("沒有找到文檔，請確保 scripts 資料夾中有 PDF 檔案")
