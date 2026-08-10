# QuizNova — API Design Guide

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Base URL (Development):** `http://localhost:5000/api/v1`  
**Base URL (Production):** `https://quiznova.com/api/v1`  
**Auth:** Session-based (Flask-Login) for browser; API key ready for future integrations  

---

## Table of Contents

1. [API Standards](#1-api-standards)
2. [Authentication Endpoints](#2-authentication-endpoints)
3. [Category & Content Endpoints](#3-category--content-endpoints)
4. [Quiz Engine Endpoints](#4-quiz-engine-endpoints)
5. [Result Endpoints](#5-result-endpoints)
6. [Certificate Endpoints](#6-certificate-endpoints)
7. [Leaderboard Endpoints](#7-leaderboard-endpoints)
8. [Dashboard Endpoints](#8-dashboard-endpoints)
9. [Admin Endpoints](#9-admin-endpoints)
10. [AI Stub Endpoints (Future)](#10-ai-stub-endpoints-future)
11. [Error Reference](#11-error-reference)

---

## 1. API Standards

### Request Format
- **Content-Type:** `application/json` (for POST/PUT body)
- **CSRF:** Required on all state-changing requests (token in header `X-CSRFToken` or form field)
- **Auth:** Session cookie automatically sent by browser; no Bearer token needed in v1

### Response Envelope

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": { "field": "error description" }
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized (not logged in) |
| 403 | Forbidden (logged in but no permission) |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable Entity |
| 429 | Rate limit exceeded |
| 500 | Internal Server Error |

### Rate Limiting (v1 plan — implement via Flask-Limiter)
- Auth endpoints: 10 requests/minute per IP
- Quiz submission: 5 per minute per user
- General API: 60 requests/minute per user

---

## 2. Authentication Endpoints

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "arjun_sharma",
  "email": "arjun@example.com",
  "password": "SecurePass@123",
  "confirm_password": "SecurePass@123"
}
```

**Validation Rules:**
- `username`: 3-30 chars, alphanumeric + underscore, unique
- `email`: valid email, unique
- `password`: min 8 chars, ≥1 uppercase, ≥1 digit, ≥1 special char
- `confirm_password`: must match password

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "user_id": 42,
    "username": "arjun_sharma",
    "email": "arjun@example.com",
    "role": "student"
  },
  "message": "Account created successfully. Welcome to QuizNova!"
}
```

---

### POST /auth/login

Authenticate an existing user.

**Request Body:**
```json
{
  "email": "arjun@example.com",
  "password": "SecurePass@123",
  "remember_me": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "user_id": 42,
    "username": "arjun_sharma",
    "role": "student",
    "redirect_url": "/dashboard"
  }
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email or password is incorrect."
  }
}
```

---

### POST /auth/logout

End the current user session.

**Success Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully.",
  "data": { "redirect_url": "/" }
}
```

---

### GET /auth/me

Get current authenticated user's profile.

**Headers:** Requires valid session

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "username": "arjun_sharma",
    "email": "arjun@example.com",
    "full_name": "Arjun Sharma",
    "bio": "CS student at IIT",
    "profile_photo_url": "/static/uploads/profiles/uuid.jpg",
    "role": "student",
    "created_at": "2026-01-15T10:30:00Z",
    "stats": {
      "total_quizzes": 128,
      "avg_score": 85.6,
      "rank": 42,
      "certificates": 12
    }
  }
}
```

---

### PUT /auth/profile

Update user profile fields.

**Request Body (multipart/form-data for photo upload, or JSON for text fields):**
```json
{
  "full_name": "Arjun Sharma",
  "bio": "Engineering student passionate about AI",
  "username": "arjun_sharma"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully.",
  "data": { "profile_photo_url": "/static/uploads/profiles/new-uuid.jpg" }
}
```

---

## 3. Category & Content Endpoints

### GET /api/v1/categories

List all active categories.

**Query Params:** `?include_stats=true`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "Programming",
        "slug": "programming",
        "description": "Code your way to the top",
        "icon": "/static/icons/programming.svg",
        "color_hex": "#7C3AED",
        "subcategory_count": 4,
        "total_questions": 120,
        "quiz_count": 1200
      }
    ],
    "total": 12
  }
}
```

---

### GET /api/v1/categories/:id/subcategories

List subcategories for a category.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "category": {
      "id": 1,
      "name": "Programming",
      "slug": "programming"
    },
    "subcategories": [
      {
        "id": 1,
        "name": "Python",
        "slug": "python",
        "description": "Python programming fundamentals to advanced",
        "questions_per_quiz": 20,
        "time_limit_minutes": 30,
        "pass_threshold": 60,
        "question_count": 125,
        "difficulty_default": "medium"
      }
    ]
  }
}
```

---

## 4. Quiz Engine Endpoints

### POST /api/v1/quiz/start

Start a new quiz attempt.

**Request Body:**
```json
{
  "subcategory_id": 1
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "attempt_id": 789,
    "subcategory": {
      "id": 1,
      "name": "Python",
      "questions_per_quiz": 20,
      "time_limit_minutes": 30,
      "pass_threshold": 60
    },
    "questions": [
      {
        "attempt_question_id": 1001,
        "question_order": 1,
        "question_text": "Which keyword is used to define a function in Python?",
        "options": [
          "function",
          "def",
          "define",
          "func"
        ]
      }
    ],
    "started_at": "2026-07-30T13:00:00Z",
    "expires_at": "2026-07-30T13:30:00Z"
  }
}
```

> **Security Note:** `correct_shuffled_index` is NEVER sent to the client. It stays server-side.

---

### POST /api/v1/quiz/:attempt_id/save-answer

Save or update a single answer (called on Next/Previous navigation).

**Request Body:**
```json
{
  "attempt_question_id": 1001,
  "selected_index": 1
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Answer saved."
}
```

---

### POST /api/v1/quiz/:attempt_id/bookmark

Toggle bookmark on a question.

**Request Body:**
```json
{
  "attempt_question_id": 1001,
  "is_bookmarked": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": { "is_bookmarked": true }
}
```

---

### POST /api/v1/quiz/:attempt_id/report-violation

Log an anti-cheat violation event.

**Request Body:**
```json
{
  "event_type": "tab_switch",
  "meta": { "timestamp": "2026-07-30T13:05:22Z" }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "violation_count": 2,
    "max_violations": 3,
    "auto_submit": false
  }
}
```

**Auto-submit triggered (200):**
```json
{
  "success": true,
  "data": {
    "violation_count": 3,
    "max_violations": 3,
    "auto_submit": true,
    "redirect_url": "/quiz/result/789"
  }
}
```

---

### POST /api/v1/quiz/:attempt_id/submit

Submit the quiz (manual or auto).

**Request Body:**
```json
{
  "auto_submitted": false,
  "answers": [
    { "attempt_question_id": 1001, "selected_index": 1 },
    { "attempt_question_id": 1002, "selected_index": null }
  ]
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "result_id": 456,
    "redirect_url": "/quiz/result/789"
  }
}
```

---

### GET /api/v1/quiz/:attempt_id/state

Recover quiz state on page refresh.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "attempt_id": 789,
    "status": "in_progress",
    "seconds_remaining": 1245,
    "violation_count": 0,
    "current_question_order": 5,
    "answers": {
      "1001": 1,
      "1002": null,
      "1003": 2
    },
    "bookmarks": [1001, 1005]
  }
}
```

---

## 5. Result Endpoints

### GET /api/v1/result/:attempt_id

Get full result data for a completed attempt.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "result": {
      "id": 456,
      "attempt_id": 789,
      "subcategory": { "id": 1, "name": "Python" },
      "total_questions": 20,
      "correct_count": 17,
      "wrong_count": 2,
      "skipped_count": 1,
      "score": 85,
      "max_score": 100,
      "percentage": 85.0,
      "rank": 42,
      "is_passed": true,
      "time_taken_seconds": 840,
      "created_at": "2026-07-30T13:14:00Z"
    },
    "topic_analysis": {
      "strong": ["Functions", "OOP", "Lists"],
      "weak": ["Decorators", "Generators"]
    },
    "suggestions": [
      "Review Python decorators — you got 1/3 correct in this topic.",
      "Practice generator functions with hands-on coding exercises."
    ],
    "certificate_available": true,
    "certificate_id": null
  }
}
```

---

### GET /api/v1/result/:attempt_id/review

Get full question-by-question review.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "question_order": 1,
        "question_text": "Which keyword is used to define a function in Python?",
        "options": ["function", "def", "define", "func"],
        "selected_index": 1,
        "correct_index": 1,
        "is_correct": true,
        "explanation": "'def' is the keyword used to define functions in Python. 'function' is used in JavaScript.",
        "difficulty": "easy"
      }
    ]
  }
}
```

---

## 6. Certificate Endpoints

### POST /api/v1/certificate/generate

Generate a certificate for a passed result (idempotent).

**Request Body:**
```json
{
  "result_id": 456
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "certificate_id": 23,
    "certificate_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "verification_id": "QN-ABC123",
    "download_url": "/api/v1/certificate/23/download",
    "verification_url": "/verify/QN-ABC123",
    "issue_date": "2026-07-30"
  }
}
```

---

### GET /api/v1/certificate/:id/download

Download a certificate PDF.

**Success Response:** Binary PDF file (Content-Disposition: attachment)

---

### GET /verify/:verification_id

Public verification endpoint (no auth required).

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "candidate_name": "Arjun Sharma",
    "quiz_name": "Python Programming",
    "category": "Programming",
    "percentage": 85.0,
    "issue_date": "2026-07-30",
    "certificate_id": "QN-ABC123"
  }
}
```

