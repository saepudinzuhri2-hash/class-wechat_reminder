# -*- coding: utf-8 -*-
"""
PushPlus微信推送模块
"""

import requests
import json
from config import PUSHPLUS_API
from utils.database import get_setting


def send_message(title, content, template="html"):
    """
    发送微信推送消息

    参数:
        title: 消息标题
        content: 消息内容
        template: 模板类型 (html/json/markdown)

    返回:
        dict: 发送结果
    """
    token = get_setting("pushplus_token")
    if not token:
        return {"success": False, "error": "未配置PushPlus Token，请在设置页面配置"}

    try:
        data = {
            "token": token,
            "title": title,
            "content": content,
            "template": template,
        }

        response = requests.post(PUSHPLUS_API, data=data, timeout=10)

        result = response.json()

        if result.get("code") == 200:
            return {"success": True, "message": "发送成功", "data": result}
        else:
            return {"success": False, "error": result.get("msg", "发送失败")}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时，请检查网络连接"}
    except Exception as e:
        return {"success": False, "error": f"发送失败: {str(e)}"}


def send_course_reminder(course, minutes_before):
    """
    发送课程提醒

    参数:
        course: 课程信息字典
        minutes_before: 提前多少分钟
    """
    # 获取当前教学周
    current_week = get_setting("current_week", "")
    from utils.week_utils import get_week_description

    if minutes_before == 15:
        title = f"📚 课程提醒（15分钟后）"
        urgency = "还有15分钟上课"
    elif minutes_before == 5:
        title = f"🚨 紧急提醒（5分钟后）"
        urgency = "还有5分钟上课！"
    else:
        title = f"📚 课程提醒"
        urgency = f"还有{minutes_before}分钟上课"

    # 构建周次信息
    week_info = f"第{current_week}周" if current_week else ""
    week_pattern = course.get("week_pattern", "all")
    pattern_desc = get_week_description(week_pattern)

    # 标题中加入周次信息
    if week_info:
        title = f"{title} - {week_info}"

    content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 400px;">
    <h3 style="color: #2563eb;">⏰ {urgency}</h3>
    <hr style="border: none; border-top: 1px solid #e5e7eb;">
    <p style="margin: 8px 0;"><strong>📖 课程名称：</strong>{course["name"]}</p>
    """

    if week_info:
        content += f'<p style="margin: 8px 0;"><strong>📅 当前周次：</strong>{week_info}（{pattern_desc}）</p>'

    content += f"""
    <p style="margin: 8px 0;"><strong>🕐 上课时间：</strong>{course["start_time"]} - {course["end_time"]}</p>
    <p style="margin: 8px 0;"><strong>📍 上课地点：</strong>{course.get("location", "未指定")}</p>
    """

    if course.get("remark"):
        content += f'<p style="margin: 8px 0;"><strong>📝 备注：</strong>{course["remark"]}</p>'

    content += """
    <hr style="border: none; border-top: 1px solid #e5e7eb;">
    <p style="color: #6b7280; font-size: 12px; text-align: center;">来自课程提醒助手</p>
    </div>
    """

    return send_message(title, content)


def test_connection():
    """测试PushPlus连接"""
    token = get_setting("pushplus_token")
    if not token:
        return {"success": False, "error": "未配置Token"}

    result = send_message(
        "✅ 连接测试成功",
        "<p>您的课程提醒助手已成功配置！</p><p>现在您可以开始接收课程提醒了。</p>",
        "html",
    )

    return result


def get_token_guide():
    """获取PushPlus注册指引"""
    guide = """
    <h3>📝 PushPlus Token 获取步骤</h3>
    <ol>
        <li>打开浏览器访问：<a href="http://www.pushplus.plus/" target="_blank">http://www.pushplus.plus/</a></li>
        <li>点击"登录"，使用微信扫码登录</li>
        <li>登录成功后，点击左侧"一对一消息"</li>
        <li>复制页面上的"Token"（一串字母和数字的组合）</li>
        <li>将Token粘贴到本系统的设置页面中</li>
        <li>点击"保存设置"，然后点击"测试连接"验证</li>
    </ol>
    <p><strong>💡 提示：</strong>Token是您的身份标识，请妥善保管，不要泄露给他人。</p>
    """
    return guide
