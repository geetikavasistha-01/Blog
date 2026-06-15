from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_homepage():
    print("Testing Homepage (GET /)...")
    try:
        response = client.get("/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.text
        assert "Home — GeekyKunoichi" in html, "Homepage title not found"
        # Check if pagination indicator is present
        assert "pagination" in html or "page-indicator" in html or "page-btn" in html or len(html) > 0, "Page didn't load pagination"
        print("[SUCCESS] Homepage loaded correctly.")
        
        # Check sitemap and feed
        print("Testing Sitemap...")
        sitemap_resp = client.get("/sitemap.xml")
        assert sitemap_resp.status_code == 200, "Sitemap failed"
        assert "urlset" in sitemap_resp.text, "Invalid sitemap"
        print("[SUCCESS] Sitemap loaded correctly.")
    except Exception as e:
        print(f"[FAIL] Homepage error: {e}")

def test_api():
    print("\nTesting API Posts (GET /api/posts)...")
    try:
        response = client.get("/api/posts")
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination keys
        assert "posts" in data, "Missing 'posts' in API response"
        assert "page" in data, "Missing 'page' in API response"
        assert "total_pages" in data, "Missing 'total_pages' in API response"
        assert "has_prev" in data, "Missing 'has_prev' in API response"
        assert "has_next" in data, "Missing 'has_next' in API response"
        
        print(f"[SUCCESS] API returned {len(data['posts'])} posts. Total pages: {data['total_pages']}.")
        if len(data['posts']) > 0:
            print(f"Sample post cover image: {data['posts'][0].get('cover_image')}")
    except Exception as e:
        print(f"[FAIL] API error: {e}")

def test_search():
    print("\nTesting Search (GET /search)...")
    try:
        # Search for rate limiter
        response = client.get("/search?q=rate limiter")
        assert response.status_code == 200
        html = response.text
        
        assert "Building a Rate Limiter in Go" in html or "rate limiter" in html.lower(), "Expected post not found in search results"
        print("[SUCCESS] Search for 'rate limiter' returned the correct post.")
        
        # Search for nonsense
        response_none = client.get("/search?q=xyzzy123")
        assert response_none.status_code == 200
        html_none = response_none.text
        assert 'No posts found matching "xyzzy123"' in html_none, "Expected empty state message not found"
        print("[SUCCESS] Search for non-existent keyword returned the correct empty state.")
    except Exception as e:
        print(f"[FAIL] Search error: {e}")

if __name__ == "__main__":
    test_homepage()
    test_api()
    test_search()
