# GoalSave API 💰🎯

A secure, goal-based savings REST API built with Django and Django REST Framework.

GoalSave allows users to create personal savings goals, fund their wallet through Paystack, and allocate funds toward financial goals while tracking their savings progress.

> 🚧 **Project Status:** Active Development

---

# Features

### Authentication

* User registration
* JWT login & refresh tokens
* Logout
* User profile
* List users (admin/testing)

### Wallet

* Automatic wallet creation
* Wallet balance
* Wallet transaction history
* Atomic wallet updates

### Goal Management

* Create savings goals
* List all user goals
* Retrieve a goal
* Pause a goal
* Resume a goal
* Complete a goal
* Delete a goal (subject to business rules)

### Payments

* Deposit initialization using Paystack
* Secure Paystack webhook
* Deposit verification
* Deposit history
* Idempotent payment processing
* Signature verification
* Atomic wallet crediting

---

# Payment Flow

```text
User initiates deposit
        │
        ▼
Paystack Payment Page
        │
        ▼
Payment Successful
        │
        ▼
Paystack sends Webhook
        │
        ▼
Verify Signature
        │
        ▼
Check Idempotency
        │
        ▼
Lock Wallet (Database Transaction)
        │
        ▼
Credit Wallet
        │
        ▼
Create Wallet Transaction
        │
        ▼
Mark Deposit Successful
```

---

# Tech Stack

* Python
* Django
* Django REST Framework
* PostgreSQL
* JWT Authentication
* Paystack API
* Docker (planned)
* Redis (planned)
* Celery (planned)

---

# API Endpoints

## Authentication

| Method | Endpoint                          | Description              |
| ------ | --------------------------------- | ------------------------ |
| POST   | `/api/account/auth/register/`     | Register a new user      |
| POST   | `/api/account/auth/login/`        | Login                    |
| POST   | `/api/account/token/refresh/`     | Refresh JWT token        |
| POST   | `/api/account/auth/logout/`       | Logout                   |
| GET    | `/api/account/auth/profile/`      | Get current user profile |
| GET    | `/api/account/auth/get_all_user/` | Get users                |

---

## Wallet

| Method | Endpoint                    | Description                |
| ------ | --------------------------- | -------------------------- |
| GET    | `/api/wallet/`              | Retrieve wallet            |
| GET    | `/api/wallet/transactions/` | Wallet transaction history |

---

## Goals

| Method | Endpoint                   | Description   |
| ------ | -------------------------- | ------------- |
| POST   | `/api/goal/`               | Create goal   |
| GET    | `/api/goal/`               | List goals    |
| GET    | `/api/goal/<id>/`          | Retrieve goal |
| DELETE | `/api/goal/<id>/`          | Delete goal   |
| PATCH  | `/api/goal/<id>/pause/`    | Pause goal    |
| PATCH  | `/api/goal/<id>/resume/`   | Resume goal   |
| PATCH  | `/api/goal/<id>/complete/` | Complete goal |

---

## Payments

| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| POST   | `/api/payments/deposit/`            | Initialize Paystack deposit |
| GET    | `/api/payments/deposits/`           | Deposit history             |
| GET    | `/api/payments/verify/<reference>/` | Verify deposit              |
| POST   | `/api/payments/webhook/`            | Paystack webhook            |

---

## Ledger

| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| GET  | `/api/admin/ledger/`            | Get all ledger entry |

| GET    | `admin/ledger/user/<int:user_id>/` | Get all ledger by user              |
| GET   | `admin/ledger/<int:pk>`            | Get ledger by single detail       |

---

# Example Create Goal Request

```json
POST /api/goal/

{
    "name": "Buy a Laptop",
    "description": "Save for a MacBook Pro",
    "target_amount": "450000.00",
    "target_date": "2026-12-31"
}
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/Tboiii-123/GoalSave.git
```

Move into the project

```bash
cd goalsave
```

Create a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run migrations

```bash
python manage.py migrate
```

Start the server

```bash
python manage.py runserver
```

---

# Future Improvements

* Goal funding from wallet
* Scheduled savings
* Goal analytics
* Email notifications
* Redis caching
* Celery background tasks
* Docker deployment
* CI/CD pipeline
* API documentation (Swagger/OpenAPI)
* Unit and integration tests

---

# License

This project is for educational and portfolio purposes.
