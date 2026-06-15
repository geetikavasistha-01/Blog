// GeekyKunoichi JavaScript utilities

document.addEventListener("DOMContentLoaded", () => {
  // 1. Tag Filtering on Homepage
  const tagButtons = document.querySelectorAll(".tag-btn");
  const postsGrid = document.getElementById("posts-grid");

  if (tagButtons.length > 0 && postsGrid) {
    tagButtons.forEach((btn) => {
      btn.addEventListener("click", async () => {
        // Remove active class from all buttons and add to the clicked one
        tagButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        const tag = btn.getAttribute("data-tag");
        await filterPosts(tag);
      });
    });
  }

  async function filterPosts(tag, page = 1) {
    try {
      postsGrid.style.opacity = "0.5";
      let url = `/api/posts?page=${page}`;
      if (tag && tag !== "All") {
        url += `&tag=${encodeURIComponent(tag)}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch posts");

      const data = await response.json();
      renderPosts(data.posts, tag === "All" || !tag);
      renderPagination(data, tag);

      // Update URL query parameters silently
      const newUrl = new URL(window.location.href);
      if (tag && tag !== "All") {
        newUrl.searchParams.set("tag", tag);
      } else {
        newUrl.searchParams.delete("tag");
      }
      // Clean up old category parameter if present
      newUrl.searchParams.delete("category");
      
      if (page > 1) {
        newUrl.searchParams.set("page", page);
      } else {
        newUrl.searchParams.delete("page");
      }
      window.history.pushState({}, "", newUrl.toString());
    } catch (error) {
      console.error("Error filtering posts:", error);
      postsGrid.innerHTML = `<p style="grid-column: 1/-1; padding: 3rem; text-align: center; color: #ff5555; font-family: monospace;">Error loading posts. Please try again.</p>`;
    } finally {
      postsGrid.style.opacity = "1";
    }
  }

  function renderPagination(data, tag) {
    let container = document.getElementById("pagination-container");
    
    if (data.total_pages <= 1) {
      if (container) {
        container.style.display = "none";
      }
      return;
    }
    
    if (!container) {
      container = document.createElement("div");
      container.id = "pagination-container";
      container.className = "pagination";
      postsGrid.parentNode.insertBefore(container, postsGrid.nextSibling);
    }
    
    container.style.display = "flex";
    container.innerHTML = "";
    
    // Previous Button
    if (data.has_prev) {
      const prevBtn = document.createElement("a");
      prevBtn.href = "#";
      prevBtn.className = "page-btn prev-btn";
      prevBtn.innerHTML = "&larr; Previous";
      prevBtn.addEventListener("click", (e) => {
        e.preventDefault();
        filterPosts(tag, data.page - 1);
      });
      container.appendChild(prevBtn);
    } else {
      const prevSpan = document.createElement("span");
      prevSpan.className = "page-btn prev-btn disabled";
      prevSpan.innerHTML = "&larr; Previous";
      container.appendChild(prevSpan);
    }
    
    // Page Indicator
    const indicator = document.createElement("span");
    indicator.className = "page-indicator";
    indicator.textContent = `Page ${data.page} of ${data.total_pages}`;
    container.appendChild(indicator);
    
    // Next Button
    if (data.has_next) {
      const nextBtn = document.createElement("a");
      nextBtn.href = "#";
      nextBtn.className = "page-btn next-btn";
      nextBtn.innerHTML = "Next &rarr;";
      nextBtn.addEventListener("click", (e) => {
        e.preventDefault();
        filterPosts(tag, data.page + 1);
      });
      container.appendChild(nextBtn);
    } else {
      const nextSpan = document.createElement("span");
      nextSpan.className = "page-btn next-btn disabled";
      nextSpan.innerHTML = "Next &rarr;";
      container.appendChild(nextSpan);
    }
  }

  function renderPosts(posts, isAllFilter) {
    if (posts.length === 0) {
      postsGrid.innerHTML = `<p style="grid-column: 1/-1; padding: 5rem; text-align: center; color: var(--muted); font-family: 'DM Mono', monospace;">// No posts found matching this filter.</p>`;
      return;
    }

    postsGrid.innerHTML = "";
    
    let onLeft = true;

    posts.forEach((post) => {
      const card = document.createElement("a");
      card.href = `/post/${post.slug}`;
      card.id = `post-${post.id}`;
      
      // Check if it's the featured post and we are on the "All" filter
      const isFeatured = post.featured && isAllFilter;
      
      if (isFeatured) {
        card.className = "post-card featured";
      } else {
        card.className = `post-card ${onLeft ? "border-right" : ""}`;
        onLeft = !onLeft;
      }

      // Date parsing/formatting or using the pre-formatted string from API
      const dateStr = post.created_date_formatted || post.created_at;
      const tagsStr = post.tags && post.tags.length > 0 ? post.tags.join(", ") : post.category;

      let cardHTML = "";
      if (post.cover_image) {
        cardHTML += `
          <div class="card-cover" style="margin-bottom:1rem;overflow:hidden;max-height:160px;">
            <img src="${post.cover_image}" alt="${post.title}"
                 style="width:100%;height:160px;object-fit:cover;filter:brightness(0.85);">
          </div>
        `;
      }
      
      cardHTML += `<div class="post-card-content">`;
      if (isFeatured) {
        cardHTML += `
          <span class="featured-badge">Featured</span>
          <div class="featured-layout">
            <div>
              <span class="post-card-category">// ${tagsStr}</span>
              <h2 class="post-card-title">${post.title}</h2>
            </div>
            <div>
              <p class="post-card-excerpt">${post.excerpt || ""}</p>
            </div>
          </div>
        `;
      } else {
        cardHTML += `
          <span class="post-card-category">// ${tagsStr}</span>
          <h2 class="post-card-title">${post.title}</h2>
          <p class="post-card-excerpt">${post.excerpt || ""}</p>
        `;
      }
      cardHTML += `
        </div>
        <div class="post-card-footer">
          <div class="post-card-meta">
            ${dateStr}<span class="separator">•</span>${post.read_time} min read
          </div>
          <div class="post-card-arrow">→</div>
        </div>
      `;

      card.innerHTML = cardHTML;
      postsGrid.appendChild(card);
    });
  }

  // Intercept server-rendered pagination clicks
  const initPaginationListeners = () => {
    const container = document.getElementById("pagination-container");
    if (container) {
      const prevBtn = container.querySelector(".prev-btn:not(.disabled)");
      const nextBtn = container.querySelector(".next-btn:not(.disabled)");
      
      const activeTag = document.querySelector(".tag-btn.active");
      const tag = activeTag ? activeTag.getAttribute("data-tag") : "All";
      
      if (prevBtn) {
        prevBtn.addEventListener("click", (e) => {
          e.preventDefault();
          const url = new URL(prevBtn.href);
          const page = parseInt(url.searchParams.get("page")) || 1;
          filterPosts(tag, page);
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener("click", (e) => {
          e.preventDefault();
          const url = new URL(nextBtn.href);
          const page = parseInt(url.searchParams.get("page")) || 1;
          filterPosts(tag, page);
        });
      }
    }
  };
  initPaginationListeners();

  // 2. Admin Live Markdown Preview
  const editorTextarea = document.getElementById("post-body");
  const previewContent = document.getElementById("preview-content");

  if (editorTextarea && previewContent) {
    let debounceTimer;

    const updatePreview = async () => {
      const markdownText = editorTextarea.value;
      if (!markdownText.trim()) {
        previewContent.innerHTML = `<p style="color: var(--muted); font-style: italic;">Nothing to preview yet...</p>`;
        return;
      }

      try {
        const response = await fetch("/api/preview", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ markdown: markdownText }),
        });

        if (response.ok) {
          const data = await response.json();
          previewContent.innerHTML = data.html;
        } else {
          previewContent.innerHTML = `<p style="color: #ff5555;">Preview failed to render.</p>`;
        }
      } catch (err) {
        console.error("Preview error:", err);
        previewContent.innerHTML = `<p style="color: #ff5555;">Error rendering live preview.</p>`;
      }
    };

    editorTextarea.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(updatePreview, 300); // 300ms debounce
    });

    // Run preview once on load if there's already content (e.g. editing)
    if (editorTextarea.value) {
      updatePreview();
    }
  }
});

