# GeekyKunoichi Blog — Production Deployment & Data Persistence Guide

This document describes how to deploy the blog in production environments with persistent SQLite storage.

---

## 1. Production Persistence (SQLite)

When deploying using the default SQLite database, you **must** configure persistent volumes. Without volumes, database writes (posts, user sessions, newsletter subscribers, uploaded media, analytics) will be lost when the container restarts or redeploys on ephemeral hosting providers (e.g., Render, Railway, Fly.io).

### Mount Path Configuration
Ensure that the following directories/files are mounted to persistent host folders or volumes:
1. **SQLite Database File**: `/app/data/blog.db`
2. **Uploaded Media Assets**: `/app/static/uploads/`

### Example Docker Compose Mount
```yaml
services:
  web:
    image: geekykunoichi-blog:latest
    volumes:
      - /var/lib/geekykunoichi/data:/app/data
      - /var/lib/geekykunoichi/uploads:/app/static/uploads
```

---

## 2. Deployment Checklist
1. **Production Mode**: Set `ENVIRONMENT=production` to secure cookies and enable strict CORS/CSP filters.
2. **Secret Credentials**: Change `ADMIN_PASSWORD_HASH` and `SECRET_KEY` in environment variables. Do not use development defaults.
3. **Analytics Salt**: Set a unique `ANALYTICS_SALT` for hashing visitor logs.
4. **Scheduled Backups**: Set up a cron job pointing to `/app/scripts/backup_db.sh` for regular gzipped backups of the SQLite database.
5. **SMTP Configuration**: Configure the SMTP environment variables for sending email updates (see section below).

---

## 3. SMTP & Email Notifications

The blog features an automatic email notification system that broadcasts new posts to subscribers in the background.

### Setup and Environment Variables
Configure the following keys in your `.env` or container settings:
* `SMTP_HOST`: Host address of the SMTP server (e.g., `smtp.gmail.com` or `smtp.mailgun.org`).
* `SMTP_PORT`: Port (usually `587` for TLS/STARTTLS or `465` for SSL).
* `SMTP_USER`: Authentication username/email.
* `SMTP_PASSWORD`: Authentication password. For Gmail, use an **App Password** generated from Google Account Settings -> Security -> App Passwords.
* `SMTP_FROM_EMAIL`: The address from which emails will be sent (usually the same as `SMTP_USER`).
* `SMTP_USE_TLS`: Set to `true` (default) to enable TLS.
* `SITE_URL`: The absolute base URL of the blog (e.g., `https://geekykunoichi.com`) used to construct post links.
* `ADMIN_EMAIL`: The admin's email address. On startup, this email is automatically added as a subscriber for QA and notification monitoring purposes.

### Unsubscribe System
As a simplification at this stage, the footer of each newsletter contains a note stating "To unsubscribe, reply directly to this email." Unsubscription requests must be handled manually by the admin by removing the email from the `email_subscribers` table or the admin interface.

