"""AI Service Module - Phase 2 AI Analytics for Driver Behavior Monitoring"""

import os
from typing import List, Dict, Any

# Score calculation weights
SCORE_WEIGHTS = {
    "overspeed_count": 0.30,
    "fatigue_count": 0.30,
    "total_overspeed_sec": 0.25,
    "total_neutral_slide_sec": 0.15,
}

# Reference max values for normalization
SCORE_REFS = {
    "overspeed_count": 3600,
    "fatigue_count": 4400,
    "total_overspeed_sec": 34000,
    "total_neutral_slide_sec": 3100,
}


def compute_driver_score(summary: Dict[str, Any]) -> int:
    """Compute a 0-100 safety score for a driver.

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
        ratio = min(value / ref, 1.0)
        penalty += weight * ratio

    score = round((1.0 - penalty) * 100)
    return max(0, min(100, score))


def get_risk_level(score: int) -> str:
    """Map score to risk label."""
    if score >= 80:
        return "LOW"
    elif score >= 60:
        return "MEDIUM"
    else:
        return "HIGH"


def detect_anomalies(
    records: List[Dict[str, Any]], contamination: float = 0.05
) -> List[Dict[str, Any]]:
    """Detect anomalous driving records using IsolationForest.

    Args:
        records: list of dicts with keys: time, speed, is_overspeed
        contamination: expected fraction of anomalies (default 5%)
    Returns:
        list of anomalous records with 'anomaly_score' added
    """
    if len(records) < 10:
        return []

    try:
        import numpy as np
        import pandas as pd
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return []

    df = pd.DataFrame(records)
    df["is_overspeed_int"] = df["is_overspeed"].astype(int)

    feature_cols = ["speed", "is_overspeed_int"]
    X = df[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=100,
        max_samples=min(256, len(X)),
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    df["anomaly_score"] = model.decision_function(X_scaled)
    df["is_anomaly"] = model.predict(X_scaled)

    anomalies = df[df["is_anomaly"] == -1].copy()
    result = []
    for _, row in anomalies.iterrows():
        record = {
            "time": row["time"],
            "speed": float(row["speed"]),
            "is_overspeed": bool(row["is_overspeed"]),
            "anomaly_score": float(row["anomaly_score"]),
        }
        result.append(record)

    return sorted(result, key=lambda x: x["anomaly_score"])


# ---------------------------------------------------------------------------
# Natural Language to SQL (Vanna.ai)
# ---------------------------------------------------------------------------

_vanna_instance = None


def _get_vanna():
    """Lazy-init Vanna instance (singleton)."""
    global _vanna_instance
    if _vanna_instance is not None:
        return _vanna_instance

    try:
        from vanna.remote import VannaDefault

        api_key = os.getenv("VANNA_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("VANNA_MODEL", "default")

        if not api_key:
            raise RuntimeError("VANNA_API_KEY or OPENAI_API_KEY not set")

        vn = VannaDefault(model=model, api_key=api_key)

        db_host = os.getenv("DB_HOST", "localhost")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "123456")
        db_name = os.getenv("DB_NAME", "driver_behavior")

        vn.connect_to_mysql(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=int(os.getenv("DB_PORT", "3306")),
        )

        # Train with schema DDL
        vn.train(
            ddl="""
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
        """
        )

        _vanna_instance = vn
        return vn

    except Exception as e:
        raise RuntimeError(f"Failed to initialize Vanna: {e}")


def nl_to_sql_query(question: str) -> Dict[str, Any]:
    """Convert a natural language question to SQL and execute it.

    Args:
        question: e.g. "Which drivers had more than 3000 overspeed events?"
    Returns:
        dict with keys: sql (str), results (list of dicts), error (str or None)
    """
    # Check if API key is configured
    api_key = os.getenv("VANNA_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "sql": None,
            "results": [],
            "error": "AI service not configured. Please set OPENAI_API_KEY or VANNA_API_KEY environment variable.",
        }

    try:
        vn = _get_vanna()
        sql = vn.generate_sql(question=question)
        df = vn.run_sql(sql=sql)

        results = df.to_dict(orient="records") if df is not None else []
        # Convert non-serializable types
        for row in results:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
                elif isinstance(v, (int,)):
                    row[k] = int(v)
                elif isinstance(v, (float,)):
                    row[k] = float(v)

        return {"sql": sql, "results": results, "error": None}

    except Exception as e:
        return {"sql": None, "results": [], "error": str(e)}


# ---------------------------------------------------------------------------
# PDF Report Generation (ReportLab)
# ---------------------------------------------------------------------------


def generate_pdf_report(
    driver_id: str, summary: Dict[str, Any], anomalies: List[Dict[str, Any]]
) -> bytes:
    """Generate a PDF driving behavior report for a driver.

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
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib import colors
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"], fontSize=18, spaceAfter=12
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontSize=13, spaceAfter=8
    )

    elements = []

    score = compute_driver_score(summary)
    risk = get_risk_level(score)
    elements.append(Paragraph("Driver Behavior Analysis Report", title_style))
    elements.append(
        Paragraph(
            f"Driver: {driver_id} | Plate: {summary.get('carPlateNumber', 'N/A')} | Safety Score: {score}/100 ({risk})",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.3 * inch))

    # Summary Table
    elements.append(Paragraph("Behavior Summary", section_style))
    risk_color = {"LOW": colors.green, "MEDIUM": colors.orange, "HIGH": colors.red}[
        risk
    ]

    summary_data = [
        ["Metric", "Value"],
        ["Safety Score", f"{score} / 100"],
        ["Risk Level", risk],
        ["Overspeed Incidents", str(summary.get("overspeed_count", 0))],
        ["Fatigue Driving Incidents", str(summary.get("fatigue_count", 0))],
        ["Total Overspeed Duration", f"{summary.get('total_overspeed_sec', 0)} sec"],
        [
            "Total Neutral Slide Duration",
            f"{summary.get('total_neutral_slide_sec', 0)} sec",
        ],
        ["Anomalies Detected", str(len(anomalies))],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ("BACKGROUND", (1, 2), (1, 2), risk_color),
                ("TEXTCOLOR", (1, 2), (1, 2), colors.white),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Anomaly Table
    if anomalies:
        elements.append(
            Paragraph(
                f"Top Anomalies (showing up to 20 of {len(anomalies)})", section_style
            )
        )
        anomaly_data = [["Timestamp", "Speed (km/h)", "Overspeed", "Anomaly Score"]]
        for a in anomalies[:20]:
            anomaly_data.append(
                [
                    str(a.get("time", ""))[:19],
                    f"{a.get('speed', 0):.1f}",
                    "Yes" if a.get("is_overspeed") else "No",
                    f"{a.get('anomaly_score', 0):.4f}",
                ]
            )
        anomaly_table = Table(
            anomaly_data, colWidths=[2.2 * inch, 1.2 * inch, 1 * inch, 1.3 * inch]
        )
        anomaly_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightyellow],
                    ),
                ]
            )
        )
        elements.append(anomaly_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
