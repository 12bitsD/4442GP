import sqlite3
import datetime
import csv
from pathlib import Path

def create_tables(cursor):
    # 创建司机摘要表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS driver_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id TEXT UNIQUE NOT NULL,
            car_plate TEXT NOT NULL,
            overspeed_count INTEGER DEFAULT 0,
            fatigue_count INTEGER DEFAULT 0,
            overspeed_total_time INTEGER DEFAULT 0,
            neutral_slide_total_time INTEGER DEFAULT 0
        )
    ''')
    # 创建速度数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS speed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id TEXT NOT NULL,
            speed INTEGER,
            timestamp DATETIME,
            is_overspeed INTEGER DEFAULT 0
        )
    ''')
    # 创建索引（可选，加速查询）
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_speed_driver_time ON speed_data(driver_id, timestamp)')

def init_database():
    conn = sqlite3.connect('driver_behavior.db')
    cursor = conn.cursor()
    create_tables(cursor)

    # 清空表，以便重新填充（避免重复数据）
    cursor.execute("DELETE FROM driver_summary")
    cursor.execute("DELETE FROM speed_data")
    conn.commit()

    # 存储司机汇总信息
    summary_data = {}
    # 存储所有速度记录（用于插入 speed_data）
    all_speed_records = []

    data_folder = Path('data')
    for filepath in data_folder.glob('detail_record_*'):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 8:
                    continue
                try:
                    ts = datetime.datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S')
                    driver_id = row[0]
                    car_plate = row[1]
                    speed = int(row[4]) if row[4].isdigit() else 0
                    # 超速标志（第13列，索引12），如果没有则默认为0
                    overspeed_flag = 0
                    if len(row) > 12 and row[12].isdigit():
                        overspeed_flag = int(row[12])

                    # 记录速度数据（原样存储，不做时间偏移）
                    all_speed_records.append((ts, driver_id, speed, overspeed_flag))

                    # 更新摘要数据
                    if driver_id not in summary_data:
                        summary_data[driver_id] = {
                            'car_plate': car_plate,
                            'overspeed_count': 0,
                            'fatigue_count': 0,
                            'overspeed_total_time': 0,
                            'neutral_slide_total_time': 0
                        }

                    # 超速累计（如果原始超速标志为1，或速度>120）
                    if overspeed_flag == 1 or speed > 120:
                        summary_data[driver_id]['overspeed_count'] += 1
                        # 超速持续时间：由于文件缺少持续时间列，这里简单增加1秒
                        summary_data[driver_id]['overspeed_total_time'] += 1

                    # 疲劳驾驶和空挡滑行：你的文件可能没有这些列，这里留空，如果你有完整数据可取消注释
                    # if len(row) > 15 and row[15].isdigit() and int(row[15]) == 1:
                    #     summary_data[driver_id]['fatigue_count'] += 1
                    # if len(row) > 10 and row[10].isdigit():
                    #     summary_data[driver_id]['neutral_slide_total_time'] += int(row[10])

                except (ValueError, IndexError):
                    continue

    # 插入司机摘要
    for driver_id, data in summary_data.items():
        cursor.execute('''
            INSERT INTO driver_summary (driver_id, car_plate, overspeed_count, fatigue_count, 
                                        overspeed_total_time, neutral_slide_total_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (driver_id, data['car_plate'], data['overspeed_count'], data['fatigue_count'],
              data['overspeed_total_time'], data['neutral_slide_total_time']))

    # 插入速度数据（保持原始时间）
    for ts, driver_id, speed, overspeed_flag in all_speed_records:
        is_overspeed = 1 if (overspeed_flag == 1 or speed > 120) else 0
        cursor.execute(
            "INSERT INTO speed_data (driver_id, speed, timestamp, is_overspeed) VALUES (?, ?, ?, ?)",
            (driver_id, speed, ts, is_overspeed)
        )

    conn.commit()
    conn.close()
    print(f"Database initialized: {len(summary_data)} drivers, {len(all_speed_records)} speed records.")

if __name__ == '__main__':
    init_database()