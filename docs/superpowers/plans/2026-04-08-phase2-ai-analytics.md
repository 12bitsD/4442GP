# Phase 2: AI-Powered Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有驾驶行为监控系统上增加 AI 分析能力，包括行为评分、异常检测、自然语言查询和智能报告生成。

**Architecture:** 在现有 Flask + MySQL 后端新增 AI 服务模块（`ai_service.py`），通过新增 REST 接口对外暴露 AI 能力；前端在现有 `index.html` 中新增 AI 面板区域，通过 SSE 流式接收 LLM 响应。AI 分析使用 scikit-learn IsolationForest 做异常检测，Vanna.ai 做自然语言转 SQL，ReportLab 生成 PDF 报告。

**Tech Stack:**
- Backend: Flask 3.x, SQLAlchemy, Vanna.ai ≥0.4, scikit-learn ≥1.5, ReportLab ≥4.4, pandas ≥2.0, OpenAI API
- Frontend: Vanilla JS (ES6+), Chart.js, SSE (EventSource API)
- Database: MySQL (现有 driver_behavior 库，无 schema 变更)

---

## 排期总览

| Phase | 任务 | 估时 | 依赖 |
|-------|------|------|------|
| **P2.1** | 后端基础 + 依赖安装 | 0.5d | 无 |
| **P2.2** | 驾驶行为评分模型 | 1d | P2.1 |
| **P2.3** | 异常检测 API | 1d | P2.1 |
| **P2.4** | 自然语言查询（NL→SQL）| 1.5d | P2.1 |
| **P2.5** | PDF 报告生成 | 1d | P2.2, P2.3 |
| **P2.6** | 前端 AI 面板 | 1.5d | P2.2, P2.3, P2.4 |
| **P2.7** | SSE 流式 LLM 对话 | 1d | P2.4, P2.6 |
| **合计** | | **~7d** | |

---

## 文件结构

```
Source code/FullStuck_v2.0(newest)/
├── app.py                    # 现有主程序 — 新增 AI 路由注册
├── ai_service.py             # 新建 — AI 分析核心逻辑
│   ├── compute_driver_score()
│   ├── detect_anomalies()
│   ├── nl_to_sql_query()
│   └── generate_pdf_report()
├── requirements.txt          # 现有 — 新增 AI 依赖
├── index.html                # 现有 — 新增 AI 面板 DOM + JS
└── tests/
    ├── test_ai_score.py      # 新建
    ├── test_anomaly.py       # 新建
    └── test_nl_query.py      # 新建
```

---

## Task 1: 安装依赖 & 环境配置

**Files:**
- Modify: `Source code/FullStuck_v2.0(newest)/requirements.txt`
- Create: `Source code/FullStuck_v2.0(newest)/.env.example`

- [ ] **Step 1: 更新 requirements.txt**

将以下内容替换 `requirements.txt`：

```txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.1
Flask-CORS==4.0.1
# AI dependencies
openai>=1.30.0
langchain>=0.3.0
langchain-openai>=0.3.0
vanna[openai]>=0.4.0
scikit-learn>=1.5.0
pandas>=2.0.0
numpy>=1.26.0
reportlab>=4.4.0
matplotlib>=3.8.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: 创建 .env.example**

```bash
OPENAI_API_KEY=sk-your-key-here
VANNA_MODEL=your-vanna-model-name
VANNA_API_KEY=your-vanna-api-key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=123456
DB_NAME=driver_behavior
```

- [ ] **Step 3: 安装依赖**

```bash
cd "Source code/FullStuck_v2.0(newest)"
pip install -r requirements.txt
```

预期输出：`Successfully installed openai-... vanna-... scikit-learn-...`

- [ ] **Step 4: 验证安装**

```bash
python -c "import openai; import vanna; import sklearn; import reportlab; print('All AI deps OK')"
```

预期输出：`All AI deps OK`

- [ ] **Step 5: Commit**

```bash
git add "Source code/FullStuck_v2.0(newest)/requirements.txt" "Source code/FullStuck_v2.0(newest)/.env.example"
git commit -m "feat(phase2): add AI dependencies to requirements"
```

---

## Task 2: 创建 AI 服务基础框架

**Files:**
- Create: `Source code/FullStuck_v2.0(newest)/ai_service.py`

- [ ] **Step 1: 写失败测试**

创建 `Source code/FullStuck_v2.0(newest)/tests/test_ai_service.py`：

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_service import compute_driver_score, detect_anomalies

def test_compute_driver_score_returns_valid_score():
    """Score must be between 0 and 100."""
    sample_summary = {
        'overspeed_count': 10,
        'fatigue_count': 5,
        'total_overspeed_sec': 300,
        'total_neutral_slide_sec': 120
    }
    score = compute_driver_score(sample_summary)
    assert 0 <= score <= 100, f"Score {score} out of range"

def test_compute_driver_score_zero_incidents():
    """A perfect driver should score 100."""
    perfect = {
        'overspeed_count': 0,
        'fatigue_count': 0,
        'total_overspeed_sec': 0,
        'total_neutral_slide_sec': 0
    }
    score = compute_driver_score(perfect)
    assert score == 100

def test_detect_anomalies_returns_list():
    """detect_anomalies should return a list of records flagged as anomaly."""
    records = [
        {'time': '2017-01-02T16:00:10', 'speed': 60.0, 'is_overspeed': False},
        {'time': '2017-01-02T16:00:20', 'speed': 180.0, 'is_overspeed': True},
        {'time': '2017-01-02T16:00:30', 'speed': 62.0, 'is_overspeed': False},
    ] * 10  # 30 records total
    anomalies = detect_anomalies(records)
    assert isinstance(anomalies, list)
    # High-speed record should be flagged
    flagged_speeds = [a['speed'] for a in anomalies]
    assert 180.0 in flagged_speeds
```

- [ ] **Step 2: 运行，确认失败**

```bash
cd "Source code/FullStuck_v2.0(newest)"
python -m pytest tests/test_ai_service.py -v
```

预期：`ImportError: cannot import name 'compute_driver_score' from 'ai_service'`

- [ ] **Step 3: 创建 ai_service.py 最小实现**

创建 `Source code/FullStuck_v2.0(newest)/ai_service.py`：

```python
"""
ai_service.py - Phase 2 AI Analytics Service
Provides: driver scoring, anomaly detection, NL-to-SQL, PDF report generation
"""
import os
import math
import json
import io
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Driver Behavior Scoring
# ---------------------------------------------------------------------------

# Penalty weights (tunable)
SCORE_WEIGHTS = {
    'overspeed_count':        0.30,  # 30% weight
    'fatigue_count':          0.30,  # 30% weight
    'total_overspeed_sec':    0.25,  # 25% weight
    'total_neutral_slide_sec': 0.15, # 15% weight
}

# Reference max values (based on dataset: max overspeed_count ~3531)
SCORE_REFS = {
    'overspeed_count':         3600,
    'fatigue_count':           4400,
    'total_overspeed_sec':    34000,
    'total_neutral_slide_sec': 3100,
}

def compute_driver_score(summary: Dict[str, Any]) -> int:
    """
    Compute a 0-100 safety score for a driver.
    100 = perfect (no violations), 0 = worst possible.

    Args:
        summary: dict with keys overspeed_count, fatigue_count,
                 total_overspeed_sec, total_neutral_slide_sec
    Returns:
        int score in [0, 100]
    """
    penalty = 0.0
    for field, weight in SCORE_WEIGHTS.items():
        value = summary.get(field, 0) or 0
        ref = SCORE_REFS[field]
        ratio = min(value / ref, 1.0)  # cap at 1.0
        penalty += weight * ratio

    score = round((1.0 - penalty) * 100)
    return max(0, min(100, score))


def get_risk_level(score: int) -> str:
    """Map score to risk label."""
    if score >= 80:
        return 'LOW'
    elif score >= 60:
        return 'MEDIUM'
    else:
        return 'HIGH'


# ---------------------------------------------------------------------------
# 2. Anomaly Detection (IsolationForest)
# ---------------------------------------------------------------------------

def detect_anomalies(records: List[Dict[str, Any]], contamination: float = 0.05) -> List[Dict[str, Any]]:
    """
    Detect anomalous driving records using IsolationForest.

    Args:
        records: list of dicts with keys: time, speed, is_overspeed
        contamination: expected fraction of anomalies (default 5%)
    Returns:
        list of anomalous records (subset of input), each with added 'anomaly_score' key
    """
    if len(records) < 10:
        return []

    df = pd.DataFrame(records)
    df['is_overspeed_int'] = df['is_overspeed'].astype(int)

    feature_cols = ['speed', 'is_overspeed_int']
    X = df[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=100,
        max_samples=min(256, len(X)),
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_scaled)

    df['anomaly_score'] = model.decision_function(X_scaled)
    df['is_anomaly'] = model.predict(X_scaled)  # -1 = anomaly

    anomalies = df[df['is_anomaly'] == -1].copy()
    result = []
    for _, row in anomalies.iterrows():
        record = {
            'time': row['time'],
            'speed': float(row['speed']),
            'is_overspeed': bool(row['is_overspeed']),
            'anomaly_score': float(row['anomaly_score'])
        }
        result.append(record)

    return sorted(result, key=lambda x: x['anomaly_score'])  # most anomalous first
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd "Source code/FullStuck_v2.0(newest)"
python -m pytest tests/test_ai_service.py -v
```

