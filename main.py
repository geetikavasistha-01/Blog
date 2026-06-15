import os
import uuid
import aiofiles
import bcrypt
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, Depends, status, HTTPException, Response, UploadFile, File, Cookie, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, get_db, SessionLocal, Base
from models import Post, PageView
from email_utils import send_new_post_emails
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load environment variables
load_dotenv(override=True)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory on startup
os.makedirs("static/uploads", exist_ok=True)

# Database Seeding Logic
def seed_database(db: Session):
    from models import Tag
    from slugify import slugify

    if db.query(Post).count() == 0:
        sample_posts = [
            Post(
                title="Building a Rate Limiter in Go That Actually Holds Under Pressure",
                category="Systems",
                excerpt="A deep dive into token bucket algorithms in Go, handling concurrent requests, and bench-testing performance under heavy load.",
                body="""When building high-throughput services, rate limiting isn't just about API discipline — it is a survival mechanism. In this write-up, we are going to build a token-bucket rate limiter in Go from scratch.

## The Problem with Naive Limiters

Many naive rate limiters rely on global mutex locks, which create severe lock contention as traffic grows. We want a rate limiter that is concurrent-safe, fast, and does not choke under pressure.

### The Token Bucket Algorithm

The token bucket algorithm works by filling a bucket with tokens at a constant rate. Each request consumes one token. If the bucket is empty, the request is rate-limited.

```go
package main

import (
	"sync"
	"time"
)

type TokenBucket struct {
	rate         float64 // tokens per second
	capacity     float64
	tokens       float64
	lastRefill   time.Time
	mu           sync.Mutex
}

func NewTokenBucket(rate, capacity float64) *TokenBucket {
	return &TokenBucket{
		rate:       rate,
		capacity:   capacity,
		tokens:     capacity,
		lastRefill: time.Now(),
	}
}

func (tb *TokenBucket) Allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()
	tb.lastRefill = now

	// Refill tokens
	tb.tokens += elapsed * tb.rate
	if tb.tokens > tb.capacity {
		tb.tokens = tb.capacity
	}

	if tb.tokens >= 1.0 {
		tb.tokens -= 1.0
		return true
	}

	return false
}
```

## Bench Testing Under Load

To evaluate lock performance, we spun up a benchmark of 1,000 goroutines hitting the rate limiter concurrently. The local lock contention was negligible due to Go's fast mutex implementation. In production, however, when distributing rate limiting across multiple instances, moving to a Redis-based token bucket with Lua scripts is the standard choice.

---
Geetika.
""",
                featured=True,
                published=True
            ),
            Post(
                title="What KPI Dashboards Taught Me About LLM Reliability",
                category="ML & AI",
                excerpt="Analyzing production performance, latency variance, and drift in large language models using dashboards and statistical monitoring.",
                body="""Large Language Models (LLMs) are notoriously non-deterministic. In this post, we discuss the challenges of monitoring LLMs in production and how statistics can help us maintain system reliability.

## Latency and Drift

Unlike traditional APIs with tight p99 latency boundaries, LLMs have highly variable execution speeds. Latency is heavily dependent on the number of generated tokens, network conditions, and model provider status.

> "If you don't monitor your model inputs and outputs, you are flying blind."

### Key Metrics to Monitor
1. **Tokens Per Second**: The throughput speed of text generation.
2. **TTFT (Time to First Token)**: Crucial for user experience in interactive chat interfaces.
3. **Semantic Drift**: Comparing vector similarity of inputs over time to identify query changes.

### Implementing a Monitor
We can log prompts and responses using an async callback handler, then aggregate latency and token counts locally. By plotting statistical histograms, we can spot sudden performance anomalies.
""",
                featured=False,
                published=True
            ),
            Post(
                title="On Being a Kunoichi in Rooms That Weren't Built For You",
                category="Career",
                excerpt="Personal essays on navigation strategies, building engineering confidence, and finding focus amidst the noise.",
                body="""Operating in elite engineering spaces can feel like navigating an unfamiliar territory. As a woman in CS and robotics, I have often found myself in rooms where I stood out.

## The Strategy of the Kunoichi

In historical contexts, a *kunoichi* (female ninja) succeeded by using intelligence, agility, and mastery of tradecraft to outmaneuver opponents who expected conventional brute force. 

When you navigate spaces where people make assumptions about your abilities:

1. **Master the Technical Fundamentals**: Let your code and system design speak for itself. Precision is the best argument.
2. **Cultivate Silent Mastery**: You do not need to speak the loudest in the room. Observe, analyze, and strike with high-quality contributions when it matters.
3. **Be Adaptable**: The tech landscape changes constantly. The capacity to learn complex concepts rapidly is your ultimate secret weapon.
""",
                featured=False,
                published=True
            ),
            Post(
                title="Spider Bots and Dark Pipes: Notes from an Autonomous Inspection Project",
                category="Robotics",
                excerpt="Designing LiDAR integration, sensor fusion, and navigation logic for spider-like inspection crawlers in dark pipeline tunnels.",
                body="""Pipeline inspection is a dirty, dangerous task. Doing it autonomously requires robots that can adapt to dark, wet, and complex environments.

## Sensor Fusion in Dark Environments

Inside dark metal pipes, standard computer vision fails. We rely on a custom sensor fusion payload:

- **Solid-State LiDAR**: For 3D spatial mapping and wall distance measurements.
- **IMU & Wheel Odometry**: To track position and detect slips inside the pipe.
- **Infrared Cameras**: To detect structural cracks.

```
+---------------+      +-------------+
|  LiDAR Range  |----->|             |
+---------------+      |   Extended  |
                       |    Kalman   |---> State Estimate (Position/Angle)
+---------------+      |    Filter   |
|   IMU Sensor  |----->|             |
+---------------+      +-------------+
```

Our team developed a navigation algorithm that tracks the tube geometry and centers the crawler automatically, correcting for roll and slip in real time.
""",
                featured=False,
                published=True
            ),
            Post(
                title="The Internship Hunt Is a Game. Here Are the Actual Rules.",
                category="Life",
                excerpt="A strategic guide for CS/ML students looking to secure competitive internships without burning out.",
                body="""The process of finding a tech internship can feel exhausting and chaotic. But if you treat it as a structured game with clear rules, you can optimize your chances of winning.

## The Pipeline

The internship funnel consists of three core phases:
1. **Resume Screen**: Pass the initial formatting check and key-word filters. Keep it clean, single-page, and metrics-focused.
2. **Technical Assessment**: Code signals and hacker ranks. Practice LeetCode consistently, focusing on patterns (e.g., sliding window, graphs) rather than memorizing questions.
3. **Interviews**: System design, code walkthroughs, and behavioral questions. Talk through your code and show how you think under pressure.

Remember: *Persistence is the game. Every rejection is just a data point to refine your system.*
""",
                featured=False,
                published=True
            ),
            Post(
                title="Why I Reach for Docker Before I Reach for Anything Else",
                category="Systems",
                excerpt="A developer's checklist for local reproducibility, dev-to-prod consistency, and sandboxed execution environments.",
                body="""There is nothing more frustrating than the "works on my machine" syndrome. That's why Docker is the first tool I set up on any new codebase.

## The Power of a Reproducible Environment

Docker guarantees that dependencies, runtime libraries, and environment variables are identical across all local developer setups and production servers.

### My Go-To FastAPI Dockerfile

```dockerfile
# Multi-stage build for micro-images
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

By isolating environments, you prevent version conflicts, simplify local integration testing, and accelerate CI/CD build scripts.
""",
                featured=False,
                published=True
            )
        ]
        db.add_all(sample_posts)
        db.commit()

    # Convert/sync category strings to Tag relationships for all posts
    posts = db.query(Post).all()
    for post in posts:
        if not post.tags and post.category:
            slug = slugify(post.category)
            tag = db.query(Tag).filter(Tag.slug == slug).first()
            if not tag:
                tag = Tag(name=post.category, slug=slug)
                db.add(tag)
                db.flush()
            if tag not in post.tags:
                post.tags.append(tag)
    db.commit()

