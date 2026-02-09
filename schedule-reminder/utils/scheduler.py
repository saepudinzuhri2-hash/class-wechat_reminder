# -*- coding: utf-8 -*-
"""
定时任务调度模块
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

from utils.database import (
    get_courses_by_day,
    get_active_courses_by_day,
    add_reminder,
    get_pending_reminders,
    mark_reminder_sent,
    clear_old_reminders,
    get_setting,
)
from utils.wechat_push import send_course_reminder
from utils.holiday_checker import should_send_reminder
from utils.week_utils import is_course_active
from config import REMINDER_TIMES

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局调度器
scheduler = None


def init_scheduler():
    """初始化定时任务调度器"""
    global scheduler

    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.start()
        logger.info("定时任务调度器已启动")

        # 添加每日扫描任务
        scheduler.add_job(
            scan_daily_courses,
            trigger=CronTrigger(hour=0, minute=5),  # 每天00:05执行
            id="daily_scan",
            replace_existing=True,
        )

        # 添加提醒检查任务（每分钟检查一次）
        scheduler.add_job(
            check_and_send_reminders,
            trigger="interval",
            minutes=1,
            id="reminder_check",
            replace_existing=True,
        )

        # 添加清理旧数据任务（每周一凌晨执行）
        scheduler.add_job(
            cleanup_old_data,
            trigger=CronTrigger(day_of_week="mon", hour=2, minute=0),
            id="weekly_cleanup",
            replace_existing=True,
        )

        # 立即执行一次今日课程扫描
        scan_daily_courses()

    return scheduler


def scan_daily_courses():
    """
    扫描今日课程，创建提醒任务
    """
    now = datetime.now()
    logger.info(f"扫描今日课程: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查今天是否应该发送提醒
    if not should_send_reminder(now):
        logger.info("今天是节假日，跳过课程提醒")
        return

    # 获取今天星期几（1-7，周一为1）
    day_of_week = now.isoweekday()

    # 获取当前教学周
    current_week = int(get_setting("current_week", 1))
    logger.info(f"当前教学周: 第{current_week}周")

    # 获取今日课程（已过滤周次）
    courses = get_active_courses_by_day(day_of_week, current_week)
    logger.info(f"今日共有 {len(courses)} 门课程需要提醒")

    # 为每门课程创建提醒
    for course in courses:
        create_course_reminders(course, now)


def create_course_reminders(course, base_date):
    """
    为单门课程创建提醒

    参数:
        course: 课程信息
        base_date: 基准日期
    """
    # 解析课程开始时间
    start_time_str = course["start_time"]
    hour, minute = map(int, start_time_str.split(":"))

    # 构建课程开始时间
    course_start = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # 如果课程已经开始，跳过
    if course_start <= datetime.now():
        logger.info(f"课程 {course['name']} 已开始或已结束，跳过")
        return

    # 为每个提醒时间点创建提醒
    for minutes_before in REMINDER_TIMES:
        remind_time = course_start - timedelta(minutes=minutes_before)

        # 如果提醒时间已过，跳过
        if remind_time <= datetime.now():
            logger.info(
                f"课程 {course['name']} 的{minutes_before}分钟提醒时间已过，跳过"
            )
            continue

        # 添加到数据库
        reminder_id = add_reminder(course["id"], remind_time)
        logger.info(
            f"已为课程 {course['name']} 创建{minutes_before}分钟提醒，时间: {remind_time.strftime('%H:%M')}"
        )


def check_and_send_reminders():
    """
    检查并发送待发送的提醒
    """
    # 获取所有待发送的提醒
    pending_reminders = get_pending_reminders()

    if pending_reminders:
        logger.info(f"发现 {len(pending_reminders)} 条待发送提醒")

    for reminder in pending_reminders:
        # 从提醒记录中获取课程信息（包括week_pattern）
        course = {
            "id": reminder["course_id"],
            "name": reminder["name"],
            "start_time": reminder["start_time"],
            "end_time": reminder["end_time"],
            "location": reminder.get("location", ""),
            "week_pattern": reminder.get("week_pattern", "all"),
        }

        # 计算提前分钟数
        remind_time = datetime.strptime(reminder["remind_time"], "%Y-%m-%d %H:%M:%S")
        start_time = datetime.strptime(
            f"{datetime.now().strftime('%Y-%m-%d')} {course['start_time']}",
            "%Y-%m-%d %H:%M",
        )
        minutes_before = int((start_time - remind_time).total_seconds() / 60)

        # 发送提醒
        result = send_course_reminder(course, minutes_before)

        if result["success"]:
            mark_reminder_sent(reminder["id"])
            logger.info(f"成功发送提醒: {course['name']} ({minutes_before}分钟)")
        else:
            logger.error(f"发送提醒失败: {course['name']}, 错误: {result.get('error')}")


def cleanup_old_data():
    """清理旧数据"""
    logger.info("清理旧数据...")
    clear_old_reminders(days=7)
    logger.info("旧数据清理完成")


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("定时任务调度器已关闭")
