# SmartAttend AI — Intelligent Student Attendance Monitoring & Shortage Prediction System

SmartAttend AI is an enterprise-grade, responsive, and predictive educational technology web application built with **Python 3, Flask, SQLAlchemy, SQLite, Bootstrap 5, and Chart.js**.

The system helps academic administrators, faculty members, and students proactively monitor attendance, classify statutory standings, compute the exact minimum number of additional consecutive classes needed to reach 75% attendance, and forecast whether recovery remains mathematically feasible before the semester concludes.

---

## 🌟 Key Features

### 1. Attendance Shortage & Condonable Classification Engine
- **Safe Attendance (`OK`)**: $\ge 75\%$ ($4A \ge 3T$)
- **Condonable Band (`CONDONABLE`)**: $65\% \le P < 75\%$ ($20A \ge 13T \text{ and } 4A < 3T$)
- **Critical Shortage (`SHORTAGE`)**: $< 65\%$ ($20A < 13T$)
- Evaluated via strict integer arithmetic to avoid floating-point inaccuracies.
- Safe zero-conducted handling ($T = 0$) prevents division-by-zero errors.

### 2. Exact Attendance Recovery Engine
- Computes the minimum consecutive future classes $k$ required to attain $\ge 75\%$:
  $$k = \max(0, 3T - 4A)$$
- Verifies mathematically that $\frac{A + k}{T + k} \ge 0.75$.
- Even students in the condonable range are shown the exact $k$ needed to attain safe standing.

### 3. Recovery Feasibility Evaluation
- Evaluates whether recovery is achievable given remaining classes $R$:
  - **On Track (`NOT_REQUIRED`)**: $k = 0$
  - **Recovery Possible (`POSSIBLE`)**: $k \le R$
  - **Recovery Impossible (`IMPOSSIBLE`)**: $k > R$ (alerts faculty/dean to unavoidable shortages).

### 4. Interactive "What-If" Scenario Simulator
- Enables students to project: *"What happens if I attend the next $x$ classes?"*
- Computes $\text{New } \% = \frac{A + x}{T + x + y} \times 100$ without modifying stored semester totals.

### 5. Streaming CSV Processor for Large Datasets
- Processes large CSV datasets row-by-row using Python generators.
- O(U) memory footprint (where $U$ is unique student-course pairs) rather than buffering raw files in RAM.
- **Dual Import Modes**:
  - **Snapshot Mode**: Overwrites stored totals with uploaded numbers to prevent accidental double-counting.
  - **Aggregate Mode**: Increments existing counts with session attendance logs.
- Configurable transactional batch sizes (default: 500 rows) with full invalid-row tracking and reporting.

### 6. Role-Based Access Control (RBAC) & 1-Click Demo Logins
- **Administrator**: College-wide analytics, student and course management, imports, reports.
- **Faculty**: Assigned course management, attendance recording/updating, batch uploads, at-risk rosters.
- **Student**: Personalized attendance profile, progress bars, recovery feasibility, and what-if simulation.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+, Flask 3.1, Flask-SQLAlchemy, SQLAlchemy 2.0, Werkzeug
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3, Chart.js 4.4, Font Awesome 6.5
- **Testing**: Python standard `unittest` library (21 automated unit and route integration tests)

---

## 📂 Project Directory Structure

```text
smartattend/
├── app.py                      # Application entry point & factory
├── config.py                   # Environment & database configuration
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation & user manual
│
├── models/                     # SQLAlchemy ORM Models
│   ├── __init__.py             # Database instance export
│   ├── user.py                 # User authentication & role model
│   ├── student.py              # Student demographics & profile model
│   ├── faculty.py              # Faculty instructors model
│   ├── course.py               # Curriculum courses model
│   ├── enrollment.py           # Student-course associations
│   ├── attendance.py           # Attendance records & evaluation bridge
│   ├── notification.py         # Real-time alert notifications
│   └── import_job.py           # Streaming CSV job execution tracker
│
├── services/                   # Core Business Logic & Calculations
│   ├── recovery_service.py     # Attendance classification & recovery engine
│   ├── attendance_service.py   # Dashboard metrics, KPIs & alert generator
│   ├── report_service.py       # Multi-criteria queries & CSV export
│   ├── import_service.py       # Streaming CSV processor & batch transactions
│   └── seed_service.py         # Automatic sample database seeder
│
├── routes/                     # Flask HTTP Blueprints & RBAC
│   ├── auth_routes.py          # Login, logout, demo logins & role decorators
│   ├── dashboard_routes.py     # Analytics console & Chart.js API
│   ├── student_routes.py       # Student CRUD, profile & What-If simulation API
│   ├── course_routes.py        # Course CRUD & faculty assignments
│   ├── attendance_routes.py    # Attendance console, single-entry & CSV uploads
│   └── report_routes.py        # 6 report presets, CSV export & notifications
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Responsive shell, navy sidebar & top navbar
│   ├── login.html              # Login portal with 1-click demo access
│   ├── dashboard.html          # Executive dashboard with 8 KPIs & 4 Chart.js charts
│   ├── students.html           # Student management directory
│   ├── courses.html            # Course & curriculum management
│   ├── attendance.html         # Attendance console & batch import
│   ├── student_profile.html    # Student attendance profile & simulator
│   ├── reports.html            # Multi-criteria reporting & print view
│   ├── notifications.html      # Notifications & alert center
│   ├── 404.html                # Friendly 404 error page
│   ├── 403.html                # Friendly 403 forbidden page
│   └── 500.html                # Friendly 500 server error page
│
├── static/
│   ├── css/
│   │   └── style.css           # Premium SaaS styling & print styles
│   └── js/
│       ├── dashboard.js        # Chart.js initialization & live feeds
│       └── attendance.js       # Live input preview & What-If simulator AJAX
│
├── data/                       # Sample CSV files & templates
│   ├── attendance_template.csv # Empty header template for uploads
│   └── sample_attendance.csv   # Pre-configured dataset for immediate testing
│
└── tests/                      # Automated Test Suite
    ├── test_recovery.py        # 11 boundary & formula mathematical unit tests
    ├── test_attendance.py      # App seeding, CSV import & validation tests
    └── test_live_routes.py     # Full integration tests for endpoints
```

