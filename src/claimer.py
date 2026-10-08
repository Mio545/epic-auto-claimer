import os
import time
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
            browser = p.chromium.launch(headless=self.headless)
            # 加载已有的凭证状态
            context = browser.new_context(storage_state=STATE_PATH)
            page = context.new_page()

            try:
                print("正在访问 Epic 免费游戏专区...")
                page.goto("https://store.epicgames.com/zh-CN/free-games", timeout=60000)
                page.wait_for_load_state("networkidle")

                # 定位本周免费游戏的卡片链接（通常带有“免费”字样，且不是预告）
                # 寻找标记为“免费现在可用”的区块
                game_cards = page.locator("a:has-text('免费现在可用')").all()
                if not game_cards:
                    # 备用选择器
                    game_cards = page.locator("a:has-text('免费')").all()

                print(f"找到可能可领取的项目数量: {len(game_cards)}")

                # 收集本周免费游戏链接
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
        page.wait_for_load_state("networkidle")

        # 检查是否已拥有
        if page.locator("button:has-text('已在库中')").is_visible() or page.locator("button:has-text('已拥有')").is_visible():
            print("该游戏已在库中，跳过。")
            return

        # 检查是否有年龄限制提示
        continue_btn = page.locator("button:has-text('继续')")
        if continue_btn.is_visible():
            continue_btn.click()
            page.wait_for_timeout(2000)

        # 点击主界面的“获取”按钮
        get_btn = page.locator("button:has-text('获取')").first
        if not get_btn.is_visible():
            print("未找到获取按钮，可能当前并非免费。")
            return

        get_btn.click()
        print("已点击获取按钮，等待订单结算页面...")

        # 等待结算 iframe 或购买弹窗
        # Epic 购买弹窗一般是一个嵌入的 web-purchase iframe
        try:
            iframe_element = page.wait_for_selector("iframe[src*='purchase']", timeout=15000)
            order_frame = iframe_element.content_frame()

            # 等待下订单按钮加载
            place_order_btn = order_frame.wait_for_selector("button:has-text('下订单')", timeout=15000)

            # 检测是否触发人机验证
            if page.locator("iframe[src*='arkose']").is_visible() or page.locator("iframe[src*='hcaptcha']").is_visible():
                self.notifier.send("Epic 需要人机验证", "脚本遇到了人机验证码，请在 3 分钟内手动完成！")
                print(">>> 检测到人机验证，脚本暂停等待 180 秒，请在浏览器中手动验证 <<<")
                page.wait_for_timeout(180000)

            place_order_btn.click()
            print("已点击下订单！等待结算完成确认...")

            # 等待完成提示或回到页面
            page.wait_for_timeout(8000)
            self.notifier.send("Epic 游戏领取成功", f"成功领取游戏: {game_url}")

        except Exception as e:
            print(f"结算环节出现异常: {e}")