# -*- coding: utf-8 -*-
"""
工具模块初始化
"""

from utils.database import init_database
from utils.scheduler import init_scheduler, shutdown_scheduler

__all__ = ["init_database", "init_scheduler", "shutdown_scheduler"]
