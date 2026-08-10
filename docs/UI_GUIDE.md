# QuizNova — UI/UX Design System Guide

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Status:** Design Authority Document  

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Spacing & Layout](#4-spacing--layout)
5. [Component Library](#5-component-library)
6. [Animation System](#6-animation-system)
7. [Page-by-Page Blueprints](#7-page-by-page-blueprints)
8. [Responsive Breakpoints](#8-responsive-breakpoints)
9. [Icon System](#9-icon-system)
10. [Accessibility Standards](#10-accessibility-standards)

---

## 1. Design Philosophy

### Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Dark-First** | Default dark theme; no light mode toggle in v1 |
| **Glassmorphism** | Semi-transparent frosted glass panels with backdrop blur |
| **Motion-Led** | Every state change is animated; nothing should "snap" |
| **Data-Rich** | Numbers and progress always visible; empty states show guidance |
| **Premium Feel** | Every shadow, gradient, and radius is intentional |

### Visual Identity
- **Brand Color:** Deep Purple `#7C3AED`
- **Accent Color:** Electric Blue `#2563EB`
- **Glow Effect:** Purple glow `rgba(124, 58, 237, 0.4)`
- **Background:** Near-black `#0A0A0F`
- **Theme:** Cosmic / Tech / Neural Network aesthetic

---

## 2. Color System

### 2.1 Base Palette (CSS Custom Properties)

```css
:root {
  /* === BACKGROUNDS === */
  --bg-primary:     #0A0A0F;   /* Page background */
  --bg-secondary:   #0F0F1A;   /* Section backgrounds */
  --bg-tertiary:    #13131F;   /* Card backgrounds */
  --bg-elevated:    #1A1A2E;   /* Elevated panels */
  --bg-glass:       rgba(255, 255, 255, 0.05);  /* Glass panels */
  --bg-glass-hover: rgba(255, 255, 255, 0.08);

  /* === BRAND COLORS === */
  --brand-purple:   #7C3AED;
  --brand-purple-light: #9D5FFC;
  --brand-purple-dark:  #5B21B6;
  --brand-blue:     #2563EB;
  --brand-blue-light:   #3B82F6;
  --brand-blue-dark:    #1D4ED8;

  /* === GRADIENTS === */
  --gradient-brand:   linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
  --gradient-glow:    linear-gradient(135deg, #9D5FFC 0%, #3B82F6 100%);
  --gradient-bg:      linear-gradient(180deg, #0A0A0F 0%, #0D0D1A 100%);
  --gradient-card:    linear-gradient(135deg, rgba(124,58,237,0.1) 0%, rgba(37,99,235,0.05) 100%);
  --gradient-hero:    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(124,58,237,0.3) 0%, transparent 70%);

  /* === TEXT COLORS === */
  --text-primary:   #F8F8FF;   /* Primary content */
  --text-secondary: #A0A0B8;   /* Muted text */
  --text-tertiary:  #6B6B85;   /* Placeholder / disabled */
  --text-accent:    #9D5FFC;   /* Accent links / highlights */

  /* === BORDER COLORS === */
  --border-default: rgba(255, 255, 255, 0.08);
  --border-brand:   rgba(124, 58, 237, 0.4);
  --border-glow:    rgba(124, 58, 237, 0.6);

  /* === SEMANTIC COLORS === */
  --success:        #10B981;
  --success-bg:     rgba(16, 185, 129, 0.1);
  --warning:        #F59E0B;
  --warning-bg:     rgba(245, 158, 11, 0.1);
  --error:          #EF4444;
  --error-bg:       rgba(239, 68, 68, 0.1);
  --info:           #3B82F6;
  --info-bg:        rgba(59, 130, 246, 0.1);

  /* === SHADOWS === */
  --shadow-sm:      0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-md:      0 4px 20px rgba(0, 0, 0, 0.4);
  --shadow-lg:      0 8px 40px rgba(0, 0, 0, 0.5);
  --shadow-glow:    0 0 30px rgba(124, 58, 237, 0.3);
  --shadow-glow-lg: 0 0 60px rgba(124, 58, 237, 0.4);

  /* === GLASS EFFECT === */
  --glass-blur:     16px;
  --glass-border:   1px solid rgba(255, 255, 255, 0.08);
  --glass-bg:       rgba(255, 255, 255, 0.04);

  /* === BORDER RADIUS === */
  --radius-sm:      6px;
  --radius-md:      12px;
  --radius-lg:      20px;
  --radius-xl:      28px;
  --radius-full:    9999px;

  /* === TRANSITIONS === */
  --transition-fast:   0.15s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow:   0.4s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-spring: 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### 2.2 Semantic Color Usage

| Element | Color Variable |
|---------|---------------|
| Page background | `--bg-primary` |
| Section alternating | `--bg-secondary` |
| Cards | `--bg-glass` + `backdrop-filter: blur(var(--glass-blur))` |
| Primary buttons | `--gradient-brand` |
| Ghost buttons | transparent + `--border-brand` |
| Danger buttons | `--error` |
| Success states | `--success` |
| Error states | `--error` |
| Active quiz option | `--brand-purple` at 20% opacity |
| Correct answer highlight | `--success` |
| Wrong answer highlight | `--error` |
| Skipped question | `--warning` |

---

## 3. Typography

### 3.1 Font Stack

```css
/* Import in base.html */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-display:  'Outfit', sans-serif;    /* Hero headings, brand */
  --font-body:     'Inter', sans-serif;      /* Body, UI, labels */
  --font-mono:     'JetBrains Mono', monospace; /* Code questions */
}
```

### 3.2 Type Scale

```css
:root {
  --text-xs:   0.75rem;   /* 12px — captions, badges */
  --text-sm:   0.875rem;  /* 14px — secondary text, labels */
  --text-base: 1rem;      /* 16px — body text */
  --text-lg:   1.125rem;  /* 18px — card titles */
  --text-xl:   1.25rem;   /* 20px — section headings */
  --text-2xl:  1.5rem;    /* 24px — card headers */
  --text-3xl:  1.875rem;  /* 30px — page titles */
  --text-4xl:  2.25rem;   /* 36px — hero subheading */
  --text-5xl:  3rem;      /* 48px — hero heading */
  --text-6xl:  3.75rem;   /* 60px — XL hero */
  --text-7xl:  4.5rem;    /* 72px — splash hero */
}
```

### 3.3 Typography Classes

| Class | Font | Size | Weight | Use |
|-------|------|------|--------|-----|
| `.hero-title` | Outfit | 4.5–7xl | 800 | Landing hero H1 |
| `.hero-subtitle` | Inter | xl–2xl | 400 | Hero descriptor |
| `.section-title` | Outfit | 3xl–4xl | 700 | Section headings |
| `.card-title` | Outfit | lg–xl | 600 | Card headers |
| `.body-text` | Inter | base | 400 | Paragraphs |
| `.label` | Inter | sm | 500 | Form labels |
| `.caption` | Inter | xs | 400 | Secondary info |
| `.badge` | Inter | xs | 600 | Pill badges |
| `.code` | JetBrains Mono | sm | 400 | Code questions |
| `.stat-number` | Outfit | 3xl–4xl | 700 | Dashboard numbers |

---

## 4. Spacing & Layout

### 4.1 Spacing Scale

```css
:root {
  --space-1:   0.25rem;  /* 4px */
  --space-2:   0.5rem;   /* 8px */
  --space-3:   0.75rem;  /* 12px */
  --space-4:   1rem;     /* 16px */
  --space-5:   1.25rem;  /* 20px */
  --space-6:   1.5rem;   /* 24px */
  --space-8:   2rem;     /* 32px */
  --space-10:  2.5rem;   /* 40px */
  --space-12:  3rem;     /* 48px */
  --space-16:  4rem;     /* 64px */
  --space-20:  5rem;     /* 80px */
  --space-24:  6rem;     /* 96px */
  --space-32:  8rem;     /* 128px */
}
```

### 4.2 Grid System

```css
/* Main container */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-6);
}

.container-narrow {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 var(--space-6);
}

/* Card grids */
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-6); }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-6); }
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-6); }
```

### 4.3 Layout Patterns

**Dashboard Layout:**
```
+--sidebar (260px fixed)--+--main content area (flex 1)--+
|  Logo                   |  Top bar                      |
|  Nav links              |  Content grid                 |
|  User info              |                               |
+-------------------------+-------------------------------+
```

**Quiz Layout:**
```
+--top bar (timer + title + progress)--------------------+
|                                                         |
+--question area (65%)--+--palette + controls (35%)------+
|  Question text         |  Grid 5x5 (questions)          |
|  Option A              |  Bookmark toggle               |
|  Option B              |  Timer                         |
|  Option C              |  Submit button                 |
|  Option D              |                                |
+------------------------+--------------------------------+
```

---

## 5. Component Library

### 5.1 Glass Card

```css
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: transform var(--transition-normal),
              box-shadow var(--transition-normal),
              border-color var(--transition-normal);
}

