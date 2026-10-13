# django-ecommerce
Modern Django E-Commerce Platform

A feature-rich, full-stack e-commerce web application built with Django 6.0 and PostgreSQL. This platform provides a clean, responsive user experience backed by robust security features, flexible payment processing (Credit/Debit Card & Cash on Delivery), real-time order tracking, comprehensive customer verification, and automated system activity logging.

🛠️ Tech Stack & Architecture

Backend Framework: Python 3.12+, Django 6.0.7

Database: PostgreSQL (with psycopg2-binary)

Frontend Design System: Bootstrap 5, Bootstrap Icons, Custom CSS Components (.modern-card)

Typography & Styling: Plus Jakarta Sans, Slate primary palette (#0f172a), Accent blue (#2563eb)

Logging & Monitoring: Custom Django Middleware (AutomaticActivityLoggerMiddleware), File Handlers (logging), and Database Audit Model (UserLog)

✨ Key Features

Unified Modern UI System: Clean, consistent visual hierarchy and component styling across all storefront, cart, checkout, tracking, and dashboard templates.

Flexible Payment Processing: Supports both Credit/Debit Card (with automatic 4-digit card masking) and Cash on Delivery (COD) payment options.

Real-Time Order Tracking: Interactive 4-stage visual progress timeline (Processing ➔ Approved ➔ Out for Delivery ➔ Delivered) that updates instantly when modified by staff.

Customer Verification & Admin Management: Captures essential customer contact and delivery details (full_name, email, phone, shipping_address) for order auditing and verification inside the Django Admin panel.

Automated Error & Activity Auditing:

Custom middleware captures site-wide HTTP errors (4xx, 5xx) and user events in real time.

File-based logging captures system traces (logs/django_errors.log & logs/user_activity.log).

Administrative audit trail model (UserLog) accessible via Django Admin.

🚀 Quick Start & Local Setup

Follow these steps to set up and run the application locally on your machine.

Prerequisites

Python 3.12+ installed on your system

PostgreSQL installed and running locally

Git

1. Clone the Repository

git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER_NAME>


2. Set Up Virtual Environment

macOS / Linux:

python3 -m venv venv
source venv/bin/activate


Windows (Command Prompt / PowerShell):

python -m venv venv
venv\Scripts\activate


3. Install Dependencies

pip install -r requirements.txt


⚙️ Environment Configuration

Create a .env file in the project root directory (alongside manage.py) and supply your local database credentials and settings:

SECRET_KEY=your-django-secure-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432


🗄️ Database Setup & Server Startup

Apply Database Migrations:

python manage.py makemigrations
python manage.py migrate


Create a Superuser (Admin Dashboard Access):

python manage.py createsuperuser


Start the Development Server:

python manage.py runserver


Access the storefront at http://127.0.0.1:8000/ and the administrator control panel at http://127.0.0.1:8000/admin/.

🛡️ Logging & Monitoring Overview

The application includes dual-layer monitoring for tracking system health:

Django Admin Audit Trail: Navigate to User Logs in the admin dashboard to review filterable records of user actions, warnings, and HTTP error events.

File Logs (/logs/):

logs/user_activity.log: Captures operational milestones (e.g., checkouts, session actions).

logs/django_errors.log: Captures Python exception tracebacks and system warnings.

👥 Collaboration & Contribution Workflow

Adding Collaborators: Repository owners can add team members via GitHub repository settings under Collaborators.

Branching Strategy: Create feature branches (git checkout -b feature/your-feature-name) before submitting pull requests for code review.