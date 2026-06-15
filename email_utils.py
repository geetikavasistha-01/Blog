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

def send_welcome_email(email: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM_EMAIL")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    site_url = os.getenv("SITE_URL", "https://geekykunoichi.com").rstrip("/")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password, smtp_from]):
        logger.warning("SMTP configuration is incomplete. Skipping welcome email.")
        return

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        logger.error(f"Invalid SMTP_PORT: {smtp_port}")
        return

    try:
        if smtp_use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to the GeekyKunoichi Newsletter!"
        msg["From"] = smtp_from
        msg["To"] = email

        text_body = f"""Welcome to GeekyKunoichi.

A place for machine learning, systems engineering, climate tech, robotics, and the occasional reflection on life, technology, and building things that matter.

Expect build logs, technical deep-dives, lessons learned, and ideas worth exploring.

No noise. Just curiosity, engineering, and continuous learning. Thanks for stopping by. Glad you're here.

---
Visit the blog: {site_url}
To unsubscribe, reply directly to this email.
"""
        html_body = f"""<html>
<body style="font-family: 'DM Sans', sans-serif; color: #0c0804; line-height: 1.6; background-color: #f2ebd9; padding: 2rem;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #f2ebd9; border: 1px solid #bcae97; padding: 2.5rem;">
    <h2 style="font-family: 'Playfair Display', serif; font-weight: normal; margin-top: 0; color: #0c0804;">Welcome to GeekyKunoichi.</h2>
    <p>A place for machine learning, systems engineering, climate tech, robotics, and the occasional reflection on life, technology, and building things that matter.</p>
    <p>Expect build logs, technical deep-dives, lessons learned, and ideas worth exploring.</p>
    <p>No noise. Just curiosity, engineering, and continuous learning. Thanks for stopping by. Glad you're here.</p>
    <p style="margin-top: 2rem;"><a href="{site_url}" style="background-color: #50300e; color: #f2ebd9; padding: 0.6rem 1.2rem; text-decoration: none; font-family: 'DM Mono', monospace; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; display: inline-block;">Visit the blog &rarr;</a></p>
    <hr style="border: none; border-top: 1px solid #bcae97; margin: 2rem 0;">
    <p style="font-size: 0.8rem; color: #777; font-family: 'DM Mono', monospace;">To unsubscribe, reply directly to this email.</p>
  </div>
</body>
</html>
"""
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        server.sendmail(smtp_from, [email], msg.as_string())
        server.quit()
        logger.info(f"Welcome email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")