.glass-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-glow);
  border-color: var(--border-brand);
}
```

### 5.2 Buttons

```css
/* Primary Button — gradient fill */
.btn-primary {
  background: var(--gradient-brand);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-weight: 600;
  font-size: var(--text-sm);
  border: none;
  cursor: pointer;
  transition: transform var(--transition-fast),
              box-shadow var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.btn-primary::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
}

.btn-primary:hover::before { opacity: 1; }
.btn-primary:active { transform: translateY(0); }

/* Ghost Button — outlined */
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-brand);
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-full);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast),
              box-shadow var(--transition-fast),
              transform var(--transition-fast);
}

.btn-ghost:hover {
  background: rgba(124, 58, 237, 0.1);
  box-shadow: 0 0 20px rgba(124, 58, 237, 0.2);
  transform: translateY(-1px);
}

/* Danger Button */
.btn-danger {
  background: var(--error);
  color: white;
  /* ... same structure as primary */
}
```

### 5.3 Form Inputs

```css
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}

.form-input {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-body);
  font-size: var(--text-base);
  color: var(--text-primary);
  outline: none;
  transition: border-color var(--transition-fast),
              box-shadow var(--transition-fast);
}

.form-input:focus {
  border-color: var(--brand-purple);
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
}

.form-input::placeholder { color: var(--text-tertiary); }
.form-input.error { border-color: var(--error); }
.form-error { font-size: var(--text-xs); color: var(--error); }
```

### 5.4 Navigation Bar

```
+-- Logo (QuizNova wordmark) --+-- Nav Links --+-- Auth Buttons --+
                                  Home
                                  Categories
                                  Leaderboard
                                  About
                                  Pricing

