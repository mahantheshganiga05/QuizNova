/**
 * QuizNova — Quiz Engine (quiz-engine.js)
 * =========================================
 * Handles quiz state, option selection, timer ring countdown,
 * question palette sync, keyboard shortcuts, and submit dialogs.
 */

'use strict';

// ── CONFIG ───────────────────────────────────────────────────
const QUIZ_CONFIG = {
  attemptId:        window.QUIZ_ATTEMPT_ID,
  totalQuestions:   window.QUIZ_TOTAL_QUESTIONS,
  timeLimitSeconds: window.QUIZ_TIME_LIMIT_SECONDS || window.QUIZ_TIME_LIMIT_SECS,
  maxViolations:    window.QUIZ_MAX_VIOLATIONS,
  csrfToken:        window.CSRF_TOKEN,
};

// ── STATE ────────────────────────────────────────────────────
const state = {
  currentIndex: 0,            // 0-indexed
  answers: {},                // { aqId: selectedIndex }
  bookmarks: new Set(),       // Set of aqId strings
  timerSeconds: window.QUIZ_SECONDS_REMAINING || QUIZ_CONFIG.timeLimitSeconds,
  timerInterval: null,
  isSubmitting: false,
};

// ── INIT ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  _restoreInitialState();
  _initTimer();
  _updateUI();
  _attachEvents();
});

function _restoreInitialState() {
  const slides = document.querySelectorAll('.question-slide');
  slides.forEach(slide => {
    const aqId = slide.dataset.aqId;
    const selected = slide.dataset.selected;
    const bookmarked = slide.dataset.bookmarked === '1';

    if (selected !== '-1' && selected !== 'null' && selected !== '' && selected !== undefined) {
      state.answers[aqId] = parseInt(selected);
    }

    if (bookmarked) {
      state.bookmarks.add(aqId);
    }
  });

  // Check window.EXISTING_ANSWERS
  if (window.EXISTING_ANSWERS) {
    for (const [aqId, sel] of Object.entries(window.EXISTING_ANSWERS)) {
      if (sel !== -1 && sel !== null) {
        state.answers[aqId] = parseInt(sel);
      }
    }
  }
}

// ── NAVIGATION ───────────────────────────────────────────────
function showQuestion(index) {
  if (index < 0 || index >= QUIZ_CONFIG.totalQuestions) return;

  const slides = document.querySelectorAll('.question-slide');
  slides.forEach((slide, i) => {
    if (i === index) {
      slide.style.display = 'flex';
      slide.classList.add('active');
    } else {
      slide.style.display = 'none';
      slide.classList.remove('active');
    }
  });

  state.currentIndex = index;
  _updateUI();
}

function nextQuestion() {
  if (state.currentIndex < QUIZ_CONFIG.totalQuestions - 1) {
    showQuestion(state.currentIndex + 1);
  }
}

function prevQuestion() {
  if (state.currentIndex > 0) {
    showQuestion(state.currentIndex - 1);
  }
}

// ── OPTION SELECTION ─────────────────────────────────────────
function selectOption(slide, optionIndex) {
  const aqId = slide.dataset.aqId;
  const options = slide.querySelectorAll('.option');

  options.forEach((opt, idx) => {
    if (idx === optionIndex) {
      opt.classList.add('selected');
      opt.setAttribute('aria-checked', 'true');
    } else {
      opt.classList.remove('selected');
      opt.setAttribute('aria-checked', 'false');
    }
  });

  slide.dataset.selected = optionIndex;
  state.answers[aqId] = optionIndex;

  _saveAnswer(aqId, optionIndex);
  _updateUI();
}