---

## 7. Leaderboard Endpoints

### GET /api/v1/leaderboard

Get leaderboard data.

**Query Params:**
- `scope`: `global` | `weekly` (default: global)
- `subcategory_id`: integer or omit for global
- `page`: integer (default: 1)
- `per_page`: integer (default: 50, max: 100)

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "scope": "global",
    "total_users": 5000,
    "current_user_rank": 42,
    "leaderboard": [
      {
        "rank": 1,
        "user_id": 101,
        "username": "sarah_wilson",
        "full_name": "Sarah Wilson",
        "profile_photo_url": "/static/uploads/profiles/sarah.jpg",
        "total_score": 9870,
        "quiz_count": 156,
        "best_percentage": 98.7,
        "badges": ["PERFECT_SCORE", "STREAK_7", "TOP_10"]
      }
    ]
  }
}
```

---

## 8. Dashboard Endpoints

### GET /api/v1/dashboard/stats

Get user's personal statistics.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "total_quizzes": 128,
    "avg_score": 85.6,
    "best_score": 100.0,
    "rank": 42,
    "certificates_earned": 12,
    "total_time_minutes": 3840,
    "current_streak_days": 5
  }
}
```

---

### GET /api/v1/dashboard/progress

Get category-wise progress.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "progress": [
      { "category": "Programming", "avg_score": 92, "quizzes": 40 },
      { "category": "Data Science", "avg_score": 78, "quizzes": 18 },
      { "category": "AI", "avg_score": 85, "quizzes": 22 }
    ]
  }
}
```

---

### GET /api/v1/dashboard/activity

Get recent activity timeline.

**Query Params:** `?limit=10`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "event_type": "quiz_completed",
        "description": "Python Quiz — 85% · Rank #42",
        "entity_type": "quiz_attempt",
        "entity_id": 789,
        "created_at": "2026-07-30T13:14:00Z"
      }
    ]
  }
}
```

