import sys
import os

# Add parent directory to path to import database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Post, PageView, post_tag

def clear_seed_data():
    db = SessionLocal()
    try:
        # 1. Update PageViews to set post_id = None
        page_views_updated = db.query(PageView).filter(PageView.post_id != None).update({PageView.post_id: None}, synchronize_session=False)
        print(f"Updated {page_views_updated} PageViews to set post_id to NULL.")

        # 2. Clear post_tag table
        post_tags_deleted = db.execute(post_tag.delete())
        print(f"Deleted rows from post_tag: {post_tags_deleted.rowcount}")

        # 3. Clear posts table
        posts_deleted = db.query(Post).delete()
        print(f"Deleted {posts_deleted} Posts.")

        db.commit()
        print("Database cleanup committed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error occurred: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    clear_seed_data()
