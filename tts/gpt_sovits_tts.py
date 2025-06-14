"""
最終版 GPT-SoVITS TTS 實現
支持原生 TTS 和 API 雙重模式
"""
import os
import sys
import time
import requests
import soundfile as sf
import importlib.util
import re
import subprocess
from typing import Optional
import nltk

# 添加專案根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TTSConfig

# 確保 nltk 資源已下載
nltk.download('averaged_perceptron_tagger_eng')

class GPTSoVITSTTS:
    """GPT-SoVITS TTS 語音合成器"""
    
    def __init__(self, output_dir=None):
        """初始化 TTS 系統"""
        # 設置路徑
        self.gpt_sovits_dir = TTSConfig.GPT_SOVITS_DIR
        self.sovits_dir = TTSConfig.SOVITS_DIR
        self.sovits_model = TTSConfig.SOVITS_MODEL_PATH
        self.gpt_model = TTSConfig.GPT_MODEL_PATH
        self.reference_audio = TTSConfig.REFERENCE_AUDIO_PATH
        self.output_dir = output_dir or TTSConfig.OUTPUT_DIR
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化狀態
        self.native_tts = None
        self.api_url = None
        
        # 優先嘗試初始化原生 TTS
        self._init_native_tts()
          # 只有在原生 TTS 初始化失敗時才嘗試 API
        if not self.native_tts:
            print("原生 TTS 初始化失敗，嘗試 API 模式...")
    
    def _init_native_tts(self):
        """初始化原生 TTS 引擎"""
        try:
            print("初始化原生 TTS 引擎...")
              # 檢查路徑是否存在
            paths = [self.gpt_sovits_dir, self.sovits_model, self.gpt_model, self.reference_audio]
            for path in paths:
                if not os.path.exists(path):
                    print(f"錯誤: 路徑不存在 - {path}")
                    return
                else:
                    print(f"路徑存在: {path}")
            
            # 添加路徑
            sys.path.insert(0, self.gpt_sovits_dir)
            sys.path.insert(0, os.path.join(self.gpt_sovits_dir, "GPT_SoVITS"))
            
            # 搜索 TTS.py 文件
            tts_py_path = None
            for root, dirs, files in os.walk(self.sovits_dir):
                if "TTS.py" in files and "TTS_infer_pack" in root:
                    tts_py_path = os.path.join(root, "TTS.py")
                    print(f"找到 TTS.py: {tts_py_path}")
                    tts_dir = os.path.dirname(tts_py_path)
                    sys.path.insert(0, os.path.dirname(tts_dir))
                    break
            
            if not tts_py_path:
                print("找不到 TTS.py 文件")
                return
            
            # 動態導入 TTS 模組
            spec = importlib.util.spec_from_file_location("TTS", tts_py_path)
            tts_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tts_module)
              # 獲取 TTS 和 TTS_Config 類
            TTS = tts_module.TTS
            TTS_Config = tts_module.TTS_Config
            
            # 預訓練模型目錄
            pretrained_dir = os.path.join(self.sovits_dir, "GPT_SoVITS" ,"pretrained_models")
            os.makedirs(pretrained_dir, exist_ok=True)
            
            bert_path = os.path.join(pretrained_dir, "chinese-roberta-wwm-ext-large")
            hubert_path = os.path.join(pretrained_dir, "chinese-hubert-base")
            
            # 設置設備
            device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
            
            # 建立 TTS 配置 - 強制使用絕對路徑防止 TTS 預設路徑
            tts_config = {
                "device": device,
                "is_half": False,
                "version": "v4",  # 確保使用正確的版本
                "t2s_weights_path": os.path.abspath(self.gpt_model),
                "vits_weights_path": os.path.abspath(self.sovits_model),
                "cnhuhubert_base_path": os.path.abspath(hubert_path),
                "bert_base_path": os.path.abspath(bert_path),
            }
            
            # 打印配置以便除錯
            print(f"TTS 配置:")
            for key, value in tts_config.items():
                print(f"  {key}: {value}")
              # 創建 TTS 實例
            try:
                print("正在創建 TTS 實例...")
                config_obj = TTS_Config(tts_config)
                # 確保 config_obj 中的路徑被正確設置
                print(f"檢查配置對象路徑:")
                print(f"  t2s_weights_path: {config_obj.t2s_weights_path}")
                print(f"  vits_weights_path: {config_obj.vits_weights_path}")
                
                self.native_tts = TTS(config_obj)
                print("原生 TTS 引擎初始化成功!")
            except Exception as e:
                print(f"創建 TTS 實例時發生錯誤: {e}")
                import traceback
                traceback.print_exc()
                self.native_tts = None
            
        except Exception as e:
            print(f"原生 TTS 初始化失敗: {e}")
            self.native_tts = None
    
    def synthesize(self, text, output_filename=None, output_path=None):
        """
        合成語音 (主入口)
        
        Args:
            text: 要合成的文本
            output_filename: 輸出文件名（可選）
            output_path: 完整的輸出路徑（可選，優先級高於 output_filename）
            
        Returns:
            str: 生成的音頻文件路徑
        """
        # 清理文本
        text = self._clean_text(text)
        
        # 確定輸出路徑
        if output_path:
            # 確保目錄存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            print(f"使用指定輸出路徑: {output_path}")
        else:
            # 生成輸出檔案名稱
            if not output_filename:
                timestamp = int(time.time())
                output_filename = f"wednesday_tts_{timestamp}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
        
        # 優先使用原生 TTS
        if self.native_tts:
            result = self._synthesize_native(text, output_path)
            if result:
                return result
        
        print("語音合成失敗，請確保 GPT-SoVITS 正在運行")
        return None
    
    def _synthesize_native(self, text: str, output_path: str) -> Optional[str]:
        """使用原生 TTS.py 進行合成"""
        try:
            import time, soundfile as sf

            print(f"🔊 使用原生 TTS 合成: {text[:30]}...")
            # 語言檢測
            lang = self._detect_language(text)
            print(f"🔤 檢測到語言: {lang}")

            # 構造 run() 參數字典，注意 key 要用 ref_wav_path
            inputs = {
                "text": text,
                "text_lang": lang,
                "ref_audio_path": self.reference_audio,       # ← 必須
                "aux_ref_audio_paths": [],
                "prompt_text": (
                    "…有那种东西才怪吧？！"
                    "我要是真跟机器头说上话了倒还好，"
                    "但现在的问题是…祂根本没有反应！"
                ),
                "prompt_lang": "zh",
                "top_k": 15,
                "top_p": 1.0,
                "temperature": 1.0,
                "text_split_method": "cut0",
                "batch_size": 1,
                "batch_threshold": 0.75,
                "split_bucket": True,
                "return_fragment": False,
                "speed_factor": 1.0,
                "fragment_interval": 0.3,
                "seed": -1,
                "parallel_infer": False,
                "repetition_penalty": 1.35,
                "sample_steps": 16,
                "super_sampling": False,
            }

            start = time.time()
            # 這裡是關鍵修改：使用 next() 從生成器獲取第一個結果
            for sample_rate, audio in self.native_tts.run(inputs):
                # 取第一個結果就退出循環
                break
            print(f"⏱️ 耗時: {time.time() - start:.2f}s")

            if audio is None:
                print("❌ 原生 TTS 返回空數據，請確認 reference_wav 路徑 & 參數正確")
                return None

            # 寫文件
            sf.write(output_path, audio, sample_rate)
            print(f"✅ 原生 TTS 合成成功: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 原生 TTS 合成失敗: {e}")
            return None
    
    
    def _detect_language(self, text):
        """自動檢測文本語言類型"""
        # 計算中文字符數量
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        # 計算英文字符數量
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # 總字符數（只計算中文和英文）
        total_chars = chinese_chars + english_chars
        
        if total_chars == 0:
            return "zh"  # 默認中文
        
        # 計算比例
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        # 判斷語言類型
        if chinese_ratio >= 0.7:
            return "all_zh"  # 主要是中文
        elif english_ratio >= 0.7:
            return "en"  # 主要是英文
        elif chinese_chars > 0 and english_chars > 0:
            return "zh"  # 中英混合
        else:
            return "all_zh"  # 默認中文
    
    def _clean_text(self, text):
        """清理文本"""
        # 移除過多的空白字符
        text = " ".join(text.split())
        
        # 移除特殊字符，保留中文、英文、基本標點
        text = re.sub(r'[^\w\s\u4e00-\u9fff。，！？；：「」『』（）、]', '', text)
        
        # 限制文本長度
        max_length = 200
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    def play_audio(self, audio_path):
        """播放音頻檔案"""
        if not os.path.exists(audio_path):
            print(f"錯誤: 音頻檔案不存在 - {audio_path}")
            return
        
        try:
            # Windows
            if os.name == 'nt':
                os.startfile(audio_path)
            # macOS
            elif os.name == 'posix' and os.uname().sysname == 'Darwin':
                subprocess.run(['open', audio_path])
            # Linux
            else:
                subprocess.run(['xdg-open', audio_path])
                
            print(f"正在播放: {audio_path}")
            
        except Exception as e:
            print(f"播放音頻時發生錯誤: {e}")


# 便利函數
def text_to_speech(text, output_dir=None):
    """將文本轉換為語音"""
    tts = GPTSoVITSTTS(output_dir=output_dir)
    return tts.synthesize(text)


def rag_to_speech(rag_response, output_dir=None):
    """將 RAG 回應轉換為語音"""
    tts = GPTSoVITSTTS(output_dir=output_dir)
    return tts.synthesize(rag_response)


# 測試函數
if __name__ == "__main__":
    print("=== GPT-SoVITS TTS 測試 ===")
    
    tts = GPTSoVITSTTS()
    
    test_text = "我是 Wednesday Addams，這個陰鬱的世界正合我意。"
    
    print(f"測試文本: {test_text}")
    
    # 合成語音
    audio_path = tts.synthesize(test_text)
    
    if audio_path:
        print(f"測試成功! 音頻檔案: {audio_path}")
        
        # 詢問是否播放
        try:
            play_choice = input("是否播放音頻？(y/n): ")
            if play_choice.lower() == 'y':
                tts.play_audio(audio_path)
        except:
            pass
    else:
        print("測試失敗")
