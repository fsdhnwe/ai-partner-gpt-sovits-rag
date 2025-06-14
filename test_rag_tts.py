"""
RAG + TTS 整合測試
測試 Wednesday Addams RAG 系統結合 GPT-SoVITS TTS 功能
"""
import os
import sys

# 添加專案根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.loader import DocumentLoader
from rag.retriever import VectorRetriever
from rag.llm_chain import LLMChain, WednesdayChat

def main():
    """主要測試函數"""
    print("=== Wednesday Addams RAG + TTS 系統 ===\n")
    
    # 1. 載入文檔
    print("📚 載入 Wednesday 相關文檔...")
    loader = DocumentLoader()
    documents = loader.load_and_split()
    
    if not documents:
        print("❌ 沒有找到文檔，請確保 scripts 資料夾中有 PDF 檔案")
        return
    
    print(f"✅ 已載入 {len(documents)} 個文檔片段")
    
    # 2. 建立檢索器
    print("\n🔍 建立向量檢索器...")
    retriever_instance = VectorRetriever()
    retriever = retriever_instance.get_retriever(documents)
    print("✅ 檢索器建立完成")
    
    # 3. 建立 LLM 鏈
    print("\n🧠 建立 LLM 鏈...")
    llm_chain = LLMChain(retriever)
    print("✅ LLM 鏈建立完成")
    
    # 4. 建立 Wednesday 聊天助手（啟用 TTS）
    print("\n🎭 初始化 Wednesday Addams 聊天助手...")
    wednesday = WednesdayChat(llm_chain, enable_tts=True)
    print("✅ Wednesday 聊天助手就緒")
    
    # 5. 互動式聊天
    print("\n" + "="*50)
    print("💬 開始與 Wednesday Addams 對話")
    print("輸入 'quit' 或 'exit' 結束對話")
    print("輸入 'tts on/off' 切換語音功能")
    print("="*50 + "\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\nWednesday: 再見了，平凡的人類。")
                break
            
            if user_input.lower() == 'tts on':
                wednesday.toggle_tts(True)
                continue
            
            if user_input.lower() == 'tts off':
                wednesday.toggle_tts(False)
                continue
            
            if not user_input:
                continue
            
            print("\nWednesday: ", end="", flush=True)
            
            # 獲取回覆和音頻
            text_response, audio_path = wednesday.chat(user_input)
            print(text_response)
            
            # 播放音頻（如果有生成）
            if audio_path:
                print(f"\n🔊 音頻已生成: {os.path.basename(audio_path)}")
                
                # 詢問是否播放
                try:
                    play_choice = input("是否播放音頻？(y/n，預設 y): ").strip().lower()
                    if play_choice in ['', 'y', 'yes']:
                        wednesday.play_audio(audio_path)
                except KeyboardInterrupt:
                    pass
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 對話已中斷")
            break
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")
            continue

def test_basic_functionality():
    """測試基本功能"""
    print("=== 基本功能測試 ===\n")
    
    try:
        # 測試 TTS
        from tts.gpt_sovits_tts import GPTSoVITSTTS
        print("📝 測試 TTS 功能...")
        
        tts = GPTSoVITSTTS()
        test_text = "我是 Wednesday Addams，黑暗是我的摯友。"
        
        audio_path = tts.synthesize(test_text)
        if audio_path:
            print(f"✅ TTS 測試成功: {audio_path}")
            return True
        else:
            print("❌ TTS 測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ TTS 測試失敗: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wednesday Addams RAG + TTS 系統")
    parser.add_argument("--test", action="store_true", help="僅執行基本功能測試")
    parser.add_argument("--no-tts", action="store_true", help="停用 TTS 功能")
    
    args = parser.parse_args()
    
    if args.test:
        test_basic_functionality()
    else:
        main()
