import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import Post, Tag

# Configure isolated test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Recreate test tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply dependency overrides
app.dependency_overrides[get_db] = override_get_db

# Redirect main.py SessionLocal calls to TestingSessionLocal
import main
main.SessionLocal = TestingSessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = TestingSessionLocal()
    db.query(Post).delete()
    db.query(Tag).delete()
    db.commit()

    # Seed one test post for checking endpoints and search
    post = Post(
        title="Building a Rate Limiter in Go That Actually Holds Under Pressure",
        category="Systems",
        excerpt="A deep dive into token bucket algorithms in Go.",
        body="This is the post content.",
        published=True,
        featured=True
    )
    db.add(post)
    db.commit()
    db.close()

def test_homepage():
    print("Testing Homepage (GET /)...")
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    html = response.text
    assert "GeekyKunoichi" in html, "Homepage title not found"
    
    # Check sitemap and feed
    print("Testing Sitemap...")
    sitemap_resp = client.get("/sitemap.xml")
    assert sitemap_resp.status_code == 200, "Sitemap failed"
    assert "urlset" in sitemap_resp.text, "Invalid sitemap"
    print("[SUCCESS] Sitemap loaded correctly.")

def test_api():
    print("\nTesting API Posts (GET /api/posts)...")
    response = client.get("/api/posts")
    assert response.status_code == 200
    data = response.json()
    
    # Verify pagination keys
    assert "posts" in data, "Missing 'posts' in API response"
    assert "page" in data, "Missing 'page' in API response"
    assert "total_pages" in data, "Missing 'total_pages' in API response"
    assert "has_prev" in data, "Missing 'has_prev' in API response"
    assert "has_next" in data, "Missing 'has_next' in API response"
    
    assert len(data["posts"]) == 1
    assert data["posts"][0]["title"] == "Building a Rate Limiter in Go That Actually Holds Under Pressure"
    print(f"[SUCCESS] API returned 1 post correctly.")

def test_search():
    print("\nTesting Search (GET /search)...")
    # Search for rate limiter (should find our post)
    response = client.get("/search?q=rate limiter")
    assert response.status_code == 200
    html = response.text
    
    assert "Building a Rate Limiter in Go" in html, "Expected post not found in search results"
    print("[SUCCESS] Search for 'rate limiter' returned the correct post.")
    
    # Search for nonsense
    response_none = client.get("/search?q=xyzzy123")
    assert response_none.status_code == 200
    html_none = response_none.text
    assert 'No posts found matching "xyzzy123"' in html_none or 'No posts found matching &quot;xyzzy123&quot;' in html_none, "Expected empty state message not found"
    print("[SUCCESS] Search for non-existent keyword returned the correct empty state.")

# Cleanup test DB after execution
def teardown_module():
    engine.dispose()
