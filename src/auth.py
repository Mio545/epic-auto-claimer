import os
from playwright.sync_api import sync_playwright

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "epic_state.json")

def generate_login_state():
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)

    with sync_playwright() as p:
        # 打开带界面的浏览器供手动交互
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context()
        page = context.new_page()

        # 强行抹除自动化 WebDriver 标记，伪装成普通人类浏览器
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

        print("正在打开 Epic 商店登录页...")
        page.goto("https://www.epicgames.com/id/login", timeout=90000, wait_until="domcontentloaded")

        print(">>> 请在弹出的浏览器中手动完成登录（包括账号、密码及 2FA 验证）<<<")
        input("完成登录并进入商店首页后，请回到终端按下 [Enter] 键继续...")

        # 导出登录凭证
        context.storage_state(path=STATE_PATH)
        print(f"登录凭证已安全保存至: {STATE_PATH}")
        browser.close()

if __name__ == "__main__":
    generate_login_state()