import sys
import os

# Set environment variables for testing
os.environ["ADMIN_PASSWORD"] = "testpassword"

from database import engine, SessionLocal, Base
from models import Post
from main import seed_database

def run_tests():
    print("--- STARTING MODEL VERIFICATION ---")
    
    # 1. Clear database and recreate tables
    print("[1/5] Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 2. Seed database
        print("[2/5] Seeding database with sample posts...")
        seed_database(db)
        post_count = db.query(Post).count()
        print(f"      Total posts seeded: {post_count}")
        assert post_count == 6, f"Expected 6 seeded posts, got {post_count}"
        
        # 3. Verify auto-generated fields on seeded data
        print("[3/5] Verifying seeded post auto-generated fields...")
        featured_post = db.query(Post).filter(Post.featured == True).first()
        assert featured_post is not None, "Featured post not found"
        assert featured_post.slug == "building-a-rate-limiter-in-go-that-actually-holds-under-pressure", \
            f"Incorrect slug: {featured_post.slug}"
        assert featured_post.read_time > 0, f"Incorrect read_time: {featured_post.read_time}"
        assert "<h2" in featured_post.body_html, "Markdown rendering failed for seeded post"
        assert featured_post.created_at is not None, "created_at is None"
        assert featured_post.updated_at is not None, "updated_at is None"
        print("      Seeded posts validated successfully.")
        
        # 4. Test programmatic new post creation (inserts)
        print("[4/5] Testing new post creation and listeners...")
        new_post = Post(
            title="LiDAR Mapping 101: Sensors and Algorithms",
            category="Robotics",
            excerpt="An introductory post about LiDAR sensor setups.",
            body="""# Introduction
LiDAR is awesome. Here is some inline `code` and some details.
""",
            featured=False,
            published=True
        )
        db.add(new_post)
        db.commit()
        
        # Reload
        db.refresh(new_post)
        
        assert new_post.slug == "lidar-mapping-101-sensors-and-algorithms", f"Incorrect slug: {new_post.slug}"
        assert new_post.read_time == 1, f"Expected 1 min read time, got {new_post.read_time}"
        assert "<h1>Introduction</h1>" in new_post.body_html, "Markdown heading not rendered"
        assert "<code>code</code>" in new_post.body_html, "Markdown inline code not rendered"
        print("      Insert listeners work perfectly.")
        
        # 5. Test programmatic update post (updates)
        print("[5/5] Testing post editing and listeners...")
        new_post.title = "LiDAR Mapping 202: Advanced Algorithms"
        new_post.body = "# Advanced LiDAR\n\nThis is a long post. " * 35  # ~280 words
        db.commit()
        db.refresh(new_post)
        
        assert new_post.slug == "lidar-mapping-202-advanced-algorithms", f"Incorrect updated slug: {new_post.slug}"
        assert new_post.read_time == 1, f"Expected 1 min read time for ~280 words, got {new_post.read_time}"
        assert "<h1>Advanced LiDAR</h1>" in new_post.body_html, "Updated Markdown not rendered"
        
        print("      Update listeners work perfectly.")
        
        print("\n--- ALL TESTS PASSED SUCCESSFULLY! ---")
        
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
