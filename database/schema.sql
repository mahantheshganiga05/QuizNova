-- ============================================================
-- QuizNova — MySQL 8.0+ Database Schema
-- ============================================================
-- Run: mysql -u root -p quiznova < database/schema.sql
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id`             INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  `username`       VARCHAR(30)     NOT NULL,
  `email`          VARCHAR(255)    NOT NULL,
  `password_hash`  VARCHAR(255)    NOT NULL,
  `full_name`      VARCHAR(100)    DEFAULT NULL,
  `bio`            TEXT            DEFAULT NULL,
  `profile_photo`  VARCHAR(255)    DEFAULT NULL,
  `role`           ENUM('student','admin') NOT NULL DEFAULT 'student',
  `is_active`      TINYINT(1)      NOT NULL DEFAULT 1,
  `email_verified` TINYINT(1)      NOT NULL DEFAULT 0,
  `last_login_at`  DATETIME        DEFAULT NULL,
  `login_count`    INT             NOT NULL DEFAULT 0,
  `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`),
  KEY `idx_users_role` (`role`),
  KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. CATEGORIES
-- ============================================================
CREATE TABLE IF NOT EXISTS `categories` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(100) NOT NULL,
  `slug`        VARCHAR(100) NOT NULL,
  `description` TEXT         DEFAULT NULL,
  `icon`        VARCHAR(255) DEFAULT NULL,
  `color_hex`   VARCHAR(7)   DEFAULT NULL,
  `sort_order`  INT          NOT NULL DEFAULT 0,
  `is_active`   TINYINT(1)   NOT NULL DEFAULT 1,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categories_name` (`name`),
  UNIQUE KEY `uq_categories_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. SUBCATEGORIES
-- ============================================================
CREATE TABLE IF NOT EXISTS `subcategories` (
  `id`                 INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  `category_id`        INT UNSIGNED  NOT NULL,
  `name`               VARCHAR(100)  NOT NULL,
  `slug`               VARCHAR(100)  NOT NULL,
  `description`        TEXT          DEFAULT NULL,
  `icon`               VARCHAR(255)  DEFAULT NULL,
  `questions_per_quiz` SMALLINT      NOT NULL DEFAULT 20,
  `time_limit_minutes` SMALLINT      NOT NULL DEFAULT 30,
  `pass_threshold`     SMALLINT      NOT NULL DEFAULT 60,
  `difficulty_default` ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium',
  `sort_order`         INT           NOT NULL DEFAULT 0,
  `is_active`          TINYINT(1)    NOT NULL DEFAULT 1,
  `created_at`         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sub_cat_slug` (`category_id`, `slug`),
  KEY `idx_sub_category` (`category_id`),
  CONSTRAINT `fk_sub_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. QUESTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS `questions` (
  `id`             INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  `subcategory_id` INT UNSIGNED  NOT NULL,
  `question_text`  TEXT          NOT NULL,
  `option_a`       VARCHAR(500)  NOT NULL,
  `option_b`       VARCHAR(500)  NOT NULL,
  `option_c`       VARCHAR(500)  NOT NULL,
  `option_d`       VARCHAR(500)  NOT NULL,
  `correct_option` ENUM('a','b','c','d') NOT NULL,
  `explanation`    TEXT          DEFAULT NULL,
  `difficulty`     ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium',
  `tags`           VARCHAR(255)  DEFAULT NULL,
  `is_active`      TINYINT(1)    NOT NULL DEFAULT 1,
  `created_by`     INT UNSIGNED  DEFAULT NULL,
  `created_at`     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_q_subcategory` (`subcategory_id`),
  KEY `idx_q_difficulty` (`difficulty`),
  KEY `idx_q_active` (`is_active`),
  CONSTRAINT `fk_q_subcategory` FOREIGN KEY (`subcategory_id`) REFERENCES `subcategories` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_q_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. QUIZ ATTEMPTS
