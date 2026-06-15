import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import SessionLocal
from models import Post, EmailSubscriber

logger = logging.getLogger("newsletter")

def send_new_post_emails(post_id: int):
    # Fetch configurations
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM_EMAIL")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    site_url = os.getenv("SITE_URL", "https://geekykunoichi.com").rstrip("/")

    # Check if SMTP configuration is present
    if not all([smtp_host, smtp_port, smtp_user, smtp_password, smtp_from]):
        logger.warning("SMTP configuration is incomplete. Skipping email notifications.")
        return

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        logger.error(f"Invalid SMTP_PORT: {smtp_port}")
        return

    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.error(f"Post with ID {post_id} not found for sending emails.")
            return

        subscribers = db.query(EmailSubscriber).all()
        if not subscribers:
            logger.info("No subscribers found to notify.")
            return

        emails = [sub.email for sub in subscribers]
        logger.info(f"Preparing to send notifications for post '{post.title}' to {len(emails)} subscribers.")

        # Establish connection
        if smtp_use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        post_url = f"{site_url}/post/{post.slug}"

        for email in emails:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"New post: {post.title}"
                msg["From"] = smtp_from
                msg["To"] = email

                text_body = f"""Hello!

A new post has been published on GeekyKunoichi:

"{post.title}"

Category: {post.category}

Excerpt:
{post.excerpt}

Read the full post here:
{post_url}

---
To unsubscribe, reply directly to this email.
"""
                html_body = f"""<html>
<body>
  <p>Hello!</p>
  <p>A new post has been published on <strong>GeekyKunoichi</strong>:</p>
  <h3><a href="{post_url}">{post.title}</a></h3>
  <p><em>Category: {post.category}</em></p>
  <p>{post.excerpt}</p>
  <p><a href="{post_url}">Read the full post &rarr;</a></p>
  <hr>
  <p style="font-size: 0.8rem; color: #777;">To unsubscribe, reply directly to this email.</p>
</body>
</html>
"""
                msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))

                server.sendmail(smtp_from, [email], msg.as_string())
                logger.info(f"Email sent successfully to {email}")
            except Exception as sub_err:
                logger.error(f"Failed to send email to {email}: {sub_err}")

        server.quit()
        logger.info("Finished email notification delivery.")
    except Exception as e:
        logger.error(f"Error in SMTP email delivery thread: {e}")
    finally:
        db.close()
