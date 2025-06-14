"""
文本處理工具模組
"""
import re

def process_llm_response(response: str) -> str:
    """
    處理 LLM 的回應，移除 deepseek 模型的思考過程標籤
    
    Args:
        response: LLM 的原始回應
        
    Returns:
        str: 處理後的回應，移除了 think 標籤
    """
    # 如果回應包含 <think> 標籤，只保留對話內容
    think_match = re.search(r'<think>.*?</think>(.*)', response, re.DOTALL)
    if think_match:
        return think_match.group(1).strip()
    return response
