import os
from playwright.sync_api import sync_playwright
from src.notifier import Notifier

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "epic_state.json")

class EpicClaimer:
    def __init__(self, notifier: Notifier, headless: bool = False):
        self.notifier = notifier
        self.headless = headless

    def run(self):
        if not os.path.exists(STATE_PATH):
            raise FileNotFoundError("未找到登录凭证，请先运行 src/auth.py 进行登录！")

        with sync_playwright() as p:
            # 调用真实浏览器并抹除机器人特征
            browser = p.chromium.launch(
                headless=self.headless,
                channel="msedge",
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(storage_state=STATE_PATH)
            page = context.new_page()

            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)

            try:
                print("正在访问 Epic 免费游戏专区...")
                page.goto("https://store.epicgames.com/zh-CN/free-games", timeout=60000)

                # 【严格锁定】最高等25秒，只认限免独有的蓝色标签文案
                try:
                    page.locator("a:has-text('现在免费'), a:has-text('免费现在可用')").first.wait_for(state="visible", timeout=25000)
                except:
                    print("等待限免游戏列表超时。")

                # 只匹配真实限免卡片，彻底删掉宽泛的“免费”备用匹配
                game_cards = page.locator("a:has-text('现在免费')").all()
                if not game_cards:
                    game_cards = page.locator("a:has-text('免费现在可用')").all()

                print(f"找到可能可领取的项目数量: {len(game_cards)}")

                target_urls = []
                for card in game_cards:
                    href = card.get_attribute("href")
                    if href and href.startswith("/"):
                        target_urls.append("https://store.epicgames.com" + href)
                target_urls = list(set(target_urls))

                for url in target_urls:
                    self._claim_single_game(page, url)

            except Exception as e:
                self.notifier.send("Epic 领取异常", f"执行遇到错误: {str(e)}")
            finally:
                browser.close()

    def _claim_single_game(self, page, game_url: str):
        print(f"正在处理游戏: {game_url}")
        page.goto(game_url, timeout=60000)

        # 【升级2：智能等待游戏页按钮】最高等25秒，等待获取、库中、或继续按钮出现
        try:
            valid_buttons = page.locator("button[data-testid='purchase-cta-button'], button:has-text('获取'), button:has-text('已在库中'), button:has-text('已拥有'), button:has-text('继续')")
            valid_buttons.first.wait_for(state="visible", timeout=25000)
        except Exception:
            print("页面加载超时，未找到有效按钮（可能盾仍未解开）。")
            return

        if page.locator("button:has-text('已在库中')").is_visible() or page.locator("button:has-text('已拥有')").is_visible():
            print("该游戏已在库中，跳过。")
            return

        # 处理18+年龄限制
        continue_btn = page.locator("button:has-text('继续')")
        if continue_btn.is_visible():
            continue_btn.click()
            try:
                page.locator("button[data-testid='purchase-cta-button'], button:has-text('获取')").first.wait_for(state="visible", timeout=10000)
            except:
                pass

        get_btn = page.locator("button[data-testid='purchase-cta-button']").first
        if not get_btn.is_visible():
            get_btn = page.locator("button:has-text('获取')").first

        if not get_btn.is_visible():
            print("未找到获取按钮，可能当前并非免费，或页面结构已变。")
            return

        get_btn.click()
        print("已点击获取按钮，等待订单结算页面...")

        try:
            iframe_element = page.wait_for_selector("iframe[src*='purchase']", timeout=20000)
            order_frame = iframe_element.content_frame()
            place_order_btn = order_frame.wait_for_selector("button:has-text('下订单')", timeout=20000)

            if page.locator("iframe[src*='arkose']").is_visible() or page.locator("iframe[src*='hcaptcha']").is_visible():
                self.notifier.send("Epic 需要人机验证", "脚本遇到了人机验证码，请在 3 分钟内手动完成！")
                print(">>> 检测到人机验证，脚本暂停等待 180 秒，请在浏览器中手动验证 <<<")
                page.wait_for_timeout(180000)

            place_order_btn.click()
            print("已点击下订单！等待结算完成确认...")
            page.wait_for_timeout(8000)
            self.notifier.send("Epic 游戏领取成功", f"成功领取游戏: {game_url}")
        except Exception as e:
            print(f"结算环节出现异常: {e}")