/**
 * QuizNova — Anti-Cheat System & Fullscreen Exam Engine (anti-cheat.js)
 * ====================================================================
 * Manages browser Fullscreen API, anti-cheat violation tracking (3-warning system),
 * exit confirmation modals, and synchronized header status badges.
 */

'use strict';

const AntiCheat = (() => {

  // Config injected from window
  const attemptId     = window.QUIZ_ATTEMPT_ID;
  const csrfToken     = window.CSRF_TOKEN;
  const maxViolations  = window.QUIZ_MAX_VIOLATIONS || 3;

  let violationCount   = window.QUIZ_VIOLATIONS || 0;
  let isFullscreen     = false;
  let isSubmitting     = false;
  let isReporting      = false;

  // -------------------------------------------------------------------------
  // INITIALIZATION
  // -------------------------------------------------------------------------
  function init() {
    _updateBadgeStatus(false);
    _attachEventListeners();
    _attemptInitialFullscreen();
    console.info('[AntiCheat] Initialized exam room engine. Max violations:', maxViolations);
  }

  // -------------------------------------------------------------------------
  // FULLSCREEN MANAGEMENT
  // -------------------------------------------------------------------------
  function requestFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) {
      return el.requestFullscreen().then(() => {
        isFullscreen = true;
        _updateBadgeStatus(true);
        _hideStartOverlay();
      }).catch(err => {
        console.warn('[AntiCheat] Fullscreen request blocked by browser policy:', err);
        _showStartOverlay();
      });
    } else if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen();
      isFullscreen = true;
      _updateBadgeStatus(true);
      _hideStartOverlay();
    } else {
      _showStartOverlay();
    }
  }

  function exitFullscreen() {
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(err => console.warn('[AntiCheat] Exit fullscreen error:', err));
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    }
    isFullscreen = false;
    _updateBadgeStatus(false);
  }

  function _attemptInitialFullscreen() {
    requestFullscreen();
  }

  function _onFullscreenChange() {
    const isNowFullscreen = !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement
    );

    if (isSubmitting) return;

    if (isFullscreen && !isNowFullscreen) {
      isFullscreen = false;
      _updateBadgeStatus(false);
      _handleViolation('fullscreen_exit', 'Fullscreen Exited');
    } else if (!isFullscreen && isNowFullscreen) {
      isFullscreen = true;
      _updateBadgeStatus(true);
      _hideWarning();
    }
  }

  function _updateBadgeStatus(active) {
    const badge = document.getElementById('fullscreen-status-badge');
    const badgeText = document.getElementById('fs-badge-text');
    if (!badge || !badgeText) return;

    if (active) {
      badge.classList.remove('lost');
      badge.classList.add('active');
      badgeText.textContent = 'FULLSCREEN ACTIVE';
    } else {
      badge.classList.remove('active');
      badge.classList.add('lost');
      badgeText.textContent = 'FULLSCREEN LOST';
    }
  }

  // -------------------------------------------------------------------------
  // START OVERLAY (Permission Fallback)
  // -------------------------------------------------------------------------
  function _showStartOverlay() {
    const overlay = document.getElementById('fullscreen-start-overlay');
    if (overlay) overlay.style.display = 'flex';
  }

  function _hideStartOverlay() {
    const overlay = document.getElementById('fullscreen-start-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  // -------------------------------------------------------------------------
  // EVENT HANDLERS (Tab Switch & Window Blur)
  // -------------------------------------------------------------------------
  function _onVisibilityChange() {
    if (document.hidden && !isSubmitting) {
      _handleViolation('tab_switch', 'Tab Switch Detected');
    }
  }

  function _preventContextMenu(e) {
    e.preventDefault();
    return false;
  }

  function _preventCopy(e) {
    e.preventDefault();
    return false;
  }

  function _preventSelection(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    e.preventDefault();
    return false;
  }

  function _onKeyDown(e) {
    const BLOCKED_COMBOS = [
      { ctrl: true, key: 'u' },
      { ctrl: true, key: 'U' },
      { ctrl: true, shift: true, key: 'I' },
      { ctrl: true, shift: true, key: 'i' },
      { ctrl: true, shift: true, key: 'J' },
      { ctrl: true, shift: true, key: 'j' },
      { ctrl: true, shift: true, key: 'C' },
      { ctrl: true, shift: true, key: 'c' },
      { key: 'F12' },
      { ctrl: true, key: 'a' },
      { ctrl: true, key: 'A' },
      { ctrl: true, key: 's' },
      { ctrl: true, key: 'S' },
      { ctrl: true, key: 'p' },
      { ctrl: true, key: 'P' },
    ];

    const isBlocked = BLOCKED_COMBOS.some(combo => {
      const ctrlMatch  = combo.ctrl  ? (e.ctrlKey || e.metaKey) : true;
      const shiftMatch = combo.shift ? e.shiftKey : true;
      const keyMatch   = e.key === combo.key;
      if (combo.ctrl !== undefined) return ctrlMatch && shiftMatch && keyMatch;
      return keyMatch;
    });

    if (isBlocked) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  }

  // -------------------------------------------------------------------------
  // VIOLATION & 3-WARNING SYSTEM (With 2s Debounce Cooldown)
  // -------------------------------------------------------------------------
  let lastViolationTime = 0;

  function _handleViolation(eventType, reasonTitle) {
    const now = Date.now();
    // Prevent duplicate event triggers within 2 seconds (e.g. visibilitychange + blur)
    if (now - lastViolationTime < 2000) return;
    lastViolationTime = now;

    if (isSubmitting || isReporting) return;
    isReporting = true;

    violationCount++;
    _updateViolationBadges();

    // Determine warning message based on count
    let title = `Warning ${violationCount}/${maxViolations} – ${reasonTitle}`;
    let message = `Please return to fullscreen mode to continue your exam.`;

    if (violationCount === 1) {
      title = `Warning 1/${maxViolations}: Please remain in fullscreen mode and stay on the quiz page.`;
      message = `You have exited fullscreen or switched away from the quiz page. Return to fullscreen to continue your exam.`;
    } else if (violationCount === 2) {
      title = `Warning 2/${maxViolations}: Leaving the quiz environment again may terminate your attempt.`;
      message = `Leaving fullscreen or switching away again will exceed the maximum violation limit and automatically submit your quiz.`;
    } else if (violationCount >= maxViolations) {
      title = `Warning 3/${maxViolations}: Maximum violations reached.`;
      message = `Maximum violation limit reached. Your quiz progress is being submitted now.`;
    }

    _reportViolationToServer(eventType);

    if (violationCount >= maxViolations) {
      _showTerminationWarning(title, message);
    } else {
      _showWarning(title, message, 'Return to Fullscreen', () => {
        isReporting = false;
        requestFullscreen();
      });
    }
  }

  async function _reportViolationToServer(eventType) {
    try {
      await fetch(`/api/v1/quiz/${attemptId}/report-violation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          event_type: eventType,
          meta: { timestamp: new Date().toISOString() }
        }),
      });
    } catch (err) {
      console.warn('[AntiCheat] Error reporting violation to server:', err);
    }
  }

  function _updateViolationBadges() {
    const counter = document.getElementById('violation-count');
    if (counter) counter.textContent = violationCount;

    const remainingNum = document.getElementById('anticheat-violation-num');
    if (remainingNum) remainingNum.textContent = violationCount;

    const badge = document.getElementById('violation-badge');
    if (badge) {
      badge.classList.remove('warning-level', 'danger-level');
      if (violationCount >= maxViolations - 1) {
        badge.classList.add('danger-level');
      } else if (violationCount > 0) {
        badge.classList.add('warning-level');
      }
    }
  }

  function _showWarning(title, message, buttonText, onConfirm) {
    const overlay = document.getElementById('anticheat-overlay');
    if (!overlay) return;

    const titleEl = document.getElementById('anticheat-title');
    const msgEl   = document.getElementById('anticheat-message');
    const btn     = document.getElementById('anticheat-dismiss-btn');

    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message;
    if (btn) {
      btn.textContent = buttonText;
      btn.onclick = () => {
        _hideWarning();
        if (onConfirm) onConfirm();
      };
    }

    overlay.style.display = 'flex';
  }

  function _hideWarning() {
    const overlay = document.getElementById('anticheat-overlay');
    if (overlay) overlay.style.display = 'none';
    isReporting = false;
  }

  function _showTerminationWarning(title, message) {
    isSubmitting = true;
    _showWarning(title, message, 'Submitting Quiz...', () => {
      _executeAutoSubmit();
    });

    setTimeout(() => {
      _executeAutoSubmit();
    }, 3000);
  }

  function _executeAutoSubmit() {
    exitFullscreen();
    if (window.QuizEngine && window.QuizEngine.autoSubmit) {
      window.QuizEngine.autoSubmit('max_violations');
    } else {
      const form = document.getElementById('final-submit-form');
      if (form) form.submit();
    }
  }

  // -------------------------------------------------------------------------
  // EXIT QUIZ & SUBMIT HANDLERS
  // -------------------------------------------------------------------------
  function _setupExitModal() {
    const exitBtn = document.getElementById('quiz-exit-btn');
    const overlay = document.getElementById('exit-quiz-overlay');
    const confirmBtn = document.getElementById('exit-confirm-btn');
    const cancelBtn  = document.getElementById('exit-cancel-btn');

    if (exitBtn && overlay) {
      exitBtn.addEventListener('click', () => {
        overlay.style.display = 'flex';
      });
    }

    if (cancelBtn && overlay) {
      cancelBtn.addEventListener('click', () => {
        overlay.style.display = 'none';
      });
    }

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => {
        isSubmitting = true;
        exitFullscreen();
        window.location.href = '/quiz/categories/';
      });
    }

    const startBtn = document.getElementById('start-fullscreen-btn');
    if (startBtn) {
      startBtn.addEventListener('click', () => {
        requestFullscreen();
      });
    }
  }

  // -------------------------------------------------------------------------
  // LISTENERS
  // -------------------------------------------------------------------------
  function _attachEventListeners() {
    document.addEventListener('fullscreenchange',       _onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', _onFullscreenChange);
    document.addEventListener('visibilitychange',       _onVisibilityChange);
    document.addEventListener('contextmenu',            _preventContextMenu);
    document.addEventListener('copy',                   _preventCopy);
    document.addEventListener('cut',                    _preventCopy);
    document.addEventListener('paste',                  _preventCopy);
    document.addEventListener('selectstart',            _preventSelection);
    document.addEventListener('keydown',                _onKeyDown, true);

    _setupExitModal();
  }

  return {
    init,
    requestFullscreen,
    exitFullscreen
  };

})();

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => AntiCheat.init());
