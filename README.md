# GeekyKunoichi Blog Platform
Blog Page
<img width="1680" height="935" alt="Screenshot 2026-06-16 at 12 59 53 AM" src="https://github.com/user-attachments/assets/06311413-bb99-4494-bd45-9df8a1b509f1" />
About Section
<img width="1680" height="930" alt="Screenshot 2026-06-16 at 1 01 29 AM" src="https://github.com/user-attachments/assets/58bdf8d9-e6d9-4732-8c66-2094794e8d79" />
Footer
<img width="1680" height="931" alt="Screenshot 2026-06-16 at 1 03 08 AM" src="https://github.com/user-attachments/assets/2cd88ef9-be22-4f69-85c2-a540228d4771" />

A professional, high-performance, minimalist personal blogging platform built using FastAPI, SQLite, SQLAlchemy, Jinja2, and custom semantic CSS. The platform includes embedded analytics, an asynchronous newsletter subscription and notification system, and an administrative control panel.

## Features

* **Content Management System**: Write articles in Markdown with automatic HTML compilation, read-time calculations, automated slug generation, tag management, and image upload capabilities.
* **Visitor Analytics**: Track page views, post-specific views, user agents, referrers, and visitor engagement metrics. All metrics utilize SHA-256 hashed client IP addresses and user agents to preserve user privacy.
* **Newsletter and Notifications**: Subscribe readers and notify them asynchronously when new articles are published, using background worker tasks and robust SMTP transport.
* **Modern Editorial Design**: A responsive, dark-editorial user interface designed using custom typography, fluid layouts, SVG icons, and edge-to-edge graphics.
* **Security Controls**: Implements secure session cookies, bcrypt-hashed passwords for administrative accounts, and request rate limiting on authentication endpoints to prevent brute-force attacks.

## Tech Stack

* **Web Framework**: FastAPI (Asynchronous Server Gateway Interface)
* **Database & ORM**: SQLite with SQLAlchemy ORM
* **Migrations**: Alembic
* **Templating Engine**: Jinja2
* **Markdown Parser**: markdown2
* **Styling**: Semantic HTML5 and Vanilla CSS3
* **Testing**: Pytest with HTTPX and AnyIO

---

## Directory Structure

* `main.py`: Main application entry point containing FastAPI endpoints, middleware, custom rate-limiters, and backend routes.
* `models.py`: Declarative SQLAlchemy models representing database entities (Posts, Tags, Subscribers, PageViews).
* `database.py`: Database connection setup, session management, and base declarative class.
* `email_utils.py`: Email validation, SMTP client abstraction, and HTML email template formatting.
* `templates/`: Jinja2 templates (base layout, home page, blog posts, about page).
* `static/`: Static assets including CSS, JavaScript, and favicon images.
* `alembic/`: Database schema version history and migration scripts.
* `tests/`: Automated unit and integration test suites.

---

## Installation & Local Development

### Prerequisites

* Python 3.10 or higher
* pip (Python package installer)
* SQLite3

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone <https://github.com/geetikavasistha-01/Blog<img width="1680" height="931" alt="Screenshot 2026-06-16 at 1 00 30 AM" src="https://github.com/user-attachments/assets/02613ae9-b659-435d-bbf0-9483b5d3f37b" />
>
   cd Blog
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and configure the settings (e.g., database file path, SMTP settings, etc.).

5. **Generate Security Keys & Credentials**
   Generate a secure random session secret key:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
   Paste the generated string into the `.env` file as `SECRET_KEY`.

   Generate a bcrypt-hashed password for the administrative account:
   ```bash
   python3 -c "import bcrypt; print(bcrypt.hashpw(b'your_secure_password', bcrypt.gensalt()).decode())"
   ```
   Paste the generated hash into the `.env` file as `ADMIN_PASSWORD_HASH`.

6. **Initialize the Database**
   Run the Alembic migrations to construct the database schema:
   ```bash
   alembic upgrade head
   ```

7. **Run the Development Server**
   ```bash
   python3 -m uvicorn main:app --reload
   ```
   The local application will be accessible at `http://127.0.0.1:8000`.

---

## Database Migrations

This project uses Alembic to manage database schema updates.

* **Apply Pending Migrations**:
  ```bash
  alembic upgrade head
  ```
* **Revert Last Migration**:
  ```bash
  alembic downgrade -1
  ```
* **Generate a New Migration Script**:
  ```bash
  alembic revision --autogenerate -m "description_of_changes"
  ```

---

## Running the Test Suite

The application includes unit and integration tests covering security, endpoints, analytics, and notification behaviors.

To run all tests:
```bash
pytest
```

To run a specific test file:
```bash
pytest test_endpoints.py
```

---

## Security Hardening for Production

* **HTTPS Enforcement**: Ensure the site is served over SSL/TLS. In `main.py`, configure session and state cookies with the `secure=True` flag.
* **Environment Separation**: Ensure the SQLite database file (`blog.db`) and credentials file (`.env`) are kept out of public version control (they are ignored by default in `.gitignore`).
* **SMTP Credentials**: Set strong, secure app-specific passwords for SMTP configurations in production to prevent spam or unauthorized email sending.
