import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variables for testing context
os.environ["ANALYTICS_SALT"] = "test_analytics_salt_key_123"
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$5abM0KYNjKGAMkFTlVqbm.dsB6muyihL3FW3kotgSAifjP3GaAEie" # bcrypt hash of 'geekykunoichi'

from database import Base, get_db
from main import app
from models import PageView, Post

from test_config import TestingSessionLocal, override_get_db, engine

# Apply dependency overrides
app.dependency_overrides[get_db] = override_get_db

# Redirect main.py SessionLocal calls to TestingSessionLocal
import main
main.SessionLocal = TestingSessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = TestingSessionLocal()
    db.query(PageView).delete()
    db.query(Post).delete()
    db.commit()
    db.close()

def test_public_route_records_page_view():
    # Make a request to a public content route
    response = client.get("/", headers={"User-Agent": "Mozilla/5.0", "Referer": "https://google.com"})
    assert response.status_code == 200
    
    # Check that a page view was recorded in the database
    db = TestingSessionLocal()
    views = db.query(PageView).all()
    assert len(views) == 1
    view = views[0]
    assert view.path == "/"
    assert view.referrer == "https://google.com"
    assert view.user_agent == "Mozilla/5.0"
    assert len(view.visitor_hash) == 64  # SHA256 length
    db.close()

def test_admin_requests_excluded():
    # Set the admin session cookie
    client.cookies.set("geeky_session", "authenticated")
    try:
        response = client.get("/", headers={"User-Agent": "Mozilla/5.0"})
        assert response.status_code == 200
        
        # Verify no view is recorded
        db = TestingSessionLocal()
        assert db.query(PageView).count() == 0
        db.close()
    finally:
        client.cookies.delete("geeky_session")

def test_bot_requests_excluded():
    # Set User-Agent to a Google bot signature
    response = client.get("/", headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
    assert response.status_code == 200
    
    db = TestingSessionLocal()
    assert db.query(PageView).count() == 0
    db.close()

def test_static_and_api_excluded():
    # Get robots.txt (excluded sitemap/robots/feed)
    client.get("/robots.txt")
    client.get("/sitemap.xml")
    client.get("/feed.xml")
    # API endpoints (excluded)
    client.get("/api/posts")
    
    db = TestingSessionLocal()
    assert db.query(PageView).count() == 0
    db.close()

def test_visitor_hash_privacy():
    response1 = client.get("/about", headers={"User-Agent": "Mozilla/5.0", "X-Forwarded-For": "192.168.1.50"})
    assert response1.status_code == 200
    
    db = TestingSessionLocal()
    views = db.query(PageView).all()
    assert len(views) == 1
    view = views[0]
    assert "192.168.1.50" not in view.visitor_hash
    assert len(view.visitor_hash) == 64
    db.close()

def test_admin_analytics_requires_auth():
    # Unauthorized access redirects to login
    response = client.get("/admin/analytics", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("location") == "/admin/login"
    
    # Authorized access loads the dashboard
    client.cookies.set("geeky_session", "authenticated")
    try:
        response_auth = client.get("/admin/analytics")
        assert response_auth.status_code == 200
        assert "Traffic History" in response_auth.text
    finally:
        client.cookies.delete("geeky_session")

def test_click_tracking_api():
    # Track a card click
    response = client.post("/api/track-click", json={"target": "click:post:rate-limiter", "source_path": "/"}, headers={"User-Agent": "Mozilla/5.0"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Check DB representation
    db = TestingSessionLocal()
    views = db.query(PageView).all()
    assert len(views) == 1
    view = views[0]
    assert view.path == "click:post:rate-limiter"
    assert view.referrer == "/"
    assert len(view.visitor_hash) == 64
    db.close()

# Cleanup test DB after execution
def teardown_module():
    engine.dispose()
