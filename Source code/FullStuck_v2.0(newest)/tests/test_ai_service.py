"""Tests for ai_service.py - Phase 2 AI Analytics"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_service import compute_driver_score, get_risk_level, detect_anomalies


def test_compute_driver_score_returns_valid_score():
    """Score must be between 0 and 100."""
    sample_summary = {
        "overspeed_count": 10,
        "fatigue_count": 5,
        "total_overspeed_sec": 300,
        "total_neutral_slide_sec": 120,
    }
    score = compute_driver_score(sample_summary)
    assert 0 <= score <= 100, f"Score {score} out of range"


def test_compute_driver_score_perfect_driver():
    """A perfect driver should score 100."""
    perfect = {
        "overspeed_count": 0,
        "fatigue_count": 0,
        "total_overspeed_sec": 0,
        "total_neutral_slide_sec": 0,
    }
    score = compute_driver_score(perfect)
    assert score == 100, f"Expected 100, got {score}"


def test_compute_driver_score_worst_driver():
    """A driver with max violations should score 0."""
    worst = {
        "overspeed_count": 10000,
        "fatigue_count": 10000,
        "total_overspeed_sec": 100000,
        "total_neutral_slide_sec": 10000,
    }
    score = compute_driver_score(worst)
    assert score == 0, f"Expected 0, got {score}"


def test_get_risk_level():
    """Test risk level mapping."""
    assert get_risk_level(85) == "LOW"
    assert get_risk_level(70) == "MEDIUM"
    assert get_risk_level(50) == "HIGH"
    assert get_risk_level(80) == "LOW"  # boundary
    assert get_risk_level(60) == "MEDIUM"  # boundary


def test_detect_anomalies_returns_list():
    """detect_anomalies should return a list."""
    records = [
        {"time": "2017-01-02T16:00:00", "speed": 60.0, "is_overspeed": False},
        {"time": "2017-01-02T16:00:10", "speed": 65.0, "is_overspeed": False},
        {"time": "2017-01-02T16:00:20", "speed": 180.0, "is_overspeed": True},
    ] * 20
    anomalies = detect_anomalies(records)
    assert isinstance(anomalies, list)
    # Verify structure if anomalies found
    for a in anomalies:
        assert "time" in a
        assert "speed" in a
        assert "anomaly_score" in a


def test_detect_anomalies_empty_input():
    """Empty input should return empty list."""
    result = detect_anomalies([])
    assert result == []


def test_detect_anomalies_too_few_records():
    """Less than 10 records should return empty list (guard)."""
    records = [
        {"time": "2017-01-02T16:00:10", "speed": 60.0, "is_overspeed": False},
    ] * 5  # Only 5 records
    result = detect_anomalies(records)
    assert result == []