Height: 64px
Background: rgba(10, 10, 15, 0.8) with backdrop-filter blur(20px)
Position: sticky top 0
Z-index: 1000
Border-bottom: 1px solid var(--border-default)
```

### 5.5 Sidebar (Dashboard/Admin)

```
Width: 260px
Background: var(--bg-secondary)
Border-right: 1px solid var(--border-default)
Position: fixed left 0, top 0, height 100vh

Sections:
- Logo (top, 80px height)
- Navigation links (with icons, active state = gradient bg pill)
- User info card (bottom, avatar + name + role)
```

### 5.6 Quiz Option Card

```css
.quiz-option {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--bg-elevated);
  border: 1.5px solid var(--border-default);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quiz-option:hover {
  border-color: var(--brand-purple);
  background: rgba(124, 58, 237, 0.08);
}

.quiz-option.selected {
  border-color: var(--brand-purple);
  background: rgba(124, 58, 237, 0.15);
  box-shadow: 0 0 0 1px var(--brand-purple);
}

.quiz-option.correct {
  border-color: var(--success);
  background: var(--success-bg);
}

.quiz-option.wrong {
  border-color: var(--error);
  background: var(--error-bg);
}

.option-label {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-glass);
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--text-sm);
  flex-shrink: 0;
}
```

### 5.7 Question Palette

```css
.question-palette {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-2);
}

.palette-item {
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--border-default);
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

