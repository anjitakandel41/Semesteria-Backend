# Semesteria Hiring Dashboard Backend

## 1. Project overview
This project implements a small hiring dashboard backend in Django REST Framework for a demo internship assessment. It supports candidate and recruiter roles, job browsing, job applications, stage updates, history logs, and role-based authorization enforced on the backend.

## 2. Technology stack
- Python
- Django
- Django REST Framework
- PostgreSQL-ready configuration
- JWT authentication via djangorestframework-simplejwt
- SQLite fallback for local test execution
- pytest/Django test runner for automated validation

## 3. Backend architecture
The backend is organized into the following apps:
- accounts: custom user model and JWT login logic
- jobs: job records and listing API
- applications: application workflow, stage transitions, and application history
- seed: safe demo-data seeding command

Business logic is centralized in `applications/services.py` so the views remain thin and enforce request handling instead of business rules.

## 4. Setup instructions
1. Create a virtual environment.
2. Install dependencies.
3. Create a `.env` file from `.env.example`.
4. Run migrations.
5. Seed demo data.
6. Start the Django development server.

On Windows PowerShell:
```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_data
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

After starting the server, open `http://127.0.0.1:8000/admin/` and sign in with the superuser created above. The admin includes users, jobs, applications, and application history. History entries are view-only audit records.

## 5. Environment variables
See `.env.example` for defaults. The checked-in example selects SQLite so a fresh local copy works without a database server. To use Neon:
1. Create a Neon project and database.
2. In Neon, copy the **pooled** connection string and keep it private.
3. Put that string in `DATABASE_URL` in your local `.env`; set `USE_SQLITE_FOR_TESTS=0`.
4. Run `.\.venv\Scripts\python.exe manage.py migrate` to create the schema in Neon.
5. Optionally seed demo records with `.\.venv\Scripts\python.exe manage.py seed_data`.

The backend reads standard `postgresql://` or `postgres://` URLs and requires SSL by default. A `sslmode` query parameter already present in the Neon URL is preserved. Do not commit `.env` or expose `DATABASE_URL` in browser code. The legacy `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` settings remain supported.

## 6. Database setup
The project uses Django ORM with PostgreSQL support. The `db.sqlite3` file is not needed when `USE_SQLITE_FOR_TESTS=0`; Django connects to the Neon database in `DATABASE_URL` instead. Leave the flag at `1` only when you intentionally want a local SQLite database.

## 7. Connecting a Next.js frontend
This repository contains the Django API, not a Next.js frontend. Keep Neon credentials in Django's `.env`; Next.js should call the Django API over HTTP rather than connect directly to the database.

For local development, Django runs at `http://127.0.0.1:8000` and API endpoints are under `/api/`. For example, Next.js can request the jobs list from `http://127.0.0.1:8000/api/jobs/`. Set `CORS_ALLOWED_ORIGINS` in the Django `.env` to the exact frontend origin (for local Next.js, `http://localhost:3000`; for deployment, your HTTPS frontend origin). Authenticated endpoints require a JWT in the `Authorization: Bearer <token>` header.

In the Next.js project, store the API base URL (not the database URL) in `.env.local`, for example `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api`, then call `${process.env.NEXT_PUBLIC_API_BASE_URL}/jobs/` from the frontend. Never use a `NEXT_PUBLIC_` variable for secrets.

### Admin and Swagger testing
Open `http://127.0.0.1:8000/swagger/` to browse and try API operations. POST/PATCH operations show their input fields:
- `POST /api/auth/login/`: `username`, `password`
- `POST /api/applications/`: `job_id` (apply as a candidate to an open job)
- `PATCH /api/applications/<id>/stage/`: `stage`, `version`

First use the login operation with a seeded account or a user created in admin. Copy its `access` token, click Swagger's **Authorize** button, and enter `Bearer <access-token>`. Then try the protected endpoints. Create and edit jobs in Django admin; the jobs API currently exposes listing only.

