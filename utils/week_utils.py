# -*- coding: utf-8 -*-
"""
周次解析工具模块
支持周次规则解析、课程有效性检查等功能
"""

import re
from typing import List, Union

# 配置常量
MAX_WEEKS = 25  # 最大支持25周
DEFAULT_TOTAL_WEEKS = 20  # 默认学期20周


def parse_week_pattern(pattern: str) -> List[int]:
    """
    解析周次规则字符串，返回有课的具体周次列表

    参数:
        pattern: 周次规则字符串
        - 'all' - 每周都有
        - 'odd' - 单周
        - 'even' - 双周
        - '1,3,5' - 特定周次
        - '1-8' - 周次范围
        - '1,3,5-10' - 混合格式

    返回:
        list: 有课的具体周次列表，如 [1, 3, 5, 6, 7, 8, 9, 10]
    """
    if not pattern or pattern == "all":
        return list(range(1, MAX_WEEKS + 1))

    pattern = str(pattern).strip().lower()

    if pattern == "odd" or pattern == "单周":
        return list(range(1, MAX_WEEKS + 1, 2))

    if pattern == "even" or pattern == "双周":
        return list(range(2, MAX_WEEKS + 1, 2))

    weeks = set()

    # 分割逗号分隔的部分
    parts = pattern.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 检查是否是范围格式 (如 "1-8")
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                # 限制在有效范围内
                start = max(1, start)
                end = min(MAX_WEEKS, end)
                weeks.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            # 单独的数字
            try:
                week = int(part)
                if 1 <= week <= MAX_WEEKS:
                    weeks.add(week)
            except ValueError:
                continue

    return sorted(list(weeks))


def is_course_active(week_pattern: str, current_week: int) -> bool:
    """
    检查课程在指定周次是否有课

    参数:
        week_pattern: 课程的周次规则
        current_week: 当前周次

    返回:
        bool: 如果当前周次有课则返回True
    """
    if current_week < 1 or current_week > MAX_WEEKS:
        return False

    active_weeks = parse_week_pattern(week_pattern)
    return current_week in active_weeks


def get_week_description(pattern: str) -> str:
    """
    获取周次规则的中文描述

    参数:
        pattern: 周次规则字符串

    返回:
        str: 中文描述
    """
    if not pattern or pattern == "all":
        return "每周"

    pattern = str(pattern).strip().lower()

    descriptions = {
        "all": "每周",
        "odd": "单周",
        "even": "双周",
        "单周": "单周",
        "双周": "双周",
    }

    if pattern in descriptions:
        return descriptions[pattern]

    # 解析并生成描述
    weeks = parse_week_pattern(pattern)

    if not weeks:
        return "无"

    if len(weeks) >= MAX_WEEKS - 2:
        return "每周"

    if len(weeks) <= 3:
        return f"第{','.join(map(str, weeks))}周"

    # 显示范围
    ranges = []
    start = weeks[0]
    end = weeks[0]

    for week in weeks[1:] + [None]:
        if week is None or week != end + 1:
            if start == end:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{end}")
            if week is not None:
                start = week
                end = week
        else:
            end = week

    return f"{','.join(ranges)}周"


def validate_week_pattern(pattern: str) -> tuple:
    """
    验证周次规则的合法性

    参数:
        pattern: 周次规则字符串

    返回:
        tuple: (is_valid, error_message)
    """
    if not pattern or pattern == "all":
        return True, ""

    valid_patterns = ["all", "odd", "even"]
    if pattern.lower() in valid_patterns:
        return True, ""

    # 检查自定义格式
    parts = pattern.split(",")

    for part in parts:
        part = part.strip()

        if not part:
            return False, f"无效的周次格式: '{part}'"

        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start < 1 or end > MAX_WEEKS:
                    return False, f"周次范围应在1-{MAX_WEEKS}之间"
                if start > end:
                    return False, f"起始周不能大于结束周"
            except ValueError:
                return False, f"无效的周次范围: '{part}'"
        else:
            try:
                week = int(part)
                if week < 1 or week > MAX_WEEKS:
                    return False, f"周次应在1-{MAX_WEEKS}之间"
            except ValueError:
                return False, f"无效的周次数字: '{part}'"

    return True, ""


def get_week_pattern_examples() -> dict:
    """
    获取周次规则的示例

    返回:
        dict: 示例字典
    """
    return {
        "all": {
            "example": "all",
            "description": "每周都有课",
            "weeks": list(range(1, 21)),
        },
        "odd": {
            "example": "odd",
            "description": "单周上课",
            "weeks": list(range(1, 21, 2)),
        },
        "even": {
            "example": "even",
            "description": "双周上课",
            "weeks": list(range(2, 21, 2)),
        },
        "custom_1": {
            "example": "1,3,5",
            "description": "第1、3、5周上课",
            "weeks": [1, 3, 5],
        },
        "custom_2": {
            "example": "1-8",
            "description": "第1-8周上课",
            "weeks": list(range(1, 9)),
        },
        "custom_3": {
            "example": "1,3,5-10,15",
            "description": "第1、3-10、15周上课",
            "weeks": [1, 3, 4, 5, 6, 7, 8, 9, 10, 15],
        },
    }


def generate_week_options(total_weeks: int = DEFAULT_TOTAL_WEEKS) -> List[dict]:
    """
    生成周次选择器的选项

    参数:
        total_weeks: 学期总周数

    返回:
        list: 周次选项列表
    """
    options = [{"value": "all", "label": "每周", "short": "全"}]

    for i in range(1, total_weeks + 1):
        if i % 2 == 1:  # 单周
            options.append({"value": "odd", "label": "单周 (1,3,5...)", "short": "单"})
            break

    for i in range(1, total_weeks + 1):
        if i % 2 == 0:  # 双周
            options.append({"value": "even", "label": "双周 (2,4,6...)", "short": "双"})
            break

    options.append({"value": "custom", "label": "自定义", "short": "自定义"})

    return options
