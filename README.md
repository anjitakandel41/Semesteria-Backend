# Semesteria Hiring Dashboard API

A Django REST Framework backend for an internship hiring dashboard assignment. The API supports candidate and recruiter accounts, job listings, job applications, role-based access, application-stage changes, optimistic concurrency checks, and application history.

## Technology

- Python 3.13 or newer
- Django and Django REST Framework
- PostgreSQL on Neon for the shared application database
- PostgreSQL as the only supported database backend
- JWT authentication with Simple JWT
- Django Jazzmin for the admin interface
- drf-yasg for Swagger and ReDoc API documentation
- `uv` for Python dependencies and commands

## Requirements

- Windows, macOS, or Linux
- Python 3.13+
- `uv`
- A Neon PostgreSQL database for the recommended setup

The project root is the folder containing `pyproject.toml` and `manage.py`. The commands below use Windows PowerShell from that folder.

## Set up the project

Install and lock the project dependencies:

```powershell
uv sync --group dev
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` before running Django:

1. Set `DATABASE_URL` to the pooled connection URL copied from your Neon project. Keep this URL private.
2. Replace `DJANGO_SECRET_KEY` with a private random value. You can generate one with:

   ```powershell
   uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. Keep `DJANGO_DEBUG=True` only for local development.
4. Set `ALLOWED_HOSTS` to the host names serving Django. For local development, `localhost,127.0.0.1` is sufficient.
5. Set `CORS_ALLOWED_ORIGINS` to the exact origin of your Next.js app, such as `http://localhost:3000`.

PostgreSQL is the only database configured by this project. The settings parse a `postgresql://` or `postgres://` URL and require SSL by default. Do not commit `.env`, paste the database URL into Swagger, or put it in a `NEXT_PUBLIC_` frontend variable.

## Set up Neon and start Django

Run database migrations, seed the demo records, create an admin login, then start Django:

```powershell
uv run python manage.py check
uv run python manage.py migrate
uv run python manage.py seed_data
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

`migrate` creates the tables in the database selected by `.env`. `seed_data` can be run again safely to add any missing demo records. `createsuperuser` prompts you to create a separate account for Django admin; seeded candidates and recruiters are not admin accounts.

## Admin and demo data

Open [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) and sign in using the superuser credentials created above. The admin lists:

- Users
- Jobs
- Applications
- Application history (read-only audit entries)

The seed command creates four demo accounts, seven open IT positions, one closed job, and six sample applications spanning all application stages. It also creates history records for stage changes. The records are synthetic assignment data.

Seeded API demo logins:

| Role | Username | Password |
| --- | --- | --- |
| Candidate | `candidate1` | `Candidate@123` |
| Candidate | `candidate2` | `Candidate@456` |
| Recruiter | `recruiter1` | `Recruiter@123` |
| Recruiter | `recruiter2` | `Recruiter@456` |

These are demo-only credentials. The seed command resets these four demo passwords when it runs; do not use seeded credentials for a production system.

## Swagger and ReDoc

With Django running, open:

- Swagger UI: [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
- ReDoc: [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

To try protected operations in Swagger:

1. Call `POST /api/auth/login/` with a demo username and password.
2. Copy the returned `access` token.
3. Select **Authorize** and enter `Bearer <access-token>`.
4. Try the candidate or recruiter endpoints using the matching role's demo login.

Swagger request fields include:

- Login: `username`, `password`
- Apply to a job: `job_id`
- Change an application stage: `stage`, `version`

## API endpoints

All API endpoints are prefixed with `/api/`.

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login/` | Public | Obtain access and refresh JWT tokens |
| `GET` | `/api/jobs/` | Candidate or recruiter | List open jobs for candidates; recruiters see all jobs |
| `POST` | `/api/applications/` | Candidate | Apply to an open job using `job_id` |
| `GET` | `/api/applications/my/` | Candidate | List the logged-in candidate's applications |
| `GET` | `/api/applications/<id>/` | Application owner or assigned recruiter | View application details |
| `POST` | `/api/applications/<id>/withdraw/` | Candidate who owns the application | Withdraw an eligible application |
| `GET` | `/api/recruiter/applications/` | Recruiter | List applications for the recruiter's jobs |
| `PATCH` | `/api/applications/<id>/stage/` | Recruiter assigned to the job | Move an application to a valid next stage |
| `GET` | `/api/applications/<id>/history/` | Application owner or assigned recruiter | View application stage history |

The recruiter application list accepts optional `job_id` and `stage` query parameters. Job creation and editing are available in Django admin; the API currently exposes job listing only.

Example request bodies:

```json
{
  "username": "candidate1",
  "password": "Candidate@123"
}
```

```json
{
  "job_id": 1
}
```

```json
{
  "stage": "SHORTLISTED",
  "version": 1
}
```

Send the access token on protected requests:

```http
Authorization: Bearer <access-token>
```

The `version` in a stage update must match the current application version. A stale version returns HTTP `409 Conflict`; refresh the application and retry with its latest version.

## Assignment business rules

- Users have either the candidate or recruiter role.
- Candidates see open jobs, apply to open jobs, and access only their own applications.
- Duplicate applications for the same candidate and job are prevented.
- Recruiters see applications only for jobs assigned to them.
- Valid stage progression is `APPLIED → SHORTLISTED → INTERVIEWED → HIRED`.
- Applications may move from `APPLIED`, `SHORTLISTED`, or `INTERVIEWED` to `REJECTED` or `WITHDRAWN`.
- `HIRED`, `REJECTED`, and `WITHDRAWN` are terminal stages.
- Candidates can withdraw their own applications while they are `APPLIED`, `SHORTLISTED`, or `INTERVIEWED`.
- Successful stage changes and withdrawals are recorded in application history.

## Run tests

```powershell
uv run python manage.py test accounts applications jobs seed --verbosity 1
```

Tests use PostgreSQL and Django creates a temporary test database. Use a dedicated, non-production PostgreSQL database or Neon branch for tests; do not run tests against a database containing data you need to keep. The database role must have permission to create and drop the temporary test database.

## Next.js integration

This repository contains the Django backend, not the Next.js frontend. Keep the Neon connection string in Django's `.env`; Next.js should make HTTP requests to Django rather than connect directly to Neon.

For local Next.js development:

1. Set `CORS_ALLOWED_ORIGINS=http://localhost:3000` in the Django `.env`.
2. In the Next.js project, set `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api` in `.env.local`.
3. Call the API using that base URL. Send `Authorization: Bearer <access-token>` for protected endpoints.

For deployment, set the CORS origin to the exact deployed frontend origin and configure the API URL through the frontend's deployment environment. Never expose database credentials to the browser.

## Project structure

```text
accounts/       Custom user model, roles, JWT login, and permissions
applications/  Application models, workflow, history, and business services
config/         Django settings and top-level URLs
jobs/           Job model and job listing endpoint
seed/           Repeatable demo-data management command
manage.py       Django management entry point
pyproject.toml  Project metadata and dependencies managed by uv
uv.lock         Locked dependency versions
```
