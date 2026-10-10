import json
import os

def convert_cookies():
    raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw_cookies.json")
    state_path = os.path.join(os.path.dirname(__file__), "..", "data", "epic_state.json")

    try:
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_cookies = json.load(f)

        # 清洗 sameSite 字段，适配 Playwright 的强类型要求
        for cookie in raw_cookies:
            if cookie.get("sameSite") is not None:
                val = str(cookie["sameSite"]).lower()
                if val in ["no_restriction", "none"]:
                    cookie["sameSite"] = "None"
                elif val == "lax":
                    cookie["sameSite"] = "Lax"
                elif val == "strict":
                    cookie["sameSite"] = "Strict"
                else:
                    del cookie["sameSite"]
            elif "sameSite" in cookie:
                # 如果值为 None，直接删除该字段让其使用默认值
                del cookie["sameSite"]

        playwright_state = {
            "cookies": raw_cookies,
            "origins": []
        }

        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(playwright_state, f, indent=4)

        print("✅ 成功将 Cookie 清洗并转换为 Playwright 格式！")

    except FileNotFoundError:
        print("❌ 找不到 raw_cookies.json 文件，请确认路径是否正确。")
    except json.JSONDecodeError:
        print("❌ JSON 格式错误。")

if __name__ == "__main__":
    convert_cookies()