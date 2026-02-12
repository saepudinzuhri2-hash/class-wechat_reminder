# -*- coding: utf-8 -*-
"""
课程提醒助手 - Flask主应用
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect
import os
import io
from datetime import datetime, timedelta

from config import BASE_DIR, DATABASE_PATH, HOST, PORT, SECRET_KEY, DEBUG
from utils.database import (
    init_database,
    add_course,
    get_all_courses,
    get_courses_by_day,
    delete_course,
    update_course,
    get_setting,
    set_setting,
)
from utils.excel_parser import parse_excel, generate_template
from utils.scheduler import init_scheduler, shutdown_scheduler
from utils.wechat_push import test_connection
from utils.holiday_checker import is_holiday, should_send_reminder

app = Flask(__name__)
app.secret_key = SECRET_KEY


# 初始化
@app.before_request
def initialize():
    """首次请求时初始化数据库"""
    if not hasattr(app, "_initialized"):
        init_database()
        init_scheduler()
        app._initialized = True


@app.teardown_appcontext
def cleanup(exception):
    """应用关闭时清理资源"""
    pass


# 页面路由
@app.route("/")
def index():
    """首页 - 课程列表"""
    courses = get_all_courses()

    # 获取今日课程
    today = datetime.now()
    day_of_week = today.isoweekday()
    today_courses = get_courses_by_day(day_of_week)

    # 星期映射
    week_days = {
        1: "周一",
        2: "周二",
        3: "周三",
        4: "周四",
        5: "周五",
        6: "周六",
        7: "周日",
    }

    today_weekday = (
        f"今天是 {week_days.get(day_of_week)} {today.strftime('%Y年%m月%d日')}"
    )
    if is_holiday(today):
        today_weekday += "（节假日）"

    return render_template(
        "index.html",
        courses=courses,
        today_courses=today_courses,
        week_days=week_days,
        today_weekday=today_weekday,
    )


@app.route("/upload")
def upload_page():
    """上传页面"""
    return render_template("upload.html")


@app.route("/settings")
def settings_page():
    """设置页面"""
    settings = {
        "pushplus_token": get_setting("pushplus_token", ""),
        "skip_holidays": get_setting("skip_holidays", "true"),
    }

    # 统计信息
    courses = get_all_courses()
    today_count = len(get_courses_by_day(datetime.now().isoweekday()))

    return render_template(
        "settings.html",
        settings=settings,
        course_count=len(courses),
        today_count=today_count,
        current_date=datetime.now().strftime("%Y年%m月%d日"),
    )


# API路由 - 课程管理
@app.route("/api/courses", methods=["GET"])
def get_courses_api():
    """获取所有课程"""
    courses = get_all_courses()
    return jsonify({"success": True, "courses": courses, "count": len(courses)})


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course_api(course_id):
    """获取单个课程"""
    courses = get_all_courses()
    course = next((c for c in courses if c["id"] == course_id), None)

    if course:
        return jsonify({"success": True, "course": course})
    else:
        return jsonify({"success": False, "error": "课程不存在"}), 404


@app.route("/api/courses", methods=["POST"])
def add_course_api():
    """添加课程"""
    data = request.get_json()

    try:
        # 验证周次规则
        from utils.week_utils import validate_week_pattern

        week_pattern = data.get("week_pattern", "all")
        is_valid, error_msg = validate_week_pattern(week_pattern)

        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400

        course_id = add_course(
            name=data["name"],
            day_of_week=data["day_of_week"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            location=data.get("location", ""),
            remark=data.get("remark", ""),
            week_pattern=week_pattern,
        )

        return jsonify(
            {"success": True, "course_id": course_id, "message": "课程添加成功"}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course_api(course_id):
    """更新课程"""
    data = request.get_json()

    try:
        update_course(course_id, **data)
        return jsonify({"success": True, "message": "课程更新成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course_api(course_id):
    """删除课程"""
    try:
        delete_course(course_id)
        return jsonify({"success": True, "message": "课程删除成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/courses/clear", methods=["DELETE"])
def clear_courses_api():
    """清空所有课程"""
    try:
        courses = get_all_courses()
        for course in courses:
            delete_course(course["id"])

        return jsonify({"success": True, "message": "已清空所有课程"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# API路由 - 文件上传
@app.route("/api/upload", methods=["POST"])
def upload_file_api():
    """上传Excel文件"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未选择文件"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "未选择文件"}), 400

    if not file.filename.endswith((".xlsx", ".xls")):
        return jsonify(
            {"success": False, "error": "请上传Excel文件（.xlsx或.xls格式）"}
        ), 400

    try:
        # 保存临时文件
        temp_path = os.path.join(BASE_DIR, "temp_upload.xlsx")
        file.save(temp_path)

        # 解析Excel
        result = parse_excel(temp_path)

        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not result["success"]:
            return jsonify(result), 400

        # 添加到数据库
        added_count = 0
        for course_data in result["courses"]:
            try:
                add_course(**course_data)
                added_count += 1
            except Exception as e:
                result["errors"].append(f"添加课程失败 {course_data['name']}: {str(e)}")

        result["count"] = added_count

        # 刷新今日课程提醒
        from utils.scheduler import scan_daily_courses

        scan_daily_courses()

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"处理文件失败: {str(e)}"}), 500


