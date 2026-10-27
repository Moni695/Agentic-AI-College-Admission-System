# Deployment Guide - Intelligent College Admission System

This guide outlines several options to deploy the **Intelligent College Admission System** (FastAPI + Bootstrap/JS + MySQL/PostgreSQL):

1. [Option 1: Docker Compose (Recommended for Local / VPS / Dedicated Server)](#option-1-docker-compose-recommended)
2. [Option 2: Cloud PaaS - Render.com (1-Click Blueprint)](#option-2-cloud-paas---rendercom)
3. [Option 3: Cloud PaaS - Railway.app](#option-3-cloud-paas---railwayapp)
4. [Option 4: Traditional Linux VPS (Ubuntu + Nginx + Systemd)](#option-4-traditional-linux-vps-ubuntu--nginx)
5. [Option 5: Local Windows / macOS Development Setup](#option-5-local-development-setup)
6. [Environment Variables Reference](#environment-variables-reference)
7. [Default Seed Credentials](#default-seed-credentials)

---

## Architecture Overview

```text
       Browser Client (Bootstrap + JS)
                      │
               HTTP Port 80 / 8000
                      ▼
        FastAPI App Server (Uvicorn)
         ├── /api/... (REST Endpoints)
         ├── /docs (Interactive Swagger UI)
         └── / (Mounted Static Frontend)
                      │
               SQLAlchemy 2.0
                      ▼
         Database (MySQL 8 / PostgreSQL)
```

---

## Option 1: Docker Compose (Recommended)

Docker Compose containerizes both the **FastAPI web application** and the **MySQL 8.0 database**, ensuring persistent data storage and automatic database initialization.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) installed.

### 1. Launch the Services
From this directory:

```bash
docker compose up -d --build
```

### 2. Verify Container Health
```bash
docker compose ps
```
Both `admission_mysql` and `admission_web` should show state `Up (healthy)`.

### 3. Access the Application
- **Main Portal**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Stopping or Resetting
```bash
# Stop containers
docker compose down

# Stop and purge database volumes (fresh start)
docker compose down -v
```

---

## Option 2: Cloud PaaS - Render.com

Render offers automated deployment directly connected to your GitHub repository.

### 1. Push Code to GitHub
Ensure the changes are pushed to your GitHub repository:
```bash
git add .
git commit -m "Add production deployment configurations"
git push origin main
```

### 2. Deploy with Blueprint (`render.yaml`)
1. Log in to [Render.com](https://render.com).
2. Go to the **Blueprints** tab and click **New Blueprint Instance**.
3. Connect your repository (`Moni695/Agentic-AI-College-Admission-System`).
4. Render will parse [`render.yaml`](./render.yaml) and automatically create:
   - A **Web Service** (Docker container running FastAPI & the static frontend).
   - A **Managed Database** (PostgreSQL database automatically linked via `DATABASE_URL`).
5. (Optional) Set `OPENAI_API_KEY` in the Render Environment Variables tab if you want OpenAI tool-assisted chat extraction.
6. Click **Apply**.

Your application will be live at `https://<your-service-name>.onrender.com`.

---

## Option 3: Cloud PaaS - Railway.app

1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. Add a Database service:
   - Click **+ New** → **Database** → **Add MySQL** (or **PostgreSQL**).
5. In your web service settings:
   - In **Variables**, add:
     - `DATABASE_URL`: Reference the connection string from the database service (`${{MySQL.DATABASE_URL}}`).
     - `SECRET_KEY`: Set to any secure random string.
     - `PORT`: Railway injects this automatically.
6. Railway automatically uses [`Dockerfile`](./Dockerfile) or [`Procfile`](./Procfile) to start the app.

---

## Option 4: Traditional Linux VPS (Ubuntu + Nginx)

### 1. System Setup
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv mysql-server nginx git
```

### 2. Configure MySQL Database
```sql
sudo mysql
CREATE DATABASE college_admission CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admission_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON college_admission.* TO 'admission_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Clone and Setup Environment
```bash
git clone https://github.com/Moni695/Agentic-AI-College-Admission-System.git /var/www/admission_system
cd /var/www/admission_system/college_admission_system/backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env` and set:
```ini
DATABASE_URL=mysql+pymysql://admission_user:StrongPassword123!@localhost:3306/college_admission
SECRET_KEY=generate_a_secure_random_key_here
```

### 4. Setup Systemd Service
Create `/etc/systemd/system/admission.service`:
```ini
[Unit]
Description=Bangalore University Admission System
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/admission_system/college_admission_system/backend
Environment="PATH=/var/www/admission_system/college_admission_system/backend/.venv/bin"
ExecStart=/var/www/admission_system/college_admission_system/backend/.venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo chown -R www-data:www-data /var/www/admission_system
sudo systemctl daemon-reload
sudo systemctl enable admission
sudo systemctl start admission
```

### 5. Setup Nginx Reverse Proxy
Create `/etc/nginx/sites-available/admission`:
```nginx
server {
    listen 80;
    server_name your-domain.com; # Or server public IP

    client_max_body_size 15M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/admission /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Option 5: Local Development Setup

### Windows
1. Double click `run_project.bat` in the repository root or project directory.
2. The batch script sets up `.venv`, installs requirements, copies `.env.example` if needed, and starts the server on [http://localhost:8000](http://localhost:8000).

---

## Environment Variables Reference

| Variable | Description | Default / Example | Required |
|---|---|---|---|
| `DATABASE_URL` | SQLAlchemy database connection URI | `mysql+pymysql://root:root@localhost:3306/college_admission` | Yes |
| `SECRET_KEY` | JWT token signature secret | `change-this-in-production` | Yes |
| `HOST` | Host address to bind the HTTP server | `0.0.0.0` | No |
| `PORT` | Port number to bind the HTTP server | `8000` | No |
| `OPENAI_API_KEY` | OpenAI API key for intelligent extraction | `sk-...` | Optional |
| `OPENAI_MODEL` | OpenAI Model name | `gpt-4o-mini` | No |
| `APPLICATION_FEE` | Simulated application fee in INR | `500.0` | No |
| `SMTP_HOST` | Outgoing SMTP host for merit emails | `smtp.gmail.com` | Optional |
| `SMTP_PORT` | Outgoing SMTP port | `587` | Optional |
| `SMTP_USERNAME` | SMTP username / email address | `your-email@gmail.com` | Optional |
| `SMTP_PASSWORD` | SMTP password / App Password | `your-app-password` | Optional |
| `SMTP_FROM_EMAIL` | Display sender address | `admissions@bcu-demo.edu` | Optional |
| `SMTP_USE_TLS` | Enable TLS for SMTP connection | `true` | No |

---

## Default Seed Credentials

The database seeds an administrator account upon initial startup:

- **Role**: System Administrator
- **Email**: `admin@bcu-demo.edu`
- **Password**: `Admin@123`
- **Dashboard URL**: [http://localhost:8000/admin.html](http://localhost:8000/admin.html)
