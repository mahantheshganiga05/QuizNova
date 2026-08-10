# QuizNova — Product Requirement Document (PRD)

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Status:** Approved for Development  
**Author:** QuizNova Architecture Team  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision](#2-product-vision)
3. [Target Audience & User Personas](#3-target-audience--user-personas)
4. [Problem Statement](#4-problem-statement)
5. [Goals & Success Metrics](#5-goals--success-metrics)
6. [Feature Inventory](#6-feature-inventory)
7. [User Stories](#7-user-stories)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Constraints & Assumptions](#9-constraints--assumptions)
10. [Release Milestones](#10-release-milestones)
11. [Risks & Mitigations](#11-risks--mitigations)

---

## 1. Executive Summary

QuizNova is a **production-grade, AI-ready, dark-themed quiz platform** targeting college students, placement aspirants, and competitive exam candidates. Built with a modern Flask backend and a premium custom frontend (no Bootstrap), it delivers a SaaS-quality experience comparable to Linear, Vercel, and Notion in terms of design polish, performance, and reliability.

The platform supports 10+ knowledge categories, 30+ subcategories, 600+ questions, randomized quiz engines, browser-based anti-cheat, auto-generated certificates, real-time leaderboards, and a comprehensive admin panel—all built with future AI capability hooks (Gemini/OpenAI) baked into the architecture.

---

## 2. Product Vision

> **"Test Your Knowledge. Ignite Your Potential."**

QuizNova transforms the mundane quiz experience into a premium, motivating, and analytically rich learning journey. Every interaction—from landing on the homepage to downloading a certificate—should feel intentional, fast, and beautiful.

### Design Philosophy
- **Dark-first** — Glassmorphism + purple/blue gradients.
- **Motion-led** — GSAP animations make the UI feel alive.
- **Data-rich** — Every quiz attempt surfaces actionable insight.
- **Security-first** — Anti-cheat, CSRF, XSS, SQL injection hardening.
- **Future-proof** — Architecture slots for AI, payments, email, CDN.

---

## 3. Target Audience & User Personas

### Persona 1 — The Placement Aspirant (Primary)
| Attribute | Detail |
|-----------|--------|
| **Name** | Arjun Sharma |
| **Age** | 21 |
| **Goal** | Crack campus placements & aptitude tests |
| **Pain Point** | Scattered study resources, no progress tracking |
| **Usage** | Daily 30-min sessions; compares rank on leaderboard |
| **Device** | Laptop + Mobile |

### Persona 2 — The Competitive Exam Candidate
| Attribute | Detail |
|-----------|--------|
| **Name** | Priya Iyer |
| **Age** | 23 |
| **Goal** | GATE, UPSC, SSC preparation |
| **Pain Point** | No timed practice with realistic exam simulation |
| **Usage** | 2-hour study blocks, downloads certificates to share |
| **Device** | Desktop |

### Persona 3 — The Tech Enthusiast
| Attribute | Detail |
|-----------|--------|
| **Name** | Rohan Das |
| **Age** | 19 |
| **Goal** | Sharpen programming and AI knowledge |
| **Pain Point** | No platform focused on CS/AI topics with quality questions |
| **Usage** | Leaderboard competitive, achievement hunting |
| **Device** | Desktop |

### Persona 4 — The Admin / Educator
| Attribute | Detail |
|-----------|--------|
| **Name** | Dr. Meera Pillai |
| **Age** | 35 |
| **Goal** | Manage question bank, monitor student performance |
| **Pain Point** | No bulk upload, no analytics, no certificate management |
| **Usage** | Weekly CSV uploads, reviews analytics dashboards |
| **Device** | Desktop |

---

## 4. Problem Statement

Existing quiz platforms suffer from:
- **Poor UX** — Outdated designs, cluttered interfaces, light-mode-only.
- **No Anti-Cheat** — Easily gamed; no exam integrity mechanisms.
- **Weak Analytics** — Pass/fail only; no topic-wise breakdown.
- **No Certificates** — Or generic, unverifiable PDFs.
- **Not AI-Ready** — No hooks for future intelligent features.
- **Monolithic Admin** — No bulk import, no export, no role management.

QuizNova solves all of the above while delivering a product-quality experience that students want to use daily.

---

## 5. Goals & Success Metrics

### Business Goals
| Goal | Metric | Target (6 months) |
|------|--------|-------------------|
| User Acquisition | Registered users | 5,000 |
| Engagement | Daily Active Users | 500/day |
| Completion | Quiz completion rate | >= 80% |
| Retention | 30-day retention | >= 40% |
| Certificates | Certificates generated | 2,000 |

### Technical Goals
| Goal | Metric | Target |
|------|--------|--------|
| Performance | Page load time | < 2s |
| Uptime | Availability | 99.5% |
| Security | OWASP Top 10 coverage | 100% |
| Mobile | Responsive breakpoints | 4 |
| Accessibility | WCAG AA compliance | >= 80% |

---

## 6. Feature Inventory

### 6.1 Authentication Module
- [x] User Registration (email + password)
- [x] Login / Logout
- [x] Password hashing (bcrypt)
- [x] Session management (Flask-Login)
- [x] Profile photo upload
- [x] Remember me token
- [x] Admin-only routes (role-based)
- [ ] OAuth (Google) — Future v2
- [ ] Two-Factor Authentication — Future v2

### 6.2 Landing & Public Pages
- [x] Hero section with animated globe/network
- [x] Stats counter (users, quizzes, questions, success rate)
- [x] Category showcase grid
- [x] Features section
- [x] Testimonials
- [x] FAQ accordion
- [x] Pricing tiers (Free / Pro — content only)
- [x] Footer with links
- [x] About page
- [x] Contact form

### 6.3 Quiz Engine
- [x] Category & Subcategory browsing
- [x] Quiz configuration (timed, randomized)
- [x] Fullscreen enforcement
- [x] Question palette (grid view)
- [x] Bookmark questions
- [x] Next / Previous navigation
- [x] Auto-submit on timer expiry
- [x] Anti-cheat monitoring
- [x] Progress indicator
- [x] Option randomization per attempt

### 6.4 Result & Review Module
- [x] Score, percentage, rank display
- [x] Correct / Wrong / Skipped breakdown
- [x] Time taken
- [x] Performance radar chart
- [x] Strong / Weak topic identification
- [x] Review all questions with explanations
- [x] Certificate download trigger

### 6.5 Certificate Module
- [x] Auto-generated on quiz completion (pass threshold)
- [x] QR code verification
- [x] Unique certificate ID
- [x] Download as PDF
- [x] Print view
- [x] Public verification URL

### 6.6 Leaderboard
- [x] Global leaderboard
- [x] Category-specific leaderboard
- [x] Weekly / All-time filters
- [x] User rank highlight
- [x] Badge display

### 6.7 User Dashboard
- [x] Statistics overview
- [x] Progress by category (bar chart)
- [x] Recent activity timeline
- [x] Certificates grid
- [x] Achievements / Badges
- [x] Recommended quizzes
- [x] Profile settings

### 6.8 Admin Panel
- [x] Admin authentication
- [x] Dashboard with system stats
- [x] Category / Subcategory / Question CRUD
- [x] CSV bulk upload
- [x] User management
- [x] Certificate management
- [x] Analytics dashboard
- [x] Export data (CSV)

### 6.9 Anti-Cheat System
- [x] Fullscreen lock & detection
- [x] Tab switch detection
- [x] Window blur detection
- [x] Right-click disable
- [x] Copy/paste disable
- [x] Text selection disable
- [x] Shortcut key blocking
- [x] Violation counter with configurable threshold
- [x] Auto-submit on max violations
- [x] Violation log stored in DB

### 6.10 Future AI Hooks (Architecture Only — No Implementation)
- [ ] /api/ai/generate-question — stub
- [ ] /api/ai/explain — stub
- [ ] /api/ai/roadmap — stub
- [ ] /api/ai/skill-gap — stub
- [ ] Adaptive difficulty engine scaffold

---

## 7. User Stories

### Authentication
- AS A new visitor, I WANT TO register with email and password SO THAT I can access quizzes and track my progress.
- AS A returning user, I WANT TO log in securely SO THAT my data and history persist across sessions.
- AS AN admin, I WANT TO log in via a separate secure admin portal SO THAT I can manage the platform without exposing admin routes.

### Quiz Taking
- AS A student, I WANT TO browse categories and subcategories SO THAT I can find quizzes relevant to my preparation.
- AS A quiz taker, I WANT THE quiz to enter fullscreen automatically SO THAT the environment simulates a real exam.
- AS A quiz taker, I WANT TO bookmark questions for later review SO THAT I can manage my time efficiently.
- AS A quiz taker, I WANT OPTIONS to be randomized each attempt SO THAT I cannot memorize patterns.
- AS A quiz taker, I WANT THE quiz to auto-submit when the timer expires SO THAT exam rules are fairly enforced.

### Results & Certificates
- AS A student, I WANT TO see detailed analytics after quiz submission SO THAT I understand my strengths and weaknesses.
- AS A student, I WANT TO download a professional certificate on passing SO THAT I can share my achievement.
- AS ANYONE, I WANT TO verify a certificate via QR code SO THAT employers can confirm authenticity.

### Admin
- AS AN admin, I WANT TO upload questions via CSV SO THAT I can bulk-import large question banks efficiently.
- AS AN admin, I WANT TO view real-time analytics SO THAT I can understand platform usage and student performance.
- AS AN admin, I WANT TO export user and result data as CSV SO THAT I can generate offline reports.

---

## 8. Non-Functional Requirements

### Performance
- First Contentful Paint (FCP): < 1.5s
- Time to Interactive (TTI): < 3s
- Database queries: < 100ms for 95th percentile
- Quiz question load: < 500ms

### Security
- Passwords stored as bcrypt hashes (cost factor >= 12)
- CSRF tokens on all forms
- Parameterized queries / ORM for all DB operations
- Secure HTTP headers (CSP, X-Frame-Options, etc.)
- File upload validation (type, size, extension whitelist)
- Session timeout: 30 minutes idle, 24h maximum

### Scalability
- Stateless backend (session via secure cookies)
- MySQL connection pooling via SQLAlchemy
- Static assets CDN-ready
- Modular route blueprints for horizontal scaling

### Reliability
- Graceful error pages (404, 500, 403)
- Form validation both client-side and server-side
- Database foreign key constraints for data integrity
- Atomic quiz submission (transaction-wrapped)

---

## 9. Constraints & Assumptions

### Constraints
- No third-party CSS frameworks (Bootstrap forbidden)
- No payment gateway in v1
- No OAuth in v1
- No live AI calls in v1 (stubs only)
- MySQL as the only supported database

### Assumptions
- Users have modern browsers (Chrome 100+, Firefox 100+, Edge 100+)
- Fullscreen API is available (required for anti-cheat)
- PDF generation happens server-side (ReportLab/WeasyPrint)
- Cloudinary optional in v1 (local storage fallback)

---

## 10. Release Milestones

| Milestone | Deliverable | Target |
|-----------|-------------|--------|
| M0 — Documentation | Full docs, DB schema, API plan | Week 1 |
| M1 — Foundation | Project scaffold, base template, design system | Week 2 |
| M2 — Auth | Registration, login, profile, session | Week 3 |
| M3 — Content | Categories, subcategories, question management | Week 4 |
| M4 — Quiz Engine | Quiz flow, anti-cheat, timer, auto-submit | Week 5-6 |
| M5 — Results | Result page, review, analytics | Week 7 |
| M6 — Certificates | PDF generation, QR, verification | Week 8 |
| M7 — Dashboard | User dashboard, achievements, leaderboard | Week 9 |
| M8 — Admin | Admin panel, CSV upload, analytics | Week 10 |
| M9 — Polish | Animations, responsive, SEO, accessibility | Week 11 |
| M10 — Deployment | Production config, environment, testing | Week 12 |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Anti-cheat bypassed via DevTools | High | Medium | Layer detection; document limitations clearly |
| Fullscreen API not supported on iOS Safari | High | Low | Graceful fallback; warn user; still allow quiz |
| PDF generation performance | Medium | Medium | Async generation; cache certificates after first download |
| Large question bank causing slow loads | Medium | High | Pagination, indexed queries, pool limits per quiz |
| CSV upload malformed data | High | Medium | Server-side validation, rollback on error, error report to admin |
| Session hijacking | Low | Critical | Secure, HTTPOnly, SameSite cookies; HTTPS in production |