预期：`3 passed`

- [ ] **Step 5: Commit**

```bash
git add "Source code/FullStuck_v2.0(newest)/ai_service.py" "Source code/FullStuck_v2.0(newest)/tests/"
git commit -m "feat(phase2): add driver scoring and anomaly detection"
```

---

## Task 3: 在 app.py 注册 AI 路由（评分 + 异常检测）

**Files:**
- Modify: `Source code/FullStuck_v2.0(newest)/app.py`

- [ ] **Step 1: 写失败测试**

创建 `Source code/FullStuck_v2.0(newest)/tests/test_ai_routes.py`：

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_ai_score_endpoint_returns_json(client):
    """GET /api/ai/score/<driver_id> should return JSON with score field."""
    mock_driver = MagicMock()
    mock_driver.overspeed_count = 100
    mock_driver.fatigue_count = 50
    mock_driver.total_overspeed_sec = 500
    mock_driver.total_neutral_slide_sec = 200

    with patch('app.DriverSummary') as mock_model:
        mock_model.query.get.return_value = mock_driver
        resp = client.get('/api/ai/score/haowei1000008')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'score' in data
        assert 0 <= data['score'] <= 100

def test_ai_score_not_found(client):
    """Should return 404 when driver does not exist."""
    with patch('app.DriverSummary') as mock_model:
        mock_model.query.get.return_value = None
        resp = client.get('/api/ai/score/nonexistent_driver')
        assert resp.status_code == 404

def test_ai_anomalies_endpoint(client):
    """GET /api/ai/anomalies/<driver_id> should return list."""
    mock_records = [MagicMock(Speed=60.0, Time=MagicMock(isoformat=lambda: '2017-01-02T16:00:00'), isOverspeed=0)] * 30
    with patch('app.RawDrivingRecord') as mock_model:
        mock_model.query.filter_by.return_value.order_by.return_value.all.return_value = mock_records
        resp = client.get('/api/ai/anomalies/haowei1000008')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'anomalies' in data
        assert isinstance(data['anomalies'], list)
```

- [ ] **Step 2: 运行，确认失败**

```bash
python -m pytest tests/test_ai_routes.py -v
```

预期：`404 Not Found` for AI routes

- [ ] **Step 3: 在 app.py 末尾添加 AI 路由**

在 `app.py` 的 `if __name__ == '__main__':` 之前插入：

```python
from ai_service import compute_driver_score, get_risk_level, detect_anomalies