---

### GET /api/v1/dashboard/achievements

Get user's achievements (earned + locked).

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "earned": [
      {
        "code": "FIRST_QUIZ",
        "name": "First Step",
        "description": "Complete your first quiz",
        "icon": "/static/icons/badges/first_quiz.svg",
        "points": 10,
        "earned_at": "2026-01-15T11:00:00Z"
      }
    ],
    "locked": [
      {
        "code": "PERFECT_SCORE",
        "name": "Perfect Score",
        "description": "Score 100% on any quiz",
        "icon": "/static/icons/badges/perfect_score.svg",
        "points": 50
      }
    ],
    "total_points": 85
  }
}
```

---

## 9. Admin Endpoints

> All admin endpoints require `role == 'admin'` and admin session. Return 403 otherwise.

### GET /api/v1/admin/stats

System-wide statistics.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "total_users": 12458,
    "active_users_today": 1245,
    "total_questions": 25680,
    "total_attempts": 85742,
    "certificates_generated": 3241,
    "new_users_today": 48,
    "new_attempts_today": 892
  }
}
```

---

### GET /api/v1/admin/users

List all users with filters.

**Query Params:** `?search=arjun&role=student&is_active=1&page=1&per_page=20`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "users": [ ... ],
    "total": 12458,
    "page": 1,
    "per_page": 20
  }
}
```

---

### PUT /api/v1/admin/users/:id

Update a user (role, ban status).

**Request Body:**
```json
{
  "role": "student",
  "is_active": false
}
```

---

### POST /api/v1/admin/questions/bulk-import

Bulk import questions from CSV data.

**Request:** multipart/form-data, field `file` = CSV file

**CSV Format:**
```
subcategory_id,question_text,option_a,option_b,option_c,option_d,correct_option,difficulty,explanation
1,"What does PEP stand for?","Python Enhancement Proposal","Python Easy Package","Package Enhancement Plan","None","a","easy","PEP stands for Python Enhancement Proposal..."
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "imported": 45,
    "skipped": 2,
    "errors": [
      { "row": 12, "message": "subcategory_id 99 does not exist" },
      { "row": 31, "message": "correct_option must be a, b, c, or d" }
    ]
  }
}
```

---

### GET /api/v1/admin/export/:resource

Export data as CSV.

**Params:** `resource` = `users` | `results` | `certificates`
**Query:** `?start_date=2026-01-01&end_date=2026-07-30`

**Success Response:** CSV file download

---

### PUT /api/v1/admin/certificates/:id/revoke

Revoke a certificate.

**Request Body:**
```json
{
  "reason": "Fraudulent submission detected"
}
```

---

## 10. AI Stub Endpoints (Future)

These endpoints exist in the codebase as stubs that return `501 Not Implemented`. They define the contract for future AI integration.

### POST /api/v1/ai/generate-question

Generate a question using AI.

**Request Body:**
```json
{
  "subcategory_id": 1,
  "difficulty": "medium",
  "topic_hint": "list comprehensions"
}
```

**Stub Response (501):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_IMPLEMENTED",
    "message": "AI question generation is coming soon. This feature will be powered by Google Gemini API.",
    "eta": "Q3 2026"
  }
}
```

