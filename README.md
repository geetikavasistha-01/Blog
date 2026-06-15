# GeekyKunoichi Blog

A dark, minimalistic, editorial personal blog built using FastAPI, SQLite, SQLAlchemy, Jinja2, and custom vanilla CSS.

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd Blog
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment configuration**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

5. **Generate an admin password hash**:
   Use `bcrypt` to generate a secure hash for your desired password:
   ```python
   import bcrypt
   print(bcrypt.hashpw(b"your_password_here", bcrypt.gensalt()).decode())
   ```
   Paste the generated hash into your `.env` file as `ADMIN_PASSWORD_HASH`.

6. **Generate a secret key**:
   Use Python's `secrets` module to generate a random session secret key:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```
   Paste the output into your `.env` file as `SECRET_KEY`.

7. **Run the development server**:
   ```bash
   python3 -m uvicorn main:app --reload
   ```

---

## ⚠️ Security Notes

* **Configuration**: Never check your `.env` file or the local database file `blog.db` into public version control. They are automatically ignored in `.gitignore`.
* **Cookie Flags**: In production environments, edit `main.py` cookie configuration to set `secure=True` (which requires HTTPS) to prevent transport interception.
* **Authentication Rate Limits**: The admin login route is rate-limited to a maximum of 5 attempts per minute per IP address. Exceeding this limit returns an HTTP 429 Too Many Requests response.
