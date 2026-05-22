# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blood Bank Management System — a Flask web application demonstrating DevOps practices (Git, Docker, Jenkins CI/CD). Core features: donor registration, blood inventory tracking (8 blood types), hospital management, blood request workflow, and a real-time dashboard.

## Development Commands

**Start the full stack (Flask + MySQL):**
```
docker-compose up --build
```
- Flask app: http://localhost:5000
- MySQL: localhost:3307 (host port mapped to avoid conflict with local 3306)

**Run tests locally (outside Docker):**
```
cd app
pip install -r requirements.txt
pytest ../tests/ -v
```

**Run a single test file:**
```
cd app
pytest ../tests/test_donors.py -v
```

**Run tests inside Docker (as Jenkins does):**
```
docker-compose run --rm app pytest ../tests/ -v
```

**Rebuild after code changes (hot-reload is enabled via volume mount in dev):**
```
docker-compose up
```

## Architecture

### Application Structure

```
app/
├── __init__.py      # App factory: registers blueprints, dashboard route, search
├── run.py           # Entry point — loads config from FLASK_ENV env var
├── config.py        # DevelopmentConfig / TestingConfig / ProductionConfig
├── utils.py         # Shared helpers (login_required decorator, etc.)
├── models/db.py     # All raw SQL via mysql-connector-python (no ORM)
└── routes/          # One blueprint per domain
    ├── auth.py      # Session-based admin login
    ├── donors.py    # Donor CRUD + eligibility (90-day rule)
    ├── hospitals.py # Hospital registration + listing
    ├── inventory.py # Blood unit tracking + history log
    └── requests.py  # Blood requests with urgency + approve/reject workflow
```

### Key Design Decisions

- **No ORM** — all queries are raw SQL in `models/db.py`. Add queries there; routes call those functions.
- **Blueprint-per-domain** — each domain has its own route file registered in `__init__.py`. Follow this pattern for new features.
- **Config via environment** — `FLASK_ENV` selects the config class. `TestingConfig` sets `BYPASS_LOGIN=True` to skip auth in tests.
- **Database schema** — managed by `db/init.sql` (runs on first MySQL container start). Schema changes go there; there is no migration framework.
- **Test isolation** — tests mock the database via `pytest-mock`; no live DB is needed. See `tests/conftest.py` for fixture patterns.

### CI/CD Pipeline (Jenkinsfile)

Windows agent. Stages: Checkout → Build (Docker image tagged with `BUILD_NUMBER`) → Test (pytest inside container) → Push (Docker Hub, credentials ID: `dockerhub-credentials`) → Deploy (`docker-compose up -d`). Registry: `mohak0039/bloodbank-app`.

### Environment Variables

Set in `docker-compose.yml` for local dev; must be provided externally in production:

| Variable | Purpose |
|---|---|
| `MYSQL_HOST` / `DB_HOST` | Database host |
| `MYSQL_DATABASE` / `DB_NAME` | Database name |
| `MYSQL_USER` / `DB_USER` | DB user |
| `MYSQL_PASSWORD` / `DB_PASSWORD` | DB password |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | App admin credentials |
| `SECRET_KEY` | Flask session secret |
| `FLASK_ENV` | `development` / `testing` / `production` |