@app.route("/api/template")
def download_template():
    """下载Excel模板"""
    try:
        wb = generate_template()

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="课程表模板.xlsx",
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# API路由 - 设置管理
@app.route("/api/settings", methods=["POST"])
def save_settings_api():
    """保存设置"""
    data = request.get_json()

    try:
        if "pushplus_token" in data:
            set_setting("pushplus_token", data["pushplus_token"])

        if "skip_holidays" in data:
            set_setting("skip_holidays", str(data["skip_holidays"]).lower())

        return jsonify({"success": True, "message": "设置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/test-push", methods=["POST"])
def test_push_api():
    """测试推送连接"""
    result = test_connection()

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


# API路由 - 系统状态
@app.route("/api/status")
def system_status():
    """获取系统状态"""
    courses = get_all_courses()
    today_count = len(get_courses_by_day(datetime.now().isoweekday()))

    return jsonify(
        {
            "success": True,
            "data": {
                "course_count": len(courses),
                "today_count": today_count,
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "is_holiday": is_holiday(),
                "scheduler_running": True,
            },
        }
    )


# API路由 - 教学周管理
@app.route("/api/teaching-week", methods=["GET"])
def get_teaching_week():
    """获取当前教学周设置"""
    try:
        current_week = get_setting("current_week", "1")
        total_weeks = get_setting("total_weeks", "20")
        semester_start = get_setting("semester_start", "")

        # 获取当前周次的中文描述
        from utils.week_utils import get_week_description

        return jsonify(
            {
                "success": True,
                "data": {
                    "current_week": int(current_week) if current_week else 1,
                    "total_weeks": int(total_weeks) if total_weeks else 20,
                    "semester_start": semester_start,
                    "week_description": f"第{current_week}周"
                    if current_week
                    else "未设置",
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/teaching-week", methods=["POST"])
def set_teaching_week():
    """设置当前教学周"""
    data = request.get_json()

    try:
        if "current_week" in data:
            current_week = data["current_week"]
            if not isinstance(current_week, int) or current_week < 1:
                return jsonify({"success": False, "error": "当前周次必须为正整数"}), 400
            set_setting("current_week", str(current_week))

        if "total_weeks" in data:
            total_weeks = data["total_weeks"]
            if not isinstance(total_weeks, int) or total_weeks < 1 or total_weeks > 25:
                return jsonify({"success": False, "error": "总周数必须在1-25之间"}), 400
            set_setting("total_weeks", str(total_weeks))

        if "semester_start" in data:
            set_setting("semester_start", data["semester_start"])

        # 重新扫描今日课程
        from utils.scheduler import scan_daily_courses

        scan_daily_courses()

        return jsonify({"success": True, "message": "教学周设置成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/teaching-week/auto", methods=["POST"])
def auto_calc_teaching_week():
    """根据开学日期自动计算当前教学周"""
    try:
        semester_start = get_setting("semester_start")

        if not semester_start:
            return jsonify({"success": False, "error": "未设置开学日期"}), 400

        start_date = datetime.strptime(semester_start, "%Y-%m-%d")
        today = datetime.now()

        days_passed = (today - start_date).days
        current_week = (days_passed // 7) + 1

        if current_week < 1:
            current_week = 1
        elif current_week > 25:
            current_week = 25

        set_setting("current_week", str(current_week))

        # 重新扫描今日课程
        from utils.scheduler import scan_daily_courses

        scan_daily_courses()

        return jsonify(
            {
                "success": True,
                "message": f"已自动计算当前周次：第{current_week}周",
                "current_week": current_week,
            }
        )
    except ValueError:
        return jsonify({"success": False, "error": "开学日期格式不正确"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/courses/week-pattern/<int:course_id>", methods=["GET"])
def get_course_week_pattern(course_id):
    """获取课程的周次安排详情"""
    courses = get_all_courses()
    course = next((c for c in courses if c["id"] == course_id), None)

    if not course:
        return jsonify({"success": False, "error": "课程不存在"}), 404

    from utils.week_utils import parse_week_pattern, get_week_description

    pattern = course.get("week_pattern", "all")
    active_weeks = parse_week_pattern(pattern)
    description = get_week_description(pattern)

    return jsonify(
        {
            "success": True,
            "data": {
                "course_id": course_id,
                "course_name": course["name"],
                "week_pattern": pattern,
                "active_weeks": active_weeks,
                "description": description,
            },
        }
    )


if __name__ == "__main__":
    # 避免Flask重载器导致重复初始化
    # WERKZEUG_RUN_MAIN只在实际运行进程（非监控进程）中设置
    is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") is None and DEBUG

    # 初始化数据库（非重载器进程或在非DEBUG模式下）
    if not is_reloader:
        init_database()

    # 初始化定时任务（非重载器进程或在非DEBUG模式下）
    if not is_reloader:
        init_scheduler()

    try:
        # 只在非重载器进程打印启动信息
        if not is_reloader:
            print("=" * 60)
            print("  课程提醒助手已启动")
            print("=" * 60)
            print(f"  访问地址: http://localhost:{PORT}")
            print(f"  数据库: {DATABASE_PATH}")
            print("=" * 60)
            print("  提示: 首次使用请先在设置页面配置PushPlus Token")
            print("=" * 60)

        # 启动Flask应用
        app.run(host=HOST, port=PORT, debug=DEBUG)

    except KeyboardInterrupt:
        print("\n正在关闭服务...")
    finally:
        shutdown_scheduler()
        print("服务已停止")
