from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)

def test_custom_404():
    print("Testing Custom 404 Page (GET /this-path-leads-nowhere)...")
    response = client.get("/this-path-leads-nowhere")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert "This path leads" in response.text or "something went wrong" in response.text or "not found" in response.text.lower()
    assert "Back to Writing" in response.text or "back to writing" in response.text.lower()
    print("[SUCCESS] Custom 404 page rendered correctly.")

def test_custom_500():
    print("Testing Custom 500 Page (GET /trigger-500)...")
    response = client.get("/trigger-500")
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    # Verify it loads the error page template and detail message, not traceback
    assert "Traceback" not in response.text
    assert "An unexpected server error occurred" in response.text or "something went wrong" in response.text.lower()
    print("[SUCCESS] Custom 500 page rendered correctly.")

if __name__ == "__main__":
    test_custom_404()
    test_custom_500()