# Lifespan context manager to handle startup seeding
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed database
    db = SessionLocal()
    try:
        if os.getenv("SEED_DEMO_DATA", "false").lower() == "true":
            seed_database(db)
        
        # Ensure admin email is subscribed
        admin_email = os.getenv("ADMIN_EMAIL")
        if admin_email:
            from models import EmailSubscriber
            existing = db.query(EmailSubscriber).filter(EmailSubscriber.email == admin_email).first()
            if not existing:
                sub = EmailSubscriber(email=admin_email)
                db.add(sub)
                db.commit()
    finally:
        db.close()
    yield

# Initialize FastAPI App
app = FastAPI(
    title="GeekyKunoichi Blog",
    lifespan=lifespan
)

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://giscus.app; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: *; "
        "frame-src 'self' https://giscus.app;"
    )
    return response

# Page Views Tracking Middleware
@app.middleware("http")
async def track_page_views(request: Request, call_next):
    response = await call_next(request)
    try:
        # Only track public GET requests that successfully return 200 OK
        if request.method == "GET" and response.status_code == 200:
            path = request.url.path
            norm_path = path.rstrip("/") if path != "/" else "/"
            
            # Content pages to track
            is_content_page = norm_path in ["/", "/about", "/archive", "/search"] or norm_path.startswith("/post/")
            if is_content_page:
                # Exclude if admin is logged in (authenticated session cookie)
                if request.cookies.get("geeky_session") != "authenticated":
                    # Exclude bot traffic
                    user_agent = request.headers.get("user-agent", "")
                    ua_lower = user_agent.lower()
                    bot_signals = ["bot", "spider", "crawl", "slurp", "tracker", "lighthouse", "python-urllib", "pytest"]
                    if not any(bot in ua_lower for bot in bot_signals):
                        # Extract client IP
                        ip_address = request.headers.get("x-forwarded-for")
                        if ip_address:
                            ip_address = ip_address.split(",")[0].strip()
                        else:
                            ip_address = request.client.host if request.client else "unknown"
                        
                        # Generate daily unique visitor hash
                        today_str = datetime.utcnow().strftime("%Y-%m-%d")
                        salt = os.getenv("ANALYTICS_SALT", "default_salt_for_geeky_kunoichi")
                        input_str = f"{ip_address}{user_agent}{today_str}{salt}"
                        visitor_hash = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
                        
                        # Extract Referrer
                        referrer = request.headers.get("referer")
                        
                        # Determine post_id for post page views
                        post_id = None
                        if norm_path.startswith("/post/"):
                            slug = norm_path.split("/post/")[1]
                            db = SessionLocal()
                            try:
                                post = db.query(Post).filter(Post.slug == slug, Post.published == True).first()
                                if post:
                                    post_id = post.id
                            finally:
                                db.close()
                                
                        # Save the view record
                        db = SessionLocal()
                        try:
                            view = PageView(
                                timestamp=datetime.utcnow(),
                                path=path,
                                post_id=post_id,
                                referrer=referrer,
                                user_agent=user_agent,
                                visitor_hash=visitor_hash
                            )
                            db.add(view)
                            db.commit()
                        finally:
                            db.close()
    except Exception as e:
        import logging
        logging.error(f"Analytics tracking middleware error: {e}", exc_info=True)
    return response


