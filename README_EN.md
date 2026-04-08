# Driver Behavior Monitoring System

🌐 [中文版本](README.md)

## Project Overview

A web-based real-time driving behavior monitoring and data analysis system for detecting and recording dangerous driving behaviors including speeding, fatigue driving, and neutral sliding.

**Tech Stack**: Python Flask + MySQL + Vanilla JavaScript + Chart.js

---

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Speed Monitoring** | Dynamic display of driver speed changes with auto-play carousel |
| **Speeding Detection** | Automatic detection of speeding (>120 km/h) with real-time alerts |
| **Fatigue Driving Detection** | Identify prolonged continuous driving behavior |
| **Neutral Sliding Detection** | Monitor neutral sliding time and frequency |
| **Data Visualization** | Speed curve charts using Chart.js with red markers for speeding points |
| **Pagination** | Date filtering and paginated historical data browsing |
| **Driver Summary** | Statistics on dangerous behavior counts and durations per driver |

---

## Architecture

### Backend
- **Framework**: Flask 2.3.3
- **ORM**: Flask-SQLAlchemy 3.0.5
- **Database**: MySQL + PyMySQL driver
- **CORS**: Flask-CORS

### Frontend
- **Charts**: Chart.js (CDN)
- **Styling**: Vanilla CSS
- **Interaction**: Vanilla JavaScript (ES6+)

### Data Model

```sql
-- Raw driving records table
raw_driving_records:
  - driverID (Driver ID)
  - carPlateNumber (License plate)
  - Speed (Speed km/h)
  - Time (Timestamp)
  - isOverspeed (Speeding flag)
  - isFatigueDriving (Fatigue flag)
  - overspeedTime (Speeding duration in seconds)
  - neutralSlideTime (Neutral slide duration in seconds)

-- Driver behavior summary table
driver_behavior_summary:
  - driverID (Driver ID)
  - carPlateNumber (License plate)
  - overspeed_count (Speeding count)
  - fatigue_count (Fatigue driving count)
  - total_overspeed_sec (Total speeding duration)
  - total_neutral_slide_sec (Total neutral slide duration)
```

---

## API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/summary` | GET | Get all driver summaries | - |
| `/api/speed/<driver_id>` | GET | Get driver speed records | `page`, `page_size`, `date` |
| `/api/driver_dates/<driver_id>` | GET | Get dates with records for driver | - |
| `/api/health` | GET | Health check | - |

---

## Quick Start

### Requirements
- Python 3.8+
- MySQL 5.7+

### Install Dependencies

```bash
cd "Source code/FullStuck_v2.0(newest)"
pip install -r requirements.txt
```

### Database Setup

1. Create MySQL database `driver_behavior`
2. Update database config in `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/driver_behavior?charset=utf8mb4'
```

3. Import data:

```bash
mysql -u root -p driver_behavior < setup_raw_data.sql
mysql -u root -p driver_behavior < summary_results.sql
```

### Run the Server

```bash
python app.py
```

Server starts at `http://localhost:5000`.

### Access Frontend

Open `index.html` directly in your browser to access the monitoring interface.

---

## Project Structure

```
Source code/
├── FullStuck_v2.0(newest)/    # Latest complete version
│   ├── app.py                  # Flask backend main program
│   ├── index.html              # Frontend monitoring page
│   ├── requirements.txt        # Python dependencies
│   ├── setup_raw_data.sql      # Raw data initialization
│   └── summary_results.sql     # Summary data initialization
├── backend_v1.0/               # Early version
└── Dataset (clean)/            # Dataset processing scripts

Google drive dataset/           # Original dataset
├── detail-records/             # Detailed driving record files
└── 2026-COMP4442-Project-Dataset.pdf

2026_COMP4442_Group_Project.pdf # Course project requirements
Report.docx                     # Project report
Presentation&Demostration.pptx  # Presentation
```

---

## Data Source

This project uses the COMP4442 course driving behavior dataset, containing GPS trip records from 10 drivers in January 2017.

**Sample Drivers**: zengpeng1000000, xiexiao1000001, hanhui1000002, likun1000003, shenxian1000004, panxian1000005, xiezhi1000006, zouan1000007, haowei1000008, duxu1000009

---

## Future Development Roadmap

### Phase 1: Multi-Tenant User System

**Goal**: Support multiple organizations/companies to independently manage their driver data

**Core Features**:
- [ ] Tenant registration and isolation
- [ ] Role-based access control (RBAC)
  - Super Admin: Global data management
  - Tenant Admin: Manage drivers under their tenant
  - Regular User: View authorized data
- [ ] Row-level security (RLS)
- [ ] JWT authentication and session management

**Technical Approach**:
- Add tenants and users tables
- Add tenant_id field to all business tables
- Use Flask-JWT-Extended for authentication
- Middleware to auto-filter current tenant data

### Phase 2: AI-Powered Analytics

**Goal**: Leverage AI models to deeply analyze driving behavior and provide intelligent insights

**Core Features**:
- [ ] Driving behavior scoring model
  - Historical data-based driving habit profiling
  - Risk level assessment (Low/Medium/High)
- [ ] Anomaly detection
  - Cluster analysis to identify abnormal driving patterns
  - Time-series prediction for early warning of potential dangers
- [ ] Natural language queries
  - Users can ask questions in Chinese/English
  - AI auto-generates SQL queries and returns results
- [ ] Intelligent report generation
  - Auto-generate weekly/monthly driving behavior analysis reports
  - Visual charts + text interpretation

**Technical Approach**:
- Integrate OpenAI/Claude API or local LLM
- Use scikit-learn/pandas for data mining
- Build driving behavior feature engineering
- Optional: Train dedicated driving behavior evaluation model

---

## Contributors

COMP4442 Course Project Team

---

## License

This project is a coursework assignment for educational purposes only.
