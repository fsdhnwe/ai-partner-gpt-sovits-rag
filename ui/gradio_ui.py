"""
Gradio Web UI 介面
提供網頁聊天介面與 Wednesday Addams 互動
"""
import gradio as gr
import os
import sys
from typing import Iterator, Tuple

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import WednesdayRAGSystem
from tts.gpt_sovits_tts import GPTSoVITSTTS
from config import UIConfig

class WednesdayGradioUI:
    """Wednesday Gradio UI 類"""
    
    def __init__(self):
        self.rag_system = WednesdayRAGSystem()
        self.tts_system = GPTSoVITSTTS()
        self._system_initialized = False
    
    def initialize_system(self):
        """初始化 RAG 系統"""
        if not self._system_initialized:
            print("🖤 初始化 Wednesday RAG 系統...")
            self.rag_system.initialize()
            self._system_initialized = True
    
    def chat_with_wednesday(self, 
                           message: str, 
                           history: list,
                           enable_tts: bool = False) -> Tuple[str, list, str]:
        """
        與 Wednesday 聊天
        
        Args:
            message: 用戶消息
            history: 聊天歷史
            enable_tts: 是否啟用 TTS
            
        Returns:
            Tuple: (回覆, 更新的歷史, 音頻路徑)
        """
        if not message.strip():
            return "", history, None
        
        # 確保系統已初始化
        self.initialize_system()
        
        try:
            # 獲取 Wednesday 的回覆
            if enable_tts:
                # 使用支持 TTS 的方法
                response, audio_path = self.rag_system.wednesday.chat(message, with_audio=True)
            else:
                # 僅文本回覆
                response, audio_path = self.rag_system.wednesday.chat(message, with_audio=False)
            
            # 更新聊天歷史
            history.append([message, response])
            
            return "", history, audio_path
            
        except Exception as e:
            error_msg = f"抱歉，我遇到了一些技術問題：{str(e)}"
            history.append([message, error_msg])
            return "", history, None
        
        try:
            # 獲取 Wednesday 的回覆
            response = ""
            for chunk in self.rag_system.chat_stream(message):
                response += chunk
            
            # 更新聊天歷史
            history.append((message, response))
            
            # TTS 合成 (如果啟用)
            audio_path = None
            if enable_tts:
                audio_path = self.tts_system.synthesize_from_response(response)
            
            return "", history, audio_path
            
        except Exception as e:
            error_msg = f"發生錯誤: {str(e)}"
            history.append((message, error_msg))
            return "", history, None
    
    def clear_chat(self):
        """清除聊天記錄"""
        return [], ""
    
    def create_interface(self):
        """創建 Gradio 介面"""
        
        # 自定義 CSS 樣式
        css = """
        .wednesday-theme {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }
        .gradio-container {
            background-color: #0d1117 !important;
        }
        .chat-message {
            background-color: #21262d !important;
            border: 1px solid #30363d !important;
        }
        """
        
        with gr.Blocks(
            title="Wednesday Addams RAG Chat",
            theme=gr.themes.Dark(),
            css=css
        ) as interface:
            
            # 標題
            gr.Markdown(
                """
                # 🖤 Wednesday Addams RAG 聊天系統
                與 Netflix《Wednesday》影集的主角 Wednesday Addams 對話
                """
            )
            
            with gr.Row():
                with gr.Column(scale=4):
                    # 聊天介面
                    chatbot = gr.Chatbot(
                        height=500,
                        label="💬 與 Wednesday 聊天",
                        show_label=True,
                        container=True,
                        bubble_full_width=False
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="輸入你想問 Wednesday 的問題...",
                            label="訊息",
                            lines=2,
                            scale=4
                        )
                        send_btn = gr.Button("📤 發送", variant="primary", scale=1)
                    
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ 清除對話", variant="secondary")
                        tts_checkbox = gr.Checkbox(
                            label="🔊 啟用語音合成 (需要配置 SoVITS 模型)",
                            value=False
                        )
                
                with gr.Column(scale=1):
                    # 側邊欄
                    gr.Markdown("## 🕸️ 系統狀態")
                    
                    status_text = gr.Textbox(
                        value="等待初始化...",
                        label="狀態",
                        interactive=False
                    )
                    
                    init_btn = gr.Button("🔄 重新初始化系統", variant="secondary")
                    
                    gr.Markdown("## 🎵 語音輸出")
                    
                    audio_output = gr.Audio(
                        label="Wednesday 的語音回覆",
                        interactive=False,
                        visible=True
                    )
                    
                    gr.Markdown(
                        """
                        ## 📝 使用說明
                        1. 在訊息框中輸入問題
                        2. 點擊發送按鈕或按 Enter
                        3. Wednesday 會根據上傳的文檔回答
                        4. 啟用 TTS 可聽到語音回覆
                        
                        ## ⚙️ 注意事項
                        - 請確保 `scripts` 資料夾中有 PDF 檔案
                        - TTS 功能需要配置 SoVITS 模型
                        - 首次使用會自動建立向量資料庫
                        """
                    )
            
            # 事件處理
            def send_message(message, history, enable_tts):
                return self.chat_with_wednesday(message, history, enable_tts)
            
            def update_status():
                if self._system_initialized:
                    return "✅ 系統已就緒"
                else:
                    return "🔄 正在初始化..."
            
            def initialize_and_update_status():
                self.initialize_system()
                return "✅ 系統已就緒"
            
            # 綁定事件
            send_btn.click(
                send_message,
                inputs=[msg_input, chatbot, tts_checkbox],
                outputs=[msg_input, chatbot, audio_output]
            )
            
            msg_input.submit(
                send_message,
                inputs=[msg_input, chatbot, tts_checkbox],
                outputs=[msg_input, chatbot, audio_output]
            )
            
            clear_btn.click(
                self.clear_chat,
                outputs=[chatbot, msg_input]
            )
            
            init_btn.click(
                initialize_and_update_status,
                outputs=[status_text]
            )
            
            # 介面載入時更新狀態
            interface.load(
                update_status,
                outputs=[status_text]
            )
        
        return interface
    
    def launch(self, 
               share: bool = False, 
               port: int = None,
               debug: bool = False):
        """
        啟動 Gradio 介面
        
        Args:
            share: 是否創建公開連結
            port: 端口號
            debug: 是否開啟調試模式
        """
        port = port or UIConfig.GRADIO_PORT
        interface = self.create_interface()
        
        print(f"🚀 啟動 Wednesday Gradio UI on port {port}")
        interface.launch(
            share=share,
            server_port=port,
            debug=debug,
            server_name="0.0.0.0"
        )

def main():
    """主函數"""
    ui = WednesdayGradioUI()
    ui.launch(debug=True)

if __name__ == "__main__":
    main()