# General Exception Handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    import logging
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": "An unexpected server error occurred. Please try again later."
        },
        status_code=500
    )

# robots.txt Route
@app.get("/robots.txt", response_class=Response, include_in_schema=False)
def robots_txt():
    content = "User-agent: *\nAllow: /\nSitemap: https://geekykunoichi.com/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")

# favicon.ico Route
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import FileResponse
    return FileResponse("static/logo.png")

# Route to trigger 500 for testing
@app.get("/trigger-500", include_in_schema=False)
def trigger_500():
    raise Exception("Test exception for 500 error page handling")

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    if "/admin" in request.url.path:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "Too many login attempts. Please try again in a minute."
            },
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
    )

# Helper to check authentication
def is_authenticated(request: Request) -> bool:
    return request.cookies.get("geeky_session") == "authenticated"

# --- PUBLIC ROUTES ---

POSTS_PER_PAGE = 6

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, page: int = 1, tag: str = None, db: Session = Depends(get_db)):
    from models import Tag
    # Build query
    query = db.query(Post).filter(Post.published == True)
    
    if tag and tag.lower() != "all":
        query = query.filter(Post.tags.any(Tag.slug == tag))
        
    total = query.count()
    total_pages = max(1, (total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)
    page = max(1, min(page, total_pages))
    
    offset = (page - 1) * POSTS_PER_PAGE
    
    if tag and tag.lower() != "all":
        posts = query.order_by(Post.created_at.desc()).offset(offset).limit(POSTS_PER_PAGE).all()
    else:
        posts = query.order_by(Post.featured.desc(), Post.created_at.desc()).offset(offset).limit(POSTS_PER_PAGE).all()

    # Fetch all tags that are linked to at least one published post, to show in the filter bar
    all_tags = db.query(Tag).join(Tag.posts).filter(Post.published == True).distinct().all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts,
            "tags": all_tags,
            "selected_tag": tag,
            "active_tab": "writing",
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    )

