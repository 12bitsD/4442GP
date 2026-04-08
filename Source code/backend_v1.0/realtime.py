import sqlite3
import datetime
import time
import csv
from pathlib import Path

def main():
    # 连接 SQLite 数据库（如果文件不存在会自动创建）
    conn = sqlite3.connect('driver_behavior.db')
    cursor = conn.cursor()

    # 创建 speed_data 表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS speed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id TEXT NOT NULL,
            speed INTEGER,
            timestamp DATETIME,
            is_overspeed INTEGER
        )
    ''')
    conn.commit()

    # 清空速度表，确保每次运行都是全新数据
    cursor.execute("DELETE FROM speed_data")
    conn.commit()
    print("speed_data table cleared.")

    # 读取原始数据文件
    data_folder = Path('data')
    records = []
    for filepath in data_folder.glob('detail_record_*'):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # 至少需要时间、司机、速度（前8列）
                if len(row) < 8:
                    continue
                try:
                    ts = datetime.datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S')
                    driver_id = row[0]
                    speed = int(row[4]) if row[4].isdigit() else 0
                    # 超速标志（第13列，索引12）
                    overspeed_flag = 0
                    if len(row) > 12 and row[12].isdigit():
                        overspeed_flag = int(row[12])
                    records.append((ts, driver_id, speed, overspeed_flag))
                except (ValueError, IndexError):
                    continue

    if not records:
        print("No records found in data folder.")
        return

    # 按原始时间排序
    records.sort(key=lambda x: x[0])
    first_ts = records[0][0]
    now = datetime.datetime.utcnow()
    time_offset = (now - first_ts).total_seconds()

    prev_ts = first_ts
    for ts, driver_id, speed, overspeed_flag in records:
        # 新时间戳 = 原始时间 + 偏移量
        new_ts = ts + datetime.timedelta(seconds=time_offset)
        # 计算与上一条记录的时间差（原始时间差），用于等待
        delta = (ts - prev_ts).total_seconds()
        if delta > 0:
            time.sleep(delta)
        # 超速判断：原始标志为1 或 速度 > 120
        is_overspeed = bool(overspeed_flag) or (speed > 120)
        cursor.execute(
            "INSERT INTO speed_data (driver_id, speed, timestamp, is_overspeed) VALUES (?, ?, ?, ?)",
            (driver_id, speed, new_ts, is_overspeed)
        )
        conn.commit()
        print(f"Inserted: {driver_id} speed {speed} at {new_ts}, overspeed={is_overspeed}")
        prev_ts = ts

    cursor.close()
    conn.close()
    print("Realtime simulation finished.")


if __name__ == '__main__':
    main()