@app.route('/api/ai/score/<driver_id>', methods=['GET'])
def get_ai_score(driver_id):
    """Return AI-computed safety score for a driver."""
    driver = DriverSummary.query.get(driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    summary = {
        'overspeed_count': driver.overspeed_count,
        'fatigue_count': driver.fatigue_count,
        'total_overspeed_sec': driver.total_overspeed_sec,
        'total_neutral_slide_sec': driver.total_neutral_slide_sec,
    }
    score = compute_driver_score(summary)
    return jsonify({
        'driverID': driver_id,
        'score': score,
        'risk_level': get_risk_level(score),
        'breakdown': summary
    })


@app.route('/api/ai/scores', methods=['GET'])
def get_all_ai_scores():
    """Return AI safety scores for all drivers."""
    drivers = DriverSummary.query.all()
    result = []
    for d in drivers:
        summary = {
            'overspeed_count': d.overspeed_count,
            'fatigue_count': d.fatigue_count,
            'total_overspeed_sec': d.total_overspeed_sec,
            'total_neutral_slide_sec': d.total_neutral_slide_sec,
        }
        score = compute_driver_score(summary)
        result.append({
            'driverID': d.driverID,
            'carPlateNumber': d.carPlateNumber,
            'score': score,
            'risk_level': get_risk_level(score)
        })
    return jsonify(sorted(result, key=lambda x: x['score']))


@app.route('/api/ai/anomalies/<driver_id>', methods=['GET'])
def get_anomalies(driver_id):
    """Return anomalous driving records for a driver using IsolationForest."""
    date_str = request.args.get('date')
    query = RawDrivingRecord.query.filter_by(driverID=driver_id)
    if date_str:
        try:
            start = datetime.strptime(date_str, '%Y-%m-%d')
            end = start.replace(hour=23, minute=59, second=59)
            query = query.filter(RawDrivingRecord.Time.between(start, end))
        except ValueError:
            pass

    records_db = query.order_by(RawDrivingRecord.Time).all()
    records = [
        {
            'time': r.Time.isoformat(),
            'speed': r.Speed,
            'is_overspeed': bool(r.isOverspeed)
        }
        for r in records_db
    ]

    anomalies = detect_anomalies(records)
    return jsonify({'driverID': driver_id, 'anomalies': anomalies, 'total': len(anomalies)})
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_ai_routes.py -v
```

预期：`3 passed`

- [ ] **Step 5: Commit**

```bash
git add "Source code/FullStuck_v2.0(newest)/app.py" "Source code/FullStuck_v2.0(newest)/tests/test_ai_routes.py"
git commit -m "feat(phase2): add /api/ai/score and /api/ai/anomalies endpoints"
```

---

## Task 4: 自然语言查询（NL→SQL via Vanna.ai）

**Files:**
- Modify: `Source code/FullStuck_v2.0(newest)/ai_service.py` — 新增 `nl_to_sql_query()`
- Modify: `Source code/FullStuck_v2.0(newest)/app.py` — 新增 `/api/ai/query` 路由

- [ ] **Step 1: 在 ai_service.py 末尾新增 NL→SQL 函数**

```python
# ---------------------------------------------------------------------------
# 3. Natural Language → SQL (Vanna.ai)
# ---------------------------------------------------------------------------

_vanna_instance = None

def _get_vanna():
    """Lazy-init Vanna instance (singleton)."""
    global _vanna_instance
    if _vanna_instance is not None:
        return _vanna_instance

    try:
        from vanna.openai import OpenAI_Chat
        from vanna.chromadb import ChromaDB_VectorStore

        class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
            def __init__(self, config=None):
                ChromaDB_VectorStore.__init__(self, config=config)
                OpenAI_Chat.__init__(self, config=config)

        vn = MyVanna(config={
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': 'gpt-4o-mini',
        })

        db_url = (
            f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:"
            f"{os.getenv('DB_PASSWORD', '123456')}@"
            f"{os.getenv('DB_HOST', 'localhost')}/"
            f"{os.getenv('DB_NAME', 'driver_behavior')}?charset=utf8mb4"
        )
        vn.connect_to_mysql(url=db_url)

        # Train with schema DDL
        vn.train(ddl="""
            CREATE TABLE driver_behavior_summary (
                driverID VARCHAR(50) PRIMARY KEY,
                carPlateNumber VARCHAR(20),
                overspeed_count INT COMMENT 'Total speeding incidents',
                fatigue_count INT COMMENT 'Total fatigue driving incidents',
                total_overspeed_sec INT COMMENT 'Total overspeed duration in seconds',
                total_neutral_slide_sec INT COMMENT 'Total neutral sliding duration in seconds'
            );
            CREATE TABLE raw_driving_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                driverID VARCHAR(50),
                carPlateNumber VARCHAR(20),
                Speed FLOAT COMMENT 'Speed in km/h',
                Time DATETIME,
                isOverspeed INT COMMENT '1=speeding (>120km/h)',
                isFatigueDriving INT COMMENT '1=fatigue detected',
                overspeedTime INT COMMENT 'Continuous overspeed seconds',
                neutralSlideTime INT COMMENT 'Neutral slide seconds'
            );
        """)

        _vanna_instance = vn
        return vn

    except Exception as e:
        raise RuntimeError(f"Failed to initialize Vanna: {e}")


def nl_to_sql_query(question: str) -> Dict[str, Any]:
    """
    Convert a natural language question to SQL and execute it.

    Args:
        question: e.g. "Which drivers had more than 3000 overspeed events?"
    Returns:
        dict with keys: sql (str), results (list of dicts), error (str or None)
    """
    try:
        vn = _get_vanna()
        sql = vn.generate_sql(question=question)
        df = vn.run_sql(sql=sql)

        results = df.to_dict(orient='records') if df is not None else []
        # Convert non-serializable types
        for row in results:
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()
                elif isinstance(v, (np.integer,)):
                    row[k] = int(v)
                elif isinstance(v, (np.floating,)):
                    row[k] = float(v)

        return {'sql': sql, 'results': results, 'error': None}

    except Exception as e:
        return {'sql': None, 'results': [], 'error': str(e)}
```

- [ ] **Step 2: 在 app.py 新增 /api/ai/query 路由**

在 AI 路由区块末尾追加：

```python
from ai_service import nl_to_sql_query

@app.route('/api/ai/query', methods=['POST'])
def ai_natural_language_query():
    """
    POST /api/ai/query
    Body: {"question": "Which driver has the most overspeed events?"}
    Returns: {sql, results, error}
    """
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'Missing field: question'}), 400

    question = data['question'].strip()
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    result = nl_to_sql_query(question)
    status = 500 if result['error'] else 200
    return jsonify(result), status