@app.get("/post/{slug}", response_class=HTMLResponse)
async def single_post(request: Request, slug: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.slug == slug, Post.published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    import re
    base_url = str(request.base_url)
    og_image = None
    if post.cover_image:
        if post.cover_image.startswith(("http://", "https://")):
            og_image = post.cover_image
        else:
            path = post.cover_image
            if path.startswith("static/"):
                og_image = f"{base_url}{path}"
            else:
                og_image = f"{base_url}static/{path}"
    else:
        # Search for first image in body_html
        img_match = re.search(r'<img[^>]+src="([^"]+)"', post.body_html or "")
        if img_match:
            src = img_match.group(1)
            if src.startswith(("http://", "https://", "data:")):
                og_image = src
            elif src.startswith("/"):
                og_image = f"{base_url}{src[1:]}"
            else:
                og_image = f"{base_url}{src}"
        else:
            og_image = f"{base_url}static/og-default.png"
    
    giscus_repo = os.getenv("GISCUS_REPO", "")
    giscus_repo_id = os.getenv("GISCUS_REPO_ID", "")
    giscus_category = os.getenv("GISCUS_CATEGORY", "")
    giscus_category_id = os.getenv("GISCUS_CATEGORY_ID", "")
    
    return templates.TemplateResponse(
        "post.html",
        {
            "request": request,
            "post": post,
            "og_image": og_image,
            "active_tab": "writing",
            "giscus_repo": giscus_repo,
            "giscus_repo_id": giscus_repo_id,
            "giscus_category": giscus_category,
            "giscus_category_id": giscus_category_id
        }
    )

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "active_tab": "about"
        }
    )

@app.get("/archive", response_class=HTMLResponse)
async def archive_page(request: Request, db: Session = Depends(get_db)):
    # Fetch posts
    posts = db.query(Post).filter(Post.published == True).order_by(Post.created_at.desc()).all()
    
    # Group posts by year
    posts_by_year = {}
    for post in posts:
        year = post.created_at.year
        if year not in posts_by_year:
            posts_by_year[year] = []
        posts_by_year[year].append(post)
    
    sorted_posts_by_year = sorted(posts_by_year.items(), key=lambda x: x[0], reverse=True)

    return templates.TemplateResponse(
        "archive.html",
        {
            "request": request,
            "posts_by_year": sorted_posts_by_year,
            "active_tab": "archive"
        }
    )

# --- ADMIN ROUTES ---

@app.post("/admin/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    geeky_session: str = Cookie(default=None)
):
    if geeky_session != "authenticated":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        return JSONResponse({"error": "Invalid file type. JPG, PNG, WEBP, GIF only."}, status_code=400)

    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        return JSONResponse({"error": "File too large. Max 5MB."}, status_code=400)

    # Generate unique filename
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = f"static/uploads/{filename}"

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    return JSONResponse({"url": f"/static/uploads/{filename}", "filename": filename})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    q: str = None, 
    status_filter: str = None, 
    db: Session = Depends(get_db)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    
    query = db.query(Post)
    if q and q.strip():
        search_filter = f"%{q.strip()}%"
        query = query.filter(Post.title.ilike(search_filter))
    
    if status_filter:
        if status_filter.lower() == "published":
            query = query.filter(Post.published == True)
        elif status_filter.lower() == "draft":
            query = query.filter(Post.published == False)
            
    posts = query.order_by(Post.created_at.desc()).all()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "posts": posts,
            "active_tab": "admin",
            "q": q or "",
            "status_filter": status_filter or ""
        }
    )

