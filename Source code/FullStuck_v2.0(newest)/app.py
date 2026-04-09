from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
from sqlalchemy import func

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:123456@localhost/driver_behavior?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class DriverSummary(db.Model):
    __tablename__ = "driver_behavior_summary"
    driverID = db.Column(db.String(50), primary_key=True)
    carPlateNumber = db.Column(db.String(20))
    overspeed_count = db.Column(db.Integer)
    fatigue_count = db.Column(db.Integer)
    total_overspeed_sec = db.Column(db.Integer)
    total_neutral_slide_sec = db.Column(db.Integer)


class RawDrivingRecord(db.Model):
    __tablename__ = "raw_driving_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driverID = db.Column(db.String(50))
    carPlateNumber = db.Column(db.String(20))
    Speed = db.Column(db.Float)
    Time = db.Column(db.DateTime)
    isOverspeed = db.Column(db.Integer)
    isFatigueDriving = db.Column(db.Integer)
    overspeedTime = db.Column(db.Integer)
    neutralSlideTime = db.Column(db.Integer)


@app.route("/api/summary", methods=["GET"])
def get_summary():
    drivers = DriverSummary.query.all()
    result = [
        {
            "driverID": d.driverID,
            "carPlateNumber": d.carPlateNumber,
            "overspeed_count": d.overspeed_count,
            "fatigue_count": d.fatigue_count,
            "total_overspeed_sec": d.total_overspeed_sec,
            "total_neutral_slide_sec": d.total_neutral_slide_sec,
        }
        for d in drivers
    ]
    return jsonify(result)


@app.route("/api/speed/<driver_id>", methods=["GET"])
def get_speed(driver_id):
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=30, type=int)
    date_str = request.args.get("date")

    query = RawDrivingRecord.query.filter_by(driverID=driver_id)
    if date_str:
        try:
            # date_str format: YYYY-MM-DD
            start_date = datetime.strptime(date_str, "%Y-%m-%d")
            end_date = start_date.replace(hour=23, minute=59, second=59)
            query = query.filter(RawDrivingRecord.Time.between(start_date, end_date))
        except:
            pass

    # 按时间正序排序，分页
    total = query.count()
    records = (
        query.order_by(RawDrivingRecord.Time)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for r in records:
        is_overspeed = (r.isOverspeed == 1) or (r.Speed > 120)
        result.append(
            {"time": r.Time.isoformat(), "speed": r.Speed, "is_overspeed": is_overspeed}
        )
    return jsonify(
        {"records": result, "total": total, "page": page, "page_size": page_size}
    )


@app.route("/api/driver_dates/<driver_id>", methods=["GET"])
def get_driver_dates(driver_id):
    # 获取该司机所有有记录的日期（按日期排序，去重）
    dates = (
        db.session.query(func.date(RawDrivingRecord.Time).label("record_date"))
        .filter(RawDrivingRecord.driverID == driver_id)
        .distinct()
        .order_by("record_date")
        .all()
    )
    # 返回格式为 YYYY-MM-DD 的列表
    result = [d.record_date.isoformat() for d in dates]
    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Phase 2: AI Analytics Routes
# ---------------------------------------------------------------------------

from ai_service import compute_driver_score, get_risk_level, detect_anomalies


@app.route("/api/ai/score/<driver_id>", methods=["GET"])
def get_ai_score(driver_id):
    """Return AI-computed safety score for a driver."""
    driver = DriverSummary.query.get(driver_id)
    if not driver:
        return jsonify({"error": "Driver not found"}), 404

    summary = {
        "overspeed_count": driver.overspeed_count,
        "fatigue_count": driver.fatigue_count,
        "total_overspeed_sec": driver.total_overspeed_sec,
        "total_neutral_slide_sec": driver.total_neutral_slide_sec,
    }
    score = compute_driver_score(summary)
    return jsonify(
        {
            "driverID": driver_id,
            "score": score,
            "risk_level": get_risk_level(score),
            "breakdown": summary,
        }
    )


@app.route("/api/ai/scores", methods=["GET"])
def get_all_ai_scores():
    """Return AI safety scores for all drivers."""
    drivers = DriverSummary.query.all()
    result = []
    for d in drivers:
        summary = {
            "overspeed_count": d.overspeed_count,
            "fatigue_count": d.fatigue_count,
            "total_overspeed_sec": d.total_overspeed_sec,
            "total_neutral_slide_sec": d.total_neutral_slide_sec,
        }
        score = compute_driver_score(summary)
        result.append(
            {
                "driverID": d.driverID,
                "carPlateNumber": d.carPlateNumber,
                "score": score,
                "risk_level": get_risk_level(score),
            }
        )
    return jsonify(sorted(result, key=lambda x: x["score"]))


@app.route("/api/ai/anomalies/<driver_id>", methods=["GET"])
def get_anomalies(driver_id):
    """Return anomalous driving records for a driver using IsolationForest."""
    date_str = request.args.get("date")
    query = RawDrivingRecord.query.filter_by(driverID=driver_id)
    if date_str:
        try:
            start = datetime.strptime(date_str, "%Y-%m-%d")
            end = start.replace(hour=23, minute=59, second=59)
            query = query.filter(RawDrivingRecord.Time.between(start, end))
        except ValueError:
            pass

    records_db = query.order_by(RawDrivingRecord.Time).all()
    records = [
        {
            "time": r.Time.isoformat(),
            "speed": r.Speed,
            "is_overspeed": bool(r.isOverspeed),
        }
        for r in records_db
    ]

    anomalies = detect_anomalies(records)
    return jsonify(
        {"driverID": driver_id, "anomalies": anomalies, "total": len(anomalies)}
    )


@app.route("/api/ai/query", methods=["POST"])
def ai_natural_language_query():
    """POST /api/ai/query - Natural language to SQL query."""
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Missing field: question"}), 400

    question = data["question"].strip()
    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    from ai_service import nl_to_sql_query

    result = nl_to_sql_query(question)
    status = 500 if result["error"] else 200
    return jsonify(result), status


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
