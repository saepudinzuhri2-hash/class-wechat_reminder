# -*- coding: utf-8 -*-
"""
设置教学周脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import set_setting, get_setting


def main():
    if len(sys.argv) < 2:
        print("用法: python set_week.py <周次>")
        print("示例: python set_week.py 5   # 设置为第5周")
        print()
        print("当前设置:")
        current = get_setting("current_week", "未设置")
        total = get_setting("total_weeks", "20")
        print(f"  当前周: 第{current}周")
        print(f"  总周数: {total}周")
        return

    try:
        week = int(sys.argv[1])
        if week < 1 or week > 25:
            print("错误: 周次必须在1-25之间")
            return

        set_setting("current_week", str(week))
        print(f"✅ 已设置为第{week}周")

        # 显示当前所有设置
        print()
        print("当前设置:")
        print(f"  当前周: 第{get_setting('current_week', '1')}周")
        print(f"  总周数: {get_setting('total_weeks', '20')}周")
        print(f"  开学日期: {get_setting('semester_start', '未设置')}")

    except ValueError:
        print("错误: 请输入有效的数字")


if __name__ == "__main__":
    main()
