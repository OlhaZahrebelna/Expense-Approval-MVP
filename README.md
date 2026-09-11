# Expense-Approval-MVP


A full-stack MVP for managing employee expense reimbursement requests inside an organization.

The application allows employees to submit expense claims, automatically routes each claim to the appropriate approver based on the expense category, and allows approvers to review, approve, or reject requests.

An AI assistant provides an additional consistency check for approvers without making the final approval decision.

## Live Demo

**Streamlit application:**
https://expense-approval-mvp.streamlit.app

**FastAPI backend:**
https://expense-approval-mvp.onrender.com

**Interactive API documentation:**
https://expense-approval-mvp.onrender.com/docs

## Key Features

### Employee workflow

Employees can:

* authenticate using email and password;
* create a new expense request;
* provide:

  * amount in USD;
  * expense category;
  * description;
  * expense date;
  * payment details;
* view all submitted expenses;
* track the current request status;
* open expense details;
* withdraw a request while it is still pending.

Supported statuses:

`pending` → `approved` / `rejected` / `withdrawn`

### Approver workflow

Approvers can:

* authenticate using the same application;
* access only expenses assigned to them;
* view their approval queue;
* inspect expense details;
* receive an AI-generated consistency analysis;
* approve pending expenses;
* reject expenses with a mandatory rejection comment.

A user may have both **Employee** and **Approver** roles.

## Automatic Approval Routing

Each expense category is connected to a specific approver.

The current MVP contains five categories:

| Category                 | Approver         |
| ------------------------ | ---------------- |
| Office                   | Finance Approver |
| Software / Subscriptions | Finance Approver |
| Other                    | Finance Approver |
| Travel                   | Travel Approver  |
| Client Entertainment     | Travel Approver  |

When an employee submits an expense, the backend automatically assigns the correct approver based on the selected category.

## AI-Assisted Review

The application integrates OpenAI to help approvers identify potentially inconsistent claims.

For example:

```text
Category: Office
Description: Flight ticket to London
```

The AI assistant can flag this expense because the description looks more consistent with the **Travel** category.

The AI response contains:

```json
{
  "summary": "Short analysis of the expense",
  "flagged": true,
  "reason": "Explanation of the detected inconsistency"
}
```

The AI does **not** approve or reject expenses. The final decision always remains with the assigned approver.

AI analysis is also implemented as a non-blocking enhancement: if the AI service is unavailable, the expense can still be reviewed and processed normally.

## Architecture

```text
┌──────────────────────┐
│   Streamlit Frontend │
│                      │
│ Login                │
│ My Expenses          │
│ New Expense          │
│ Approval Queue       │
│ Expense Details      │
└──────────┬───────────┘
           │ HTTP / REST
           ▼
┌──────────────────────┐
│    FastAPI Backend   │
│                      │
│ Authentication       │
│ Expense workflow     │
│ Authorization        │
│ Category routing     │
└──────┬────────┬──────┘
       │        │
       │        └──────────────► OpenAI API
       │                         Expense analysis
       ▼
┌──────────────────────┐
│      SQLAlchemy      │
│       SQLite         │
│                      │
│ Users                │
│ Categories           │
│ Expenses             │
└──────────────────────┘
```

## Tech Stack

**Backend**

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* SQLite
* JWT authentication
* Passlib / bcrypt

**Frontend**

* Streamlit
* Requests

**AI**

* OpenAI API
* GPT-5 mini

**Testing**

* pytest
* FastAPI TestClient

**Deployment**

* Render — FastAPI backend
* Streamlit Community Cloud — frontend

## Project Structure

