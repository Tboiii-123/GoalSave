# GoalSave API 💰🎯

**GoalSave** is a secure, production-ready goal-based savings REST API built with Django and Django REST Framework.

It enables users to create and manage personal and shared savings goals, securely fund their wallets through Paystack, allocate funds toward their goals, invite members to collaborate on shared goals, track contributions and savings progress, request withdrawals, and monitor transactions through a complete wallet and ledger system. The API also includes JWT authentication, role-based access control, rate limiting, AI-powered financial features, API documentation with Swagger/OpenAPI, and a background-ready architecture for notifications and asynchronous tasks.

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

### Shared Savings Goals
* Invite users to collaborate on savings goals
* Email notifications for goal invitations
* In-app notification indicators for pending invitations
* View and manage goal invitations
* Accept goal invitations
* Decline goal invitations
* Goal membership and role management
* Support for owner, contributor, and viewer roles
* Invitation status tracking

## Notifications
* Email notifications for goal invitations
* Notification indicators for incoming invitations
* Invitation status updates when invitations are accepted or declined

## Background Tasks
* Celery integration for asynchronous task processing
* Redis message broker integration (where configured)
* Background processing for supported tasks, including email notifications


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


# Withdrwal flow

```text
User
   │
   ▼
POST /withdrawals/request/
   │
   ▼
GoalWithdrawal
Status = PENDING

────────────────────────────

Admin Dashboard
   │
   ▼
View Pending Withdrawals
   │
   ▼
Transfer money manually
   │
   ▼
Click Approve
   │
   ▼
transaction.atomic()
   │
   ├── Lock Withdrawal
   ├── Lock Goal
   ├── Lock Wallet
   ├── Verify Balance
   ├── Deduct Goal Balance
   ├── Create Ledger Entry
   ├── Mark SUCCESS
   └── Save processed_at
```
---


# AI Financial service LLm Integration


```text
                   GOAL AI
                      │
          ┌───────────┴───────────┐
          │                       │
       RETRIEVAL             CALCULATION
          │                       │
          ▼                       ▼
   Database Data          Python Backend Logic
          │                       │
          ├── Goal                ├── Remaining
          ├── Wallet              ├── Progress
          └── Fundings            ├── Weekly Target
                                  ├── Monthly Target
                                  └── Saving Pace
                       │
                       ▼
                  AI CONTEXT
                       │
                       ▼
                    GROQ LLM
                       │
                       ▼
                 AI RESPONSE
```
---



# Tech Stack

* Python - Backend programming language
* Django - framework
* Django REST Framework -  REST API development
* PostgreSQL - Relational database
* Simple JWT — JWT-based authentication
* Paystack API -  Payment processing
* Docker (planned)
* Redis -  Caching
* Celery (planned)
* drf-spectacular -  OpenAPI schema and Swagger API documentation      
* Python Logging -  Application logging and error monitoring 
* Groq API — LLM integration and AI-powered features


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


### Shared Goals

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/goals/<id>/invite/` | Invite member by email |
| GET | `/api/goals/<id>/members/` | List goal members |
| DELETE | `/api/goals/<id>/members/<member_id>/` | Remove a member |
| POST | `/api/goals/<id>/leave/` | Leave shared goal |
| GET | `/api/goals/<id>/contributions/` | View contribution history |
| GET | `/api/goals/<id>/activities/` | View activity feed |

---

### Goal Invitations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/goals/invitations/` | List my pending invitations |
| POST | `/api/goals/invitations/<token>/accept/` | Accept invitation |
| POST | `/api/goals/invitations/<token>/decline/` | Decline invitation |

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
| GET    | `/api/admin/ledger/`                  | Get all ledger entry |
| GET    | `admin/ledger/user/<int:user_id>/`  | Get all ledger by user        |
| GET    | `admin/ledger/<int:pk>/`             | Get ledger by single detail       |

---

## Analytics

| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| GET    | `/api/analytics/goal/summary/`      | Get all ledger entry |
| GET    | `/api/analytics/goals/?period=2m`   | Get all goals savings by preiod  eg period=2 month  |
| GET    | `api/analytics/goals/top/`          | Get the top goal savings     |

---


## Notifications

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/notifications/` | Get the authenticated user's notifications. Supports `unread`, `limit`, and `offset` query parameters. |
| GET | `/api/notifications/unread-count/` | Get the number of unread notifications. |
| PATCH | `/api/notifications/read-all/` | Mark all the authenticated user's notifications as read. |
| PATCH | `/api/notifications/{notification_id}/read/` | Mark a specific notification as read. |
| DELETE | `/api/notifications/{notification_id}/` | Delete a specific notification. |



---


## Swagger doc


| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| GET    | `/api/docs`                  | Get Swagger doc View |


---

## Smart AI with Groq


| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| POST   | `/api/goal/ai/plan-goal/`           | Generate a structured savings goal plan from a natural-language prompt |
| POST   | `/api/goal/goals/goal_id/ai/`        | Generate a structured savings goal plan from a natural-language prompt for personal goal |

api/goal/goals/2/ai/



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


## How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.com/Tboiii-123/GoalSave.git
cd GoalSave
```

### 2. Configure Environment Variables

Create a `.env` file in the project root and add the required environment variables.

Use `.env.example` as a reference if available.

### 3. Build and Start the Application

Run the following command to build the Docker images and start the application services:

```bash
docker compose up --build
```

This starts the services defined in `docker-compose.yml`, including the Django application, PostgreSQL database, Redis, and Celery worker, if configured.

### 4. Access the Application

Once the services are running, open:

- **API:** http://localhost:8000/
- **API Documentation (Swagger):** http://localhost:8000/api/docs/
- **API Schema:** http://localhost:8000/api/schema/

*The URLs depend on your `docker-compose.yml` and URL configuration.*

### 5. Run Database Migrations Manually (If Needed)

If migrations are not applied automatically when the container starts, run:

```bash
docker compose exec web python manage.py migrate
```

Replace `web` with the Django service name defined in your `docker-compose.yml` if different.

### 6. Stop the Application

Press `Ctrl + C`, or run:

```bash
docker compose down
```

To stop the containers and remove the containers and default network while **preserving database data in named volumes**, use the command above. To remove the volumes as well, use:

```bash
docker compose down -v
```

**Warning:** `docker compose down -v` deletes the Compose-managed database volumes and can permanently remove your local database data.
---

# Future Improvements

* Scheduled savings
* Email notifications  --done
* Redis caching   --done
* Celery background tasks  --done
* Docker deployment        --done
* CI/CD pipeline
* Unit and integration tests      --processing

---

# License

This project is for educational and portfolio purposes.