/* States */
.palette-item.answered    { background: var(--success-bg); border-color: var(--success); color: var(--success); }
.palette-item.current     { background: var(--brand-purple); border-color: var(--brand-purple); color: white; }
.palette-item.bookmarked  { background: var(--warning-bg); border-color: var(--warning); color: var(--warning); }
.palette-item.skipped     { background: var(--error-bg); border-color: var(--error); color: var(--error); }
```

### 5.8 Stat Card

```css
.stat-card {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.stat-card .stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--gradient-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: var(--space-2);
}

.stat-card .stat-value {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
}

.stat-card .stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.stat-card .stat-change {
  font-size: var(--text-xs);
  color: var(--success);  /* or --error */
  display: flex;
  align-items: center;
  gap: 4px;
}
```

### 5.9 Badge / Achievement

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.025em;
  text-transform: uppercase;
}

.badge-purple { background: rgba(124,58,237,0.15); color: var(--brand-purple-light); }
.badge-success { background: var(--success-bg); color: var(--success); }
.badge-warning { background: var(--warning-bg); color: var(--warning); }
.badge-error { background: var(--error-bg); color: var(--error); }
```

### 5.10 Loading Screen

```
Full-page overlay: background var(--bg-primary)
Center: QuizNova logo + animated neural network dots
Progress bar at bottom with gradient animation
Fade out on complete (GSAP opacity 0, display none)
```

---

## 6. Animation System

### 6.1 GSAP Animations

```javascript
// Page entrance
gsap.from('.hero-title', {
  duration: 1,
  y: 60,
  opacity: 0,
  ease: 'power3.out'
});

// Counter animation
gsap.to('.stat-counter', {
  innerText: targetValue,
  duration: 2,
  ease: 'power2.out',
  snap: { innerText: 1 },
  scrollTrigger: { trigger: '.stats-section', start: 'top 80%' }
});

// Card stagger on scroll
gsap.from('.category-card', {
  duration: 0.6,
  y: 40,
  opacity: 0,
  stagger: 0.1,
  ease: 'power2.out',
  scrollTrigger: { trigger: '.categories-grid', start: 'top 75%' }
});

// Quiz option ripple
function rippleEffect(element, event) {
  const ripple = document.createElement('span');
  ripple.classList.add('ripple');
  element.appendChild(ripple);
  gsap.fromTo(ripple, 
    { scale: 0, opacity: 0.5 }, 
    { scale: 4, opacity: 0, duration: 0.6, onComplete: () => ripple.remove() }
  );
}
```

### 6.2 AOS Configuration

```javascript
AOS.init({
  duration: 600,
  easing: 'ease-out-cubic',
  once: true,
  offset: 80,
  delay: 50
});
```

```html
<!-- Usage in HTML -->
<div class="category-card" data-aos="fade-up" data-aos-delay="100">...</div>
<div class="category-card" data-aos="fade-up" data-aos-delay="200">...</div>
```

### 6.3 CSS Micro-Animations

```css
/* Pulse glow on active timer */
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(124,58,237,0.3); }
  50% { box-shadow: 0 0 40px rgba(124,58,237,0.6); }
}

/* Floating animation (hero graphic) */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

/* Shimmer loading skeleton */
@keyframes shimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

.skeleton {
  background: linear-gradient(90deg, 
    var(--bg-elevated) 25%, 
    rgba(255,255,255,0.05) 50%, 
    var(--bg-elevated) 75%);
  background-size: 2000px 100%;
  animation: shimmer 1.5s infinite linear;
}

/* Score reveal animation */
@keyframes score-count {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Timer warning pulse */
@keyframes timer-urgent {
  0%, 100% { color: var(--error); }
  50% { color: var(--warning); }
}
```

---

## 7. Page-by-Page Blueprints

### 7.1 Landing Page (`home.html`)

