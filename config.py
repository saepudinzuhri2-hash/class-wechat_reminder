# -*- coding: utf-8 -*-
"""
配置文件
"""

import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库路径
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

# 节假日文件路径
HOLIDAYS_PATH = os.path.join(BASE_DIR, "holidays.json")

# Flask配置
SECRET_KEY = "schedule-reminder-secret-key-2024"
DEBUG = True

# 服务器配置
HOST = "0.0.0.0"
PORT = 5000

# 提醒时间配置（分钟）
REMINDER_TIMES = [15, 5]  # 提前15分钟和5分钟提醒

# PushPlus配置
PUSHPLUS_API = "http://www.pushplus.plus/send"

# 日志配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