```

- [ ] **Step 3: 手动测试（需要真实 OpenAI key）**

```bash
# 启动服务
python app.py &

# 测试 NL 查询
curl -X POST http://localhost:5000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which driver had the most overspeed events?"}'
```

预期响应：
```json
{
  "sql": "SELECT driverID, overspeed_count FROM driver_behavior_summary ORDER BY overspeed_count DESC LIMIT 1",
  "results": [{"driverID": "panxian1000005", "overspeed_count": 3531}],
  "error": null
}
```

- [ ] **Step 4: Commit**

```bash
git add "Source code/FullStuck_v2.0(newest)/ai_service.py" "Source code/FullStuck_v2.0(newest)/app.py"
git commit -m "feat(phase2): add NL-to-SQL query endpoint via Vanna.ai"
```

---

## Task 5: PDF 报告生成

**Files:**
- Modify: `Source code/FullStuck_v2.0(newest)/ai_service.py` — 新增 `generate_pdf_report()`
- Modify: `Source code/FullStuck_v2.0(newest)/app.py` — 新增 `/api/ai/report/<driver_id>` 路由

- [ ] **Step 1: 在 ai_service.py 末尾新增报告生成函数**

```python
# ---------------------------------------------------------------------------
# 4. PDF Report Generation (ReportLab)
# ---------------------------------------------------------------------------