// ─── Theme Toggle: Kunoichi Animation ───────────────────────────────────────

let themeAnimating = false;

function triggerThemeToggle() {
  if (themeAnimating) return;
  themeAnimating = true;

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const isLight = !isDark;
  const W = window.innerWidth;
  const H = window.innerHeight;
  const fig = document.getElementById('k-figure');
  const star = document.getElementById('k-shuriken');
  const burst = document.getElementById('k-burst');
  const btn = document.getElementById('theme-toggle');

  // Disable button during animation
  btn.style.pointerEvents = 'none';

  // Step 1: Slide kunoichi in from left
  fig.style.cssText = `
    position: absolute;
    bottom: 80px;
    left: -100px;
    width: 72px;
    height: 110px;
    opacity: 1;
    transition: left 0.55s cubic-bezier(0.22, 1, 0.36, 1);
  `;
  setTimeout(() => { fig.style.left = '50px'; }, 20);

  // Step 2: Throw shuriken after she arrives
  setTimeout(() => {
    const startX = 122;
    const startY = H - 150;

    star.style.cssText = `
      position: absolute;
      width: 20px;
      height: 20px;
      opacity: 1;
      left: ${startX}px;
      top: ${startY}px;
    `;

    const targetX = W - 10;
    const targetY = startY;
    const arcHeight = 22;
    let t0 = null;
    const duration = 440;

    function flyShuriken(ts) {
      if (!t0) t0 = ts;
      const p = Math.min((ts - t0) / duration, 1);
      // ease in-out
      const e = p < 0.5 ? 2 * p * p : -1 + (4 - 2 * p) * p;
      const cx = startX + (targetX - startX) * e;
      // slight arc upward then down
      const cy = startY - Math.sin(p * Math.PI) * arcHeight;
      star.style.left = cx + 'px';
      star.style.top = cy + 'px';
      star.style.transform = `rotate(${p * 900}deg)`;
      if (p < 1) {
        requestAnimationFrame(flyShuriken);
      } else {
        onImpact(targetX, startY);
      }
    }
    requestAnimationFrame(flyShuriken);
  }, 580);

  // Step 3: Impact — burst expands, theme switches
  function onImpact(ix, iy) {
    star.style.opacity = '0';

    const burstColor = isLight ? '#0e0e0e' : '#f5f0e8';
    const size = Math.max(W, H) * 3;

    burst.style.cssText = `
      position: absolute;
      border-radius: 50%;
      width: ${size}px;
      height: ${size}px;
      background: ${burstColor};
      left: ${ix - size / 2}px;
      top: ${iy - size / 2}px;
      opacity: 1;
      transform: scale(0);
      transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
      pointer-events: none;
    `;

    // Trigger burst expand
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        burst.style.transform = 'scale(1)';
      });
    });

    // Switch theme at burst midpoint
    setTimeout(() => {
      const nextTheme = isDark ? null : 'dark';
      if (nextTheme) {
        document.documentElement.setAttribute('data-theme', nextTheme);
        localStorage.setItem('gk-theme', 'dark');
        btn.textContent = '☀ Light Mode';
      } else {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('gk-theme', 'light');
        btn.textContent = '☽ Dark Mode';
      }

      updateGiscusTheme();

      // Step 4: Fade burst out, slide kunoichi off-screen
      setTimeout(() => {
        burst.style.opacity = '0';
        burst.style.transition = 'opacity 0.3s ease';
        fig.style.transition = 'left 0.4s ease-in, opacity 0.25s ease';
        fig.style.left = '-110px';
        fig.style.opacity = '0';

        setTimeout(() => {
          // Reset burst for next use
          burst.style.transform = 'scale(0)';
          burst.style.transition = 'none';
          burst.style.opacity = '1';
          themeAnimating = false;
          btn.style.pointerEvents = 'auto';
        }, 420);
      }, 220);
    }, 380);
  }
}

