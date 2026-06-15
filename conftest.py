import os
import pytest
from database import engine

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    # Dispose engine connections
    engine.dispose()
    # Remove the shared test database file
    if os.path.exists("./test_blog.db"):
        try:
            os.remove("./test_blog.db")
        except Exception:
            pass
