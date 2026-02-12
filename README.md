# 课程提醒助手

简单好用的本地课程管理与微信提醒系统

## 功能特性

- ✅ **Excel导入** - 支持.xlsx和.xls格式批量导入课程
- ✅ **双重提醒** - 课前15分钟和5分钟自动微信提醒
- ✅ **节假日跳过** - 自动识别节假日和周末，不发送提醒
- ✅ **Web管理** - 简洁的网页界面管理课程
- ✅ **一键部署** - Windows双击启动，无需复杂配置

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- Windows 操作系统

### 2. 安装步骤

**方法一：使用启动脚本（推荐）**

```bash
双击运行 start.bat
```

**方法二：手动安装**

```bash
# 创建虚拟环境（可选）
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

### 3. 配置微信提醒

1. 访问 [PushPlus官网](http://www.pushplus.plus/)
2. 使用微信扫码登录
3. 点击左侧"一对一消息"
4. 复制Token（一串字母数字组合）
5. 打开本系统的设置页面
6. 粘贴Token并点击"保存设置"
7. 点击"测试连接"验证是否成功

### 4. 导入课程

**Excel格式要求：**

| 课程名称 | 星期 | 开始时间 | 结束时间 | 地点 | 备注 |
|---------|------|---------|---------|------|------|
| 高等数学 | 周一 | 08:00 | 09:40 | A101 | 带教材 |
| 大学英语 | 2 | 14:00 | 15:40 | B203 | 演讲 |

- **星期**：支持1-7（周一到周日）或"周一"、"Tuesday"等格式
- **时间**：支持08:00、9:30、1430等多种格式

## 使用说明

### Web界面

启动后访问 `http://localhost:5000`

- **首页** - 查看今日课程和全部课程
- **导入Excel** - 上传Excel课表文件
- **设置** - 配置PushPlus Token和系统选项

### 提醒机制

- 每天00:05自动扫描今日课程
- 课前15分钟发送第一次提醒（蓝色）
- 课前5分钟发送第二次提醒（红色，更紧急）
- 节假日和周末自动跳过

### 数据存储

- 课程数据存储在本地SQLite数据库
- 数据库文件：`database.db`
- 节假日数据：`holidays.json`

## 目录结构

```
schedule-reminder/
├── app.py              # 主应用
├── config.py           # 配置文件
├── requirements.txt    # Python依赖
├── holidays.json      # 节假日数据
├── start.bat          # Windows启动脚本
├── database.db        # SQLite数据库（自动生成）
├── utils/             # 工具模块
│   ├── database.py    # 数据库操作
│   ├── excel_parser.py # Excel解析
│   ├── scheduler.py   # 定时任务
│   ├── wechat_push.py # 微信推送
│   └── holiday_checker.py # 节假日检查
├── templates/         # HTML模板
└── static/            # 静态资源
    ├── css/
    └── js/
```

## 常见问题

**Q: 为什么收不到微信提醒？**

A: 请检查以下几点：
1. PushPlus Token是否正确配置
2. 点击"测试连接"查看是否能收到测试消息
3. 检查是否为节假日（系统会自动跳过）
4. 确保程序保持运行状态

**Q: Excel导入失败怎么办？**

A: 请检查：
1. 文件格式是否为.xlsx或.xls
2. 必需列（课程名称、星期、开始时间、结束时间）是否存在
3. 时间格式是否正确
4. 可以先下载模板，按照模板格式填写

**Q: 如何修改提醒时间？**

A: 当前版本固定为15分钟和5分钟双重提醒，如需修改请编辑 `config.py` 中的 `REMINDER_TIMES` 配置。

**Q: 如何更新节假日数据？**

A: 编辑 `holidays.json` 文件，按照已有格式添加新的节假日数据。

## 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite
- **定时任务**: APScheduler
- **微信推送**: PushPlus
- **前端**: Bootstrap 5 + Vanilla JS

## 开源协议

MIT License

## 更新日志

### v1.0.0 (2024-01)
- 初始版本发布
- 支持Excel导入课程
- 支持微信提醒
- 支持节假日自动跳过
- 简洁的Web管理界面