```
[NAVBAR] — sticky, glass
[HERO SECTION]
  - Animated orbital/network graphic (canvas or CSS)
  - H1: "Test Your Knowledge" + gradient "Ignite Your Potential"
  - Subtext + CTA buttons (Start Quiz Now | Explore Categories)
  - Floating stat badges (50K+ Users, 10K+ Quizzes)

[STATS BAR] — horizontal, animated counters
  50K+ Users | 10K+ Quizzes | 1M+ Questions | 95% Success Rate

[CATEGORIES GRID]
  - Section title
  - 6-column card grid (scrollable on mobile)
  - Each card: icon + name + quiz count + hover glow

[FEATURES SECTION]
  - 3-column feature grid with icons and descriptions
  Features: Smart Quiz Engine | Real-time Analytics | Certificates |
            Compete & Rank | Secure & Reliable | Fullscreen Protection |
            Instant Results | Learn & Improve

[HOW IT WORKS]
  - 4-step horizontal timeline
  1. Sign Up 2. Choose Topic 3. Take Quiz 4. Get Certified

[LEADERBOARD PREVIEW]
  - Top 5 users table teaser
  - CTA to full leaderboard

[TESTIMONIALS]
  - 3 card carousel with avatar, quote, name, role

[PRICING]
  - 2 cards: Free | Pro
  - Feature comparison list

[FAQ]
  - Accordion, 8-10 questions

[CTA SECTION]
  - Full-width gradient banner
  - "Ready to Test Your Knowledge?" + buttons

[FOOTER]
  - Logo + tagline
  - Link columns: Product | Categories | Company | Support
  - Social icons
  - Copyright
```

### 7.2 Quiz Interface (`quiz/attempt.html`)

```
[TOP BAR — full width]
  Left: Quiz title + category badge
  Center: Progress bar (current/total questions)
  Right: Timer (MM:SS countdown) + [X] Exit button

[MAIN AREA — two columns]

[LEFT — Question Panel, 65%]
  Question number pill (e.g., "Question 8 of 25")
  Question text (large, clear font)
  Code block if code question
  4 Options (A/B/C/D) as clickable cards

[RIGHT — Controls Panel, 35%]
  Timer (large, prominent)
  Question Palette (5x5 grid or variable rows)
  Legend: Answered | Current | Bookmarked | Skipped | Not Visited
  Bookmark toggle button
  Submit Quiz button (danger style)

[BOTTOM BAR]
  [← Previous] [Next →]
  [Bookmark] toggle
```

### 7.3 Result Page (`quiz/result.html`)

```
[HEADER]
  "Great Job, {Name}!" with animation
  Trophy or Star graphic

[SCORE OVERVIEW — 4 cards]
  Your Score: X/Y | Percentage: Z% | Time: MM:SS | Rank: #N

[BREAKDOWN — horizontal stat row]
  Correct: N (green) | Wrong: N (red) | Skipped: N (yellow)

[CHARTS SECTION — 2 columns]
  Left: Donut chart (correct/wrong/skipped)
  Right: Radar chart (topic performance)

[TOPIC ANALYSIS]
  Strong Topics (green check list)
  Weak Topics (red x list)
  Suggestions card

[ACTIONS ROW]
  [Review Answers] [Download Certificate] [Retake Quiz] [Dashboard]
```

### 7.4 Dashboard (`dashboard/index.html`)

```
[SIDEBAR]
  Logo | Dashboard | Categories | Quizzes | Leaderboard | Certificates |
  Achievements | Profile | Settings | Logout

[MAIN CONTENT]

[TOP BAR]
  "Welcome back, {Name}!" + date
  Quick stats: Total Quizzes | Avg Score | Rank | Certificates

[STATS ROW — 4 cards]
  Quizzes Taken | Score | Rank | Certificates

[CONTENT GRID — 3 columns]
  [Progress by Category — bar chart]
  [Recent Activity — timeline list]
  [Recommended Quizzes — 2x3 grid]

[BOTTOM ROW — 2 columns]
  [Leaderboard position card]
  [Achievements progress]
```

### 7.5 Admin Dashboard (`admin/dashboard.html`)

