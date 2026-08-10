# QuizNova — Software Requirements Specification (SRS)

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Document Type:** Software Requirements Specification  
**Project:** QuizNova AI Quiz Platform  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Architecture](#3-system-architecture)
4. [Functional Requirements](#4-functional-requirements)
5. [External Interface Requirements](#5-external-interface-requirements)
6. [System Features — Detailed Specs](#6-system-features--detailed-specs)
7. [Security Requirements](#7-security-requirements)
8. [Performance Requirements](#8-performance-requirements)
9. [Software Quality Attributes](#9-software-quality-attributes)
10. [Appendix — Glossary](#10-appendix--glossary)

---

## 1. Introduction

### 1.1 Purpose
This SRS defines the complete functional and non-functional requirements for QuizNova version 1.0. It serves as the single source of truth for all development, testing, and deployment activities.

### 1.2 Scope
QuizNova is a web-based quiz platform built with:
- **Frontend:** HTML5, CSS3 (custom), JavaScript ES6, GSAP, AOS
- **Backend:** Python Flask with SQLAlchemy ORM
- **Database:** MySQL 8.x
- **Authentication:** Flask-Login, bcrypt
- **PDF Generation:** ReportLab or WeasyPrint
- **QR Code:** qrcode Python library

### 1.3 Definitions
| Term | Definition |
|------|-----------|
| Quiz Attempt | A single instance of a user starting and completing/submitting a quiz |
| Anti-Cheat Violation | A detected suspicious behavior event during a quiz |
| Certificate | Auto-generated PDF awarded upon passing a quiz |
| Subcategory | A topic subdivision within a Category |
| Question Pool | All questions available for a subcategory |
| Option Randomization | Shuffling A/B/C/D order per attempt |

### 1.4 References
- PRD.md (Product Requirement Document)
- DATABASE.md (Schema Design)
- UI_GUIDE.md (Design System)
- API_GUIDE.md (API Specification)

---

## 2. Overall Description

### 2.1 Product Perspective
QuizNova operates as a standalone web application. It is designed to be deployed on any Linux server (Ubuntu 22.04 LTS recommended) with Nginx as reverse proxy and Gunicorn as WSGI server. The system exposes:
- Public web pages (no auth required)
- Authenticated user pages (Flask-Login sessions)
- Admin pages (role-based access control)
- REST API endpoints (JSON) for potential future SPA or mobile app

### 2.2 Product Functions Summary
1. User registration & authentication
2. Category/subcategory browsing
3. Quiz taking with randomization & timing
4. Anti-cheat enforcement
5. Result analysis & review
6. Certificate generation & verification
7. Leaderboard display
8. User dashboard & progress tracking
9. Admin management of all content
10. Analytics & reporting

### 2.3 User Classes
| Class | Description | Access Level |
|-------|-------------|--------------|
| Guest | Unauthenticated visitor | Public pages only |
| Student | Registered user | All user features |
| Admin | Platform administrator | All features + admin panel |

### 2.4 Operating Environment
- **Server OS:** Ubuntu 22.04 LTS (production), Windows 11 (development)
- **Web Server:** Nginx 1.24 + Gunicorn 21.x
- **Python:** 3.11+
- **MySQL:** 8.0+
- **Browser Support:** Chrome 100+, Firefox 100+, Edge 100+, Safari 15+

### 2.5 Design Constraints
- No external CSS frameworks
- No JavaScript frameworks (vanilla JS only)
- All animations via GSAP and/or CSS
- MySQL is the only supported RDBMS
- No external API calls in v1 (AI stubs only)

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
+------------------+       HTTPS        +------------------------+
|   Browser        | <----------------> |  Nginx (Reverse Proxy) |
|  (HTML/CSS/JS)   |                    +------------------------+
+------------------+                              |
                                                  | uwsgi/HTTP
                                     +------------------------+
                                     |  Gunicorn + Flask App  |
                                     +------------------------+
                                       |         |         |
                                  +-------+ +--------+ +----------+
                                  | MySQL | | Static | | File     |
                                  |  DB   | | Files  | | Storage  |
                                  +-------+ +--------+ +----------+
```

### 3.2 Flask Application Structure

```
Flask App (app.py)
├── Blueprint: auth     (/auth/*)
├── Blueprint: quiz     (/quiz/*)
├── Blueprint: dashboard (/dashboard/*)
├── Blueprint: admin    (/admin/*)
├── Blueprint: api      (/api/v1/*)
├── SQLAlchemy Models
├── Services Layer
└── Utils Layer
```

### 3.3 Request Lifecycle
1. Browser sends HTTPS request to Nginx
2. Nginx proxies to Gunicorn → Flask
3. Flask route decorator matches URL
4. Auth middleware validates session
5. Route handler calls Service layer
6. Service layer calls Model layer
7. Model executes parameterized SQL via SQLAlchemy
8. Response rendered via Jinja2 template
9. HTML/CSS/JS returned to browser

---

## 4. Functional Requirements

### 4.1 Authentication System

#### FR-AUTH-001: User Registration
- **Input:** username, email, password, confirm_password
- **Validation:**
  - Username: 3–30 chars, alphanumeric + underscore
  - Email: valid RFC 5322 format, unique in DB
  - Password: min 8 chars, >= 1 uppercase, >= 1 digit, >= 1 special char
- **Process:** Hash password with bcrypt (cost=12), store user record
- **Output:** Redirect to dashboard, flash success message
- **Error:** Re-render form with field-level error messages

#### FR-AUTH-002: User Login
- **Input:** email, password, remember_me checkbox
- **Validation:** Email exists, bcrypt hash comparison
- **Process:** Create Flask-Login session, set remember cookie if checked
- **Output:** Redirect to dashboard
- **Error:** Flash generic "Invalid credentials" (no user enumeration)

#### FR-AUTH-003: User Logout
- **Process:** Clear Flask-Login session, invalidate remember cookie
- **Output:** Redirect to home page

#### FR-AUTH-004: Profile Management
- **Update fields:** display_name, bio, profile_photo
- **Photo upload:** JPEG/PNG only, max 2MB, rename to UUID, store in /static/uploads/profiles/
- **Output:** Flash success, reload profile page

#### FR-AUTH-005: Admin Authentication
- **Route:** /admin/login (separate from /auth/login)
- **Validation:** Email + password + role == 'admin'
- **Process:** Admin-specific session flag set
- **Security:** 5 failed attempt lockout for 15 minutes

---

### 4.2 Category & Content System

#### FR-CAT-001: Category Listing
- **Public endpoint:** GET /categories
- **Returns:** All active categories with icon, name, quiz count
- **Admin:** Can add, edit, deactivate categories

#### FR-CAT-002: Subcategory Listing
- **Public endpoint:** GET /categories/<category_id>/subcategories
- **Returns:** All active subcategories under category with question count

#### FR-CAT-003: Question Management (Admin)
- Add single question with 4 options, correct option index, explanation, difficulty, category, subcategory
- Edit existing question
- Delete (soft delete — mark inactive)
- Bulk import via CSV (see FR-ADMIN-006)

---

### 4.3 Quiz Engine

#### FR-QUIZ-001: Quiz Start
- **Trigger:** User clicks "Start Quiz" on subcategory page
- **Pre-conditions:** User is authenticated
- **Process:**
  1. Create QuizAttempt record in DB (status=in_progress)
  2. Randomly select N questions from pool (default N=20)
  3. For each question, randomly shuffle options array, record correct_index_shuffled
  4. Store question+order snapshot in attempt_questions table
  5. Redirect to /quiz/<attempt_id>

#### FR-QUIZ-002: Fullscreen Enforcement
- **On load:** Call document.documentElement.requestFullscreen()
- **On fullscreen exit:** Increment violation counter, show warning overlay
- **Overlay:** "Fullscreen exited! Return to fullscreen to continue." with button
- **Auto-submit:** If violations >= configurable threshold (default=3)

#### FR-QUIZ-003: Quiz Interface
- Left panel: Question with 4 options (A/B/C/D rendered from shuffled array)
- Right panel: Question palette grid, timer, bookmark toggle
- Bottom bar: Previous, Next, Submit button
- Selected option stored in JS state AND synced to server every 30 seconds
- Answer persisted to attempt_answers table on each Next/Previous navigation

#### FR-QUIZ-004: Timer
- Duration: configurable per subcategory (default: 30 minutes)
- Displayed as MM:SS countdown
- At 0:00: auto-submit triggered
- Warning pulse animation when < 5 minutes remaining
- Timer state stored client-side (sessionStorage backup for tab refresh)

#### FR-QUIZ-005: Bookmark
- Toggle bookmark on any question
- Bookmarked questions shown with star icon in palette
- Bookmarks stored in JS state, synced to DB on submission

#### FR-QUIZ-006: Quiz Submission
- **Manual:** User clicks Submit, confirmation dialog shown
- **Auto:** Timer expiry or max violations
- **Process:**
  1. Mark attempt status = submitted
  2. Calculate score (for each attempt_answer, compare user_option to correct_option_shuffled_index)
  3. Compute time_taken = now - attempt.started_at
  4. Insert Result record
  5. Update leaderboard
  6. Determine if certificate should be generated (score >= pass_threshold)
  7. Redirect to /quiz/result/<attempt_id>

#### FR-QUIZ-007: Anti-Cheat System
- **Events monitored:**
  - document.addEventListener('visibilitychange') → tab switch
  - window.addEventListener('blur') → window minimize / alt-tab
  - document.addEventListener('fullscreenchange') → fullscreen exit
  - document.addEventListener('contextmenu', e => e.preventDefault()) → right click
  - document.addEventListener('copy', e => e.preventDefault()) → copy
  - document.addEventListener('paste', e => e.preventDefault()) → paste
  - document.addEventListener('selectstart', e => e.preventDefault()) → text select
  - document.addEventListener('keydown') → block F12, Ctrl+U, Ctrl+Shift+I, Ctrl+A
- **Violation counter:** Stored in sessionStorage + synced to server
- **Threshold:** Configurable in config.py (default: 3 violations = auto-submit)
- **Logging:** Each violation logged to anti_cheat_logs table with event_type, timestamp

---

### 4.4 Result System

#### FR-RESULT-001: Result Display
- Score out of total
- Percentage with color coding (green >= 70%, yellow 40–69%, red < 40%)
- Global rank (based on subcategory leaderboard)
- Correct / Wrong / Skipped counts
- Time taken (formatted MM:SS)
- Performance donut chart (Chart.js)
- Radar chart of topic coverage
- Strong topics (>= 80% in that topic group)
- Weak topics (< 50% in that topic group)
- Personalized suggestions based on weak topics

#### FR-RESULT-002: Review Mode
- List all questions in original order
- Show user's answer highlighted
- Show correct answer highlighted
- Show explanation text
- Show difficulty level badge
- "Back to Results" button

#### FR-RESULT-003: Certificate Trigger
- If score >= pass_threshold (default 60%) AND not already generated:
  - Auto-generate certificate
  - Show "Download Certificate" button on result page

---

### 4.5 Certificate System

#### FR-CERT-001: Certificate Generation
- Triggered server-side on quiz completion if pass condition met
- Generated using ReportLab or WeasyPrint from HTML template
- Stored at /static/certificates/<cert_uuid>.pdf
- Record stored in certificates table with:
  - certificate_id (UUID)
  - user_id, quiz_attempt_id
  - issue_date, score, percentage
  - qr_code_data (URL to verification page)
  - verification_id (8-char alphanumeric)

#### FR-CERT-002: Certificate Contents
- QuizNova logo (top left)
- "Certificate of Achievement" header
- Candidate photo (circular crop)
- Candidate name (large, serif font)
- "has successfully completed" text
- Quiz name & category
- Score and percentage
- Completion date
- Certificate ID
- QR code (bottom left)
- Verification URL text
- Instructor signature image (configurable)
- Official seal image (configurable)
- Professional decorative border

#### FR-CERT-003: Certificate Verification
- Public endpoint: GET /verify/<verification_id>
- No authentication required
- Returns: Certificate validity, candidate name, quiz name, date, score
- QR code points to this URL

---

### 4.6 Leaderboard

#### FR-LEAD-001: Global Leaderboard
- Ranks all users by highest total score across all quizzes
- Displays: rank, avatar, username, score, quizzes taken, badges
- Paginated (50 per page)
- User's own row always highlighted

#### FR-LEAD-002: Category Leaderboard
- Filtered by category_id
- Same display format
- "All Categories" tab defaults to global

#### FR-LEAD-003: Time Filter
- "All Time" (default) and "This Week" toggle
- Week filter: attempts with started_at >= now - 7 days

---

### 4.7 Dashboard

#### FR-DASH-001: Statistics Overview
- Quizzes taken (total count)
- Average score (%)
- Global rank
- Certificates earned

#### FR-DASH-002: Progress Charts
- Bar chart: score by category
- Line chart: score trend over time (last 10 attempts)
- Donut chart: correct vs wrong vs skipped (last 5 quizzes)

#### FR-DASH-003: Activity Timeline
- List of recent quiz attempts with: subcategory, score, date, result link

#### FR-DASH-004: Achievements
- Badge system with 15+ achievements
- Unlocked/locked display
- Progress bar for in-progress achievements

#### FR-DASH-005: Recommended Quizzes
- Based on: lowest score subcategories + not-yet-attempted subcategories
- Max 6 recommendations displayed

---

### 4.8 Admin Panel

#### FR-ADMIN-001: Admin Dashboard
- Total users, quizzes, questions, certificates (live counts)
- New registrations chart (last 30 days)
- Quiz attempts chart (last 30 days)
- Top 5 most popular subcategories

#### FR-ADMIN-002: Category Management
- Create, Read, Update, Delete categories
- Soft delete (deactivate) instead of hard delete
- Icon upload (SVG preferred)

#### FR-ADMIN-003: Subcategory Management
- Full CRUD tied to category
- Set question count per quiz, time limit, pass threshold

#### FR-ADMIN-004: Question Management
- Full CRUD with rich text explanation
- Difficulty level: Easy / Medium / Hard
- Preview question before saving

#### FR-ADMIN-005: User Management
- List all users with search and filter
- View user profile, stats, quiz history
- Ban/unban user (sets is_active=False)
- Change user role (student/admin)

#### FR-ADMIN-006: CSV Bulk Import
- Upload CSV with columns: category, subcategory, question_text, option_a, option_b, option_c, option_d, correct_option, difficulty, explanation
- Server validates all rows before any insert
- On validation failure: return error report with row numbers
- On success: bulk insert using SQLAlchemy core for performance

#### FR-ADMIN-007: Certificate Management
- List all certificates
- View/download any certificate
- Revoke certificate (mark invalid in DB)

#### FR-ADMIN-008: Analytics
- User retention cohort chart
- Score distribution histogram
- Category popularity chart
- Daily/weekly/monthly active users chart

#### FR-ADMIN-009: Data Export
- Export users table as CSV
- Export results table as CSV
- Export certificates table as CSV
- Date range filter on exports

---

## 5. External Interface Requirements

### 5.1 User Interface
- Dark theme with glassmorphism panels
- Purple (#7C3AED) and blue (#2563EB) primary palette
- Custom CSS (no Bootstrap, no Tailwind)
- Google Fonts: Inter (UI), Outfit (headings)
- GSAP for page transitions and hero animations
- AOS for scroll-triggered animations
- Chart.js for data visualizations
- All pages fully responsive (320px–2560px)

### 5.2 Hardware Interfaces
- None required beyond standard HTTP

### 5.3 Software Interfaces
| Interface | Purpose | Version |
|-----------|---------|---------|
| MySQL | Primary database | 8.0+ |
| Redis (optional) | Session caching, rate limiting | 7.x |
| SMTP server | Email notifications (v1 optional) | — |
| Cloudinary (optional) | Image CDN | API v2 |

### 5.4 Communication Interfaces
- HTTPS required in production (TLS 1.2+)
- HTTP/2 supported via Nginx
- WebSocket not required in v1

---

## 6. System Features — Detailed Specs

### 6.1 Quiz State Machine

```
States: NOT_STARTED → IN_PROGRESS → SUBMITTED → REVIEWED

Transitions:
NOT_STARTED  → IN_PROGRESS : User clicks "Start Quiz"
IN_PROGRESS  → SUBMITTED   : Manual submit OR timer expiry OR max violations
SUBMITTED    → REVIEWED    : User clicks "Review Answers"
```

### 6.2 Achievement Triggers

| Achievement | Trigger Condition |
|-------------|------------------|
| First Step | Complete first quiz |
| Perfect Score | Score 100% on any quiz |
| Speed Demon | Complete quiz with > 50% time remaining |
| Streak Master | Complete quizzes 7 days in a row |
| Category Champion | Score >= 90% in all subcategories of a category |
| Bookworm | Bookmark 50+ questions total |
| Top Ranker | Reach top 10 on global leaderboard |
| Certificate Collector | Earn 5 certificates |
| Explorer | Attempt quizzes in 5+ different categories |
| Consistent Learner | Complete 30 quizzes total |

### 6.3 Question Randomization Algorithm

```
1. Pool = all active questions for subcategory (min 30 questions required)
2. N = quiz_config.questions_per_attempt (default 20)
3. selected = random.sample(pool, N)  # Python random.sample — no repeats
4. For each selected question:
   a. options_list = [q.option_a, q.option_b, q.option_c, q.option_d]
   b. correct_text = options_list[q.correct_option_index]
   c. random.shuffle(options_list)
   d. new_correct_index = options_list.index(correct_text)
   e. Store: question_id, shuffled_options (JSON), new_correct_index
```

### 6.4 Certificate Verification Flow
```
User scans QR → Browser opens /verify/<verification_id>
→ DB lookup certificates WHERE verification_id = ?
→ If found AND is_valid=True: show green "Valid Certificate" page with details
→ If found AND is_valid=False: show red "Certificate Revoked" page
→ If not found: show "Certificate Not Found" page
```

---

## 7. Security Requirements

### 7.1 Authentication Security
- SR-001: Passwords hashed with bcrypt, minimum cost factor 12
- SR-002: No plaintext password storage at any point (including logs)
- SR-003: Login rate limiting: 5 attempts per 10 minutes per IP
- SR-004: Session token rotation on privilege change
- SR-005: Secure, HttpOnly, SameSite=Lax cookie flags
- SR-006: CSRF token required on all state-changing requests

### 7.2 Input Validation
- SR-007: All form inputs validated server-side (client-side is UX only)
- SR-008: Parameterized queries for all DB operations (no string concatenation)
- SR-009: File uploads: whitelist extensions, validate MIME type, cap file size
- SR-010: HTML escaping in all Jinja2 templates (autoescaping enabled)

### 7.3 Application Security
- SR-011: HTTPS enforced in production (HTTP → HTTPS redirect)
- SR-012: Security headers set by Nginx:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Content-Security-Policy: strict policy
  - Referrer-Policy: same-origin
- SR-013: Admin routes behind separate authentication + IP whitelist (optional)
- SR-014: No sensitive data in URL parameters
- SR-015: Error pages must not expose stack traces or system info

### 7.4 File Security
- SR-016: Uploaded files stored outside web root or with restricted direct access
- SR-017: File names sanitized (UUID rename, not user-provided name)
- SR-018: Certificates served via Flask send_file, not direct static URL

---

## 8. Performance Requirements

| Metric | Requirement |
|--------|-------------|
| Home page load | < 2 seconds on 4G |
| Quiz start | < 1 second after button click |
| Answer save (auto-sync) | < 200ms round-trip |
| Result page render | < 1.5 seconds |
| Certificate PDF generation | < 3 seconds |
| Admin dashboard load | < 3 seconds |
| Concurrent users | Support 200 concurrent sessions |
| DB query p95 | < 100ms |

---

## 9. Software Quality Attributes

### 9.1 Maintainability
- All Python functions < 50 lines
- All JS files < 300 lines (split by responsibility)
- Docstrings on all public functions
- No magic numbers — use constants/config
- Services layer separates business logic from routes

### 9.2 Testability
- Routes use dependency injection pattern
- DB access isolated in models layer
- Services can be unit-tested with mocked DB
- JS logic separated from DOM manipulation

### 9.3 Portability
- Docker-ready: app is 12-factor compliant (config via env)
- No OS-specific file paths in Python code
- Database migrations via Alembic (future)

### 9.4 Accessibility
- ARIA roles on custom components
- Tab-index managed for quiz interface
- Color contrast >= 4.5:1 on body text
- Focus visible on all interactive elements

---

## 10. Appendix — Glossary

| Term | Definition |
|------|-----------|
| SRS | Software Requirements Specification |
| PRD | Product Requirements Document |
| CRUD | Create, Read, Update, Delete |
| ORM | Object-Relational Mapper (SQLAlchemy) |
| CSRF | Cross-Site Request Forgery |
| XSS | Cross-Site Scripting |
| UUID | Universally Unique Identifier |
| WCAG | Web Content Accessibility Guidelines |
| GSAP | GreenSock Animation Platform |
| AOS | Animate On Scroll library |
| FCP | First Contentful Paint |
| TTI | Time to Interactive |
| QR | Quick Response (code) |
| bcrypt | Adaptive password hashing algorithm |
| CSP | Content Security Policy |
