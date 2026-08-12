# Sinevestpremium Backend

The **Sinevestpremium Backend** is the server-side application powering the Sinevestpremium investment platform.

It provides the APIs and backend infrastructure required for user authentication, account management, investment-plan management, deposits, withdrawals, transactions, notifications, and administrative operations.

The backend is designed to provide a secure and scalable API layer that can be consumed by the Sinevestpremium React frontend and other authorized clients.

> **Important:** The investment-plan figures described in this repository are configuration values supplied for the project. They should not be interpreted as guaranteed financial returns. Before deploying a real-money investment service, all products, return representations, payment mechanisms, and regulatory requirements should be reviewed by qualified legal and financial professionals.

---

# Table of Contents

* [Overview](#overview)
* [Core Responsibilities](#core-responsibilities)
* [Investment Plans](#investment-plans)
* [Payment Assets](#payment-assets)
* [Features](#features)
* [Technology Stack](#technology-stack)
* [Project Architecture](#project-architecture)
* [Project Structure](#project-structure)
* [Prerequisites](#prerequisites)
* [Getting Started](#getting-started)
* [Creating the Virtual Environment](#creating-the-virtual-environment)
* [Activating the Virtual Environment](#activating-the-virtual-environment)
* [Installing Dependencies](#installing-dependencies)
* [Environment Variables](#environment-variables)
* [Database Configuration](#database-configuration)
* [Database Migrations](#database-migrations)
* [Creating a Superuser](#creating-a-superuser)
* [Running the Development Server](#running-the-development-server)
* [API Documentation](#api-documentation)
* [Authentication](#authentication)
* [Investment Management](#investment-management)
* [Deposit Management](#deposit-management)
* [Withdrawal Management](#withdrawal-management)
* [Transaction Management](#transaction-management)
* [Security](#security)
* [Production Deployment](#production-deployment)
* [Git Workflow](#git-workflow)
* [Testing](#testing)
* [Troubleshooting](#troubleshooting)
* [Financial and Regulatory Compliance](#financial-and-regulatory-compliance)
* [Disclaimer](#disclaimer)
* [License](#license)

---

# Overview

Sinevestpremium Backend is a REST API built with Django and Django REST Framework.

The backend acts as the central layer between the frontend application, database, authentication system, payment infrastructure, and administrative interface.

The system is responsible for securely processing and managing platform data.

### Main responsibilities

The backend handles:

* User registration
* User authentication
* User profiles
* Account management
* Investment plans
* Investment records
* Deposits
* Withdrawals
* Transactions
* Account balances
* Payment verification
* Notifications
* Administrative management
* API authentication
* Database operations

---

# Core Responsibilities

## Authentication

The backend provides authentication functionality for:

* User registration
* Login
* Logout
* Token authentication
* Token refresh
* Password management
* Account verification

---

## User Management

The backend stores and manages user information including:

* User account
* Personal profile
* Account status
* Verification status
* Investment history
* Transaction history
* Deposit history
* Withdrawal history

Sensitive user information should be protected through appropriate access-control mechanisms.

---

# Investment Plans

The platform currently contains five major investment-plan categories.

## Silver Plan

| Parameter         | Value    |
| ----------------- | -------- |
| Minimum           | $50      |
| Maximum           | $499     |
| Advertised Return | 20%      |
| Duration          | 24 hours |

---

## Gold Plan

| Parameter         | Value       |
| ----------------- | ----------- |
| Minimum           | $500        |
| Maximum           | $999        |
| Advertised Return | 17.5% daily |
| Duration          | 2 days      |

---

## Forex Plan

| Parameter         | Value     |
| ----------------- | --------- |
| Minimum           | $1,000    |
| Maximum           | $1,999    |
| Advertised Return | 20% daily |
| Duration          | 4 days    |

---

## Company Shares

| Parameter         | Value     |
| ----------------- | --------- |
| Minimum           | $2,000    |
| Maximum           | $3,999    |
| Advertised Return | 40% daily |
| Duration          | 3 days    |

---

## Real Estate

| Parameter         | Value     |
| ----------------- | --------- |
| Minimum           | $4,000    |
| Maximum           | Unlimited |
| Advertised Return | 75% daily |
| Duration          | 2 days    |

> **Important:** These advertised returns should be treated as configurable platform data rather than guaranteed financial outcomes. Any public representation of returns should be legally reviewed and accurately substantiated.

---

# Payment Assets

The platform is designed to support cryptocurrency deposits.

Supported assets include:

* Bitcoin (BTC)
* Tether (USDT — TRC20)
* Ethereum (ETH)

The backend should be responsible for validating deposit information received from supported payment infrastructure.

A deposit should not be marked as successful solely because a user submits a transaction hash.

Where applicable, the system should verify:

* Transaction hash
* Blockchain network
* Destination address
* Amount
* Confirmation status
* Transaction timestamp
* Transaction status

---

# Features

## 1. Authentication

* User registration
* Login
* JWT authentication
* Token refresh
* Password hashing
* Password reset
* Account verification
* Account status management

---

## 2. User Dashboard APIs

The backend provides data required by the frontend dashboard.

Possible dashboard information includes:

* Available balance
* Total invested
* Active investments
* Completed investments
* Total deposits
* Total withdrawals
* Recent transactions
* Investment performance
* Account information

---

## 3. Investment Management

Investment functionality includes:

* Investment-plan listing
* Investment-plan details
* Investment creation
* Investment validation
* Investment status
* Investment start date
* Investment end date
* Investment amount
* Investment return calculation
* Investment history

The backend should perform all financial calculations server-side rather than trusting values supplied by the frontend.

---

## 4. Deposit Management

The deposit module manages:

* Deposit requests
* Deposit amount
* Cryptocurrency type
* Deposit address
* Transaction hash
* Deposit status
* Deposit verification
* Deposit timestamps
* Deposit history

Possible deposit states include:

```text
PENDING
PROCESSING
CONFIRMED
FAILED
CANCELLED
```

---

## 5. Withdrawal Management

The withdrawal module manages:

* Withdrawal requests
* Withdrawal amount
* Destination wallet
* Withdrawal status
* Administrative review
* Transaction reference
* Withdrawal history

Possible withdrawal states include:

```text
PENDING
PROCESSING
APPROVED
COMPLETED
REJECTED
CANCELLED
```

Withdrawals should be validated on the backend before being processed.

---

## 6. Transaction Management

The transaction system maintains records of financial activity.

Possible transaction types include:

```text
DEPOSIT
WITHDRAWAL
INVESTMENT
RETURN
FEE
ADJUSTMENT
```

Each transaction should maintain an auditable record containing information such as:

* User
* Transaction type
* Amount
* Currency
* Status
* Reference
* Timestamp
* Related investment
* Related deposit or withdrawal

---

# Technology Stack

The backend is built using modern Python web technologies.

### Backend

* Python
* Django
* Django REST Framework

### Authentication

* Django authentication
* JWT authentication
* Simple JWT

### Database

* PostgreSQL

### API Documentation

* drf-spectacular
* OpenAPI / Swagger

### Configuration

* python-decouple
* Environment variables

### CORS

* django-cors-headers

### Development Tools

* Git
* GitHub
* Virtual environments
* pip

---

# Project Architecture

The backend follows a modular Django architecture.

A typical architecture can look like:

```text
Frontend
   │
   │ HTTP / REST API
   ▼
Django REST Framework
   │
   ├── Authentication
   ├── Users
   ├── Investments
   ├── Deposits
   ├── Withdrawals
   ├── Transactions
   └── Notifications
   │
   ▼
PostgreSQL Database
```

External payment services can communicate with the backend through secure APIs and webhooks.

---

# Project Structure

A typical project structure may look like:

```text
sinevestpremium-backend/
│
├── venv/
│
├── manage.py
│
├── core/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── authentication/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── investments/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── deposits/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── withdrawals/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── transactions/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

The exact structure may differ depending on the current implementation.

---

# Prerequisites

Before running the backend, install:

* Python
* pip
* PostgreSQL
* Git

Check Python:

```powershell
python --version
```

Check pip:

```powershell
pip --version
```

Check Git:

```powershell
git --version
```

---

# Getting Started

Clone the repository:

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate into the project:

```powershell
cd sinevestpremium-backend
```

---

# Creating the Virtual Environment

Create a Python virtual environment:

```powershell
python -m venv venv
```

This creates:

```text
venv/
```

inside the project directory.

---

# Activating the Virtual Environment

## Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

After activation, your terminal should look similar to:

```text
(venv) PS C:\Projects\sinevestpremium-backend>
```

## Windows CMD

```cmd
venv\Scripts\activate
```

## Deactivate

When finished working:

```powershell
deactivate
```

---

# Installing Dependencies

With the virtual environment activated:

```powershell
pip install -r requirements.txt
```

If a `requirements.txt` file has not yet been created, install the core dependencies:

```powershell
pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary python-decouple django-cors-headers drf-spectacular
```

Then generate the requirements file:

```powershell
pip freeze > requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=your-database-url

ALLOWED_HOSTS=localhost,127.0.0.1

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Additional environment variables may be required depending on the payment provider, email service, deployment platform, or other integrations.

### Never commit `.env`

Your `.gitignore` should include:

```gitignore
venv/
__pycache__/
*.pyc
.env
.env.*
!.env.example
db.sqlite3
media/
staticfiles/
```

---

# Database Configuration

The recommended production database is PostgreSQL.

The application can use a database URL such as:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

The exact database configuration depends on your deployment environment.

For local development, you may use PostgreSQL or another development database depending on your project configuration.

---

# Database Migrations

After creating or modifying Django models, create migrations:

```powershell
python manage.py makemigrations
```

Apply migrations:

```powershell
python manage.py migrate
```

Check migration status:

```powershell
python manage.py showmigrations
```

---

# Creating a Superuser

Create an administrator account:

```powershell
python manage.py createsuperuser
```

Follow the prompts:

```text
Username:
Email address:
Password:
Password confirmation:
```

After starting the server, the Django administration interface is normally available at:

```text
http://127.0.0.1:8000/admin/
```

---

# Running the Development Server

Start Django:

```powershell
python manage.py runserver
```

The backend will normally be available at:

```text
http://127.0.0.1:8000/
```

---

# API Documentation

If `drf-spectacular` is configured, the project can expose OpenAPI documentation.

Typical endpoints include:

```text
/api/schema/
/api/docs/
/api/redoc/
```

The exact URLs depend on the project's URL configuration.

The API documentation should provide information about:

* Available endpoints
* Request parameters
* Authentication requirements
* Request bodies
* Response formats
* HTTP status codes

---

# Authentication

The API uses token-based authentication.

A typical authentication flow is:

```text
User
  │
  │ Login
  ▼
Authentication API
  │
  │ Access Token
  ▼
Frontend
  │
  │ Authorization: Bearer <token>
  ▼
Protected API
```

Example authorization header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Access tokens should be treated as sensitive credentials.

---

# Investment Management

Investment endpoints should validate all investment information server-side.

For example:

```text
POST /api/investments/
GET  /api/investments/
GET  /api/investments/<id>/
```

The backend should verify:

* Authenticated user
* Selected investment plan
* Minimum investment
* Maximum investment
* Available balance
* Investment status
* Transaction validity

The frontend should never be trusted to calculate or authorize financial transactions.

---

# Deposit Management

Example API structure:

```text
POST /api/deposits/
GET  /api/deposits/
GET  /api/deposits/<id>/
```

The backend should validate deposit transactions before crediting user balances.

For blockchain payments, transaction verification should preferably be performed through an appropriate blockchain/payment provider.

---

# Withdrawal Management

Example API structure:

```text
POST /api/withdrawals/
GET  /api/withdrawals/
GET  /api/withdrawals/<id>/
```

Before processing a withdrawal, the backend should verify:

* User authentication
* Available balance
* Withdrawal amount
* Destination address
* Account status
* Transaction status
* Required verification
* Applicable withdrawal restrictions

---

# Transaction Management

Example API structure:

```text
GET /api/transactions/
GET /api/transactions/<id>/
```

Transactions should be immutable or carefully audited once finalized.

Financial records should maintain sufficient information to reconstruct the history of an account.

---

# Administrative Management

Django Admin can be used to manage platform data.

Administrators may be able to manage:

* Users
* Investment plans
* Investments
* Deposits
* Withdrawals
* Transactions
* Platform configuration

Administrative permissions should follow the principle of least privilege.

Only authorized administrators should be allowed to approve financial operations.

---

# Security

Because the backend may process financial and personal information, security should be treated as a primary requirement.

Recommended security measures include:

### Authentication Security

* Strong password hashing
* JWT expiration
* Refresh-token security
* Account verification
* Login rate limiting
* Brute-force protection

### API Security

* Authentication on protected endpoints
* Permission classes
* Object-level authorization
* Input validation
* Rate limiting
* Request validation

### Database Security

* Strong database credentials
* Restricted database access
* Encrypted connections where supported
* Regular backups
* Database monitoring

### Environment Security

Never store secrets in source code.

Do not commit:

```text
.env
private keys
API secrets
database passwords
JWT secrets
payment-provider credentials
```

---

# Production Deployment

Before deploying to production:

## 1. Set DEBUG to False

```env
DEBUG=False
```

## 2. Configure allowed hosts

Example:

```env
ALLOWED_HOSTS=api.sinevestpremium.com
```

## 3. Configure HTTPS

The production API should use HTTPS.

Example:

```text
https://api.sinevestpremium.com
```

## 4. Configure the production database

Use a production PostgreSQL database.

## 5. Run migrations

```powershell
python manage.py migrate
```

## 6. Collect static files

```powershell
python manage.py collectstatic --noinput
```

## 7. Use a production WSGI server

For example:

```powershell
gunicorn core.wsgi:application
```

The exact command depends on the Django project's WSGI module and deployment platform.

---

# Deployment Checklist

Before going live:

```text
[ ] DEBUG=False
[ ] Production SECRET_KEY configured
[ ] Production database configured
[ ] ALLOWED_HOSTS configured
[ ] CORS configured
[ ] HTTPS enabled
[ ] Static files configured
[ ] Media storage configured
[ ] Database migrations applied
[ ] Admin account secured
[ ] API authentication tested
[ ] Deposit processing tested
[ ] Withdrawal processing tested
[ ] Transaction logging tested
[ ] Error handling tested
[ ] Database backups configured
[ ] Monitoring configured
[ ] Rate limiting configured
[ ] Secrets removed from source code
[ ] Legal and regulatory review completed
```

---

# Testing

Run Django's test suite:

```powershell
python manage.py test
```

For a specific application:

```powershell
python manage.py test authentication
```

You should create tests for critical functionality such as:

* Registration
* Login
* Authentication
* Investment creation
* Investment validation
* Deposit verification
* Withdrawal validation
* Transaction creation
* Permission checks
* Administrative actions

Financial operations should receive particularly strong automated test coverage.

---

# Useful Django Commands

### Check Django version

```powershell
python -m django --version
```

### Start the server

```powershell
python manage.py runserver
```

### Create migrations

```powershell
python manage.py makemigrations
```

### Apply migrations

```powershell
python manage.py migrate
```

### Create superuser

```powershell
python manage.py createsuperuser
```

### Open Django shell

```powershell
python manage.py shell
```

### Collect static files

```powershell
python manage.py collectstatic
```

### Run tests

```powershell
python manage.py test
```

---

# Git Workflow

Initialize Git:

```powershell
git init
```

Add files:

```powershell
git add .
```

Commit:

```powershell
git commit -m "Initial backend setup"
```

Rename the branch to main:

```powershell
git branch -M main
```

Add GitHub remote:

```powershell
git remote add origin YOUR_GITHUB_REPOSITORY_URL
```

Push:

```powershell
git push -u origin main
```

For future updates:

```powershell
git add .
git commit -m "Update backend"
git push
```

---

# Troubleshooting

## Virtual environment does not activate

For PowerShell, try:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## Django command not found

Make sure the virtual environment is activated:

```powershell
.\venv\Scripts\Activate.ps1
```

Then install Django:

```powershell
pip install django
```

---

## Migration errors

Check the migration status:

```powershell
python manage.py showmigrations
```

Then:

```powershell
python manage.py makemigrations
python manage.py migrate
```

---

## Database connection errors

Verify:

* Database URL
* Database username
* Database password
* Database host
* Database port
* Database availability
* Environment variables

---

## CORS errors

Verify that the frontend URL has been added to the backend's CORS configuration.

For local development, this may be:

```text
http://localhost:5173
```

Production should use the actual frontend domain.

---

# Financial and Regulatory Compliance

Sinevestpremium should not be deployed as a live financial service without appropriate legal and regulatory review.

Depending on the jurisdictions involved, the platform may need to address requirements relating to:

* Investment services
* Financial licensing
* KYC
* AML
* Customer identification
* Cryptocurrency transactions
* Consumer protection
* Data protection
* Financial reporting
* Taxation
* Record keeping
* Marketing and investment-return claims

The platform should only offer financial products and services that the operator is legally authorized to provide.

---

# Disclaimer

This repository contains backend software for the Sinevestpremium platform.

The software itself does not constitute financial advice, an investment recommendation, or a guarantee of investment returns.

Investment products can involve significant financial risk, including loss of capital.

Any investment returns displayed by the application must accurately reflect the legally approved terms of the applicable product and must not be represented as guaranteed unless legally permitted and appropriately substantiated.

The platform operator is responsible for ensuring compliance with all applicable laws, regulations, licensing requirements, consumer-protection requirements, and financial-services obligations.

---

# License

This project is proprietary software.

Unless explicitly authorized by the project owner, unauthorized copying, modification, distribution, sublicensing, or commercial use of this source code is prohibited.

---

# Contact

For technical, administrative, or platform-related inquiries, contact the Sinevestpremium administration team through the official contact channels provided by the platform.

---

# Project Status

**Status:** Active Development

Sinevestpremium Backend is currently under active development. API endpoints, database models, authentication mechanisms, payment integrations, investment-plan configurations, and deployment infrastructure may change as development progresses.