---

### POST /api/v1/ai/explain

Get AI explanation for a question.

**Request Body:**
```json
{
  "question_id": 101,
  "user_answer_index": 2
}
```

**Stub Response (501):** Same pattern as above.

---

### POST /api/v1/ai/skill-gap

Get AI-powered skill gap analysis.

**Request Body:**
```json
{
  "user_id": 42,
  "target_role": "Data Scientist"
}
```

**Stub Response (501):** Same pattern as above.

---

### POST /api/v1/ai/roadmap

Generate a personalized study roadmap.

**Request Body:**
```json
{
  "user_id": 42,
  "goal": "Pass GATE CS 2027",
  "available_hours_per_week": 15
}
```

**Stub Response (501):** Same pattern as above.

---

## 11. Error Reference

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `INVALID_CREDENTIALS` | 401 | Login failed |
| `UNAUTHORIZED` | 401 | Not logged in |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource does not exist |
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `DUPLICATE_ENTRY` | 409 | Unique constraint violation |
| `QUIZ_ALREADY_SUBMITTED` | 409 | Attempt already has result |
| `QUIZ_NOT_IN_PROGRESS` | 400 | Attempt status is not in_progress |
| `QUIZ_EXPIRED` | 400 | Timer expired server-side |
| `INSUFFICIENT_QUESTIONS` | 400 | Subcategory has < required questions |
| `CERTIFICATE_NOT_ELIGIBLE` | 400 | Score below pass threshold |
| `NOT_IMPLEMENTED` | 501 | Feature not yet available |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `RATE_LIMITED` | 429 | Too many requests |
