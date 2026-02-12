# -*- coding: utf-8 -*-
"""
数据库操作模块
"""

import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 创建课程表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            location TEXT,
            remark TEXT,
            week_pattern TEXT DEFAULT 'all',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建提醒记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            remind_time TIMESTAMP NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    """)

    # 迁移：如果week_pattern列不存在，则添加
    cursor.execute("PRAGMA table_info(courses)")
    columns = [col[1] for col in cursor.fetchall()]
    if "week_pattern" not in columns:
        cursor.execute("ALTER TABLE courses ADD COLUMN week_pattern TEXT DEFAULT 'all'")
        print("[数据库] 已添加 week_pattern 字段")

    # 初始化教学周设置
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('current_week', '1')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('total_weeks', '20')"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('semester_start', '')"
    )
    conn.commit()
    conn.close()

    print("[数据库] 初始化完成")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 课程相关操作
def add_course(
    name, day_of_week, start_time, end_time, location="", remark="", week_pattern="all"
):
    """添加课程"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO courses (name, day_of_week, start_time, end_time, location, remark, week_pattern)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (name, day_of_week, start_time, end_time, location, remark, week_pattern),
    )
    course_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return course_id


def get_all_courses():
    """获取所有课程"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY day_of_week, start_time")
    courses = cursor.fetchall()
    conn.close()
    return [dict(course) for course in courses]


def get_courses_by_day(day_of_week):
    """获取指定星期的课程"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM courses
        WHERE day_of_week = ?
        ORDER BY start_time
    """,
        (day_of_week,),
    )
    courses = cursor.fetchall()
    conn.close()
    return [dict(course) for course in courses]


def get_active_courses_by_day(day_of_week, current_week):
    """获取指定星期且在当前周有课的课程"""
    from utils.week_utils import is_course_active

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM courses
        WHERE day_of_week = ?
        ORDER BY start_time
    """,
        (day_of_week,),
    )
    courses = cursor.fetchall()
    conn.close()

    # 过滤出当周有课的课程
    active_courses = [
        course
        for course in [dict(c) for c in courses]
        if is_course_active(course.get("week_pattern", "all"), current_week)
    ]
    return active_courses


def delete_course(course_id):
    """删除课程"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()


def update_course(course_id, **kwargs):
    """更新课程信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    allowed_fields = [
        "name",
        "day_of_week",
        "start_time",
        "end_time",
        "location",
        "remark",
        "week_pattern",
    ]
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if updates:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [course_id]
        cursor.execute(f"UPDATE courses SET {set_clause} WHERE id = ?", values)
        conn.commit()

    conn.close()


# 配置相关操作
def get_setting(key, default=None):
    """获取配置项"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result["value"] if result else default


def set_setting(key, value):
    """设置配置项"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
    """,
        (key, value, datetime.now()),
    )
    conn.commit()
    conn.close()


# 提醒记录相关操作
def add_reminder(course_id, remind_time):
    """添加提醒记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reminders (course_id, remind_time, sent)
        VALUES (?, ?, FALSE)
    """,
        (course_id, remind_time),
    )
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id


def get_pending_reminders():
    """获取待发送的提醒"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.*, c.name, c.location, c.start_time, c.end_time, c.week_pattern
        FROM reminders r
        JOIN courses c ON r.course_id = c.id
        WHERE r.sent = FALSE AND r.remind_time <= ?
    """,
        (datetime.now(),),
    )
    reminders = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reminders]


def mark_reminder_sent(reminder_id):
    """标记提醒为已发送"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE reminders 
        SET sent = TRUE, sent_at = ? 
        WHERE id = ?
    """,
        (datetime.now(), reminder_id),
    )
    conn.commit()
    conn.close()


def clear_old_reminders(days=7):
    """清理旧提醒记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM reminders 
        WHERE remind_time < datetime('now', '-{} days')
    """.format(days)
    )
    conn.commit()
    conn.close()
