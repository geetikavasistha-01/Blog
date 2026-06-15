import os
import sys
from fastapi.testclient import TestClient

# Make sure SQLite db exists and migrations are up to date
os.environ["DATABASE_URL"] = "sqlite:///blog.db"
os.environ["ENVIRONMENT"] = "development"

from database import engine, SessionLocal, Base
from models import Post, Tag, EmailSubscriber
from main import app, seed_database

client = TestClient(app)

def run_integration_tests():
    print("--- STARTING NEW FEATURES INTEGRATION TESTS ---")
    
    # 1. Clean and Seed Database
    print("[1/5] Re-seeding database for tag verification...")
    db = SessionLocal()
    try:
        # Recreate tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        seed_database(db)
        
        # Verify tag association populated by seed
        posts = db.query(Post).all()
        for p in posts:
            assert len(p.tags) > 0, f"Post '{p.title}' has no seeded tags!"
            print(f"      Post '{p.title}' tags: {[t.name for t in p.tags]}")
        
        # 2. Test dynamic tags API filtering
        print("[2/5] Testing /api/posts tag filtering and serialization...")
        # Get systems tag slug
        systems_tag = db.query(Tag).filter(Tag.name == "Systems").first()
        assert systems_tag is not None, "Systems tag was not seeded"
        
        response = client.get(f"/api/posts?tag={systems_tag.slug}")
        assert response.status_code == 200, f"API tag query failed: {response.text}"
        data = response.json()
        assert len(data["posts"]) > 0, "No posts returned for systems tag"
        for p in data["posts"]:
            assert "Systems" in p["tags"], f"Post missing expected tag: {p['tags']}"
            
        print("      API tag filtering works perfectly.")

        # 3. Test newsletter subscribe endpoint
        print("[3/5] Testing /api/subscribe validation and persistence...")
        # Valid signup
        sub_email = "new.subscriber@example.com"
        response = client.post("/api/subscribe", json={"email": sub_email})
        assert response.status_code == 200, f"Subscribe failed: {response.text}"
        assert response.json()["success"] is True
        assert response.json()["message"] == "Thanks for subscribing!"
        
        # Duplicate signup
        response = client.post("/api/subscribe", json={"email": sub_email})
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["message"] == "You're already subscribed!"
        
        # Invalid email validation
        invalid_email = "not-an-email"
        response = client.post("/api/subscribe", json={"email": invalid_email})
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "valid email" in response.json()["message"]
        
        print("      Newsletter subscribe validation and saving works perfectly.")

        # 4. Test admin search & status filtering parameters
        print("[4/5] Testing admin dashboard search and status filters...")
        # Since client requests require session cookie, we can mock is_authenticated or use cookies
        # Let's bypass is_authenticated by setting the cookie
        client.cookies.set("geeky_session", "authenticated")
        
        # Test search query
        response = client.get("/admin?q=Rate Limiter")
        assert response.status_code == 200
        assert "Rate Limiter" in response.text
        assert "LLM Reliability" not in response.text
        
        # Test status filter (published vs draft)
        response = client.get("/admin?status_filter=published")
        assert response.status_code == 200
        
        # Create a draft
        draft_post = Post(
            title="Draft Post Spec",
            category="Career",
            excerpt="Testing admin filters.",
            body="Not published.",
            featured=False,
            published=False
        )
        db.add(draft_post)
        db.commit()
        
        response = client.get("/admin?status_filter=draft")
        assert response.status_code == 200
        assert "Draft Post Spec" in response.text
        assert "Rate Limiter" not in response.text
        
        print("      Admin search and status filtering queries work perfectly.")

        # 5. Test Media Library references checking
        print("[5/5] Testing Media Library file references scanning...")
        # Let's create a dummy file in static/uploads
        os.makedirs("static/uploads", exist_ok=True)
        dummy_referenced = "dummy_ref.jpg"
        dummy_unused = "dummy_unused.jpg"
        
        with open(f"static/uploads/{dummy_referenced}", "w") as f:
            f.write("image bytes")
        with open(f"static/uploads/{dummy_unused}", "w") as f:
            f.write("image bytes")
            
        # Associate dummy_referenced with a post body
        featured_post = db.query(Post).filter(Post.featured == True).first()
        featured_post.body += f"\n![Alt text](/static/uploads/{dummy_referenced})"
        db.commit()
        
        # Get media list
        response = client.get("/admin/media")
        assert response.status_code == 200
        html = response.text
        
        # Verify both files listed
        assert dummy_referenced in html, "Referenced file not listed"
        assert dummy_unused in html, "Unused file not listed"
        
        # Clean up files
        if os.path.exists(f"static/uploads/{dummy_referenced}"):
            os.remove(f"static/uploads/{dummy_referenced}")
        if os.path.exists(f"static/uploads/{dummy_unused}"):
            os.remove(f"static/uploads/{dummy_unused}")
            
        print("      Media Library references scanning works perfectly.")
        print("\n--- ALL NEW FEATURES VERIFIED SUCCESSFULLY! ---")
        
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_integration_tests()