function updateGiscusTheme() {
  const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'transparent_dark' : 'light';
  const iframe = document.querySelector('iframe.giscus-frame');
  if (!iframe) return;
  iframe.contentWindow.postMessage({
    giscus: {
      setConfig: {
        theme: theme
      }
    }
  }, 'https://giscus.app');
}

// ─── Reading Progress Bar ────────────────────────────────────────────────────

function initReadingProgress() {
  const bar = document.getElementById('reading-progress');
  if (!bar) return; // only runs on post pages

  function updateProgress() {
    const postBody = document.querySelector('.post-body');
    if (!postBody) return;

    const bodyTop = postBody.getBoundingClientRect().top + window.scrollY;
    const bodyBottom = bodyTop + postBody.offsetHeight;
    const viewportHeight = window.innerHeight;
    const scrolled = window.scrollY;

    // Progress goes from when post body starts to when it ends
    const start = bodyTop - viewportHeight * 0.1;
    const end = bodyBottom - viewportHeight * 0.9;
    const range = end - start;

    if (range <= 0) {
      bar.style.width = '100%';
      return;
    }

    const progress = Math.min(Math.max((scrolled - start) / range, 0), 1);
    bar.style.width = (progress * 100) + '%';
  }

  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress(); // set on load
}

// ─── Copy Code Buttons ───────────────────────────────────────────────────────