@app.get("/admin/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})

@app.post("/admin/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def login_post(request: Request, password: str = Form(...)):
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    
    is_valid = False
    if stored_hash:
        try:
            is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            pass
            
    if is_valid:
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="geeky_session",
            value="authenticated",
            httponly=True,        # not accessible via JS
            samesite="strict",    # CSRF protection
            secure=(ENVIRONMENT == "production"),
            max_age=60 * 60 * 8,  # 8 hours
        )
        return response
    
    return templates.TemplateResponse(
        "admin/login.html", 
        {"request": request, "error": "// incorrect password"},
        status_code=401
    )

@app.get("/admin/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("geeky_session")
    return response

@app.get("/admin/post/new", response_class=HTMLResponse)
async def new_post_get(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin/editor.html", {"request": request, "post": None, "tags_str": ""})

@app.post("/admin/post/new")
async def new_post_post(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    category: str = Form(...),
    excerpt: str = Form(...),
    body: str = Form(...),
    tags: str = Form(None),
    featured: bool = Form(False),
    published: bool = Form(False),
    cover_image: str = Form(None),
    db: Session = Depends(get_db)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    new_post = Post(
        title=title,
        category=category,
        excerpt=excerpt,
        body=body,
        featured=featured,
        published=published,
        cover_image=cover_image
    )
    
    # Process many-to-many tags
    from models import Tag
    from slugify import slugify
    tag_objects = []
    if tags:
        for t_name in [t.strip() for t in tags.split(",") if t.strip()]:
            slug = slugify(t_name)
            tag = db.query(Tag).filter(Tag.slug == slug).first()
            if not tag:
                tag = Tag(name=t_name, slug=slug)
                db.add(tag)
                db.flush()
            tag_objects.append(tag)
    new_post.tags = tag_objects
    
    db.add(new_post)
    db.flush()
    if new_post.published and not new_post.notification_sent:
        background_tasks.add_task(send_new_post_emails, new_post.id)
        new_post.notification_sent = True
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/post/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_get(request: Request, post_id: int, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    tags_str = ", ".join([t.name for t in post.tags])
    return templates.TemplateResponse("admin/editor.html", {"request": request, "post": post, "tags_str": tags_str})

@app.post("/admin/post/{post_id}/edit")
async def edit_post_post(
    request: Request,
    post_id: int,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    category: str = Form(...),
    excerpt: str = Form(...),
    body: str = Form(...),
    tags: str = Form(None),
    featured: bool = Form(False),
    published: bool = Form(False),
    cover_image: str = Form(None),
    db: Session = Depends(get_db)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    was_published = post.published
        
    post.title = title
    post.category = category
    post.excerpt = excerpt
    post.body = body
    post.featured = featured
    post.published = published
    post.cover_image = cover_image
    
    # Process many-to-many tags
    from models import Tag
    from slugify import slugify
    tag_objects = []
    if tags:
        for t_name in [t.strip() for t in tags.split(",") if t.strip()]:
            slug = slugify(t_name)
            tag = db.query(Tag).filter(Tag.slug == slug).first()
            if not tag:
                tag = Tag(name=t_name, slug=slug)
                db.add(tag)
                db.flush()
            tag_objects.append(tag)
    post.tags = tag_objects
    
    if post.published and not was_published and not post.notification_sent:
        background_tasks.add_task(send_new_post_emails, post.id)
        post.notification_sent = True
        
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/post/{post_id}/delete")
async def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    db.delete(post)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/media", response_class=HTMLResponse)
async def admin_media(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    uploads_dir = "static/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Get all uploaded files
    filenames = []
    for f in os.listdir(uploads_dir):
        if os.path.isfile(os.path.join(uploads_dir, f)) and not f.startswith('.'):
            filenames.append(f)
            
    # Fetch all posts to check references
    posts = db.query(Post).all()
    
    files_data = []
    for fname in filenames:
        fpath = os.path.join(uploads_dir, fname)
        size_bytes = os.path.getsize(fpath)
        size_kb = round(size_bytes / 1024, 1)
        
        # Check references
        referencing_posts = []
        for post in posts:
            referenced = False
            # Check cover_image
            if post.cover_image and fname in post.cover_image:
                referenced = True
            # Check body (markdown)
            if post.body and fname in post.body:
                referenced = True
                
            if referenced:
                referencing_posts.append(post)
                
        files_data.append({
            "filename": fname,
            "url": f"/static/uploads/{fname}",
            "size_kb": size_kb,
            "referenced": len(referencing_posts) > 0,
            "referencing_posts": referencing_posts
        })
        
    # Sort files_data by referenced (unused first) and size
    files_data.sort(key=lambda x: (x["referenced"], -x["size_kb"]))
    
    return templates.TemplateResponse(
        "admin/media.html",
        {
            "request": request,
            "files": files_data,
            "active_tab": "admin"
        }
    )

@app.post("/admin/media/{filename}/delete")
async def delete_media(request: Request, filename: str):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    # Security: check directory traversal
    clean_filename = os.path.basename(filename)
    if clean_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    filepath = os.path.join("static/uploads", clean_filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        
    return RedirectResponse(url="/admin/media", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    from sqlalchemy import func, desc, distinct
    from datetime import datetime, timedelta
    from urllib.parse import urlparse
    
    # 1. Timestamps
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # 2. Summary stats (excluding clicks)
    total_views_all_time = db.query(PageView).filter(~PageView.path.like("click:%")).count()
    total_views_7_days = db.query(PageView).filter(~PageView.path.like("click:%"), PageView.timestamp >= seven_days_ago).count()
    total_views_30_days = db.query(PageView).filter(~PageView.path.like("click:%"), PageView.timestamp >= thirty_days_ago).count()
    
    uniques_7_days = db.query(func.count(distinct(PageView.visitor_hash))).filter(
        ~PageView.path.like("click:%"), PageView.timestamp >= seven_days_ago
    ).scalar() or 0
    
    uniques_30_days = db.query(func.count(distinct(PageView.visitor_hash))).filter(
        ~PageView.path.like("click:%"), PageView.timestamp >= thirty_days_ago
    ).scalar() or 0
    
    # 3. Top posts by view count (exclude draft and clicks)
    top_posts_data = db.query(
        Post,
        func.count(PageView.id).label("views")
    ).join(
        PageView, PageView.post_id == Post.id
    ).filter(
        Post.published == True,
        ~PageView.path.like("click:%")
    ).group_by(
        Post.id
    ).order_by(
        desc("views")
    ).limit(10).all()
    
    # Format list of top posts
    top_posts = []
    for post, views in top_posts_data:
        top_posts.append({
            "title": post.title,
            "slug": post.slug,
            "views": views
        })
        
    # 4. Top referrers (grouped & normalized, excluding local domains)
    referrers_raw = db.query(PageView.referrer).filter(
        ~PageView.path.like("click:%"),
        PageView.referrer.isnot(None),
        PageView.referrer != ""
    ).all()
    
    local_domains = ["geekykunoichi.com", "localhost", "127.0.0.1"]
    domain_counts = {}
    for (ref,) in referrers_raw:
        try:
            parsed = urlparse(ref)
            domain = parsed.netloc or parsed.path
            if not domain:
                continue
            if domain.startswith("www."):
                domain = domain[4:]
            # Filter out local referrers
            if any(ld in domain for ld in local_domains):
                continue
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        except Exception:
            pass
            
    top_referrers = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 5. Click through counts (newsletter and posts)
    newsletter_clicks = db.query(PageView).filter(PageView.path == "click:newsletter_cta").count()
    
    post_clicks_data = db.query(
        Post.title,
        Post.slug,
        func.count(PageView.id).label("clicks")
    ).join(
        PageView, PageView.post_id == Post.id
    ).filter(
        PageView.path.like("click:post:%")
    ).group_by(
        Post.id
    ).order_by(
        desc("clicks")
    ).all()
    
    post_clicks = []
    for title, slug, clicks in post_clicks_data:
        post_clicks.append({
            "title": title,
            "slug": slug,
            "clicks": clicks
        })
        
    # 6. Views per day for the last 30 days (inline SVG bar chart)
    # Group in SQLite using strftime
    daily_views_data = db.query(
        func.strftime("%Y-%m-%d", PageView.timestamp).label("day"),
        func.count(PageView.id).label("views"),
        func.count(distinct(PageView.visitor_hash)).label("uniques")
    ).filter(
        ~PageView.path.like("click:%"),
        PageView.timestamp >= thirty_days_ago
    ).group_by(
        "day"
    ).all()
    
    daily_map = {row[0]: {"views": row[1], "uniques": row[2]} for row in daily_views_data}
    
    views_per_day = []
    for i in range(29, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        stats = daily_map.get(day_str, {"views": 0, "uniques": 0})
        views_per_day.append({
            "date_label": day.strftime("%b %d"),
            "date_full": day_str,
            "views": stats["views"],
            "uniques": stats["uniques"]
        })
        
    # 7. Generate SVG values
    max_val = max([d["views"] for d in views_per_day] or [1])
    if max_val == 0:
        max_val = 1
        
    chart_height = 200
    bar_width = 18
    gap = 8
    
    bars = []
    for i, day in enumerate(views_per_day):
        v_height = (day["views"] / max_val) * chart_height
        u_height = (day["uniques"] / max_val) * chart_height
        
        # Draw from bottom (y = 220)
        v_y = 220 - v_height
        u_y = 220 - u_height
        
        x = i * (bar_width + gap) + 40
        
        bars.append({
            "date": day["date_label"],
            "views": day["views"],
            "uniques": day["uniques"],
            "x": x,
            "v_y": v_y,
            "v_height": v_height,
            "u_y": u_y,
            "u_height": u_height
        })
        
    return templates.TemplateResponse(
        "admin/analytics.html",
        {
            "request": request,
            "total_views_all_time": total_views_all_time,
            "total_views_7_days": total_views_7_days,
            "total_views_30_days": total_views_30_days,
            "uniques_7_days": uniques_7_days,
            "uniques_30_days": uniques_30_days,
            "top_posts": top_posts,
            "top_referrers": top_referrers,
            "newsletter_clicks": newsletter_clicks,
            "post_clicks": post_clicks,
            "bars": bars,
            "chart_width": 29 * (bar_width + gap) + 80
        }
    )

# --- API ENDPOINTS ---


@app.get("/api/posts")
async def api_posts(page: int = 1, category: str = None, tag: str = None, db: Session = Depends(get_db)):
    from models import Tag
    query = db.query(Post).filter(Post.published == True)
    
    # Support filtering by tag or category (for backward compatibility)
    if tag and tag.lower() != "all":
        query = query.filter(Post.tags.any(Tag.slug == tag))
    elif category and category.lower() != "all":
        query = query.filter(Post.category == category)
        
    total = query.count()
    total_pages = max(1, (total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)
    page = max(1, min(page, total_pages))
    
    offset = (page - 1) * POSTS_PER_PAGE
    
    if (tag and tag.lower() != "all") or (category and category.lower() != "all"):
        posts = query.order_by(Post.created_at.desc()).offset(offset).limit(POSTS_PER_PAGE).all()
    else:
        posts = query.order_by(Post.featured.desc(), Post.created_at.desc()).offset(offset).limit(POSTS_PER_PAGE).all()
        
    posts_data = []
    for post in posts:
        posts_data.append({
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "category": post.category,
            "tags": [t.name for t in post.tags],
            "excerpt": post.excerpt,
            "read_time": post.read_time,
            "featured": post.featured,
            "published": post.published,
            "cover_image": post.cover_image,
            "created_at": post.created_at.isoformat(),
            "created_date_formatted": post.created_at.strftime('%B %d, %Y')
        })
        
    return JSONResponse(content={
        "posts": posts_data,
        "page": page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    })

class PreviewRequest(BaseModel):
    markdown: str

@app.post("/api/preview")
async def api_preview(data: PreviewRequest):
    import markdown2
    rendered = markdown2.markdown(
        data.markdown,
        extras=["fenced-code-blocks", "tables", "strike", "code-friendly"]
    )
    return {"html": rendered}

class SubscribeRequest(BaseModel):
    email: str

@app.post("/api/subscribe")
async def api_subscribe(data: SubscribeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    import re
    from models import EmailSubscriber
    from email_utils import send_welcome_email
    
    email = data.email.strip().lower()
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        return JSONResponse(
            content={"success": False, "message": "Please enter a valid email address."},
            status_code=400
        )
        
    existing = db.query(EmailSubscriber).filter(EmailSubscriber.email == email).first()
    if not existing:
        new_sub = EmailSubscriber(email=email)
        db.add(new_sub)
        db.commit()
        
    background_tasks.add_task(send_welcome_email, email)
    
    return JSONResponse(
        content={"success": True, "message": "Thanks for subscribing!"}
    )

class ClickTrackRequest(BaseModel):
    target: str
    source_path: str

@app.post("/api/track-click")
async def track_click(payload: ClickTrackRequest, request: Request, db: Session = Depends(get_db)):
    try:
        # Exclude if admin is logged in (authenticated session cookie)
        if request.cookies.get("geeky_session") == "authenticated":
            return {"status": "skipped", "reason": "admin"}

        # Exclude bots
        user_agent = request.headers.get("user-agent", "")
        ua_lower = user_agent.lower()
        bot_signals = ["bot", "spider", "crawl", "slurp", "tracker", "lighthouse", "python-urllib", "pytest"]
        if any(bot in ua_lower for bot in bot_signals):
            return {"status": "skipped", "reason": "bot"}

        # Extract client IP
        ip_address = request.headers.get("x-forwarded-for")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else "unknown"

        # Generate daily unique visitor hash
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        salt = os.getenv("ANALYTICS_SALT", "default_salt_for_geeky_kunoichi")
        input_str = f"{ip_address}{user_agent}{today_str}{salt}"
        visitor_hash = hashlib.sha256(input_str.encode("utf-8")).hexdigest()

        target = payload.target
        source_path = payload.source_path

        # Determine post_id for post click tracking
        post_id = None
        if target.startswith("click:post:"):
            slug = target.split("click:post:")[1]
            post = db.query(Post).filter(Post.slug == slug).first()
            if post:
                post_id = post.id

        view = PageView(
            timestamp=datetime.utcnow(),
            path=target,
            post_id=post_id,
            referrer=source_path,
            user_agent=user_agent,
            visitor_hash=visitor_hash
        )
        db.add(view)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        import logging
        logging.error(f"Click tracking API error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = "", db: Session = Depends(get_db)):
    posts = []
    if q.strip():
        search_filter = f"%{q}%"
        posts = db.query(Post).filter(
            Post.published == True,
            (Post.title.ilike(search_filter) | 
             Post.excerpt.ilike(search_filter) | 
             Post.body.ilike(search_filter))
        ).order_by(Post.created_at.desc()).all()
        
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "posts": posts,
            "query": q,
            "active_tab": "search"
        }
    )

@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.published == True).all()
    base = "https://geekykunoichi.com"

    urls = [
        f"""
  <url>
    <loc>{base}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""",
        f"""
  <url>
    <loc>{base}/about</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>""",
        f"""
  <url>
    <loc>{base}/archive</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>""",
    ]

    for post in posts:
        urls.append(f"""
  <url>
    <loc>{base}/post/{post.slug}</loc>
    <lastmod>{post.updated_at.strftime('%Y-%m-%d') if post.updated_at else post.created_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>"""

    return Response(content=xml, media_type="application/xml")


@app.get("/feed.xml", include_in_schema=False)
def rss_feed(db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.published == True).order_by(Post.created_at.desc()).limit(20).all()
    base = "https://geekykunoichi.com"
    now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    for post in posts:
        pub_date = post.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")
        items.append(f"""
    <item>
      <title><![CDATA[{post.title}]]></title>
      <link>{base}/post/{post.slug}</link>
      <guid isPermaLink="true">{base}/post/{post.slug}</guid>
      <description><![CDATA[{post.excerpt}]]></description>
      <pubDate>{pub_date}</pubDate>
      <category>{post.category}</category>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>GeekyKunoichi</title>
    <link>{base}</link>
    <description>Technical deep-dives, personal essays, and everything in between. Written by Geetika.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
    {''.join(items)}
  </channel>
</rss>"""

    return Response(content=xml, media_type="application/rss+xml")
# Trigger reload