## 8. Migration commands
```bash
python manage.py makemigrations
python manage.py migrate
```

## 9. Seed command
```bash
python manage.py seed_data
```
The seed command can be run repeatedly; it creates demo users, seven open IT positions, a closed example job, and sample applications and history records.

## 10. Demo credentials
Use these demo accounts for local testing:
- candidate1 / Candidate@123
- recruiter1 / Recruiter@123
- recruiter2 / Recruiter@456

## 11. API endpoint list
### Authentication
- POST /api/auth/login/

### Jobs
- GET /api/jobs/

### Candidate endpoints
- GET /api/applications/my/
- POST /api/applications/
- GET /api/applications/<id>/
- POST /api/applications/<id>/withdraw/

### Recruiter endpoints
- GET /api/recruiter/applications/
- PATCH /api/applications/<id>/stage/
- GET /api/applications/<id>/history/

## 12. Authentication
JWT bearer tokens are used. After login, attach the token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

## 13. Candidate workflow
Candidates can:
- log in
- view open jobs
- apply to open jobs
- view only their own applications
- withdraw eligible applications

## 14. Recruiter workflow
Recruiters can:
- log in
- view jobs assigned to them
- view applications for assigned jobs
- filter applications by job and stage
- view application details
- update application stages
- inspect application history

## 15. Stage transition rules
The system enforces a strict progression model:
- APPLIED -> SHORTLISTED -> INTERVIEWED -> HIRED
- APPLIED, SHORTLISTED, and INTERVIEWED can also transition to REJECTED
- APPLIED, SHORTLISTED, and INTERVIEWED can transition to WITHDRAWN
- HIRED, REJECTED, and WITHDRAWN are terminal
- no skipped stages are allowed

## 16. Withdrawal policy
Candidates may withdraw an application only when it is in APPLIED, SHORTLISTED, or INTERVIEWED. A successful withdrawal records a history event and marks the application as WITHDRAWN.

## 17. Authorization rules
- Candidate users can only access their own applications.
- Recruiters can only access applications tied to jobs assigned to them.
- Duplicate application creation is blocked at both the business layer and the database constraint layer.
- Stage updates require a matching version value.

## 18. Concurrency handling
The application includes a `version` field and stage changes are protected by optimistic concurrency control. If the application was changed by another user, the endpoint responds with HTTP 409 and forces the client to refresh.

## 19. History/audit design
Every successful stage update or withdrawal writes an `ApplicationHistory` record containing:
- application id
- actor
- timestamp
- previous_stage
- new_stage

The history creation is performed in the same database transaction as the stage update to preserve consistency.

## 20. Automated tests
The project contains automated API tests covering:
- candidate application flow
- closed-job rejection
- duplicate prevention
- applicant access restrictions
- recruiter access restrictions
- stage transition validation
- history creation
- stale-version concurrency checks

## 21. Test results
The final validation result for the assessment API test suite is:
```bash
python manage.py test applications.tests --verbosity 1
```
Result: all tests passed.

## 22. Manual verification performed
Manual checks were performed for:
- JWT login flow
- application creation and duplicate rejection
- recruiter-only stage updates
- history and stale version behavior

## 23. Known limitations
- This project is intentionally a local assessment backend with synthetic data only.
- It does not implement user registration, password reset, admin dashboards, or external integrations.

## 24. Unfinished work, if any
No unfinished work is required for the assessment scope.

## 25. Time breakdown
- Project scaffold and config: 20%
- Models and permissions: 25%
- Services and business rules: 25%
- Tests and validation: 20%
- Documentation: 10%

## 26. Next steps
- Add production-grade deployment settings
- Move from SQLite to PostgreSQL in staging/production
- Add CI pipeline and linting

## 27. Brief AI-use note
This project was scaffolded and iterated with AI-assisted coding in the VS Code environment, then validated with Django's test runner.
