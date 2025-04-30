import requests
import time

def safe_api_get(url, min_delay=1, **kwargs):
    """
    包裝 requests.get，加上自動 retry / sleep 控制，避免 Steam API 被封鎖。
    min_delay: 每次請求之間固定延遲秒數（不論成功或失敗）
    """
    max_retries = 3
    backoff_time = 30  # 秒數，遇到 429 時等待時間

    for attempt in range(max_retries):
        try:
            response = requests.get(url, **kwargs)
            if response.status_code == 429:
                print(f"⚠️ [safe_api_get] 429 Too Many Requests - retrying in {backoff_time} sec...")
                time.sleep(backoff_time)
                continue
            time.sleep(min_delay)
            return response
        except Exception as e:
            print(f"⚠️ [safe_api_get] Exception on attempt {attempt+1}: {e}")
            time.sleep(10)
    return None
