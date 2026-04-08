import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# 司机摘要数据（字段名已改为组员要求）
MOCK_SUMMARY = [
    {
        "driverID": "likun1000003",
        "carPlateNumber": "苏AVM936",
        "overspeed_count": 12,
        "fatigue_count": 3,
        "total_overspeed_sec": 156,
        "total_neutral_slide_sec": 45
    },
    {
        "driverID": "xiexiao1000001",
        "carPlateNumber": "苏AEB132",
        "overspeed_count": 8,
        "fatigue_count": 1,
        "total_overspeed_sec": 98,
        "total_neutral_slide_sec": 22
    },
    {
        "driverID": "hanhui1000002",
        "carPlateNumber": "苏AZI419",
        "overspeed_count": 5,
        "fatigue_count": 2,
        "total_overspeed_sec": 67,
        "total_neutral_slide_sec": 11
    },
    {
        "driverID": "duxu1000009",
        "carPlateNumber": "苏AT75H8",
        "overspeed_count": 15,
        "fatigue_count": 4,
        "total_overspeed_sec": 210,
        "total_neutral_slide_sec": 89
    }
]

def generate_speed_data(driver_id):
    """为指定司机生成最近30秒的速度数据"""
    now = datetime.utcnow()
    data = []
    for i in range(0, 31, 5):
        ts = now - timedelta(seconds=30 - i)
        speed = random.randint(60, 140)
        is_overspeed = speed > 120
        data.append({
            "time": ts.isoformat(),
            "speed": speed,
            "is_overspeed": is_overspeed
        })
    return data

@app.route('/api/summary', methods=['GET'])
def get_summary():
    print("GET /api/summary - returning mock data")
    return jsonify(MOCK_SUMMARY)

@app.route('/api/speed/<driver_id>', methods=['GET'])
def get_speed(driver_id):
    print(f"GET /api/speed/{driver_id}")
    data = generate_speed_data(driver_id)
    return jsonify(data)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)