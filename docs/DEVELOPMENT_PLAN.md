# QuizNova — Development Plan & Roadmap

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Total Estimated Duration:** 12 Weeks  

---

## Table of Contents

1. [Folder Structure](#1-folder-structure)
2. [Development Phases](#2-development-phases)
3. [Module Build Order](#3-module-build-order)
4. [Coding Standards](#4-coding-standards)
5. [Testing Checklist](#5-testing-checklist)
6. [Deployment Guide](#6-deployment-guide)
7. [Future Roadmap (v2+)](#7-future-roadmap-v2)
8. [Technology Versions](#8-technology-versions)

---

## 1. Folder Structure

```
QuizNova/
│
├── app.py                          # Flask app factory + blueprint registration
├── config.py                       # Configuration classes (Dev, Prod, Test)
├── requirements.txt                # Python dependencies
├── README.md                       # Project overview and setup instructions
├── .env                            # Environment variables (never committed)
├── .env.example                    # Template for .env
├── .gitignore                      # Git ignore rules
│
├── instance/                       # Flask instance folder (auto-created)
│   └── quiznova.db                 # (unused — MySQL used instead)
│
├── database/
│   ├── schema.sql                  # Complete MySQL DDL
│   └── seed.py                     # Seed script: categories, questions, admin
│
├── models/
│   ├── __init__.py                 # SQLAlchemy db instance
│   ├── user.py                     # User model
│   ├── category.py                 # Category model
│   ├── subcategory.py              # Subcategory model
│   ├── question.py                 # Question model
│   ├── quiz.py                     # QuizAttempt, AttemptQuestion, AttemptAnswer
│   ├── result.py                   # Result model
│   ├── certificate.py              # Certificate model
│   ├── achievement.py              # Achievement, AchievementEarned models
│   ├── leaderboard.py              # LeaderboardCache model
│   └── log.py                      # ActivityLog, AntiCheatLog, Settings
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                     # /auth/* routes (login, register, logout, profile)
│   ├── quiz.py                     # /quiz/* routes (browse, start, attempt, result)
│   ├── dashboard.py                # /dashboard/* routes (main, achievements, settings)
│   ├── admin.py                    # /admin/* routes (all admin pages)
│   └── api.py                      # /api/v1/* REST endpoints
│
├── services/
│   ├── __init__.py
│   ├── certificate_service.py      # PDF generation, QR code, file storage
│   ├── randomizer.py               # Question selection & option shuffling logic
│   ├── leaderboard.py              # Rank calculation, cache refresh
│   ├── analytics.py                # Stats aggregation for dashboard/admin
│   └── achievement_service.py      # Achievement trigger evaluation
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py                  # Utility functions (format_time, slugify, etc.)
│   ├── validators.py               # Input validation functions
│   ├── decorators.py               # @login_required, @admin_required, @quiz_required
│   └── security.py                 # CSRF helpers, secure headers
│
├── templates/
│   ├── base.html                   # Master layout (navbar, footer, scripts)
│   ├── home.html                   # Landing page
│   ├── about.html                  # About page
│   ├── contact.html                # Contact page
│   ├── faq.html                    # FAQ page
│   ├── pricing.html                # Pricing page
│   ├── errors/
│   │   ├── 404.html
│   │   ├── 500.html
│   │   └── 403.html
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── profile.html
│   ├── quiz/
│   │   ├── categories.html         # Category browsing
│   │   ├── subcategories.html      # Subcategory listing
│   │   ├── attempt.html            # Quiz taking interface
│   │   ├── result.html             # Result + analytics
│   │   ├── review.html             # Question-by-question review
│   │   └── leaderboard.html        # Leaderboard page
│   ├── dashboard/
│   │   ├── index.html              # Main dashboard
│   │   ├── achievements.html       # Achievements page
│   │   ├── certificates.html       # Certificates list
│   │   └── settings.html          # User settings
│   ├── certificate/
│   │   ├── view.html               # Certificate preview
│   │   └── verify.html             # Public verification page
│   └── admin/
│       ├── base.html               # Admin layout (admin sidebar)
│       ├── login.html              # Admin login
│       ├── dashboard.html          # Admin dashboard
│       ├── categories.html         # Category management
│       ├── subcategories.html      # Subcategory management
│       ├── questions.html          # Question CRUD + CSV upload
│       ├── users.html              # User management
│       ├── certificates.html       # Certificate management
│       └── analytics.html          # Analytics dashboard
│
├── static/
│   ├── css/
│   │   ├── main.css                # Global styles + CSS variables (design system)
│   │   ├── components.css          # Reusable components (buttons, cards, inputs)
│   │   ├── animations.css          # Keyframe animations + transitions
│   │   ├── quiz.css                # Quiz-specific styles
│   │   ├── dashboard.css           # Dashboard & sidebar styles
│   │   ├── admin.css               # Admin panel styles
│   │   └── certificate.css         # Certificate print/view styles
│   ├── js/
│   │   ├── main.js                 # Global JS (navbar, AOS init, utils)
│   │   ├── quiz-engine.js          # Quiz state machine, timer, navigation
│   │   ├── anti-cheat.js           # All anti-cheat detection logic
│   │   ├── charts.js               # Chart.js initializations (result, dashboard)
│   │   ├── dashboard.js            # Dashboard-specific interactions
│   │   ├── admin.js                # Admin panel interactions, CSV upload
│   │   ├── certificate.js          # Certificate download/print logic
│   │   └── animations.js           # GSAP animations, scroll effects
│   ├── images/
│   │   ├── logo.svg                # QuizNova logo
│   │   ├── logo-dark.svg           # Dark variant
│   │   ├── hero-globe.svg          # Hero section graphic
│   │   ├── og-image.png            # Open Graph image for social sharing
│   │   └── patterns/               # Background pattern SVGs
│   ├── icons/
│   │   ├── categories/             # Category SVG icons
│   │   └── badges/                 # Achievement badge SVGs
│   ├── certificates/               # Generated certificate PDFs (runtime)
│   ├── uploads/
│   │   └── profiles/               # User profile photos (runtime)
│   └── vendor/
│       ├── gsap.min.js
│       ├── aos.min.js
│       ├── aos.min.css
│       └── chart.min.js
│
└── docs/
    ├── PRD.md
    ├── SRS.md
    ├── DATABASE.md
    ├── UI_GUIDE.md
    ├── API_GUIDE.md
    └── DEVELOPMENT_PLAN.md         (this file)
```

---

## 2. Development Phases

### Phase 0 — Documentation & Architecture (Week 1)
**Goal:** Lock all decisions before writing a single line of application code.

- [x] PRD.md — Product requirements
- [x] SRS.md — Software requirements  
- [x] DATABASE.md — Schema with full SQL
- [x] UI_GUIDE.md — Design system
- [x] API_GUIDE.md — All API contracts
- [x] DEVELOPMENT_PLAN.md — This document
- [ ] Validate schema with team

**Deliverables:** All 6 doc files approved and committed.

---

### Phase 1 — Foundation (Week 2)
**Goal:** Working Flask app with design system loaded.

**Tasks:**
1. Initialize Flask app factory (`app.py`, `config.py`)
2. Set up MySQL + SQLAlchemy models
3. Run `schema.sql` to create all tables
4. Create `base.html` with full navbar, footer, meta tags
5. Implement CSS design system (`main.css`, `components.css`, `animations.css`)
6. Integrate GSAP, AOS, Chart.js (vendor files)
7. Create landing page (`home.html`) — static layout only, no data
8. Create 404, 500, 403 error pages
9. Test responsive layout on all breakpoints

**Key Files Created:**
- `app.py`, `config.py`, `requirements.txt`
- `models/__init__.py` (db = SQLAlchemy())
- All model files (stub classes with columns)
- `static/css/main.css` (full design system)
- `templates/base.html`
- `templates/home.html`

---

### Phase 2 — Authentication Module (Week 3)
**Goal:** Full user auth flow.

**Tasks:**
1. Implement User model with bcrypt
2. Register route with validation
3. Login route with Flask-Login
4. Logout
5. Admin login (separate route)
6. Profile page (view + edit)
7. Profile photo upload with UUID renaming
8. `@login_required` and `@admin_required` decorators
9. CSRF protection on all forms
10. Auth templates (login.html, register.html, profile.html)
11. Flash message system styled in CSS

**Test Checklist:**
- [ ] Register with valid data → success
- [ ] Register with duplicate email → error
- [ ] Register with weak password → field error
- [ ] Login with correct credentials → dashboard redirect
- [ ] Login with wrong password → error (no user enumeration)
- [ ] Logout → session cleared
- [ ] Admin login with student account → 403
- [ ] Profile photo with non-image file → rejected

---

### Phase 3 — Content Management (Week 4)
**Goal:** Categories, subcategories, questions in DB with admin CRUD.

**Tasks:**
1. Seed script: all 12 categories, 48 subcategories, 1200 questions
2. Category model + routes (public + admin)
3. Subcategory model + routes
4. Question model + routes
5. Admin CRUD interfaces (categories.html, subcategories.html, questions.html)
6. CSV bulk import endpoint + template
7. Public category/subcategory browsing pages
8. Search/filter for admin question list

**Test Checklist:**
- [ ] All 12 categories visible on public page
- [ ] Subcategories load correctly per category
- [ ] Admin can add/edit/delete category
- [ ] Admin can import 50-question CSV successfully
- [ ] Malformed CSV row shows error report without importing anything
- [ ] Soft-deleted question doesn't appear in quiz pool

---

### Phase 4 — Quiz Engine (Week 5–6)
**Goal:** Full quiz flow with anti-cheat.

**Tasks:**
1. Quiz start: randomizer.py (question selection + option shuffle)
2. Attempt creation and snapshot storage
3. Quiz interface (attempt.html) — fullscreen, palette, timer
4. GSAP animations for option selection
5. Next/Previous navigation with answer persistence (AJAX)
6. Bookmark toggle (AJAX)
7. Timer (client-side countdown + server-side validation on submit)
8. Anti-cheat system (anti-cheat.js) — all 8 detection types
9. Violation reporting endpoint + auto-submit logic
10. Manual submit with confirmation dialog
11. Auto-submit on timer expiry
12. Submit endpoint: score calculation, result insert, leaderboard update

**Key Files:**
- `services/randomizer.py`
- `static/js/quiz-engine.js`
- `static/js/anti-cheat.js`
- `templates/quiz/attempt.html`
- `routes/quiz.py` (start, save-answer, bookmark, report-violation, submit)

**Test Checklist:**
- [ ] Quiz starts with exactly N shuffled questions
- [ ] Each attempt has different question order
- [ ] Options are in different order per attempt
- [ ] Correct option index maps correctly after shuffle
- [ ] Fullscreen requested on load
- [ ] Tab switch detected and violation logged
- [ ] 3 violations triggers auto-submit
- [ ] Timer expires → auto-submit
- [ ] Answers saved on navigation
- [ ] Page refresh → state recovered from server
- [ ] Right-click disabled during quiz
- [ ] Keyboard shortcuts blocked

---

### Phase 5 — Results & Review (Week 7)
**Goal:** Rich result display with analytics.

**Tasks:**
1. Result page (result.html) with all stats
2. Score/percentage with color coding
3. Chart.js: donut (correct/wrong/skipped) + radar (topic performance)
4. Topic analysis: strong/weak detection
5. Personalized suggestions generation
6. Review page (review.html) — question by question with explanations
7. Rank display (from leaderboard_cache)
8. Achievement check service on result (trigger unlocks)
9. Activity log entry on quiz completion

**Test Checklist:**
- [ ] Score calculates correctly
- [ ] Percentage rounds to 2 decimal places
- [ ] Rank displays correctly
- [ ] Donut chart renders with correct values
- [ ] Radar chart shows topic breakdown
- [ ] Review shows correct answer highlighting
- [ ] Wrong answer highlighted in red
- [ ] Explanations display for each question
- [ ] "First Quiz" achievement unlocked on first completion
- [ ] "Perfect Score" achievement unlocked on 100%

---

### Phase 6 — Certificate Module (Week 8)
**Goal:** Auto-generated, verifiable PDF certificates.

**Tasks:**
1. certificate_service.py: PDF generation with ReportLab or WeasyPrint
2. Certificate template design (HTML→PDF or ReportLab canvas)
3. QR code generation (qrcode library)
4. Certificate record creation with UUID + verification_id
5. Download endpoint (send_file)
6. Print view CSS
7. Public verification page (verify.html) — no auth
8. Admin certificate management page
9. Admin revoke certificate functionality

**Test Checklist:**
- [ ] Certificate generated only when percentage >= pass_threshold
- [ ] Certificate not generated twice for same attempt
- [ ] PDF downloads correctly with all fields populated
- [ ] QR code scans to correct verification URL
- [ ] Verification page shows correct info for valid cert
- [ ] Revoked certificate shows "revoked" on verification page
- [ ] Download counter increments on each download
- [ ] Certificate PDF contains: name, quiz, score, date, QR, cert ID

---

### Phase 7 — Dashboard & Leaderboard (Week 9)
**Goal:** Premium user dashboard with all widgets.

**Tasks:**
1. Dashboard layout with sidebar (dashboard.html)
2. Stats overview cards (AJAX populated)
3. Progress bar chart by category
4. Recent activity timeline
5. Recommended quizzes widget
6. Achievements page (earned + locked with progress)
7. Certificates gallery page
8. Settings page (profile edit, password change)
9. Leaderboard page (leaderboard.html) with global/category/weekly filters

**Test Checklist:**
- [ ] Dashboard stats match actual DB counts
- [ ] Progress chart renders correctly
- [ ] Activity timeline shows last 10 events
- [ ] Achievements show correct earned/locked states
- [ ] Leaderboard pagination works
- [ ] Weekly filter shows only last 7 days
- [ ] Current user row highlighted in leaderboard
- [ ] Settings save correctly (name, bio, photo)

---

### Phase 8 — Admin Panel (Week 10)
**Goal:** Full admin panel with analytics.

**Tasks:**
1. Admin dashboard with system stats
2. User management (list, search, ban, role change)
3. Analytics page (4 charts: growth, attempts, scores, categories)
4. Data export (CSV download for users, results, certificates)
5. Settings management (CRUD on settings table)
6. Complete audit of all admin security (403 on student access)

**Test Checklist:**
- [ ] Admin dashboard shows real-time stats
- [ ] User search works (by name, email)
- [ ] Ban user prevents login
- [ ] Export CSV contains correct data
- [ ] Analytics charts render with real data
- [ ] All admin routes return 403 for non-admin users
- [ ] Revoked certificate invalidated correctly

---

### Phase 9 — Polish & SEO (Week 11)
**Goal:** Production-quality finish.

**Tasks:**
1. Complete GSAP animations on all pages (hero, counters, card entrances)
2. AOS scroll animations on all content sections
3. Loading screen with brand animation
4. Mobile responsive audit and fixes
5. Skeleton loading states for AJAX content
6. SEO meta tags on all pages (title, description, OG tags)
7. Performance audit (lazy images, defer scripts)
8. Accessibility audit (contrast, ARIA, keyboard nav)
9. Error message styling complete
10. Empty state designs (no quizzes, no achievements, etc.)

---

### Phase 10 — Deployment (Week 12)
**Goal:** Production-ready deployment.

**See Section 6 for full deployment guide.**

---

## 3. Module Build Order

Build in this exact sequence to respect dependencies:

```
1. Foundation (DB + base template + CSS)
2. Auth (users table required)
3. Categories + Subcategories (required for questions)
4. Questions (required for quiz)
5. Quiz Engine (requires questions + users)
6. Results (requires quiz_attempts)
7. Leaderboard (requires results)
8. Certificates (requires results)
9. Dashboard (requires all above)
10. Admin Panel (manages all above)
11. AI Stubs (standalone, no dependencies)
```

---

## 4. Coding Standards

### Python (PEP 8 + Project Conventions)

```python
# File header
"""
Module: routes/quiz.py
Description: Quiz-related routes for QuizNova.
"""

# Function docstrings
def start_quiz(subcategory_id: int, user_id: int) -> dict:
    """
    Create a new quiz attempt for the given user and subcategory.
    
    Args:
        subcategory_id: ID of the subcategory to quiz on.
        user_id: ID of the authenticated user.
    
    Returns:
        dict containing attempt_id and question list.
    
    Raises:
        ValueError: If subcategory has insufficient questions.
    """
    ...

# Constants in config.py (not hardcoded)
MAX_VIOLATIONS = 3
QUESTIONS_DEFAULT = 20
TIME_LIMIT_DEFAULT = 30  # minutes

# Route naming: verb_noun pattern
@quiz_bp.route('/start', methods=['POST'])
@login_required
def start_quiz():
    ...

# Services never import from routes
# Models never import from services or routes
```

### JavaScript (ES6+ Conventions)

```javascript
/**
 * QuizEngine — manages quiz state, navigation, timer, and submission.
 * @module quiz-engine
 */

// Constants at top of file
const QUIZ_CONFIG = {
  MAX_VIOLATIONS: 3,
  SYNC_INTERVAL_MS: 30000,  // 30 seconds
  CONFIRM_SUBMIT_TEXT: 'Are you sure you want to submit the quiz?'
};

// State object (single source of truth)
const quizState = {
  attemptId: null,
  currentQuestion: 1,
  totalQuestions: 0,
  answers: {},      // { attemptQuestionId: selectedIndex }
  bookmarks: new Set(),
  violations: 0,
  timerSeconds: 0,
  isSubmitting: false
};

// Named functions (no anonymous arrow functions at top level)
function navigateToQuestion(order) { ... }
function saveAnswer(attemptQuestionId, selectedIndex) { ... }

// AJAX: always use fetch with async/await
async function syncAnswer(attemptQuestionId, selectedIndex) {
  try {
    const response = await fetch(`/api/v1/quiz/${quizState.attemptId}/save-answer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({ attempt_question_id: attemptQuestionId, selected_index: selectedIndex })
    });
    const data = await response.json();
    if (!data.success) console.error('Answer sync failed:', data.error);
  } catch (err) {
    console.warn('Answer sync network error:', err);
    // Queue for retry — don't alert user on every failure
  }
}
```

### HTML/CSS Conventions

```html
<!-- Semantic HTML structure -->
<main id="main-content" role="main">
  <section class="hero-section" aria-label="Hero">
    <div class="container">
      <h1 class="hero-title">...</h1>
    </div>
  </section>
</main>

<!-- CSS: BEM-lite naming -->
.quiz-option { }           /* Block */
.quiz-option__label { }    /* Element */
.quiz-option--selected { } /* Modifier */

<!-- No inline styles ever -->
<!-- No style attributes -->
<!-- ID only for JS hooks, not styling -->
```

### File Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Python files | snake_case | `quiz_service.py` |
| Templates | snake_case | `quiz_attempt.html` |
| CSS files | kebab-case | `quiz-engine.css` |
| JS files | kebab-case | `quiz-engine.js` |
| Static assets | kebab-case | `hero-globe.svg` |
| Routes | snake_case | `quiz_bp` blueprint |

---

## 5. Testing Checklist

### Security Tests
- [ ] XSS: Submit `<script>alert(1)</script>` in all text inputs → should be escaped
- [ ] CSRF: POST without CSRF token → 400 rejected
- [ ] SQLi: Submit `' OR 1=1 --` in all inputs → no DB error, no data exposure
- [ ] Auth bypass: Access /dashboard without login → redirect to login
- [ ] Admin bypass: Access /admin as student → 403 Forbidden
- [ ] File upload: Upload .php file as profile photo → rejected
- [ ] File upload: Upload 10MB image → rejected
- [ ] Horizontal access: User A accesses User B's attempt result → 403

### Functional Tests
- [ ] Full registration → login → take quiz → get result → download certificate flow
- [ ] Retake same quiz → different questions/option order
- [ ] Auto-submit on timer: run quiz, wait for timer → submission occurs
- [ ] Anti-cheat: switch tabs 3 times → auto-submit
- [ ] Leaderboard rank updates after quiz completion
- [ ] Achievement unlocks trigger correctly

### Performance Tests
- [ ] Home page load < 2s on throttled 4G
- [ ] Quiz start < 1s
- [ ] 20 concurrent quiz attempts (manual stress test)
- [ ] Admin question list with 1000+ questions: pagination works

### Responsive Tests
- [ ] All pages on 375px (iPhone SE) — no horizontal scroll
- [ ] Quiz interface on 768px tablet — usable palette and controls
- [ ] Dashboard on 375px — sidebar converts to bottom nav
- [ ] Admin panel on 1024px — sidebar + content both visible

---

## 6. Deployment Guide

### Prerequisites
- Ubuntu 22.04 LTS server (minimum 1 CPU, 2GB RAM, 20GB storage)
- Domain name pointed to server IP
- Python 3.11+, pip, venv
- MySQL 8.0+
- Nginx 1.24+
- Certbot (for HTTPS)

### Step-by-Step Deployment

#### 1. Server Setup
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip nginx mysql-server certbot -y
```

#### 2. MySQL Setup
```bash
sudo mysql_secure_installation
sudo mysql -u root -p
```
```sql
CREATE DATABASE quiznova CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'quiznova_user'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON quiznova.* TO 'quiznova_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. Application Deployment
```bash
# Clone project
git clone https://github.com/yourorg/quiznova.git /var/www/quiznova
cd /var/www/quiznova

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with production values
nano .env
```

#### 4. .env Configuration
```bash
FLASK_ENV=production
FLASK_SECRET_KEY=<generate-with-python-secrets-token-hex-32>
DATABASE_URL=mysql+pymysql://quiznova_user:STRONG_PASSWORD@localhost/quiznova
UPLOAD_MAX_MB=2
CERTIFICATE_PASS_THRESHOLD=60
MAX_VIOLATIONS=3
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=noreply@quiznova.com
MAIL_PASSWORD=<app-password>
```

#### 5. Database Initialization
```bash
mysql -u quiznova_user -p quiznova < database/schema.sql
python database/seed.py
```

#### 6. Gunicorn Service
Create `/etc/systemd/system/quiznova.service`:
```ini
[Unit]
Description=QuizNova Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/quiznova
Environment="PATH=/var/www/quiznova/venv/bin"
ExecStart=/var/www/quiznova/venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/var/www/quiznova/quiznova.sock \
  --timeout 60 \
  app:create_app()

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable quiznova
sudo systemctl start quiznova
```

#### 7. Nginx Configuration
Create `/etc/nginx/sites-available/quiznova`:
```nginx
server {
    listen 80;
    server_name quiznova.com www.quiznova.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name quiznova.com www.quiznova.com;

    ssl_certificate /etc/letsencrypt/live/quiznova.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/quiznova.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy same-origin;

    # Static files served directly by Nginx (faster)
    location /static {
        alias /var/www/quiznova/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Certificates download (restricted)
    location /static/certificates {
        internal;  # Only accessible via send_file redirect
    }

    # Proxy to Flask
    location / {
        proxy_pass http://unix:/var/www/quiznova/quiznova.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    # File upload limit
    client_max_body_size 10M;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/quiznova /etc/nginx/sites-enabled/
sudo certbot --nginx -d quiznova.com -d www.quiznova.com
sudo nginx -t && sudo systemctl reload nginx
```

#### 8. Post-Deployment Verification
- [ ] Homepage loads at https://quiznova.com
- [ ] HTTPS works (A grade on SSL Labs)
- [ ] Admin login works
- [ ] Quiz can be started and submitted
- [ ] Certificate downloads
- [ ] Static files served by Nginx (check response headers: Server: nginx)

---

## 7. Future Roadmap (v2+)

### v2.0 — AI Integration (Q3 2026)
- Activate Gemini API for question generation
- AI-powered explanations for wrong answers
- Skill gap analysis with personalized study paths
- Adaptive difficulty engine

### v2.1 — Collaboration Features
- Study groups
- Challenge friends to same quiz
- Team leaderboards

### v2.2 — Monetization
- Stripe payment integration
- Pro plan: ad-free, custom certificates, advanced analytics
- Institutional licensing (colleges, coaching centers)

### v2.3 — Mobile App
- React Native or Flutter
- Offline quiz mode (download questions)
- Push notifications for streaks and reminders

### v2.4 — Content Expansion
- Video explanations for questions
- Rich text questions with images
- Code execution for programming questions (Judge0 API)

### v3.0 — Platform Ecosystem
- Public API for third-party quiz builders
- Webhook support for LMS integration
- SSO via SAML for institutional deployments

---

## 8. Technology Versions

### Core Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Flask | 3.0+ | Web framework |
| Flask-Login | 0.6+ | Session management |
| Flask-SQLAlchemy | 3.1+ | ORM |
| Flask-WTF | 1.2+ | CSRF protection |
| PyMySQL | 1.1+ | MySQL driver |
| bcrypt | 4.1+ | Password hashing |
| ReportLab | 4.x | PDF generation |
| qrcode | 7.x | QR code generation |
| Pillow | 10.x | Image processing |
| python-dotenv | 1.x | .env loading |
| Gunicorn | 21.x | WSGI server |

### requirements.txt

```
Flask==3.0.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
PyMySQL==1.1.1
bcrypt==4.1.3
cryptography==42.0.8
reportlab==4.2.2
qrcode[pil]==7.4.2
Pillow==10.3.0
python-dotenv==1.0.1
gunicorn==22.0.0
email-validator==2.2.0
```

### Frontend Libraries (CDN/Vendor)

| Library | Version | Purpose |
|---------|---------|---------|
| GSAP | 3.12+ | Premium animations |
| AOS | 2.3 | Scroll animations |
| Chart.js | 4.4+ | Data visualizations |
| Google Fonts | — | Inter + Outfit |