```
[ADMIN SIDEBAR]
  Logo | Dashboard | Categories | Subcategories | Questions |
  Users | Certificates | Analytics | Settings

[MAIN CONTENT]

[TOP STATS — 4 cards]
  Total Users | Active Quizzes | Total Questions | Certificates Generated

[CHARTS ROW — 3 columns]
  User Growth (line) | Quiz Attempts (bar) | Score Distribution (histogram)

[TABLES SECTION — 2 columns]
  Recent Registrations table
  Recent Quiz Attempts table

[QUICK ACTIONS]
  Add Question | Upload CSV | Manage Users | View Reports
```

---

## 8. Responsive Breakpoints

```css
/* === BREAKPOINTS === */
/* Mobile:  320px – 767px */
/* Tablet:  768px – 1023px */
/* Laptop:  1024px – 1279px */
/* Desktop: 1280px+ */

@media (max-width: 767px) {
  .container { padding: 0 var(--space-4); }
  .grid-4 { grid-template-columns: repeat(2, 1fr); }
  .grid-3 { grid-template-columns: 1fr; }
  .hero-title { font-size: var(--text-4xl); }
  /* Sidebar converts to bottom nav */
  .sidebar { display: none; }
  .mobile-nav { display: flex; }
  /* Quiz converts to single column */
  .quiz-layout { flex-direction: column; }
  .question-palette { grid-template-columns: repeat(6, 1fr); }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .grid-4 { grid-template-columns: repeat(2, 1fr); }
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
  .sidebar { width: 80px; } /* Icon-only sidebar */
}

@media (min-width: 1024px) and (max-width: 1279px) {
  .grid-4 { grid-template-columns: repeat(3, 1fr); }
  .sidebar { width: 220px; }
}

@media (min-width: 1280px) {
  .sidebar { width: 260px; }
}
```

---

## 9. Icon System

Use **SVG icons inline** only. No icon font libraries.

### Sources
- Custom SVG icons for category logos (Programming = `</>`, AI = brain, etc.)
- Heroicons (MIT license) for UI icons (check, x, arrow, star, etc.)
- All SVGs inlined in HTML or loaded as separate .svg files
- Icons colored via `fill: currentColor` to inherit text color

### Category Icon Map

| Category | Icon Concept | Color |
|----------|-------------|-------|
| Programming | `</>` code brackets | #7C3AED |
| AI | Neural network nodes | #2563EB |
| Data Science | Bar chart | #0891B2 |
| Cyber Security | Shield | #DC2626 |
| Cloud Computing | Cloud | #D97706 |
| Computer Science | CPU chip | #059669 |
| Mathematics | Sigma symbol | #7C3AED |
| Science | Flask/Atom | #DB2777 |
| General Knowledge | Globe | #EA580C |
| Current Affairs | Newspaper | #65A30D |
| English | Book | #0284C7 |
| Soft Skills | People | #9333EA |

---

## 10. Accessibility Standards

### Required Standards
- **WCAG 2.1 Level AA** compliance
- Minimum contrast ratio: **4.5:1** for body text, **3:1** for large text

### Implementation Requirements
- All images have descriptive `alt` attributes
- Form inputs have associated `<label>` elements
- Focus indicators visible on all interactive elements (`outline: 2px solid var(--brand-purple)`)
- ARIA roles on custom components (quiz options, palette, modal)
- Keyboard navigation fully functional in quiz interface
- Error messages announced via `aria-live="polite"`
- Modal dialogs trap focus and restore on close
- Skip to main content link (hidden until focused) at top of every page

### ARIA Pattern Examples

```html
<!-- Quiz Option -->
<button 
  class="quiz-option" 
  role="radio" 
  aria-checked="false"
  aria-label="Option A: Indentation"
  id="option-a">
  <span class="option-label" aria-hidden="true">A</span>
  <span class="option-text">Indentation</span>
</button>

<!-- Timer -->
<div 
  role="timer" 
  aria-label="Time remaining" 
  aria-live="polite"
  id="quiz-timer">
  26:36
</div>

<!-- Anti-cheat warning -->
<div 
  role="alert" 
  aria-live="assertive"
  class="anticheat-warning">
  Warning: Fullscreen exited! This is violation 1 of 3.
</div>
```