def generate_pdf_report(driver_id: str, summary: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> bytes:
    """
    Generate a PDF driving behavior report for a driver.

    Args:
        driver_id: driver identifier string
        summary: dict with overspeed_count, fatigue_count, total_overspeed_sec,
                 total_neutral_slide_sec, carPlateNumber
        anomalies: list of anomaly records from detect_anomalies()
    Returns:
        bytes: PDF file content
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13, spaceAfter=8)

    elements = []

    # ---- Title ----
    score = compute_driver_score(summary)
    risk = get_risk_level(score)
    elements.append(Paragraph("Driver Behavior Analysis Report", title_style))
    elements.append(Paragraph(f"Driver: {driver_id} | Plate: {summary.get('carPlateNumber', 'N/A')} | Safety Score: {score}/100 ({risk})", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Summary Table ----
    elements.append(Paragraph("Behavior Summary", section_style))
    risk_color = {'LOW': colors.green, 'MEDIUM': colors.orange, 'HIGH': colors.red}[risk]

    summary_data = [
        ['Metric', 'Value'],
        ['Safety Score', f'{score} / 100'],
        ['Risk Level', risk],
        ['Overspeed Incidents', str(summary.get('overspeed_count', 0))],
        ['Fatigue Driving Incidents', str(summary.get('fatigue_count', 0))],
        ['Total Overspeed Duration', f"{summary.get('total_overspeed_sec', 0)} sec"],
        ['Total Neutral Slide Duration', f"{summary.get('total_neutral_slide_sec', 0)} sec"],
        ['Anomalies Detected', str(len(anomalies))],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('BACKGROUND', (1, 2), (1, 2), risk_color),
        ('TEXTCOLOR', (1, 2), (1, 2), colors.white),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ---- Anomaly Table ----
    if anomalies:
        elements.append(Paragraph(f"Top Anomalies (showing up to 20 of {len(anomalies)})", section_style))
        anomaly_data = [['Timestamp', 'Speed (km/h)', 'Overspeed', 'Anomaly Score']]
        for a in anomalies[:20]:
            anomaly_data.append([
                str(a.get('time', ''))[:19],
                f"{a.get('speed', 0):.1f}",
                'Yes' if a.get('is_overspeed') else 'No',
                f"{a.get('anomaly_score', 0):.4f}"
            ])
        anomaly_table = Table(anomaly_data, colWidths=[2.2 * inch, 1.2 * inch, 1 * inch, 1.3 * inch])
        anomaly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightyellow]),
        ]))
        elements.append(anomaly_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
```

- [ ] **Step 2: 在 app.py 新增报告路由**

```python
from ai_service import generate_pdf_report
from flask import send_file

@app.route('/api/ai/report/<driver_id>', methods=['GET'])
def get_driver_report(driver_id):
    """
    GET /api/ai/report/<driver_id>
    Returns a PDF driving behavior report for the driver.
    """
    driver = DriverSummary.query.get(driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    summary = {
        'overspeed_count': driver.overspeed_count,
        'fatigue_count': driver.fatigue_count,
        'total_overspeed_sec': driver.total_overspeed_sec,
        'total_neutral_slide_sec': driver.total_neutral_slide_sec,
        'carPlateNumber': driver.carPlateNumber,
    }

    records_db = RawDrivingRecord.query.filter_by(driverID=driver_id).order_by(RawDrivingRecord.Time).all()
    records = [
        {'time': r.Time.isoformat(), 'speed': r.Speed, 'is_overspeed': bool(r.isOverspeed)}
        for r in records_db
    ]
    anomalies = detect_anomalies(records)

    pdf_bytes = generate_pdf_report(driver_id, summary, anomalies)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'driver_{driver_id}_report.pdf'
    )
```

- [ ] **Step 3: 手动测试**

```bash
curl -o /tmp/test_report.pdf http://localhost:5000/api/ai/report/haowei1000008
open /tmp/test_report.pdf
```

预期：PDF 文件打开，显示驾驶员评分、风险等级、异常记录表格。

- [ ] **Step 4: Commit**

```bash
git add "Source code/FullStuck_v2.0(newest)/ai_service.py" "Source code/FullStuck_v2.0(newest)/app.py"
git commit -m "feat(phase2): add PDF report generation endpoint"
```

---

## Task 6: 前端 AI 面板（评分 + 异常 + 自然语言查询 + 报告下载）

**Files:**
- Modify: `Source code/FullStuck_v2.0(newest)/index.html`

- [ ] **Step 1: 在 `<style>` 中追加 AI 面板样式**

在 `index.html` 的 `</style>` 之前插入：

```css
/* ---- AI Panel ---- */
.ai-panel { margin: 24px 0; padding: 20px; background: #f0f4ff; border-radius: 8px; border-left: 4px solid #3b5bdb; }
.ai-panel h2 { margin-top: 0; color: #1e3a8a; }
.score-badge { display: inline-block; padding: 8px 18px; border-radius: 20px; font-size: 22px; font-weight: bold; margin-right: 10px; }
.score-badge.LOW { background: #d3f9d8; color: #1e7e34; }
.score-badge.MEDIUM { background: #fff3cd; color: #856404; }
.score-badge.HIGH { background: #f8d7da; color: #721c24; }
.ai-scores-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
.ai-scores-table th, .ai-scores-table td { border: 1px solid #ddd; padding: 6px 10px; text-align: center; }
.ai-scores-table th { background: #3b5bdb; color: white; }
.nl-query-box { display: flex; gap: 8px; margin: 12px 0; }
.nl-query-box input { flex: 1; padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
.nl-query-result { background: white; border-radius: 6px; padding: 12px; margin-top: 10px; font-family: monospace; font-size: 13px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; }
.anomaly-badge { background: #ffecb3; color: #e65100; padding: 3px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; }
```

- [ ] **Step 2: 在 Summary 表格之后插入 AI 面板 HTML**

在 `</div>` (container 结束) 之前，`<script>` 之前插入：

```html
<!-- AI Analysis Panel -->
<div class="ai-panel">
  <h2>🤖 AI Safety Analysis</h2>

  <!-- All-drivers score overview -->
  <h3>Driver Safety Scores</h3>
  <div id="ai-loading" style="color:#666; font-size:14px;">Loading AI scores...</div>
  <table class="ai-scores-table" id="ai-scores-table" style="display:none;">
    <thead>
      <tr>
        <th>Driver ID</th>
        <th>Plate</th>
        <th>Safety Score</th>
        <th>Risk Level</th>
        <th>Report</th>
      </tr>
    </thead>
    <tbody id="ai-scores-tbody"></tbody>
  </table>

  <!-- Anomalies for selected driver -->
  <h3>Anomaly Detection — <span id="anomaly-driver-label">Select a driver above</span></h3>
  <div id="anomaly-result" style="color:#888; font-size:14px;">Select a driver to run anomaly detection.</div>

  <!-- Natural language query -->
  <h3>💬 Ask in Natural Language</h3>
  <div class="nl-query-box">
    <input type="text" id="nl-input" placeholder="e.g. Which driver had the most fatigue events?" />
    <button id="nl-submit-btn" onclick="submitNLQuery()">Ask AI</button>
  </div>
  <div id="nl-sql-display" style="font-size:12px; color:#555; margin-bottom:4px;"></div>
  <div class="nl-query-result" id="nl-result" style="display:none;"></div>
</div>
```

- [ ] **Step 3: 在 `<script>` 末尾追加 AI 面板 JS**

在 `window.addEventListener('load', loadSummary);` 之后追加：

```javascript
// ========== AI Panel Logic ==========

async function loadAIScores() {
    try {
        const res = await fetch(`${API_BASE}/api/ai/scores`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const scores = await res.json();

        document.getElementById('ai-loading').style.display = 'none';
        const table = document.getElementById('ai-scores-table');
        table.style.display = 'table';
        const tbody = document.getElementById('ai-scores-tbody');
        tbody.innerHTML = '';

        scores.forEach(d => {
            const tr = document.createElement('tr');
            const riskColor = { LOW: '#d3f9d8', MEDIUM: '#fff3cd', HIGH: '#f8d7da' }[d.risk_level] || '#fff';
            tr.innerHTML = `
                <td>${d.driverID}</td>
                <td>${d.carPlateNumber}</td>
                <td><span class="score-badge ${d.risk_level}">${d.score}</span></td>
                <td style="background:${riskColor}; font-weight:bold;">${d.risk_level}</td>
                <td><a href="${API_BASE}/api/ai/report/${d.driverID}" target="_blank">📄 PDF</a></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        document.getElementById('ai-loading').textContent = 'AI scores unavailable: ' + err.message;
        console.error('loadAIScores error:', err);
    }
}

async function loadAnomalies(driverId) {
    document.getElementById('anomaly-driver-label').textContent = driverId;
    document.getElementById('anomaly-result').textContent = 'Detecting anomalies...';
    try {
        const res = await fetch(`${API_BASE}/api/ai/anomalies/${driverId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.anomalies.length === 0) {
            document.getElementById('anomaly-result').textContent = '✅ No anomalies detected for this driver.';
        } else {
            let html = `<span class="anomaly-badge">⚠️ ${data.total} anomalies detected</span><br><br>`;
            html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
            html += '<tr style="background:#eee;"><th>Time</th><th>Speed</th><th>Overspeed</th><th>Score</th></tr>';
            data.anomalies.slice(0, 10).forEach(a => {
                html += `<tr>
                    <td>${a.time.slice(0, 19)}</td>
                    <td style="color:${a.is_overspeed ? 'red' : 'black'}">${a.speed.toFixed(1)} km/h</td>
                    <td>${a.is_overspeed ? '⚠️ Yes' : 'No'}</td>
                    <td>${a.anomaly_score.toFixed(4)}</td>
                </tr>`;
            });
            html += '</table>';
            document.getElementById('anomaly-result').innerHTML = html;
        }
    } catch (err) {
        document.getElementById('anomaly-result').textContent = 'Anomaly detection failed: ' + err.message;
    }
}

async function submitNLQuery() {
    const question = document.getElementById('nl-input').value.trim();
    if (!question) return;

    const btn = document.getElementById('nl-submit-btn');
    btn.textContent = 'Thinking...';
    btn.disabled = true;

    document.getElementById('nl-result').style.display = 'block';
    document.getElementById('nl-result').textContent = '⏳ Generating SQL and querying...';
    document.getElementById('nl-sql-display').textContent = '';

    try {
        const res = await fetch(`${API_BASE}/api/ai/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await res.json();

        if (data.error) {
            document.getElementById('nl-result').textContent = '❌ Error: ' + data.error;
        } else {
            document.getElementById('nl-sql-display').textContent = '🔍 SQL: ' + data.sql;
            document.getElementById('nl-result').textContent = JSON.stringify(data.results, null, 2);
        }
    } catch (err) {
        document.getElementById('nl-result').textContent = 'Query failed: ' + err.message;
    } finally {
        btn.textContent = 'Ask AI';
        btn.disabled = false;
    }
}

// Hook into existing driver select change
const _origDriverChange = onDriverChange;
async function onDriverChange() {
    await _origDriverChange();
    const driverId = document.getElementById('driver-select').value;
    if (driverId) loadAnomalies(driverId);
}

// Load AI scores on page load
window.addEventListener('load', loadAIScores);
```

- [ ] **Step 4: 手动验证前端**

```bash
# 确保后端运行
python app.py

# 浏览器打开 index.html
# 确认：
# 1. AI Safety Scores 表格正常显示，有评分和风险等级
# 2. 选择驾驶员后 Anomaly Detection 显示结果
# 3. 自然语言查询输入框可用（需要 OpenAI key）
# 4. PDF 下载链接可点击
```

- [ ] **Step 5: Commit**

```bash
git add "Source code/FullStuck_v2.0(newest)/index.html"
git commit -m "feat(phase2): add AI analysis panel to frontend"
```

---

## Task 7: 最终验证 & Push

- [ ] **Step 1: 运行全部测试**

```bash
cd "Source code/FullStuck_v2.0(newest)"
python -m pytest tests/ -v
```

预期：所有测试通过

- [ ] **Step 2: 启动服务端到端验证**

```bash
python app.py
# 测试所有 AI 接口
curl http://localhost:5000/api/ai/scores
curl http://localhost:5000/api/ai/score/haowei1000008
curl http://localhost:5000/api/ai/anomalies/haowei1000008
curl -o /tmp/report.pdf http://localhost:5000/api/ai/report/haowei1000008
curl -X POST http://localhost:5000/api/ai/query -H "Content-Type: application/json" -d '{"question":"top 3 drivers by overspeed count"}'
```

- [ ] **Step 3: 更新 README.md — 新增 Phase 2 完成状态**

在 `README.md` 的 Phase 2 plan 区域将 `- [ ]` 改为 `- [x]` for 已完成项。

- [ ] **Step 4: Push feature branch & 创建 PR**

```bash
git push origin feature/phase2-ai-analytics
gh pr create --title "feat: Phase 2 AI-Powered Analytics" \
  --body "Add AI analytics: driver safety scoring, anomaly detection (IsolationForest), NL-to-SQL queries (Vanna.ai), PDF report generation"
```

---

## 依赖关系图

```
Task 1 (依赖安装)
    └── Task 2 (ai_service.py 基础)
            ├── Task 3 (评分+异常 API)
            ├── Task 4 (NL→SQL)
            └── Task 5 (PDF 报告)
                    └── Task 6 (前端面板)
                            └── Task 7 (验证+PR)
```

---

## 风险与注意事项

| 风险 | 说明 | 缓解方案 |
|------|------|---------|
| OpenAI API Key | NL→SQL 和 Vanna 均需要 key | `.env` 管理，无 key 时该功能返回 503 |
| Vanna 冷启动慢 | 首次 init 需要连接 DB + 加载 embedding | 懒加载 + 缓存单例 |
| IsolationForest 数据量少 | <10 条记录无法检测 | 已加 `if len(records) < 10: return []` 守卫 |
| 前端 CORS | `index.html` 直接用 `file://` 打开时 | Flask-CORS 已配置，无问题 |
