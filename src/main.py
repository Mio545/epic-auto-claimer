import sys
from src.claimer import EpicClaimer
from src.notifier import Notifier

def main():
    # 配置你的通知 Token（可选）
    notifier = Notifier(token="")

    # 本地测试时保持 headless=False，方便排查定位问题；
    # 稳定后可改为 True 静默运行
    claimer = EpicClaimer(notifier=notifier, headless=False)

    print("开始执行 Epic 免费游戏自动领取任务...")
    claimer.run()
    print("任务执行结束。")

if __name__ == "__main__":
    main()