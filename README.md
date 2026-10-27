# Agentic AI-Based Intelligent College Admission System

A focused academic FastAPI project for Bangalore University. It provides a student admission journey powered by a grounded admission agent: it captures student information, applies database eligibility rules, ranks courses, recommends Bangalore University programmes, accepts an application, simulates an application-fee payment, and exposes an administrator dashboard.

> All course, fee, and eligibility records seeded by the application are **demo academic data**. They are not official Bangalore University admissions information.

## Quick Start with Docker (Recommended)

Run the full stack (FastAPI web app + MySQL database) with a single command:

```bash
docker compose up -d --build
```

Access the application at [http://localhost:8000](http://localhost:8000). See [DEPLOYMENT.md](DEPLOYMENT.md) for full cloud and VPS deployment options (Render, Railway, Nginx).

## What is implemented

- Student registration, bcrypt password hashing, JWT login/logout, and editable academic profile.
- Three role portals on the home page: Student, College Faculty, and Administrator.
- Faculty registration with 10-digit phone validation, college selection, pending approval, and approval/rejection by an administrator. Approved faculty can view only their college's applied-student list and release a merit list ranked by applicant percentage.
- Separate browser pages for the Student Portal (`student.html`), College Faculty Portal (`college.html`), Admin Portal (`admin.html`), Student Admission Process (`student-admission.html`), and Student Selection Status (`student-status.html`). Logged-in users see their name and a logout action in the top-right navigation.
- The home page is a landing page; the portal cards are on the separate `portals.html` page, opened through the **Open portals** button.
- The demo catalog is intentionally limited to one institution: **Bangalore University**, Jnanabharathi, Bengaluru.
- Faculty merit release supports a selected course and a top-N count (for example, top 10 or top 20). Student selection status is fetched from the released merit list.
- Agentic Admission Assistant: natural-language fact extraction; missing-information questions; persisted profile data; eligibility, course and college tool flow.
- OpenAI function/tool calling for extraction when `OPENAI_API_KEY` is configured. The local extractor and rule engine remain fully functional without an API key, allowing a reproducible academic demonstration.
- Database-grounded eligibility engine — it never makes up requirements.
- Explainable course scoring based on eligibility, degree, percentage, interest keywords and budget.
- College recommendations based on offered course, location and budget.
- Admission applications, unique application numbers, pending status, simulated payment and confirmation.
- Eligibility-led application flow: students enter qualification, percentage and interests; eligible course details are analyzed before an application can be submitted.
- Student document upload and administrator verification for marks cards, ID proof, certificates and photos (PDF/image files up to 10 MB).
- Application status timeline with stored history for submitted, reviewed, approved, rejected and merit-list updates.
- Database-backed in-app notifications for registration, document review, payment, faculty approval, application updates and merit-list release.
- Email congratulations sent to every selected student's registered email when faculty releases a merit list (SMTP configured through `.env`).
- Admin dashboard with totals, application review, and pending/approved/rejected updates.
- Course and college CRUD API endpoints for the administrator.

## Architecture

```text
Bootstrap + JavaScript browser interface
                |
          FastAPI REST API
     /          |          \
Admission Agent Eligibility   Admission + Payment
     \          |          /
          MySQL + SQLAlchemy
```

The agent flow is: student message → fact extraction → missing-details check → stored-rule eligibility → course scoring → college matching → explained result. The agent uses data from the backend and does not autonomously approve an application.

## Folder structure

```text
college_admission_system/
├── backend/                 # FastAPI API, ORM models, rules and AI agent
│   ├── app/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/                # Bootstrap HTML, CSS and browser JavaScript
├── database/schema.sql      # Optional manual MySQL schema
├── Dockerfile               # Container build definition
├── docker-compose.yml       # Multi-service stack (MySQL + Web App)
├── render.yaml              # Render Cloud deployment blueprint
├── Procfile                 # PaaS process configuration
├── DEPLOYMENT.md            # Comprehensive production deployment guide
├── run_project.bat
└── README.md
```

## Manual Setup (Windows / Python 3.12)

1. Install and start MySQL Server.
2. Run `database/schema.sql` in MySQL Workbench, or allow the API to create tables after you create the `college_admission` database.
3. In PowerShell, run:

```powershell
cd college_admission_system\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

4. Edit `backend/.env`; set the MySQL password in `DATABASE_URL`, create a strong `SECRET_KEY`, and optionally add `OPENAI_API_KEY`. To send merit-list emails, also copy the `SMTP_*` values from `.env.example`.
5. Start the project:

```powershell
python run.py
```

Or double-click `run_project.bat` from the repository root.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