function initCopyCodeButtons() {
  const preBlocks = document.querySelectorAll('.post-body pre');
  if (!preBlocks.length) return;

  preBlocks.forEach(pre => {
    // Wrap in a relative container
    const wrapper = document.createElement('div');
    wrapper.className = 'code-block-wrapper';
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    // Create copy button
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'copy';
    btn.setAttribute('aria-label', 'Copy code to clipboard');
    wrapper.appendChild(btn);

    btn.addEventListener('click', async () => {
      const code = pre.querySelector('code');
      const text = code ? code.innerText : pre.innerText;

      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = 'copied ✓';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = 'copy';
          btn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        // Fallback for older browsers
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = 'copied ✓';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = 'copy';
          btn.classList.remove('copied');
        }, 2000);
      }
    });
  });
}

// ─── Init on DOM Ready ───────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initReadingProgress();
  initCopyCodeButtons();
  initMediumEditor();
  initChangingWord();
  initNewsletter();
  initClickTracking();

  // Set correct button label on page load
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.textContent = isDark ? '☀ Light Mode' : '☽ Dark Mode';
  }
});

function initClickTracking() {
  document.addEventListener('click', (e) => {
    const postCard = e.target.closest('.post-card');
    if (postCard) {
      const href = postCard.getAttribute('href');
      if (href && href.startsWith('/post/')) {
        const slug = href.substring('/post/'.length);
        fetch('/api/track-click', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            target: `click:post:${slug}`,
            source_path: window.location.pathname
          }),
          keepalive: true
        }).catch(() => {});
      }
    }
  });
}

function initNewsletter() {
  const form = document.getElementById("newsletter-form");
  if (!form) return;
  
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const emailInput = document.getElementById("newsletter-email");
    const email = emailInput.value.trim();
    const submitBtn = form.querySelector("button[type='submit']");
    const originalText = submitBtn.textContent;
    
    // Track newsletter button click
    fetch("/api/track-click", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        target: "click:newsletter_cta",
        source_path: window.location.pathname
      }),
      keepalive: true
    }).catch(() => {});
    
    try {
      submitBtn.disabled = true;
      submitBtn.textContent = "Saving...";
      
      const response = await fetch("/api/subscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        emailInput.value = "";
        submitBtn.textContent = data.message || "Subscribed ✓";
        submitBtn.style.backgroundColor = "#7ec87e";
        submitBtn.style.color = "#000";
        setTimeout(() => {
          submitBtn.textContent = originalText;
          submitBtn.style.backgroundColor = "";
          submitBtn.style.color = "";
          submitBtn.disabled = false;
        }, 3000);
      } else {
        alert(data.message || "Failed to subscribe. Please try again.");
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    } catch (err) {
      console.error("Subscription error:", err);
      alert("An error occurred. Please try again.");
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  });
}

