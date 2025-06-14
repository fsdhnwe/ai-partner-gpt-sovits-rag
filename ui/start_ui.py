"""
Wednesday AI Partner 啟動腳本
一鍵啟動整個系統
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """檢查必要依賴"""
    print("🔍 檢查系統依賴...")
    
    required_packages = [
        'flask', 'flask-cors', 'requests', 'langchain', 
        'chromadb', 'sentence-transformers', 'soundfile'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依賴包: {', '.join(missing_packages)}")
        print("請執行以下命令安裝:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 依賴檢查完成")
    return True

def check_models():
    """檢查模型檔案"""
    print("🔍 檢查模型檔案...")
    
    # 檢查 GPT-SoVITS 模型目錄
    gpt_sovits_dir = Path("GPT-SoVITS-0601-cu124")
    if not gpt_sovits_dir.exists():
        print(f"⚠️ GPT-SoVITS 目錄不存在: {gpt_sovits_dir}")
        return False
    
    # 檢查必要檔案
    required_files = [
        "GPT-SoVITS-0601-cu124/custom_refs/base-audio.wav",
        "scripts"  # 文檔資料夾
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️ 缺少以下檔案/資料夾: {', '.join(missing_files)}")
        print("請確保所有必要檔案都已準備好")
        return False
    
    print("✅ 模型檔案檢查完成")
    return True

def start_api_server():
    """啟動 API 服務"""
    print("🚀 啟動 API 服務...")
    
    api_script = Path("ui/fast_api_server.py")
    if not api_script.exists():
        print(f"❌ API 服務腳本不存在: {api_script}")
        return None
    
    try:
        # 設置環境變數以確保正確的編碼
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 使用正確的編碼啟動 API 服務器
        process = subprocess.Popen(
            [sys.executable, str(api_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',  # 指定編碼
            text=True,  # 使用文本模式
            env=env,  # 使用修改過的環境變數
            creationflags=subprocess.CREATE_NO_WINDOW  # Windows下隱藏命令窗口
        )
        
        # 等待服務器啟動
        time.sleep(3)
        
        # 檢查進程狀態
        if process.poll() is None:
            # 非阻塞方式檢查錯誤輸出
            stderr_data = process.stderr.readline()
            if stderr_data:
                print(f"⚠️ API 服務啟動時有警告:")
                print(stderr_data.strip())
            print("✅ API 服務已啟動")
            return process
        else:
            # 如果進程已結束，獲取輸出
            stdout, stderr = process.communicate()
            print(f"❌ API 服務啟動失敗:")
            if stdout:
                print(f"輸出: {stdout.strip()}")
            if stderr:
                print(f"錯誤: {stderr.strip()}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 啟動 API 服務時發生錯誤: {error_msg}")
        
        # 如果是 Windows 錯誤，提供更多信息
        if hasattr(e, 'winerror'):
            print(f"Windows錯誤代碼: {e.winerror}")
        
        # 如果是編碼錯誤，提供解決建議
        if isinstance(e, UnicodeDecodeError):
            print("\n🔧 解決建議:")
            print("1. 確認所有Python檔案以UTF-8編碼保存")
            print("2. 設置PYTHONIOENCODING環境變數:")
            print("   Windows PowerShell: $env:PYTHONIOENCODING='utf-8'")
            print("   Windows CMD: set PYTHONIOENCODING=utf-8")
        
        return None

def open_web_interface():
    """開啟網頁介面"""
    print("🌐 開啟網頁介面...")
    
    ui_file = Path("ui/index.html")
    if not ui_file.exists():
        print(f"❌ 網頁介面檔案不存在: {ui_file}")
        return False
    
    try:
        # 使用絕對路徑開啟網頁
        file_url = f"file://{ui_file.resolve()}"
        webbrowser.open(file_url)
        print(f"✅ 已開啟網頁介面: {file_url}")
        return True
        
    except Exception as e:
        print(f"❌ 開啟網頁介面失敗: {e}")
        return False

def main():
    """主函數"""
    print("🕷️ Wednesday AI Partner 啟動程式")
    print("=" * 50)
    
    # 檢查依賴
    if not check_dependencies():
        print("\n❌ 依賴檢查失敗，請先安裝必要套件")
        return
    
    # 檢查模型
    if not check_models():
        print("\n⚠️ 模型檢查未完全通過，系統可能無法正常運作")
        response = input("是否繼續啟動？(y/N): ")
        if response.lower() != 'y':
            return
    
    # 啟動 API 服務
    api_process = start_api_server()
    if not api_process:
        print("\n❌ API 服務啟動失敗")
        return
    
    # 等待 API 服務完全啟動
    print("⏳ 等待 API 服務完全啟動...")
    time.sleep(5)
    
    # 開啟網頁介面
    if open_web_interface():
        print("\n🎉 系統啟動成功！")
        print("📋 使用說明:")
        print("   - 網頁介面已自動開啟")
        print("   - API 服務運行在 http://localhost:11434")
        print("   - 按 Ctrl+C 停止服務")
        print("\n🖤 Wednesday 已準備好為你服務...")
        
        try:
            # 保持 API 服務運行
            api_process.wait()
        except KeyboardInterrupt:
            print("\n👋 正在關閉服務...")
            api_process.terminate()
            api_process.wait()
            print("✅ 服務已關閉")
    else:
        print("\n❌ 網頁介面開啟失敗")
        api_process.terminate()

if __name__ == "__main__":
    main()
