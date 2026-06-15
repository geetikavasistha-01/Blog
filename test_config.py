import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_blog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
