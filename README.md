# 驾驶行为监控系统 (Driver Behavior Monitoring System)

🌐 [English Version](README_EN.md)

## 项目简介

这是一个基于 Web 的驾驶行为实时监控与数据分析系统，用于检测和记录驾驶员的超速、疲劳驾驶、空挡滑行等危险行为。

**核心技术栈**：Python Flask + MySQL + 原生 JavaScript + Chart.js

---

## 功能特性

| 功能模块 | 描述 |
|---------|------|
| **实时速度监控** | 动态展示驾驶员实时速度变化，支持自动轮播播放 |
| **超速检测** | 自动检测超速行为 (>120 km/h)，实时预警提示 |
| **疲劳驾驶检测** | 识别长时间连续驾驶行为 |
| **空挡滑行检测** | 监控空挡滑行时间及频次 |
| **数据可视化** | 使用 Chart.js 绘制速度曲线图，超速点红色标注 |
| **分页浏览** | 支持按日期筛选，分页查看历史驾驶数据 |
| **驾驶员摘要** | 统计每位驾驶员的危险行为总次数和持续时间 |

---

## 技术架构

### 后端 (Backend)
- **框架**: Flask 2.3.3
- **ORM**: Flask-SQLAlchemy 3.0.5
- **数据库**: MySQL + PyMySQL 驱动
- **跨域支持**: Flask-CORS

### 前端 (Frontend)
- **图表库**: Chart.js (CDN)
- **样式**: 原生 CSS
- **交互**: 原生 JavaScript (ES6+)

### 数据模型

```sql
-- 原始驾驶记录表
raw_driving_records:
  - driverID (驾驶员ID)
  - carPlateNumber (车牌号)
  - Speed (速度 km/h)
  - Time (时间戳)
  - isOverspeed (是否超速)
  - isFatigueDriving (是否疲劳驾驶)
  - overspeedTime (超速持续时间秒)
  - neutralSlideTime (空挡滑行时间秒)

-- 驾驶员行为摘要表
driver_behavior_summary:
  - driverID (驾驶员ID)
  - carPlateNumber (车牌号)
  - overspeed_count (超速次数)
  - fatigue_count (疲劳驾驶次数)
  - total_overspeed_sec (超速总时长)
  - total_neutral_slide_sec (空挡滑行总时长)
```

---

## API 接口

| 接口 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/summary` | GET | 获取所有驾驶员摘要 | - |
| `/api/speed/<driver_id>` | GET | 获取驾驶员速度记录 | `page`, `page_size`, `date` |
| `/api/driver_dates/<driver_id>` | GET | 获取驾驶员有记录的日期列表 | - |
| `/api/health` | GET | 健康检查 | - |

---

## 快速开始

### 环境要求
- Python 3.8+
- MySQL 5.7+

### 安装依赖

```bash
cd "Source code/FullStuck_v2.0(newest)"
pip install -r requirements.txt
```

### 数据库配置

1. 创建 MySQL 数据库 `driver_behavior`
2. 修改 `app.py` 中的数据库连接配置：

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/driver_behavior?charset=utf8mb4'
```

3. 导入数据：

```bash
mysql -u root -p driver_behavior < setup_raw_data.sql
mysql -u root -p driver_behavior < summary_results.sql
```

### 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 访问前端

直接在浏览器中打开 `index.html` 文件即可访问监控界面。

---

## 项目结构

```
Source code/
├── FullStuck_v2.0(newest)/    # 最新完整版本
│   ├── app.py                  # Flask 后端主程序
│   ├── index.html              # 前端监控页面
│   ├── requirements.txt        # Python 依赖
│   ├── setup_raw_data.sql      # 原始数据初始化
│   └── summary_results.sql     # 摘要数据初始化
├── backend_v1.0/               # 早期版本
└── Dataset (clean)/            # 数据集处理脚本

Google drive dataset/           # 原始数据集
├── detail-records/             # 详细驾驶记录文件
└── 2026-COMP4442-Project-Dataset.pdf

2026_COMP4442_Group_Project.pdf # 课程项目要求
Report.docx                     # 项目报告
Presentation&Demostration.pptx  # 演示文稿
```

---

## 数据来源

本项目使用 COMP4442 课程提供的驾驶行为数据集，包含 10 位驾驶员在 2017 年 1 月的 GPS 行驶记录数据。

**样本驾驶员**: zengpeng1000000, xiexiao1000001, hanhui1000002, likun1000003, shenxian1000004, panxian1000005, xiezhi1000006, zouan1000007, haowei1000008, duxu1000009

---

## 后续开发计划

### Phase 1: 多租户用户系统 (Multi-Tenant User System)

**目标**: 支持多企业/组织独立管理各自的驾驶员数据

**核心功能**:
- [ ] 租户注册与隔离 (Tenant Isolation)
- [ ] 基于角色的权限控制 (RBAC)
  - 超级管理员：全局数据管理
  - 租户管理员：管理本租户下的驾驶员
  - 普通用户：查看授权数据
- [ ] 数据行级安全 (Row-Level Security)
- [ ] JWT 认证与 Session 管理

**技术方案**:
- 添加租户表 (tenants) 和用户表 (users)
- 所有业务表增加 tenant_id 字段
- 使用 Flask-JWT-Extended 处理认证
- 中间件自动过滤当前租户数据

### Phase 2: AI 数据分析 (AI-Powered Analytics)

**目标**: 利用 AI 模型深度分析驾驶行为，提供智能洞察

**核心功能**:
- [ ] 驾驶行为评分模型
  - 基于历史数据的驾驶习惯画像
  - 风险等级评估 (低/中/高)
- [ ] 异常检测
  - 聚类分析识别异常驾驶模式
  - 时序预测预警潜在危险
- [ ] 自然语言查询
  - 用户可用中文/英文直接提问
  - AI 自动生成 SQL 查询并返回结果
- [ ] 智能报告生成
  - 自动生成周/月度驾驶行为分析报告
  - 可视化图表 + 文字解读

**技术方案**:
- 集成 OpenAI/Claude API 或本地 LLM
- 使用 scikit-learn/pandas 进行数据挖掘
- 构建驾驶行为特征工程
- 可选：训练专用驾驶行为评估模型

---

## 贡献者

COMP4442 课程项目团队

---

## 许可证

本项目为课程作业，仅供学习交流使用。