-- ============================================================
CREATE TABLE IF NOT EXISTS `quiz_attempts` (
  `id`                  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  `user_id`             INT UNSIGNED  NOT NULL,
  `subcategory_id`      INT UNSIGNED  NOT NULL,
  `status`              ENUM('in_progress','submitted','abandoned') NOT NULL DEFAULT 'in_progress',
  `started_at`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `submitted_at`        DATETIME      DEFAULT NULL,
  `time_taken_seconds`  INT           DEFAULT NULL,
  `violation_count`     SMALLINT      NOT NULL DEFAULT 0,
  `auto_submitted`      TINYINT(1)    NOT NULL DEFAULT 0,
  `ip_address`          VARCHAR(45)   DEFAULT NULL,
  `user_agent`          VARCHAR(255)  DEFAULT NULL,
  `created_at`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_qa_user` (`user_id`),
  KEY `idx_qa_sub` (`subcategory_id`),
  KEY `idx_qa_status` (`status`),
  CONSTRAINT `fk_qa_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_qa_sub` FOREIGN KEY (`subcategory_id`) REFERENCES `subcategories` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. ATTEMPT QUESTIONS (Snapshot)
-- ============================================================
CREATE TABLE IF NOT EXISTS `attempt_questions` (
  `id`                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `attempt_id`             INT UNSIGNED NOT NULL,
  `question_id`            INT UNSIGNED NOT NULL,
  `question_order`         SMALLINT     NOT NULL,
  `shuffled_options`       TEXT         NOT NULL,
  `correct_shuffled_index` SMALLINT     NOT NULL,
  `is_bookmarked`          TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_aq_attempt_question` (`attempt_id`, `question_id`),
  KEY `idx_aq_attempt_order` (`attempt_id`, `question_order`),
  CONSTRAINT `fk_aq_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_aq_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. ATTEMPT ANSWERS
-- ============================================================
CREATE TABLE IF NOT EXISTS `attempt_answers` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `attempt_id`          INT UNSIGNED NOT NULL,
  `attempt_question_id` INT UNSIGNED NOT NULL,
  `selected_index`      SMALLINT     DEFAULT NULL,
  `is_correct`          TINYINT(1)   DEFAULT NULL,
  `answered_at`         DATETIME     DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_aa_attempt_q` (`attempt_id`, `attempt_question_id`),
  CONSTRAINT `fk_aa_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_aa_aq` FOREIGN KEY (`attempt_question_id`) REFERENCES `attempt_questions` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 8. RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS `results` (
  `id`              INT UNSIGNED   NOT NULL AUTO_INCREMENT,
  `attempt_id`      INT UNSIGNED   NOT NULL,
  `user_id`         INT UNSIGNED   NOT NULL,
  `subcategory_id`  INT UNSIGNED   NOT NULL,
  `total_questions` SMALLINT       NOT NULL,
  `correct_count`   SMALLINT       NOT NULL,
  `wrong_count`     SMALLINT       NOT NULL,
  `skipped_count`   SMALLINT       NOT NULL,
  `score`           INT            NOT NULL,
  `max_score`       INT            NOT NULL,
  `percentage`      DECIMAL(5,2)   NOT NULL,
  `rank_at_time`    INT            DEFAULT NULL,
  `is_passed`       TINYINT(1)     NOT NULL,
  `created_at`      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_result_attempt` (`attempt_id`),
  KEY `idx_result_user` (`user_id`),
  KEY `idx_result_sub` (`subcategory_id`),
  CONSTRAINT `fk_result_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_result_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_result_sub` FOREIGN KEY (`subcategory_id`) REFERENCES `subcategories` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 9. CERTIFICATES
-- ============================================================
CREATE TABLE IF NOT EXISTS `certificates` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `certificate_uuid` VARCHAR(36)  NOT NULL,
  `verification_id`  VARCHAR(12)  NOT NULL,
  `user_id`          INT UNSIGNED NOT NULL,
  `result_id`        INT UNSIGNED NOT NULL,
  `file_path`        VARCHAR(500) DEFAULT NULL,
  `issue_date`       DATE         NOT NULL,
  `is_valid`         TINYINT(1)   NOT NULL DEFAULT 1,
  `revoked_at`       DATETIME     DEFAULT NULL,
  `revoke_reason`    TEXT         DEFAULT NULL,
  `download_count`   INT          NOT NULL DEFAULT 0,
  `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cert_uuid` (`certificate_uuid`),
  UNIQUE KEY `uq_cert_verif` (`verification_id`),
  UNIQUE KEY `uq_cert_result` (`result_id`),
  KEY `idx_cert_user` (`user_id`),
  CONSTRAINT `fk_cert_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cert_result` FOREIGN KEY (`result_id`) REFERENCES `results` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 10. ACHIEVEMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS `achievements` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code`          VARCHAR(50)  NOT NULL,
  `name`          VARCHAR(100) NOT NULL,
  `description`   TEXT         NOT NULL,
  `icon`          VARCHAR(255) DEFAULT NULL,
  `points`        SMALLINT     NOT NULL DEFAULT 0,
  `trigger_type`  VARCHAR(50)  NOT NULL,
  `trigger_value` INT          DEFAULT NULL,
  `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ach_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 11. ACHIEVEMENTS EARNED
-- ============================================================
CREATE TABLE IF NOT EXISTS `achievements_earned` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`        INT UNSIGNED NOT NULL,
  `achievement_id` INT UNSIGNED NOT NULL,
  `earned_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `context`        TEXT         DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ae_user_ach` (`user_id`, `achievement_id`),
  CONSTRAINT `fk_ae_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_ae_ach` FOREIGN KEY (`achievement_id`) REFERENCES `achievements` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 12. LEADERBOARD CACHE
-- ============================================================
CREATE TABLE IF NOT EXISTS `leaderboard_cache` (
  `id`              INT UNSIGNED   NOT NULL AUTO_INCREMENT,
  `user_id`         INT UNSIGNED   NOT NULL,
  `subcategory_id`  INT UNSIGNED   DEFAULT NULL,
  `total_score`     INT            NOT NULL DEFAULT 0,
  `quiz_count`      INT            NOT NULL DEFAULT 0,
  `best_percentage` DECIMAL(5,2)   NOT NULL DEFAULT 0.00,
  `rank_position`   INT            DEFAULT NULL,
  `updated_at`      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lb_user_sub` (`user_id`, `subcategory_id`),
  KEY `idx_lb_sub_score` (`subcategory_id`, `total_score`),
  CONSTRAINT `fk_lb_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_lb_sub` FOREIGN KEY (`subcategory_id`) REFERENCES `subcategories` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 13. ACTIVITY LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS `activity_logs` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`     INT UNSIGNED NOT NULL,
  `event_type`  VARCHAR(50)  NOT NULL,
  `entity_type` VARCHAR(50)  DEFAULT NULL,
  `entity_id`   INT          DEFAULT NULL,
  `description` TEXT         DEFAULT NULL,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_al_user_date` (`user_id`, `created_at`),
  CONSTRAINT `fk_al_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 14. ANTI-CHEAT LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS `anti_cheat_logs` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `attempt_id`  INT UNSIGNED NOT NULL,
  `event_type`  ENUM('tab_switch','fullscreen_exit','window_blur','right_click','copy_paste','keyboard_shortcut') NOT NULL,
  `occurred_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `meta`        TEXT         DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_acl_attempt` (`attempt_id`),
  CONSTRAINT `fk_acl_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 15. SETTINGS
-- ============================================================
CREATE TABLE IF NOT EXISTS `settings` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `setting_key`   VARCHAR(100) NOT NULL,
  `setting_value` TEXT         NOT NULL,
  `description`   TEXT         DEFAULT NULL,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_settings_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
