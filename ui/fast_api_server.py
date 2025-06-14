"""
FastAPI 服務器
為 Vue.js 前端提供 RESTful API 接口
"""
import os
import sys
import json
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import requests
import logging
from pydantic import BaseModel

# 設置日誌
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加專案根目錄到 Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)  # 上一層目錄才是專案根目錄
sys.path.append(root_dir)

try:
    from main import WednesdayRAGSystem
    logger.info(f"✅ 成功導入所需模組，專案根目錄: {root_dir}")
except ImportError as e:
    logger.error(f"❌ 導入模組失敗: {e}")
    logger.error(f"Python 路徑: {sys.path}")
    raise

app = FastAPI(
    title="Wednesday AI Partner API",
    description="Wednesday AI Partner 的 FastAPI 服務器",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該指定確切的來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
OLLAMA_BASE_URL = 'http://localhost:11434'  # Ollama API 位址

# 全域變數
wednesday_system = None
current_model = "deepseek-r1:latest"
is_processing = False

def initialize_system():
    """初始化 Wednesday RAG 系統"""
    global wednesday_system
    if wednesday_system is None:
        try:
            logger.info("🖤 初始化 Wednesday RAG 系統...")
            wednesday_system = WednesdayRAGSystem()
            wednesday_system.initialize()
            logger.info("✅ 系統初始化完成！")
        except Exception as e:
            logger.error(f"❌ 系統初始化失敗: {e}")
            raise e
    return wednesday_system

# 請求/回應模型
class ChatRequest(BaseModel):
    message: str
    use_tts: bool = True
    model: Optional[str] = "deepseek-r1:latest"
    output_path: Optional[str] = "output"

class ChatResponse(BaseModel):
    message: str
    audio_path: Optional[str] = None
    response_time: float
    model: str
    timestamp: float
    tts_status: str = "ready"

@app.get("/")
async def root():
    """根路徑歡迎訊息"""
    return {
        "message": "Wednesday AI Partner API Service",
        "status": "running",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    global is_processing
    
    # 如果有其他操作正在處理中，返回簡略狀態
    if is_processing:
        return {
            "status": "busy",
            "message": "系統正在處理其他操作",
            "timestamp": time.time()
        }
    
    try:
        # 檢查 Ollama 服務
        try:
            ollama_response = requests.get(f'{OLLAMA_BASE_URL}/api/version')
            ollama_status = 'online' if ollama_response.ok else 'offline'
            ollama_version = ollama_response.json().get('version') if ollama_response.ok else None
        except requests.exceptions.RequestException as e:
            logger.warning(f"無法連接到 Ollama 服務: {e}")
            ollama_status = 'offline'
            ollama_version = None
        
        # 檢查我們的系統
        system = initialize_system()
        
        return {
            "status": "online",
            "ollama_status": ollama_status,
            "ollama_version": ollama_version,
            "model": current_model,
            "timestamp": time.time(),
            "tts_available": system.tts is not None,
            "rag_available": system.wednesday is not None
        }
        
    except Exception as e:
        error_msg = f"健康檢查錯誤: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天對話端點"""
    try:
        global current_model, is_processing
        
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="訊息不能為空")
        
        # 初始化系統
        system = initialize_system()
        
        logger.info(f"🔤 收到用戶訊息: {request.message[:50]}...")
        start_time = time.time()
        
        # 標記為正在處理
        is_processing = True
        try:
            # 先獲取文字回應，不等待TTS
            text_response, _ = system.wednesday.chat(request.message, with_audio=False)
            
            response_time = time.time() - start_time
            logger.info(f"⏱️ AI 文字回應時間: {response_time:.2f}s")
            
            # 如果啟用了 TTS，在後台生成音頻
            audio_path = None
            tts_status = "disabled"
            
            if request.use_tts and system.tts:
                try:
                    logger.info("🎙️ 開始後台語音合成...")
                    import threading                    # 使用相对路径，始终存储在 output 目录下
                    audio_filename = f"wednesday_tts_{int(time.time() * 1000)}.wav"
                    # 返回给前端的路径只要文件名
                    audio_path = audio_filename
                    # 实际存储路径
                    absolute_audio_path = os.path.join(root_dir, 'output', audio_filename)
                    tts_status = "generating"
                    
                    def generate_audio():
                        try:
                            # 確保輸出目錄存在
                            os.makedirs(os.path.dirname(absolute_audio_path), exist_ok=True)
                            # 合成音頻
                            system.tts.synthesize(text_response, output_path=absolute_audio_path)
                            logger.info(f"✅ 後台語音合成完成: {audio_filename}")
                        except Exception as e:
                            logger.error(f"❌ 後台TTS合成失敗: {e}")
                    
                    # 在後台執行音頻生成
                    audio_thread = threading.Thread(target=generate_audio)
                    audio_thread.daemon = True
                    audio_thread.start()
                    
                except Exception as e:
                    logger.error(f"❌ 無法啟動TTS後台處理: {e}")
                    tts_status = "error"
            
            return ChatResponse(
                message=text_response,
                audio_path=audio_path,
                response_time=response_time,
                model=request.model,
                timestamp=time.time(),
                tts_status=tts_status
            )
            
        finally:
            # 確保無論成功或失敗都重置處理標記
            is_processing = False
            
    except Exception as e:
        logger.error(f"❌ 聊天處理錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """獲取音頻文件"""
    try:
        # 統一使用 output 目錄，移除任何路徑分隔符
        clean_filename = os.path.basename(filename)
        audio_path = os.path.join(root_dir, 'output', clean_filename)
        
        logger.info(f"請求音頻文件: {audio_path}")
        logger.info(f"原始檔名: {filename}, 清理後: {clean_filename}")
        
        if not os.path.exists(audio_path):
            logger.error(f"❌ 音頻文件未找到: {clean_filename}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": "音頻文件未找到",
                    "filename": clean_filename,
                    "path": audio_path
                }
            )
            
        # 檢查檔案大小
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            logger.error(f"❌ 音頻文件為空: {clean_filename}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "音頻文件為空",
                    "filename": clean_filename,
                    "size": 0
                }
            )
            
        logger.info(f"✅ 提供音頻文件下載: {clean_filename} (大小: {file_size} bytes)")
        return FileResponse(
            path=audio_path,
            media_type="audio/wav",
            filename=clean_filename
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取音頻文件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio_status/{filename}")
async def check_audio_status(filename: str):
    """檢查音頻文件是否已生成完成"""
    try:
        # 統一使用 output 目錄，移除任何路徑分隔符
        clean_filename = os.path.basename(filename)
        audio_path = os.path.join(root_dir, 'output', clean_filename)
        
        logger.info(f"檢查音頻文件狀態: {audio_path}")
        logger.info(f"原始檔名: {filename}, 清理後: {clean_filename}")
        
        # 確保輸出目錄存在
        output_dir = os.path.dirname(audio_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"創建輸出目錄: {output_dir}")
        
        if os.path.exists(audio_path):
            if os.path.getsize(audio_path) > 0:
                logger.info(f"✅ 音頻文件已就緒: {clean_filename} (大小: {os.path.getsize(audio_path)} bytes)")
                return {
                    "status": "ready",
                    "message": "音頻文件已準備就緒",
                    "filename": clean_filename,
                    "timestamp": time.time()
                }
            else:
                logger.warning(f"⚠️ 發現空文件: {clean_filename}")
                return {
                    "status": "generating",
                    "message": "音頻文件正在生成中...",
                    "filename": clean_filename,
                    "timestamp": time.time()
                }
        else:
            logger.info(f"⏳ 音頻文件尚未生成: {clean_filename}")
            return {
                "status": "generating",
                "message": "音頻文件正在生成中...",
                "filename": clean_filename,
                "timestamp": time.time()
            }
            
    except Exception as e:
        logger.error(f"❌ 檢查音頻狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")
