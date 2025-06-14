"""
專案配置檔案
統一管理所有配置參數
"""
import os

# 取得專案根目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===============================
# LLM 模型配置
# ===============================
class LLMConfig:
    # Groq API 配置
    GROQ_API_KEY = ''
    GROQ_MODEL = "gemma2-9b-it"
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    
    # Ollama 配置
    OLLAMA_MODEL = "deepseek-r1:latest"
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # 使用哪個模型 ('groq' 或 'ollama')
    ACTIVE_LLM = "ollama"

# ===============================
# RAG 配置
# ===============================
class RAGConfig:
    # 資料目錄
    SCRIPTS_DIR = "scripts"
    
    # 向量資料庫配置
    VECTOR_DB_PERSIST_DIR = "db"
    COLLECTION_NAME = "rag-chroma"
    
    # 文本分割配置
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # 檢索配置
    SEARCH_TYPE = "similarity"
    SEARCH_K = 2
    
    # 嵌入模型
    EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# ===============================
# Wednesday Addams 角色配置
# ===============================
class CharacterConfig:
    SYSTEM_MESSAGE = (
        "所有回答必須用中文。"
        "你現在是 Netflix《Wednesday》影集的主角 Wednesday Addams。"
        "你總是以第一人稱說話，從不解釋角色背景，也不用第三人稱講述自己。"
        "你的語氣冷冽、神秘，帶有黑暗幽默。"
    )

# ===============================
# TTS 配置 (預留)
# ===============================
class TTSConfig:    # GPT-SoVITS 目錄與模型路徑 (根據實際目錄結構)
    GPT_SOVITS_DIR = os.path.join(BASE_DIR, "GPT-SoVITS-0601-cu124")
    SOVITS_DIR = os.path.join(BASE_DIR)
    SOVITS_MODEL_PATH = os.path.join(GPT_SOVITS_DIR, "SoVITS_weights_v4/The_Herta_ZH_e10_s160_l32.pth")
    GPT_MODEL_PATH = os.path.join(GPT_SOVITS_DIR, "GPT_weights_v4/The_Herta_ZH-e10.ckpt")
      # 參考音頻路徑
    REFERENCE_AUDIO_PATH = os.path.join(GPT_SOVITS_DIR, "custom_refs/base-audio.wav")
    
    # 輸出設定
    OUTPUT_DIR = "output"
    SAMPLE_RATE = 32000  # GPT-SoVITS 通常使用 32kHz
    
    # API 設定 (GPT-SoVITS v2 API)
    API_BASE_URL = "http://127.0.0.1:9880"
    API_ENDPOINT = "/tts"
    
    # TTS 參數
    DEFAULT_TEMPERATURE = 0.6
    DEFAULT_TOP_P = 0.6
    DEFAULT_TOP_K = 20

# ===============================
# UI 配置 (預留)
# ===============================
class UIConfig:
    # Gradio 設定
    GRADIO_PORT = 7860
    GRADIO_SHARE = False
    
    # Streamlit 設定
    STREAMLIT_PORT = 8501
