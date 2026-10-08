import requests

class Notifier:
    def __init__(self, token: str = ""):
        # 如果需要微信通知，可在 http://www.pushplus.plus 获取 token，不填则仅控制台打印
        self.token = token
        self.api_url = "https://www.pushplus.plus/send"

    def send(self, title: str, content: str):
        print(f"[{title}] {content}")
        if not self.token:
            return

        payload = {
            "token": self.token,
            "title": title,
            "content": content,
            "template": "html"
        }
        try:
            requests.post(self.api_url, json=payload, timeout=5)
        except Exception as e:
            print(f"推送通知发送失败: {e}")