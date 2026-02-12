# -*- coding: utf-8 -*-
"""
节假日检查模块
"""

import json
from datetime import datetime
from config import HOLIDAYS_PATH
import os


def load_holidays():
    """加载节假日数据"""
    try:
        with open(HOLIDAYS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def is_holiday(date=None):
    """
    检查指定日期是否为节假日

    参数:
        date: datetime对象或日期字符串(YYYY-MM-DD)，默认为今天

    返回:
        bool: 是否为节假日
    """
    if date is None:
        date = datetime.now()

    # 统一转换为日期字符串
    if isinstance(date, datetime):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = str(date)

    year = date_str[:4]
    holidays_data = load_holidays()

    # 获取当年的节假日和调休工作日
    year_data = holidays_data.get(year, {})
    holidays = year_data.get("holidays", [])
    workdays = year_data.get("workdays", [])

    # 如果是调休工作日，返回False（不是节假日）
    if date_str in workdays:
        return False

    # 如果是节假日，返回True
    if date_str in holidays:
        return True

    # 检查是否为周末（周六=5, 周日=6）
    weekday = datetime.strptime(date_str, "%Y-%m-%d").weekday()
    if weekday >= 5:  # 周六或周日
        # 检查是否为调休工作日
        if date_str not in workdays:
            return True

    return False


def get_holiday_name(date=None):
    """获取节假日名称（简化版）"""
    if date is None:
        date = datetime.now()

    if isinstance(date, datetime):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = str(date)

    # 常见节假日名称映射
    holiday_names = {
        "01-01": "元旦",
        "除夕": "春节",
        "春节": "春节",
        "清明节": "清明节",
        "劳动节": "劳动节",
        "端午节": "端午节",
        "中秋节": "中秋节",
        "国庆节": "国庆节",
    }

    # 这里简化处理，实际可以根据具体日期返回名称
    if is_holiday(date):
        month_day = date_str[5:]
        if month_day == "01-01":
            return "元旦"
        elif date_str[5:7] in ["01", "02"] and "春节" in date_str:
            return "春节"
        return "节假日"

    return None


def should_send_reminder(date=None):
    """
    检查是否应该发送提醒

    参数:
        date: 指定日期，默认为今天

    返回:
        bool: 是否应该发送提醒
    """
    return not is_holiday(date)
