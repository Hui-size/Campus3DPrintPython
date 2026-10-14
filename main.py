"""VS Code 终端运行：python main.py"""

import argparse
from pathlib import Path

from input_utils import evaluate, parse_values, explain
from modules.orders import Service
from modules.pricing import money

ROOT = Path(__file__).resolve().parent


def interactive() -> None:
    service = Service()
    prompts = {
        "1": "输入 长 宽 高（各 1~200 mm，例如 200 100 100）：",
        "2": "输入 重量(g) 时长(min) 材料(0=PLA/1=PETG) 加急(0/1)\n例如：100 120 1 1",
        "3": "输入 提前天数(0~7) 时长(1~600) 剩余时间(0~600) 维护(0/1)\n例如：3 120 120 0",
        "4": "输入 长 宽 高 重量 时长 材料 加急 提前天数\n例如：100 100 100 100 120 0 0 0",
        "6": "输入 提前天数(0~7) 维护状态(0/1)，例如：1 1",
    }
    while True:
        print("\n校园 3D 打印服务系统（Python）")
        print("1 尺寸检查  2 费用计算  3 预约条件检查")
        print("4 提交完整订单  5 查看订单及容量  6 设置维护状态")
        print("7 运行全部测试  0 退出")
        try:
            choice = input("请选择功能编号：").strip()
            if choice == "0":
                print("程序已退出。")
                return
            if choice == "5":
                print(f"订单数：{len(service.orders)}")
                for order in service.orders:
                    print(f"订单 {order.id} / 提前 {order.day} 天 / {order.grams} g / "
                          f"{order.minutes} 分钟 / {money(order.cents)} 元")
                print("各日剩余容量：" + "，".join(f"{d}天:{service.remaining(d)}分钟" for d in range(8)))
                continue
            if choice == "7":
                from test_runner import run_all
                code = run_all()
                print("全部测试通过。" if code == 0 else "测试未通过，请查看 results 目录。")
                continue
            if choice not in prompts:
                print("无效菜单项，请输入 0~7 中的一个功能编号。")
                continue
            print(prompts[choice])
            args = input("参数（空格分隔）：").split()
            if choice in ("1", "2", "3"):
                result = evaluate({"1": "size", "2": "quote", "3": "booking"}[choice], args)
            else:
                try:
                    values = parse_values(args, 8 if choice == "4" else 2)
                    result = service.submit(*values) if choice == "4" else service.set_maintenance(*values)
                except ValueError as error:
                    result = str(error)
            print("结果：" + result)
            print("说明：" + explain(result))
        except (EOFError, KeyboardInterrupt):
            print("\n程序已退出。")
            return


def main() -> int:
    parser = argparse.ArgumentParser(description="校园 3D 打印服务系统")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--test", action="store_true", help="执行全部自动测试")
    group.add_argument("--integration", action="store_true", help="执行 15 项连续订单流程检查")
    group.add_argument("--eval", nargs="+", metavar="参数", help="直接检查，例如 --eval size 200 100 100")
    args = parser.parse_args()
    if args.test or args.integration:
        from test_runner import run_all, run_integration
        return run_integration(ROOT / "results") if args.integration else run_all()
    if args.eval:
        result = evaluate(args.eval[0], args.eval[1:])
        print("结果：" + result)
        print("说明：" + explain(result))
        return 0
    interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
