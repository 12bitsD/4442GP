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