---

## ⚡ Quick Start & Execution Instructions

### 1. Open Terminal in the Project Directory
```powershell
cd "C:\Users\V CHETAN\.gemini\antigravity\scratch\smartattend"
```

### 2. (Optional) Create and Activate Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Automated Test Suite
Execute the 21 test cases verifying all required mathematical boundary cases:
```powershell
python -m unittest discover -s tests
```
*Expected output: `Ran 21 tests in ...s - OK`*

### 5. Launch the Web Application
```powershell
python app.py
```

### 6. Open in Browser
Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Demo Login Credentials

The application automatically seeds realistic sample users and attendance records on its first boot. You can sign in using standard credentials or the **1-Click Demo Login** buttons on `/login`:

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Institutional dashboard, course & student management, CSV uploads, college-wide reports. |
| **Faculty Member** | `faculty` | `faculty123` | Assigned subjects, entering/updating attendance, viewing at-risk rosters. |
| **Student (Rahul Verma / S1)** | `student` | `student123` | Personal attendance profile, course standings, What-If scenario simulations. |

---

## 📐 Mathematical Recovery Formulation

Let:
- $A = \text{number of classes attended}$
- $T = \text{total classes conducted}$
- $R = \text{classes remaining in the semester}$
- $k = \text{minimum consecutive future classes that must be attended}$

To satisfy the statutory benchmark of $75\%$ attendance:
$$\frac{A + k}{T + k} \ge \frac{3}{4}$$

Cross-multiplying (for $T + k > 0$):
$$4(A + k) \ge 3(T + k)$$
$$4A + 4k \ge 3T + 3k$$
$$k \ge 3T - 4A$$

Since $k$ must be non-negative:
$$k = \max(0, 3T - 4A)$$

### Test Case Verification:
- **Case 1**: $A=40, T=50 \implies P=80\% \implies \text{OK}$
- **Case 2**: $A=36, T=50 \implies P=72\% \implies \text{CONDONABLE}$
- **Case 3**: $A=32, T=50 \implies P=64\% \implies \text{SHORTAGE}$
- **Case 4**: $A=30, T=50 \implies P=60\% \implies k = 3(50) - 4(30) = 30 \implies \text{SHORTAGE}$
  - Verification: $\frac{30 + 30}{50 + 30} = \frac{60}{80} = 75\%$
- **Case 5**: $A=45, T=60 \implies P=75\% \implies k = 0 \implies \text{OK}$
- **Case 6**: $A=65, T=100 \implies P=65\% \implies \text{CONDONABLE}$
- **Case 7**: $A=0, T=0 \implies \text{No classes conducted yet}$ (safe handling, no zero division)
- **Case 8**: $A=55, T=50 \implies \text{Validation error}$ ($A > T$)
- **Case 9**: $k=30, R=20 \implies \text{IMPOSSIBLE}$ ($k > R$)
- **Case 10**: $k=30, R=40 \implies \text{POSSIBLE}$ ($k \le R$)

---

## 📥 Sample CSV Import Format

Download the template directly from the navigation bar or use the following structure:

```csv
StudentID,CourseID,Attended,Total,RemainingClasses
S1,CS101,40,50,20
S1,CS102,30,50,40
S2,CS101,36,50,10
S3,CS101,45,50,20
S4,EC201,45,60,25
```

### Import Modes:
1. **Snapshot Mode (Default)**: Overwrites current totals with uploaded values. Use when exporting master totals from an LMS or external attendance ledger.
2. **Aggregate Mode**: Adds attended and total counts to existing database records. Use when uploading incremental attendance logs.

---

## 📄 License & Attribution
Developed for the **SmartAttend AI** project. Built with Python, Flask, and SQLAlchemy.
