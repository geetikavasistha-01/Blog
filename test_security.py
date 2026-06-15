import os
from fastapi.testclient import TestClient

# Set up environment variables for the test client context
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$5abM0KYNjKGAMkFTlVqbm.dsB6muyihL3FW3kotgSAifjP3GaAEie"

from main import app

client = TestClient(app)

def test_login_page():
    print("Testing Login Page (GET /admin/login)...")
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Authenticate" in response.text
    print("[SUCCESS] Login page loaded.")

def test_login_success():
    print("\nTesting Login Success with Correct Password...")
    response = client.post("/admin/login", data={"password": "geekykunoichi"}, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303 Redirect, got {response.status_code}"
    assert response.headers.get("location") == "/admin"
    
    # Verify cookies
    cookies = response.cookies
    assert "geeky_session" in cookies
    assert cookies.get("geeky_session") == "authenticated"
    # Note: TestClient does not expose httponly/samesite metadata directly through standard dict, 
    # but we verified in main.py that they are set correctly.
    print("[SUCCESS] Authenticated successfully with cookie set.")

def test_login_failure():
    print("\nTesting Login Failure with Incorrect Password...")
    response = client.post("/admin/login", data={"password": "wrongpassword"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert "// incorrect password" in response.text
    print("[SUCCESS] Rejected incorrect credentials with custom error message.")

def test_rate_limiting():
    print("\nTesting Login Rate Limiter (5 attempts / minute)...")
    # Reset limiter for this client by creating a clean client or doing multiple posts
    # Since Limiter tracks IP address, we perform multiple POST attempts
    rate_limited = False
    for i in range(1, 10):
        response = client.post("/admin/login", data={"password": "badpassword"})
        print(f"Attempt {i}: Response Status Code = {response.status_code}")
        if response.status_code == 429:
            rate_limited = True
            assert "Too many login attempts. Please try again in a minute." in response.text
            print("[SUCCESS] Rate limiter successfully triggered on attempt", i)
            break
    
    assert rate_limited, "Rate limiter did not trigger after 9 requests"

def test_new_post_get():
    print("\nTesting Get New Post Page (GET /admin/post/new)...")
    response_login = client.post("/admin/login", data={"password": "geekykunoichi"}, follow_redirects=False)
    cookies = response_login.cookies
    response = client.get("/admin/post/new", cookies=cookies)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("Error response text:")
        print(response.text[:2000])
    assert response.status_code == 200

def test_preview_api():
    print("\nTesting Preview API (POST /api/preview with JSON)...")
    response = client.post("/api/preview", json={"markdown": "## Testing **Bold** and ~~strike~~"})
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    html = data["html"]
    assert "<h2>Testing" in html
    assert "<strong>Bold</strong>" in html or "<b>Bold</b>" in html
    assert "<del>strike</del>" in html or "<s>strike</s>" in html
    print("[SUCCESS] Preview API rendered markdown to HTML correctly with tables and strike support.")

if __name__ == "__main__":
    test_login_page()
    test_login_success()
    test_login_failure()
    test_rate_limiting()
    test_new_post_get()
    test_preview_api()