// ─── Changing Word Animation ──────────────────────────────────────────────────
function initChangingWord() {
  const elements = document.querySelectorAll('.changing-word');
  if (elements.length === 0) return;

  const words = ['Geeky', 'Cheeky'];
  let index = 0;

  setInterval(() => {
    index = (index + 1) % words.length;
    const nextWord = words[index];

    elements.forEach(el => {
      el.classList.add('fade-out');
    });

    setTimeout(() => {
      elements.forEach(el => {
        el.textContent = nextWord;
        el.classList.remove('fade-out');
      });
    }, 200);
  }, 1000);
}



// ─── Medium-Style Editor ─────────────────────────────────────────────────────
function initMediumEditor() {
  const editorContent = document.getElementById('editor-content');
  if (!editorContent) return;

  const toolbar = document.getElementById('floating-toolbar');
  const linkPopover = document.getElementById('link-popover');
  const previewBody = document.getElementById('preview-body');
  const wordCountEl = document.getElementById('word-count');
  const bodyHidden = document.getElementById('body-hidden');

  // Load existing content
  const existingBody = bodyHidden ? bodyHidden.value.trim() : '';
  if (existingBody) {
    editorContent.innerHTML = existingBody;
  }

  // Show floating toolbar on text selection
  let selTimeout;
  document.addEventListener('selectionchange', () => {
    clearTimeout(selTimeout);
    selTimeout = setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !sel.toString().trim()) {
        hideToolbar(); return;
      }
      const range = sel.getRangeAt(0);
      if (!editorContent.contains(range.commonAncestorContainer)) {
        hideToolbar(); return;
      }
      showToolbar(range);
    }, 80);
  });

  function showToolbar(range) {
    const rect = range.getBoundingClientRect();
    toolbar.style.display = 'flex';
    linkPopover.style.display = 'none';
    const tw = toolbar.offsetWidth;
    let left = rect.left + rect.width / 2 - tw / 2;
    left = Math.max(12, Math.min(left, window.innerWidth - tw - 12));
    toolbar.style.left = left + 'px';
    toolbar.style.top = (rect.top + window.scrollY - toolbar.offsetHeight - 12) + 'px';
  }

  function hideToolbar() {
    toolbar.style.display = 'none';
    linkPopover.style.display = 'none';
  }

  document.addEventListener('mousedown', (e) => {
    if (!toolbar.contains(e.target) && !linkPopover.contains(e.target)) {
      setTimeout(hideToolbar, 150);
    }
  });

  // Format buttons
  toolbar.querySelectorAll('.fmt-btn').forEach(btn => {
    btn.addEventListener('mousedown', (e) => {
      e.preventDefault();
      applyFormat(btn.dataset.cmd);
    });
  });

  function applyFormat(cmd) {
    editorContent.focus();
    switch (cmd) {
      case 'bold':      document.execCommand('bold'); break;
      case 'italic':    document.execCommand('italic'); break;
      case 'h2':        document.execCommand('formatBlock', false, 'h2'); break;
      case 'h3':        document.execCommand('formatBlock', false, 'h3'); break;
      case 'blockquote':document.execCommand('formatBlock', false, 'blockquote'); break;
      case 'code':      wrapWith('code'); break;
      case 'link':      showLinkPopover(); return;
    }
    syncAndPreview();
    hideToolbar();
  }

  function wrapWith(tag) {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0);
    const el = document.createElement(tag);
    try { range.surroundContents(el); }
    catch (e) { el.appendChild(range.extractContents()); range.insertNode(el); }
    sel.removeAllRanges();
  }

  function showLinkPopover() {
    linkPopover.style.display = 'flex';
    linkPopover.style.left = toolbar.style.left;
    linkPopover.style.top = (parseInt(toolbar.style.top) + toolbar.offsetHeight + 4) + 'px';
    document.getElementById('link-url-input').value = '';
    document.getElementById('link-url-input').focus();
  }

  window.applyLink = function () {
    const url = document.getElementById('link-url-input').value.trim();
    if (!url) return;
    editorContent.focus();
    document.execCommand('createLink', false, url);
    syncAndPreview();
    hideToolbar();
  };

  document.getElementById('link-url-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') window.applyLink();
    if (e.key === 'Escape') hideToolbar();
  });

  // Sync to hidden textarea
  function syncBodyToHidden() {
    if (bodyHidden) bodyHidden.value = editorContent.innerHTML;
  }

  // Word count
  function updateWordCount() {
    const words = editorContent.innerText.trim().split(/\s+/).filter(Boolean).length;
    if (wordCountEl) wordCountEl.textContent = words + (words === 1 ? ' word' : ' words');
  }

  // Live preview
  let previewTimeout;
  async function triggerPreview() {
    clearTimeout(previewTimeout);
    previewTimeout = setTimeout(async () => {
      const text = editorContent.innerText.trim();
      if (!text) {
        previewBody.innerHTML = '<p class="preview-empty">Nothing to preview yet...</p>';
        return;
      }
      try {
        const res = await fetch('/api/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ markdown: editorContent.innerHTML })
        });
        const data = await res.json();
        previewBody.innerHTML = data.html || editorContent.innerHTML;
      } catch {
        previewBody.innerHTML = editorContent.innerHTML;
      }
    }, 300);
  }

  function syncAndPreview() {
    syncBodyToHidden();
    updateWordCount();
    triggerPreview();
  }

  editorContent.addEventListener('input', syncAndPreview);

  if (existingBody) { syncAndPreview(); }

  // Cover image upload
  document.getElementById('cover-file-input')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/admin/upload-image', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.url) {
      document.getElementById('cover-image-value').value = data.url;
      document.getElementById('cover-strip').innerHTML = `
        <div class="cover-preview-inline">
          <img src="${data.url}" alt="cover">
          <button type="button" class="remove-cover" onclick="removeCover()">✕</button>
        </div>
        <input type="hidden" id="cover-image-value" name="cover_image" value="${data.url}">
        <input type="file" id="cover-file-input" accept="image/*" style="display:none">
      `;
    }
  });

  window.removeCover = function () {
    document.getElementById('cover-strip').innerHTML = `
      <button type="button" class="add-cover-btn" onclick="document.getElementById('cover-file-input').click()">+ Add cover image</button>
      <input type="file" id="cover-file-input" accept="image/*" style="display:none">
      <input type="hidden" id="cover-image-value" name="cover_image" value="">
    `;
  };

  // Submit post
  window.submitPost = async function () {
    syncBodyToHidden();
    const title = document.getElementById('post-title').value.trim();
    if (!title) { alert('Title is required.'); return; }
    const fd = new FormData();
    fd.append('title', title);
    fd.append('excerpt', document.getElementById('post-excerpt').value.trim());
    fd.append('category', document.getElementById('category').value);
    fd.append('body', bodyHidden.value);
    fd.append('tags', document.getElementById('post-tags').value.trim());
    fd.append('cover_image', document.getElementById('cover-image-value')?.value || '');
    if (document.getElementById('featured').checked) fd.append('featured', 'on');
    if (document.getElementById('published').checked) fd.append('published', 'on');

    const isEdit = window.location.pathname.includes('/edit');
    const action = window.location.pathname;
    const res = await fetch(action, { method: 'POST', body: fd });
    if (res.redirected) window.location.href = res.url;
    else if (res.ok) window.location.href = '/admin';
    else alert('Something went wrong. Check the console.');
  };

  // Cmd/Ctrl + Enter to publish
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') window.submitPost();
  });
}


