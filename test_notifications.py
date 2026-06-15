import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$5abM0KYNjKGAMkFTlVqbm.dsB6muyihL3FW3kotgSAifjP3GaAEie" # bcrypt of 'geekykunoichi'

from database import Base, get_db
from main import app
from models import Post, EmailSubscriber
from email_utils import send_new_post_emails

from test_config import TestingSessionLocal, override_get_db, engine

# Initialize tables
from test_config import init_test_db
init_test_db()

app.dependency_overrides[get_db] = override_get_db

import main
main.SessionLocal = TestingSessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = TestingSessionLocal()
    db.query(Post).delete()
    db.query(EmailSubscriber).delete()
    db.commit()
    db.close()

@patch("email_utils.smtplib.SMTP")
def test_send_emails_success(mock_smtp_class):
    # Setup mock SMTP
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance

    # Set env vars
    os.environ["SMTP_HOST"] = "smtp.test.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USER"] = "user@test.com"
    os.environ["SMTP_PASSWORD"] = "pass"
    os.environ["SMTP_FROM_EMAIL"] = "from@test.com"
    os.environ["SMTP_USE_TLS"] = "true"

    db = TestingSessionLocal()
    # Add subscriber
    sub = EmailSubscriber(email="subscriber@test.com")
    db.add(sub)
    
    # Add post
    post = Post(
        title="Test Post Title",
        category="Tech",
        excerpt="Test Excerpt",
        body="Body",
        published=True
    )
    db.add(post)
    db.commit()

    post_id = post.id
    db.close()

    # Call sender
    send_new_post_emails(post_id)

    # Verify SMTP was called
    mock_smtp_class.assert_called_once_with("smtp.test.com", 587, timeout=15)
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("user@test.com", "pass")
    assert mock_smtp_instance.sendmail.call_count >= 1
    mock_smtp_instance.quit.assert_called_once()

def test_post_publish_triggers_background_task():
    # Login admin client
    login_resp = client.post("/admin/login", data={"password": "geekykunoichi"}, follow_redirects=False)
    cookies = login_resp.cookies

    with patch("main.send_new_post_emails") as mock_send:
        # Create published post
        response = client.post(
            "/admin/post/new",
            data={
                "title": "Published Post",
                "category": "ML",
                "excerpt": "Excerpt",
                "body": "Body text",
                "published": "true"
            },
            cookies=cookies,
            follow_redirects=False
        )
        assert response.status_code == 303
        
        # TestClient runs background tasks synchronously before returning the response
        mock_send.assert_called_once()

def teardown_module():
    engine.dispose()