async function _saveAnswer(aqId, selectedIndex) {
  try {
    await fetch(`/api/v1/quiz/${QUIZ_CONFIG.attemptId}/save-answer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': QUIZ_CONFIG.csrfToken,
      },
      body: JSON.stringify({
        attempt_question_id: parseInt(aqId),
        selected_index: selectedIndex,
      }),
    });
  } catch (err) {
    console.warn('Answer background save notice:', err);
  }
}

// ── BOOKMARK ─────────────────────────────────────────────────
function toggleBookmark(index) {
  const slide = document.getElementById(`slide-${index}`);
  if (!slide) return;

  const aqId = slide.dataset.aqId;
  const isBookmarked = state.bookmarks.has(aqId);
  const btn = slide.querySelector('.bookmark-btn');

  if (isBookmarked) {
    state.bookmarks.delete(aqId);
    slide.dataset.bookmarked = '0';
    if (btn) {
      btn.classList.remove('bookmarked');
      btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>`;
    }
  } else {
    state.bookmarks.add(aqId);
    slide.dataset.bookmarked = '1';
    if (btn) {
      btn.classList.add('bookmarked');
      btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>`;
    }
  }

  _saveBookmark(aqId, !isBookmarked);
  _updateUI();
}

async function _saveBookmark(aqId, isBookmarked) {
  try {
    await fetch(`/api/v1/quiz/${QUIZ_CONFIG.attemptId}/bookmark`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': QUIZ_CONFIG.csrfToken,
      },
      body: JSON.stringify({ attempt_question_id: parseInt(aqId), is_bookmarked: isBookmarked }),
    });
  } catch (err) {
    console.warn('Bookmark background sync notice:', err);
  }
}

// ── TIMER ────────────────────────────────────────────────────
function _initTimer() {
  _renderTimer(state.timerSeconds);
  state.timerInterval = setInterval(() => {
    state.timerSeconds--;
    _renderTimer(state.timerSeconds);

    if (state.timerSeconds <= 0) {
      clearInterval(state.timerInterval);
      _autoSubmit();
    }
  }, 1000);
}

function _renderTimer(seconds) {
  if (seconds < 0) seconds = 0;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  const topText = document.getElementById('quiz-timer-text');
  const largeText = document.getElementById('timer-large-text');

  if (topText) topText.textContent = formatted;
  if (largeText) largeText.textContent = formatted;

  // Ring Dash Offset calculation (r=18 top, r=38 large)
  const topCircle = document.getElementById('timer-ring-circle');
  if (topCircle && QUIZ_CONFIG.timeLimitSeconds > 0) {
    const pct = seconds / QUIZ_CONFIG.timeLimitSeconds;
    const offset = 113.1 * (1 - pct);
    topCircle.style.strokeDashoffset = offset;
    topCircle.style.stroke = seconds <= 60 ? 'var(--error)' : seconds <= 300 ? 'var(--warning)' : 'var(--brand-purple)';
  }

  const largeCircle = document.getElementById('timer-ring-large');
  if (largeCircle && QUIZ_CONFIG.timeLimitSeconds > 0) {
    const pct = seconds / QUIZ_CONFIG.timeLimitSeconds;
    const offset = 238.8 * (1 - pct);
    largeCircle.style.strokeDashoffset = offset;
    largeCircle.style.stroke = seconds <= 60 ? 'var(--error)' : seconds <= 300 ? 'var(--warning)' : 'var(--brand-purple)';
  }
}

// ── UI REFRESH ───────────────────────────────────────────────
function _updateUI() {
  // Progress bar
  const total = QUIZ_CONFIG.totalQuestions;
  const currentNum = state.currentIndex + 1;
  const progressText = document.getElementById('quiz-progress-text');
  const progressFill = document.getElementById('quiz-progress-fill');
  const progressPct = document.getElementById('quiz-progress-pct');
  const paletteCounter = document.getElementById('palette-counter-text');

  const pctVal = Math.round((currentNum / total) * 100);

  // Count actually attempted/answered questions
  const answeredCount = Object.keys(state.answers).filter(k => state.answers[k] !== undefined && state.answers[k] !== null && state.answers[k] !== -1).length;
  const pendingCount = total - answeredCount;

  if (progressText) progressText.textContent = `Question ${currentNum} of ${total}`;
  if (progressFill) progressFill.style.width = `${pctVal}%`;
  if (progressPct) progressPct.textContent = `${pctVal}% Completed`;
  if (paletteCounter) paletteCounter.textContent = `${answeredCount} / ${total} Attempted`;

  // Mobile Sticky Progress Bar Update
  const mobCurrent = document.getElementById('mobile-sp-current');
  const mobAnswered = document.getElementById('mobile-sp-answered');
  const mobPending = document.getElementById('mobile-sp-pending');

  if (mobCurrent) mobCurrent.textContent = `Q ${currentNum} / ${total}`;
  if (mobAnswered) mobAnswered.textContent = `✓ ${answeredCount} Answered`;
  if (mobPending) mobPending.textContent = `• ${pendingCount} Pending`;

  // Collapsible Palette Header Summary Update
  const palSubCur = document.getElementById('pal-sub-cur');
  const palSubAns = document.getElementById('pal-sub-ans');
  const palSubPen = document.getElementById('pal-sub-pen');

  if (palSubCur) palSubCur.textContent = `${currentNum}/${total}`;
  if (palSubAns) palSubAns.textContent = `${answeredCount} Answered`;
  if (palSubPen) palSubPen.textContent = `${pendingCount} Pending`;

  // Palette Buttons
  const paletteBtns = document.querySelectorAll('.palette-btn');
  paletteBtns.forEach((btn, i) => {
    const order = parseInt(btn.dataset.order);
    const slide = document.getElementById(`slide-${order}`);
    const aqId = slide ? slide.dataset.aqId : null;

    btn.className = 'palette-btn';

    if (order === state.currentIndex) {
      btn.classList.add('current');
    } else if (aqId && state.bookmarks.has(aqId)) {
      btn.classList.add('bookmarked');
    } else if (aqId && state.answers[aqId] !== undefined && state.answers[aqId] !== null) {
      btn.classList.add('answered');
    }
  });
}

// ── CONFIRM & SUBMIT ─────────────────────────────────────────
function openConfirmModal() {
  const answeredCount = Object.keys(state.answers).length;
  const total = QUIZ_CONFIG.totalQuestions;
  const unansweredCount = total - answeredCount;
  const bookmarkedCount = state.bookmarks.size;

  const csAns = document.getElementById('cs-answered');
  const csUnans = document.getElementById('cs-unanswered');
  const csBook = document.getElementById('cs-bookmarked');

  if (csAns) csAns.textContent = answeredCount;
  if (csUnans) csUnans.textContent = unansweredCount;
  if (csBook) csBook.textContent = bookmarkedCount;

  const modal = document.getElementById('confirm-overlay');
  if (modal) modal.classList.add('active');
}

function _autoSubmit() {
  if (state.isSubmitting) return;
  state.isSubmitting = true;

  const form = document.getElementById('final-submit-form');
  if (form) {
    const autoInput = document.createElement('input');
    autoInput.type = 'hidden';
    autoInput.name = 'auto_submitted';
    autoInput.value = 'true';
    form.appendChild(autoInput);
    form.submit();
  }
}

// ── EVENTS ───────────────────────────────────────────────────
function _attachEvents() {
  // Option clicks
  document.addEventListener('click', (e) => {
    const optionBtn = e.target.closest('.option');
    if (optionBtn) {
      const slide = optionBtn.closest('.question-slide');
      const optIdx = parseInt(optionBtn.dataset.optionIndex);
      if (slide && !isNaN(optIdx)) {
        selectOption(slide, optIdx);
      }
      return;
    }

    const bookmarkBtn = e.target.closest('.bookmark-btn');
    if (bookmarkBtn) {
      const order = parseInt(bookmarkBtn.dataset.order);
      if (!isNaN(order)) {
        toggleBookmark(order);
      }
      return;
    }

    const paletteBtn = e.target.closest('.palette-btn');
    if (paletteBtn) {
      const order = parseInt(paletteBtn.dataset.order);
      if (!isNaN(order)) {
        showQuestion(order);
        // Scroll question card into view smoothly on mobile
        const slide = document.getElementById(`slide-${order}`);
        if (slide) slide.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      return;
    }

    const collapseToggle = e.target.closest('#palette-collapse-toggle');
    if (collapseToggle) {
      const card = document.getElementById('palette-panel-card');
      if (card) {
        card.classList.toggle('expanded');
        const isExpanded = card.classList.contains('expanded');
        collapseToggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
      }
      return;
    }

    const actionBtn = e.target.closest('[data-action]');
    if (actionBtn) {
      const action = actionBtn.dataset.action;
      if (action === 'prev') prevQuestion();
      if (action === 'next') nextQuestion();
      if (action === 'confirm-submit') openConfirmModal();
    }
  });

  // Keyboard Shortcuts (A, B, C, D or 1, 2, 3, 4, Arrow Left/Right)
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    if (e.key === 'ArrowRight') nextQuestion();
    if (e.key === 'ArrowLeft') prevQuestion();

    const slide = document.getElementById(`slide-${state.currentIndex}`);
    if (!slide) return;

    if (e.key === 'a' || e.key === 'A' || e.key === '1') selectOption(slide, 0);
    if (e.key === 'b' || e.key === 'B' || e.key === '2') selectOption(slide, 1);
    if (e.key === 'c' || e.key === 'C' || e.key === '3') selectOption(slide, 2);
    if (e.key === 'd' || e.key === 'D' || e.key === '4') selectOption(slide, 3);
  });
}

// ── GLOBAL EXPORTS ───────────────────────────────────────────
window.QuizEngine = {
  showQuestion,
  nextQuestion,
  prevQuestion,
  openConfirmModal,
};
