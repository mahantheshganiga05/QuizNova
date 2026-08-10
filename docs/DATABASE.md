# QuizNova — Database Design & Schema

**Version:** 1.0.0  
**Date:** 2026-07-30  
**Database:** MySQL 8.0+  
**ORM:** SQLAlchemy (Flask-SQLAlchemy)  

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Entity Relationship Overview](#2-entity-relationship-overview)
3. [Table Definitions](#3-table-definitions)
4. [Indexes & Performance](#4-indexes--performance)
5. [Complete SQL Schema](#5-complete-sql-schema)
6. [Seed Data Plan](#6-seed-data-plan)
7. [Query Patterns](#7-query-patterns)

---

## 1. Design Principles

- **Normalization:** 3NF minimum. No data duplication.
- **Soft Deletes:** Use `is_active` boolean instead of hard DELETE for categories, subcategories, questions, users.
- **Timestamps:** Every table has `created_at` and `updated_at` (auto-managed).
- **UUIDs for External IDs:** Certificates, verifications use UUID strings. Internal PKs are auto-increment integers for JOIN performance.
- **JSON Columns:** Used sparingly for shuffled options snapshot per quiz attempt (MySQL 8 JSON type).
- **Foreign Keys:** All FKs enforced at DB level with ON DELETE RESTRICT unless otherwise noted.
- **Charset:** utf8mb4 (supports emojis, all Unicode).

---

## 2. Entity Relationship Overview

```
users
  |-- (1:N) --> quiz_attempts
  |-- (1:N) --> certificates
  |-- (1:N) --> achievements_earned
  |-- (1:N) --> activity_logs
  |-- (1:N) --> anti_cheat_logs

categories
  |-- (1:N) --> subcategories
                    |-- (1:N) --> questions
                    |-- (1:N) --> quiz_attempts
                                      |-- (1:N) --> attempt_questions
                                      |                   |-- (1:1) --> attempt_answers
                                      |-- (1:1) --> results
                                      |-- (1:1) --> certificates

leaderboard_cache  (denormalized, refreshed periodically)
settings           (key-value config store)
achievements       (master list of all achievements)
achievements_earned (junction: user x achievement)
```

---

## 3. Table Definitions

---

### 3.1 `users`

Stores all registered users including admins.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | Internal user ID |
| username | VARCHAR(30) | UNIQUE, NOT NULL | Display username |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(100) | NULL | Optional full name |
| bio | TEXT | NULL | Profile bio |
| profile_photo | VARCHAR(255) | NULL | File path/URL |
| role | ENUM('student','admin') | NOT NULL, DEFAULT 'student' | Access level |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | Soft delete / ban |
| email_verified | TINYINT(1) | NOT NULL, DEFAULT 0 | Email verification flag |
| last_login_at | DATETIME | NULL | Track last login |
| login_count | INT UNSIGNED | NOT NULL, DEFAULT 0 | Total login count |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | |

---

### 3.2 `categories`

Top-level knowledge domains (Programming, AI, Data Science, etc.)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Category name |
| slug | VARCHAR(100) | NOT NULL, UNIQUE | URL-friendly name |
| description | TEXT | NULL | Short description |
| icon | VARCHAR(255) | NULL | SVG icon path |
| color_hex | VARCHAR(7) | NULL | Theme color (#RRGGBB) |
| sort_order | INT UNSIGNED | NOT NULL, DEFAULT 0 | Display order |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | |

---

### 3.3 `subcategories`

Topic subdivisions within each category.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| category_id | INT UNSIGNED | FK → categories.id, NOT NULL | Parent category |
| name | VARCHAR(100) | NOT NULL | Subcategory name |
| slug | VARCHAR(100) | NOT NULL | URL-friendly |
| description | TEXT | NULL | |
| icon | VARCHAR(255) | NULL | |
| questions_per_quiz | TINYINT UNSIGNED | NOT NULL, DEFAULT 20 | Q count per attempt |
| time_limit_minutes | TINYINT UNSIGNED | NOT NULL, DEFAULT 30 | Quiz time limit |
| pass_threshold | TINYINT UNSIGNED | NOT NULL, DEFAULT 60 | % needed to pass |
| difficulty_default | ENUM('easy','medium','hard') | NOT NULL, DEFAULT 'medium' | Default difficulty |
| sort_order | INT UNSIGNED | NOT NULL, DEFAULT 0 | |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | |

UNIQUE KEY: (category_id, slug)

---

### 3.4 `questions`

The central question bank.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| subcategory_id | INT UNSIGNED | FK → subcategories.id, NOT NULL | |
| question_text | TEXT | NOT NULL | The question (supports HTML entities) |
| option_a | VARCHAR(500) | NOT NULL | Option A text |
| option_b | VARCHAR(500) | NOT NULL | Option B text |
| option_c | VARCHAR(500) | NOT NULL | Option C text |
| option_d | VARCHAR(500) | NOT NULL | Option D text |
| correct_option | ENUM('a','b','c','d') | NOT NULL | Correct option key |
| explanation | TEXT | NULL | Post-attempt explanation |
| difficulty | ENUM('easy','medium','hard') | NOT NULL, DEFAULT 'medium' | |
| tags | VARCHAR(255) | NULL | Comma-separated topic tags |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | Soft delete |
| created_by | INT UNSIGNED | FK → users.id, NULL | Admin who added |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | |

---

### 3.5 `quiz_attempts`

One record per user quiz session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| user_id | INT UNSIGNED | FK → users.id, NOT NULL | |
| subcategory_id | INT UNSIGNED | FK → subcategories.id, NOT NULL | |
| status | ENUM('in_progress','submitted','abandoned') | NOT NULL, DEFAULT 'in_progress' | |
| started_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| submitted_at | DATETIME | NULL | Set on submission |
| time_taken_seconds | INT UNSIGNED | NULL | Calculated on submit |
| violation_count | TINYINT UNSIGNED | NOT NULL, DEFAULT 0 | Anti-cheat violations |
| auto_submitted | TINYINT(1) | NOT NULL, DEFAULT 0 | 1 if timer/violation auto-submit |
| ip_address | VARCHAR(45) | NULL | For audit |
| user_agent | VARCHAR(255) | NULL | For audit |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

INDEX: (user_id, subcategory_id), (user_id, status), (subcategory_id, submitted_at)

---

### 3.6 `attempt_questions`

Snapshot of which questions were shown in an attempt, with shuffled options.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| attempt_id | INT UNSIGNED | FK → quiz_attempts.id, NOT NULL | |
| question_id | INT UNSIGNED | FK → questions.id, NOT NULL | |
| question_order | TINYINT UNSIGNED | NOT NULL | Display position (1-based) |
| shuffled_options | JSON | NOT NULL | ["opt_text_1", "opt_text_2", "opt_text_3", "opt_text_4"] |
| correct_shuffled_index | TINYINT UNSIGNED | NOT NULL | 0-based index of correct option in shuffled_options |
| is_bookmarked | TINYINT(1) | NOT NULL, DEFAULT 0 | |

UNIQUE KEY: (attempt_id, question_id)
INDEX: (attempt_id, question_order)

---

### 3.7 `attempt_answers`

User's response to each question in an attempt.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| attempt_id | INT UNSIGNED | FK → quiz_attempts.id, NOT NULL | |
| attempt_question_id | INT UNSIGNED | FK → attempt_questions.id, NOT NULL | |
| selected_index | TINYINT | NULL | 0-3 for A-D, NULL = skipped |
| is_correct | TINYINT(1) | NULL | Computed on submission |
| answered_at | DATETIME | NULL | Timestamp of last answer change |

UNIQUE KEY: (attempt_id, attempt_question_id)

---

### 3.8 `results`

Aggregated result record for each submitted attempt.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| attempt_id | INT UNSIGNED | FK → quiz_attempts.id, UNIQUE, NOT NULL | One-to-one |
| user_id | INT UNSIGNED | FK → users.id, NOT NULL | Denormalized for queries |
| subcategory_id | INT UNSIGNED | FK → subcategories.id, NOT NULL | Denormalized |
| total_questions | TINYINT UNSIGNED | NOT NULL | |
| correct_count | TINYINT UNSIGNED | NOT NULL | |
| wrong_count | TINYINT UNSIGNED | NOT NULL | |
| skipped_count | TINYINT UNSIGNED | NOT NULL | |
| score | SMALLINT UNSIGNED | NOT NULL | Raw score (correct * points_per_q) |
| max_score | SMALLINT UNSIGNED | NOT NULL | |
| percentage | DECIMAL(5,2) | NOT NULL | 0.00–100.00 |
| rank | INT UNSIGNED | NULL | Computed rank at time of submission |
| is_passed | TINYINT(1) | NOT NULL | percentage >= pass_threshold |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

INDEX: (user_id, created_at), (subcategory_id, percentage DESC)

---

### 3.9 `certificates`

Generated certificates for passed quizzes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| certificate_uuid | CHAR(36) | NOT NULL, UNIQUE | UUID v4 for file naming |
| verification_id | VARCHAR(12) | NOT NULL, UNIQUE | Short alphanumeric for QR |
| user_id | INT UNSIGNED | FK → users.id, NOT NULL | |
| result_id | INT UNSIGNED | FK → results.id, UNIQUE, NOT NULL | |
| file_path | VARCHAR(500) | NULL | Local path to PDF |
| issue_date | DATE | NOT NULL | |
| is_valid | TINYINT(1) | NOT NULL, DEFAULT 1 | Admin can revoke |
| revoked_at | DATETIME | NULL | |
| revoke_reason | TEXT | NULL | |
| download_count | INT UNSIGNED | NOT NULL, DEFAULT 0 | |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

---

### 3.10 `leaderboard_cache`

Denormalized leaderboard scores (refreshed every 15 minutes via cron or on-submit).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| user_id | INT UNSIGNED | FK → users.id, NOT NULL | |
| subcategory_id | INT UNSIGNED | FK → subcategories.id, NULL | NULL = global |
| total_score | INT UNSIGNED | NOT NULL, DEFAULT 0 | Sum of best scores |
| quiz_count | INT UNSIGNED | NOT NULL, DEFAULT 0 | |
| best_percentage | DECIMAL(5,2) | NOT NULL, DEFAULT 0 | |
| rank | INT UNSIGNED | NULL | |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | |

UNIQUE KEY: (user_id, subcategory_id)
INDEX: (subcategory_id, total_score DESC)

---

### 3.11 `achievements`

Master list of all achievement definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| code | VARCHAR(50) | NOT NULL, UNIQUE | e.g. "PERFECT_SCORE" |
| name | VARCHAR(100) | NOT NULL | Display name |
| description | TEXT | NOT NULL | How to earn |
| icon | VARCHAR(255) | NULL | Badge icon path |
| points | SMALLINT UNSIGNED | NOT NULL, DEFAULT 0 | XP points awarded |
| trigger_type | VARCHAR(50) | NOT NULL | e.g. "score_100", "streak_7" |
| trigger_value | INT UNSIGNED | NULL | Threshold value |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | |

---

### 3.12 `achievements_earned`

Junction table for user achievements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| user_id | INT UNSIGNED | FK → users.id, NOT NULL | |
| achievement_id | INT UNSIGNED | FK → achievements.id, NOT NULL | |
| earned_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| context | JSON | NULL | e.g. {"attempt_id": 123} |

UNIQUE KEY: (user_id, achievement_id)

---

### 3.13 `anti_cheat_logs`

Audit log for all detected violations during quiz attempts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| attempt_id | INT UNSIGNED | FK → quiz_attempts.id, NOT NULL | |
| event_type | ENUM('tab_switch','fullscreen_exit','window_blur','right_click','copy_paste','keyboard_shortcut') | NOT NULL | |
| occurred_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| meta | JSON | NULL | Extra event data |

INDEX: (attempt_id, occurred_at)

---

### 3.14 `activity_logs`

General user activity for timeline and analytics.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| user_id | INT UNSIGNED | FK → users.id, NOT NULL | |
| event_type | VARCHAR(50) | NOT NULL | e.g. "quiz_completed", "certificate_downloaded" |
| entity_type | VARCHAR(50) | NULL | e.g. "quiz_attempt", "certificate" |
| entity_id | INT UNSIGNED | NULL | FK to entity |
| description | TEXT | NULL | Human-readable description |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

INDEX: (user_id, created_at DESC)

---

### 3.15 `settings`

Platform-wide configuration key-value store.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT UNSIGNED | PK, AUTO_INCREMENT | |
| setting_key | VARCHAR(100) | NOT NULL, UNIQUE | |
| setting_value | TEXT | NOT NULL | |
| description | TEXT | NULL | |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | |

---

## 4. Indexes & Performance

```sql
-- Critical query: get user's results ordered by date
CREATE INDEX idx_results_user_date ON results (user_id, created_at DESC);

-- Critical query: leaderboard by subcategory
CREATE INDEX idx_leaderboard_sub_score ON leaderboard_cache (subcategory_id, total_score DESC);

-- Critical query: admin user list with filters
CREATE INDEX idx_users_role_active ON users (role, is_active);

-- Critical query: questions by subcategory for quiz generation
CREATE INDEX idx_questions_sub_active ON questions (subcategory_id, is_active);

-- Critical query: attempt questions for a given attempt
CREATE INDEX idx_attempt_q_attempt ON attempt_questions (attempt_id, question_order);
```

---

## 5. Complete SQL Schema

```sql
-- ============================================================
-- QuizNova Database Schema v1.0
-- MySQL 8.0+
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS quiznova;
CREATE DATABASE quiznova
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE quiznova;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE users (
  id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  username      VARCHAR(30)     NOT NULL,
  email         VARCHAR(255)    NOT NULL,
  password_hash VARCHAR(255)    NOT NULL,
  full_name     VARCHAR(100)    NULL,
  bio           TEXT            NULL,
  profile_photo VARCHAR(255)    NULL,
  role          ENUM('student','admin') NOT NULL DEFAULT 'student',
  is_active     TINYINT(1)      NOT NULL DEFAULT 1,
  email_verified TINYINT(1)     NOT NULL DEFAULT 0,
  last_login_at DATETIME        NULL,
  login_count   INT UNSIGNED    NOT NULL DEFAULT 0,
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  INDEX idx_users_role_active (role, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: categories
-- ============================================================
CREATE TABLE categories (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  name        VARCHAR(100)  NOT NULL,
  slug        VARCHAR(100)  NOT NULL,
  description TEXT          NULL,
  icon        VARCHAR(255)  NULL,
  color_hex   VARCHAR(7)    NULL,
  sort_order  INT UNSIGNED  NOT NULL DEFAULT 0,
  is_active   TINYINT(1)    NOT NULL DEFAULT 1,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categories_slug (slug),
  INDEX idx_categories_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: subcategories
-- ============================================================
CREATE TABLE subcategories (
  id                  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  category_id         INT UNSIGNED  NOT NULL,
  name                VARCHAR(100)  NOT NULL,
  slug                VARCHAR(100)  NOT NULL,
  description         TEXT          NULL,
  icon                VARCHAR(255)  NULL,
  questions_per_quiz  TINYINT UNSIGNED NOT NULL DEFAULT 20,
  time_limit_minutes  TINYINT UNSIGNED NOT NULL DEFAULT 30,
  pass_threshold      TINYINT UNSIGNED NOT NULL DEFAULT 60,
  difficulty_default  ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium',
  sort_order          INT UNSIGNED  NOT NULL DEFAULT 0,
  is_active           TINYINT(1)    NOT NULL DEFAULT 1,
  created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sub_cat_slug (category_id, slug),
  INDEX idx_sub_category_active (category_id, is_active),
  CONSTRAINT fk_sub_category
    FOREIGN KEY (category_id) REFERENCES categories(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: questions
-- ============================================================
CREATE TABLE questions (
  id              INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  subcategory_id  INT UNSIGNED  NOT NULL,
  question_text   TEXT          NOT NULL,
  option_a        VARCHAR(500)  NOT NULL,
  option_b        VARCHAR(500)  NOT NULL,
  option_c        VARCHAR(500)  NOT NULL,
  option_d        VARCHAR(500)  NOT NULL,
  correct_option  ENUM('a','b','c','d') NOT NULL,
  explanation     TEXT          NULL,
  difficulty      ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium',
  tags            VARCHAR(255)  NULL,
  is_active       TINYINT(1)    NOT NULL DEFAULT 1,
  created_by      INT UNSIGNED  NULL,
  created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_questions_sub_active (subcategory_id, is_active),
  CONSTRAINT fk_q_subcategory
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_q_created_by
    FOREIGN KEY (created_by) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: quiz_attempts
-- ============================================================
CREATE TABLE quiz_attempts (
  id               INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  user_id          INT UNSIGNED  NOT NULL,
  subcategory_id   INT UNSIGNED  NOT NULL,
  status           ENUM('in_progress','submitted','abandoned')
                                 NOT NULL DEFAULT 'in_progress',
  started_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  submitted_at     DATETIME      NULL,
  time_taken_seconds INT UNSIGNED NULL,
  violation_count  TINYINT UNSIGNED NOT NULL DEFAULT 0,
  auto_submitted   TINYINT(1)    NOT NULL DEFAULT 0,
  ip_address       VARCHAR(45)   NULL,
  user_agent       VARCHAR(255)  NULL,
  created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_attempt_user_status (user_id, status),
  INDEX idx_attempt_sub_date (subcategory_id, submitted_at),
  CONSTRAINT fk_attempt_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_attempt_sub
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: attempt_questions
-- ============================================================
CREATE TABLE attempt_questions (
  id                    INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  attempt_id            INT UNSIGNED     NOT NULL,
  question_id           INT UNSIGNED     NOT NULL,
  question_order        TINYINT UNSIGNED NOT NULL,
  shuffled_options      JSON             NOT NULL,
  correct_shuffled_index TINYINT UNSIGNED NOT NULL,
  is_bookmarked         TINYINT(1)       NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_aq_attempt_question (attempt_id, question_id),
  INDEX idx_aq_attempt_order (attempt_id, question_order),
  CONSTRAINT fk_aq_attempt
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_aq_question
    FOREIGN KEY (question_id) REFERENCES questions(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: attempt_answers
-- ============================================================
CREATE TABLE attempt_answers (
  id                  INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  attempt_id          INT UNSIGNED    NOT NULL,
  attempt_question_id INT UNSIGNED    NOT NULL,
  selected_index      TINYINT         NULL,
  is_correct          TINYINT(1)      NULL,
  answered_at         DATETIME        NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_aa_attempt_q (attempt_id, attempt_question_id),
  CONSTRAINT fk_aa_attempt
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_aa_aq
    FOREIGN KEY (attempt_question_id) REFERENCES attempt_questions(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: results
-- ============================================================
CREATE TABLE results (
  id               INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  attempt_id       INT UNSIGNED    NOT NULL,
  user_id          INT UNSIGNED    NOT NULL,
  subcategory_id   INT UNSIGNED    NOT NULL,
  total_questions  TINYINT UNSIGNED NOT NULL,
  correct_count    TINYINT UNSIGNED NOT NULL,
  wrong_count      TINYINT UNSIGNED NOT NULL,
  skipped_count    TINYINT UNSIGNED NOT NULL,
  score            SMALLINT UNSIGNED NOT NULL,
  max_score        SMALLINT UNSIGNED NOT NULL,
  percentage       DECIMAL(5,2)    NOT NULL,
  rank_at_time     INT UNSIGNED    NULL,
  is_passed        TINYINT(1)      NOT NULL,
  created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_results_attempt (attempt_id),
  INDEX idx_results_user_date (user_id, created_at DESC),
  INDEX idx_results_sub_pct (subcategory_id, percentage DESC),
  CONSTRAINT fk_results_attempt
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_results_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_results_sub
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: certificates
-- ============================================================
CREATE TABLE certificates (
  id               INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  certificate_uuid CHAR(36)      NOT NULL,
  verification_id  VARCHAR(12)   NOT NULL,
  user_id          INT UNSIGNED  NOT NULL,
  result_id        INT UNSIGNED  NOT NULL,
  file_path        VARCHAR(500)  NULL,
  issue_date       DATE          NOT NULL,
  is_valid         TINYINT(1)    NOT NULL DEFAULT 1,
  revoked_at       DATETIME      NULL,
  revoke_reason    TEXT          NULL,
  download_count   INT UNSIGNED  NOT NULL DEFAULT 0,
  created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cert_uuid (certificate_uuid),
  UNIQUE KEY uq_cert_verif (verification_id),
  UNIQUE KEY uq_cert_result (result_id),
  INDEX idx_cert_user (user_id),
  CONSTRAINT fk_cert_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_cert_result
    FOREIGN KEY (result_id) REFERENCES results(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: leaderboard_cache
-- ============================================================
CREATE TABLE leaderboard_cache (
  id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  user_id         INT UNSIGNED    NOT NULL,
  subcategory_id  INT UNSIGNED    NULL,
  total_score     INT UNSIGNED    NOT NULL DEFAULT 0,
  quiz_count      INT UNSIGNED    NOT NULL DEFAULT 0,
  best_percentage DECIMAL(5,2)    NOT NULL DEFAULT 0.00,
  rank_position   INT UNSIGNED    NULL,
  updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_lb_user_sub (user_id, subcategory_id),
  INDEX idx_lb_sub_score (subcategory_id, total_score DESC),
  CONSTRAINT fk_lb_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_lb_sub
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: achievements
-- ============================================================
CREATE TABLE achievements (
  id            INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  code          VARCHAR(50)   NOT NULL,
  name          VARCHAR(100)  NOT NULL,
  description   TEXT          NOT NULL,
  icon          VARCHAR(255)  NULL,
  points        SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  trigger_type  VARCHAR(50)   NOT NULL,
  trigger_value INT UNSIGNED  NULL,
  is_active     TINYINT(1)    NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_achievement_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: achievements_earned
-- ============================================================
CREATE TABLE achievements_earned (
  id             INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  user_id        INT UNSIGNED  NOT NULL,
  achievement_id INT UNSIGNED  NOT NULL,
  earned_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  context        JSON          NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ae_user_ach (user_id, achievement_id),
  CONSTRAINT fk_ae_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ae_achievement
    FOREIGN KEY (achievement_id) REFERENCES achievements(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: anti_cheat_logs
-- ============================================================
CREATE TABLE anti_cheat_logs (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  attempt_id  INT UNSIGNED  NOT NULL,
  event_type  ENUM('tab_switch','fullscreen_exit','window_blur',
              'right_click','copy_paste','keyboard_shortcut') NOT NULL,
  occurred_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  meta        JSON          NULL,
  PRIMARY KEY (id),
  INDEX idx_acl_attempt_time (attempt_id, occurred_at),
  CONSTRAINT fk_acl_attempt
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: activity_logs
-- ============================================================
CREATE TABLE activity_logs (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED  NOT NULL,
  event_type  VARCHAR(50)   NOT NULL,
  entity_type VARCHAR(50)   NULL,
  entity_id   INT UNSIGNED  NULL,
  description TEXT          NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_al_user_date (user_id, created_at DESC),
  CONSTRAINT fk_al_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: settings
-- ============================================================
CREATE TABLE settings (
  id           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  setting_key  VARCHAR(100)  NOT NULL,
  setting_value TEXT         NOT NULL,
  description  TEXT          NULL,
  updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_settings_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
```

---

## 6. Seed Data Plan

The `database/seed.py` script will populate:

### Categories (12 total)
| # | Name | Color |
|---|------|-------|
| 1 | Programming | #7C3AED |
| 2 | Artificial Intelligence | #2563EB |
| 3 | Data Science | #0891B2 |
| 4 | Cyber Security | #DC2626 |
| 5 | Cloud Computing | #D97706 |
| 6 | Computer Science | #059669 |
| 7 | Mathematics | #7C3AED |
| 8 | Science | #DB2777 |
| 9 | General Knowledge | #EA580C |
| 10 | Current Affairs | #65A30D |
| 11 | English | #0284C7 |
| 12 | Soft Skills | #9333EA |

### Subcategories (4 per category = 48 total)

**Programming:** Python, Java, C Programming, JavaScript  
**Artificial Intelligence:** Machine Learning, Deep Learning, NLP, Computer Vision  
**Data Science:** Statistics, Data Analysis, Data Visualization, Big Data  
**Cyber Security:** Network Security, Ethical Hacking, Cryptography, Web Security  
**Cloud Computing:** AWS, Azure, GCP, DevOps  
**Computer Science:** Data Structures, Algorithms, OS, DBMS  
**Mathematics:** Algebra, Probability, Calculus, Discrete Math  
**Science:** Physics, Chemistry, Biology, Astronomy  
**General Knowledge:** History, Geography, Culture, Sports  
**Current Affairs:** Politics, Economy, Technology, International  
**English:** Grammar, Vocabulary, Reading Comprehension, Writing  
**Soft Skills:** Communication, Leadership, Problem Solving, Time Management  

### Questions: 25 per subcategory = 1,200 total questions (seed target)

### Settings Seed
```sql
INSERT INTO settings (setting_key, setting_value, description) VALUES
('max_violations', '3', 'Anti-cheat: violations before auto-submit'),
('site_name', 'QuizNova', 'Platform name'),
('pass_threshold_global', '60', 'Global default pass percentage'),
('certificate_enabled', '1', 'Enable certificate generation'),
('maintenance_mode', '0', 'Toggle maintenance mode'),
('registration_open', '1', 'Allow new user registrations');
```

### Achievements Seed (10 initial)
```sql
INSERT INTO achievements (code, name, description, points, trigger_type, trigger_value) VALUES
('FIRST_QUIZ', 'First Step', 'Complete your first quiz', 10, 'quiz_count', 1),
('PERFECT_SCORE', 'Perfect Score', 'Score 100% on any quiz', 50, 'score_100', NULL),
('SPEED_DEMON', 'Speed Demon', 'Finish quiz with >50% time remaining', 30, 'time_remaining_50pct', NULL),
('STREAK_7', 'Streak Master', 'Quiz 7 days in a row', 70, 'streak_days', 7),
('QUIZ_10', 'Getting Serious', 'Complete 10 quizzes', 20, 'quiz_count', 10),
('QUIZ_30', 'Consistent Learner', 'Complete 30 quizzes', 40, 'quiz_count', 30),
('CERT_1', 'Certified', 'Earn your first certificate', 25, 'cert_count', 1),
('CERT_5', 'Certificate Collector', 'Earn 5 certificates', 100, 'cert_count', 5),
('CAT_EXPLORER', 'Explorer', 'Attempt quizzes in 5+ categories', 35, 'category_count', 5),
('TOP_10', 'Top Ranker', 'Reach top 10 on global leaderboard', 150, 'rank_top', 10);
```

---

## 7. Query Patterns

### Get user dashboard stats
```sql
SELECT 
  COUNT(*) AS total_quizzes,
  AVG(percentage) AS avg_score,
  SUM(CASE WHEN is_passed=1 THEN 1 ELSE 0 END) AS passed,
  MAX(percentage) AS best_score
FROM results
WHERE user_id = :user_id;
```

### Get subcategory leaderboard (top 50)
```sql
SELECT 
  lc.rank_position,
  u.username, u.profile_photo,
  lc.total_score, lc.quiz_count, lc.best_percentage
FROM leaderboard_cache lc
JOIN users u ON u.id = lc.user_id
WHERE lc.subcategory_id = :sub_id OR (lc.subcategory_id IS NULL AND :sub_id IS NULL)
ORDER BY lc.total_score DESC
LIMIT 50;
```

### Get quiz questions for attempt (all shuffled)
```sql
SELECT 
  aq.id AS attempt_question_id,
  aq.question_order,
  q.question_text,
  aq.shuffled_options,
  aq.is_bookmarked,
  aa.selected_index
FROM attempt_questions aq
JOIN questions q ON q.id = aq.question_id
LEFT JOIN attempt_answers aa ON aa.attempt_question_id = aq.id
WHERE aq.attempt_id = :attempt_id
ORDER BY aq.question_order;
```

### Get user's weak topics (subcategory-level performance)
```sql
SELECT 
  s.name AS subcategory,
  COUNT(*) AS attempts,
  AVG(r.percentage) AS avg_pct
FROM results r
JOIN subcategories s ON s.id = r.subcategory_id
WHERE r.user_id = :user_id
GROUP BY r.subcategory_id
HAVING avg_pct < 50
ORDER BY avg_pct ASC;
```
