/**
 * QuizNova — Anti-Cheat System (anti-cheat.js)
 * ===============================================
 * Detects suspicious behavior during a quiz attempt.
 * Reports violations to the server and auto-submits when threshold is reached.
 *
 * BROWSER LIMITATIONS (documented honestly):
 * - Fullscreen can always be exited by the browser itself (no JS can prevent ESC key in all browsers)
 * - Tab switching via keyboard shortcuts may not be fully preventable on all OS/browsers
 * - Developer tools detection via DevTools is unreliable across browsers
 * - iOS Safari does not support the Fullscreen API at all
 *
 * WHAT WE DO IMPLEMENT:
 * - Request fullscreen on quiz start
 * - Detect and log fullscreen exit (visibilitychange, fullscreenchange)
 * - Detect tab switch (visibilitychange)
 * - Detect window minimize / alt-tab (window blur)
 * - Disable right-click context menu
 * - Disable copy/paste/cut
 * - Disable text selection
 * - Block common developer shortcuts
 * - Report all violations to server
 * - Auto-submit on max violation threshold
 */

'use strict';

const AntiCheat = (() => {

  // Config injected from template
  const attemptId    = window.QUIZ_ATTEMPT_ID;
  const csrfToken    = window.CSRF_TOKEN;
  const maxViolations = window.QUIZ_MAX_VIOLATIONS || 3;

  let violationCount  = window.QUIZ_VIOLATIONS || 0;
  let isFullscreen    = false;
  let quizSubmitted   = false;
  let warningVisible  = false;

  // -------------------------------------------------------------------------
  // INITIALIZATION
  // -------------------------------------------------------------------------
  function init() {
    _requestFullscreen();
    _attachListeners();
    console.info('[AntiCheat] Initialized. Max violations:', maxViolations);
  }

  // -------------------------------------------------------------------------
  // FULLSCREEN
  // -------------------------------------------------------------------------
  function _requestFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) {
      el.requestFullscreen().then(() => {
        isFullscreen = true;
      }).catch(() => {
        // Fullscreen request blocked (some browsers require user gesture)
        console.warn('[AntiCheat] Fullscreen request was blocked or not supported.');
      });
    } else if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen();
      isFullscreen = true;
    }
  }

  function _onFullscreenChange() {
    const isNowFullscreen = !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement
    );

    if (isFullscreen && !isNowFullscreen) {
      // Fullscreen was exited
      isFullscreen = false;
      _reportViolation('fullscreen_exit');
      _showWarning('⚠️ Fullscreen Exited',
        `You have exited fullscreen mode. This has been recorded as a violation (${violationCount + 1}/${maxViolations}). Return to fullscreen to continue.`,
        'Return to Fullscreen',
        _requestFullscreen
      );
    } else if (!isFullscreen && isNowFullscreen) {
      isFullscreen = true;
      _hideWarning();
    }
  }

  // -------------------------------------------------------------------------
  // TAB SWITCH / VISIBILITY
  // -------------------------------------------------------------------------
  function _onVisibilityChange() {
    if (document.hidden) {
      _reportViolation('tab_switch');
    }
  }

  // -------------------------------------------------------------------------
  // WINDOW BLUR (minimize or alt-tab without changing visibility)
  // -------------------------------------------------------------------------
  function _onWindowBlur() {
    // Only fire if not already in a fullscreen-exit violation
    if (!document.hidden) {
      _reportViolation('window_blur');
    }
  }

  // -------------------------------------------------------------------------
  // CONTEXT MENU (right-click)
  // -------------------------------------------------------------------------
  function _preventContextMenu(e) {
    e.preventDefault();
    _reportViolation('right_click');
    return false;
  }

  // -------------------------------------------------------------------------
  // COPY / PASTE / CUT
  // -------------------------------------------------------------------------
  function _preventCopy(e) {
    e.preventDefault();
    _reportViolation('copy_paste');
    return false;
  }

  // -------------------------------------------------------------------------
  // TEXT SELECTION
  // -------------------------------------------------------------------------
  function _preventSelection(e) {
    // Allow selection in input fields and textareas
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    e.preventDefault();
    return false;
  }

  // -------------------------------------------------------------------------
  // KEYBOARD SHORTCUTS
  // -------------------------------------------------------------------------
  function _onKeyDown(e) {
    const BLOCKED_COMBOS = [
      { ctrl: true, key: 'u' },   // View source
      { ctrl: true, key: 'U' },
      { ctrl: true, shift: true, key: 'I' }, // DevTools
      { ctrl: true, shift: true, key: 'i' },
      { ctrl: true, shift: true, key: 'J' }, // Console
      { ctrl: true, shift: true, key: 'j' },
      { ctrl: true, shift: true, key: 'C' }, // Inspect
      { ctrl: true, shift: true, key: 'c' },
      { key: 'F12' },                         // DevTools
      { ctrl: true, key: 'a' },               // Select all
      { ctrl: true, key: 'A' },
      { ctrl: true, key: 's' },               // Save
      { ctrl: true, key: 'S' },
      { ctrl: true, key: 'p' },               // Print
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
      _reportViolation('keyboard_shortcut');
      return false;
    }
  }

  // -------------------------------------------------------------------------
  // VIOLATION REPORTING
  // -------------------------------------------------------------------------
  async function _reportViolation(eventType) {
    if (quizSubmitted) return;

    violationCount++;
    _updateViolationCounter();

    try {
      const res = await fetch(`/api/v1/quiz/${attemptId}/report-violation`, {
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

      const data = await res.json();

      if (data.success && data.data.auto_submit) {
        quizSubmitted = true;
        _showAutoSubmitScreen();
      }
    } catch (err) {
      console.warn('[AntiCheat] Failed to report violation:', err);
      // Still enforce locally if server unreachable
      if (violationCount >= maxViolations) {
        _showAutoSubmitScreen();
      }
    }
  }

  function _updateViolationCounter() {
    const counter = document.getElementById('violation-count');
    if (!counter) return;

    counter.textContent = `${violationCount}/${maxViolations} violations`;
    counter.parentElement.classList.remove('warning-level', 'danger-level');

    if (violationCount >= maxViolations - 1) {
      counter.parentElement.classList.add('danger-level');
    } else if (violationCount > 0) {
      counter.parentElement.classList.add('warning-level');
    }
  }

  // -------------------------------------------------------------------------
  // WARNING OVERLAY
  // -------------------------------------------------------------------------
  function _showWarning(title, message, buttonText, onConfirm) {
    if (warningVisible) return;
    warningVisible = true;

    const overlay = document.getElementById('anticheat-overlay');
    if (!overlay) return;

    overlay.querySelector('#ac-title').textContent   = title;
    overlay.querySelector('#ac-message').textContent = message;

    const btn = overlay.querySelector('#ac-action-btn');
    btn.textContent = buttonText;
    btn.onclick = () => {
      _hideWarning();
      if (onConfirm) onConfirm();
    };

    overlay.style.display = 'flex';
  }

  function _hideWarning() {
    const overlay = document.getElementById('anticheat-overlay');
    if (overlay) overlay.style.display = 'none';
    warningVisible = false;
  }

  function _showAutoSubmitScreen() {
    const overlay = document.getElementById('anticheat-overlay');
    if (overlay) {
      overlay.querySelector('#ac-title').textContent   = '🚫 Quiz Auto-Submitted';
      overlay.querySelector('#ac-message').textContent =
        `You have exceeded ${maxViolations} anti-cheat violations. Your quiz has been automatically submitted.`;
      const btn = overlay.querySelector('#ac-action-btn');
      btn.textContent = 'View Results';
      btn.onclick = () => {
        // Trigger quiz engine auto-submit
        if (window.QuizEngine) {
          window.QuizEngine.autoSubmit?.('max_violations');
        } else {
          window.location.href = `/quiz/result/${attemptId}`;
        }
      };
      overlay.style.display = 'flex';
    }
  }

  // -------------------------------------------------------------------------
  // ATTACH ALL LISTENERS
  // -------------------------------------------------------------------------
  function _attachListeners() {
    document.addEventListener('fullscreenchange',       _onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', _onFullscreenChange);
    document.addEventListener('visibilitychange',       _onVisibilityChange);
    window.addEventListener('blur',                     _onWindowBlur);
    document.addEventListener('contextmenu',            _preventContextMenu);
    document.addEventListener('copy',                   _preventCopy);
    document.addEventListener('cut',                    _preventCopy);
    document.addEventListener('paste',                  _preventCopy);
    document.addEventListener('selectstart',            _preventSelection);
    document.addEventListener('keydown',                _onKeyDown, true);

    // CSS-level selection prevention (belt-and-suspenders)
    document.body.style.userSelect = 'none';
    document.body.style.webkitUserSelect = 'none';
  }

  // -------------------------------------------------------------------------
  // PUBLIC API
  // -------------------------------------------------------------------------
  return { init };

})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => AntiCheat.init());
