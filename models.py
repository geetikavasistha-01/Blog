from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, event, Table, ForeignKey
from sqlalchemy.orm import relationship
from slugify import slugify
import markdown2
from database import Base

# Association table for post-to-tag many-to-many relationship
post_tag = Table(
    'post_tag',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)  # auto-generated from title
    category = Column(String, nullable=False)           # technical, personal, ml, robotics, life
    excerpt = Column(Text)
    body = Column(Text)                                  # raw Markdown
    body_html = Column(Text)                             # rendered HTML (cached)
    read_time = Column(Integer)                          # auto-calculated (words / 200)
    featured = Column(Boolean, default=False)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # default=datetime.utcnow is added to avoid NULL values on initial insert
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cover_image = Column(String, nullable=True)  # stores path like "uploads/my-image.jpg"

    # Many-to-many relationship with Tag
    tags = relationship("Tag", secondary=post_tag, back_populates="posts")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)

    posts = relationship("Post", secondary=post_tag, back_populates="tags")

class EmailSubscriber(Base):
    __tablename__ = "email_subscribers"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PageView(Base):
    __tablename__ = "page_views"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    path = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='SET NULL'), nullable=True)
    referrer = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    visitor_hash = Column(String, nullable=False)

    post = relationship("Post")


# SQLAlchemy listener to auto-populate fields before insert
@event.listens_for(Post, "before_insert")
def receive_before_insert(mapper, connection, target):
    if not target.slug and target.title:
        target.slug = slugify(target.title)
    
    if target.body:
        words = len(target.body.split())
        target.read_time = max(1, words // 200)
        target.body_html = markdown2.markdown(target.body, extras=["fenced-code-blocks", "code-friendly"])
    else:
        target.read_time = 1
        target.body_html = ""

# SQLAlchemy listener to auto-populate fields before update
@event.listens_for(Post, "before_update")
def receive_before_update(mapper, connection, target):
    # Regenerate slug if title is modified (or ensure it is always present)
    if target.title:
        target.slug = slugify(target.title)
        
    if target.body:
        words = len(target.body.split())
        target.read_time = max(1, words // 200)
        target.body_html = markdown2.markdown(target.body, extras=["fenced-code-blocks", "code-friendly"])
    else:
        target.read_time = 1
        target.body_html = ""
