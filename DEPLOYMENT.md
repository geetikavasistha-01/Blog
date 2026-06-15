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