```text
Expense-Approval-MVP/
│
├── app/
│   ├── __init__.py
│   ├── ai_service.py
│   ├── auth.py
│   ├── database.py
│   ├── expenses.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── seed.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_expenses.py
│
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## API Overview

### Authentication

| Method | Endpoint         | Description                  |
| ------ | ---------------- | ---------------------------- |
| POST   | `/auth/register` | Register a new employee      |
| POST   | `/auth/login`    | Authenticate and receive JWT |
| GET    | `/auth/me`       | Get the current user         |

### Expenses

| Method | Endpoint                  | Description                  |
| ------ | ------------------------- | ---------------------------- |
| POST   | `/expenses`               | Create an expense            |
| GET    | `/expenses/categories`    | Get available categories     |
| GET    | `/expenses/my`            | Get employee's expenses      |
| GET    | `/expenses/queue`         | Get approver's pending queue |
| GET    | `/expenses/{id}`          | Get expense details          |
| POST   | `/expenses/{id}/approve`  | Approve an expense           |
| POST   | `/expenses/{id}/reject`   | Reject an expense            |
| POST   | `/expenses/{id}/withdraw` | Withdraw a pending expense   |

### System

| Method | Endpoint  | Description          |
| ------ | --------- | -------------------- |
| GET    | `/health` | Backend health check |

## Authentication and Authorization

The backend uses JWT Bearer authentication.

After login, the API returns an access token:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Protected requests use:

```text
Authorization: Bearer <token>
```

Authorization rules are enforced on the backend rather than relying only on the UI.

Examples:

* only employees can create expenses;
* only approvers can access the approval queue;
* approvers can only process expenses assigned to them;
* employees cannot access another employee's expense;
* only the expense owner can withdraw a request;
* only pending expenses can be approved, rejected, or withdrawn.

## Demo / Seed Data

Seed data creates two approver accounts.

### Finance Approver

```text
Email: finance@test.com
Password: Finance12345
```

Responsible for:

* Office
* Software / Subscriptions
* Other

### Travel Approver

```text
Email: travel@test.com
Password: Travel12345
```

Responsible for:

* Travel
* Client Entertainment

Both seeded users have both employee and approver permissions, so they can also create expense requests.

For local development, seed the database with:

```bash
python3 -m app.seed
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/OlhaZahrebelna/Expense-Approval-MVP.git
cd Expense-Approval-MVP
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` based on `.env.example`:

```env
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OPENAI_API_KEY=your-openai-api-key
```

Do not commit the real `.env` file or API keys to GitHub.

### 5. Seed the database

```bash
python3 -m app.seed
```

### 6. Start FastAPI

```bash
python3 -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Start Streamlit

In another terminal:

```bash
streamlit run streamlit_app.py
```

The frontend uses:

```env
API_URL=http://127.0.0.1:8000
```

by default.

For deployment, set `API_URL` to the deployed FastAPI service.

## Tests

Run the automated test suite with:

```bash
python3 -m pytest -v
```

The tests cover core business and authorization scenarios including:

* successful and unsuccessful authentication;
* expense creation;
* automatic approver assignment;
* approver queue access;
* approval workflow;
* rejection with mandatory comment;
* prevention of approval by the wrong approver;
* withdrawal of pending expenses;
* prevention of withdrawal after approval;
* protection against unauthorized expense access;
* invalid repeated status transitions;
* graceful handling of AI service failure.

## Business Rules

The main workflow follows several explicit rules:

1. Every expense starts with `pending` status.
2. Expense categories determine the assigned approver automatically.
3. Only the assigned approver may approve or reject a claim.
4. Rejection requires a comment.
5. Only pending claims may be approved or rejected.
6. Employees may withdraw only their own pending claims.
7. Other employees cannot access someone else's request.
8. AI analysis is advisory and never makes the final decision.
9. AI failure must not interrupt the core approval workflow.

## MVP Scope

The project intentionally focuses on the core expense approval workflow.

Current MVP limitations include:

* SQLite instead of a production database;
* no email or Slack notifications;
* no receipt/file attachments;
* no currency conversion;
* no audit log;
* no password reset flow;
* basic role management;
* AI analysis is performed on demand rather than asynchronously.

These would be natural next steps for a production version.

## Possible Next Steps

Potential improvements include:

* PostgreSQL migration;
* database migrations with Alembic;
* receipt upload and storage;
* structured audit trail;
* email/Slack notifications;
* configurable approval rules;
* multiple approval levels;
* organization-level user management;
* CI/CD pipeline;
* Docker deployment;
* structured AI output validation;
* rate limiting and monitoring.

