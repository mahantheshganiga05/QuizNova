# QuizNova

> **Test Your Knowledge. Ignite Your Potential.**

A production-ready, AI-ready, dark-themed quiz platform built with Flask + MySQL.

---

## Features

- 12 knowledge categories, 48 subcategories, 1200+ questions
- Randomized questions and options per attempt
- Fullscreen quiz with anti-cheat enforcement
- Auto-generated verifiable PDF certificates with QR codes
- Real-time leaderboard (global + category + weekly)
- Premium user dashboard with charts, achievements, activity timeline
- Admin panel: CRUD, CSV bulk import, analytics, data export
- GSAP + AOS animations, glassmorphism design, fully responsive
- Flask-Login session management + bcrypt password hashing
- AI-ready architecture (Gemini/OpenAI stubs built-in)

---

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Node.js (optional — for tooling)

### Setup

```bash
# 1. Clone and enter directory
git clone <repo-url> QuizNova
cd QuizNova

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your MySQL credentials and secret key

# 5. Create database
mysql -u root -p -e "CREATE DATABASE quiznova CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p quiznova < database/schema.sql

# 6. Seed data
python database/seed.py

# 7. Run development server
flask run
```

Open http://localhost:5000 in your browser.

Default admin credentials (from seed):
- Email: `admin@quiznova.com`
- Password: `Admin@QuizNova1`

---

## Project Structure

```
QuizNova/
├── app.py              # Flask app factory
├── config.py           # Configuration classes
├── requirements.txt    # Python dependencies
├── .env                # Environment variables
├── database/           # SQL schema + seed script
├── models/             # SQLAlchemy models
├── routes/             # Flask blueprints
├── services/           # Business logic layer
├── utils/              # Helpers, validators, decorators
├── templates/          # Jinja2 HTML templates
├── static/             # CSS, JS, images, icons
└── docs/               # Full project documentation
```

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for the complete folder structure.

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](docs/PRD.md) | Product Requirements Document |
| [SRS.md](docs/SRS.md) | Software Requirements Specification |
| [DATABASE.md](docs/DATABASE.md) | Database schema, ER relationships, SQL |
| [UI_GUIDE.md](docs/UI_GUIDE.md) | Design system, color tokens, components |
| [API_GUIDE.md](docs/API_GUIDE.md) | REST API contracts for all endpoints |
| [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | Roadmap, coding standards, deployment |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3 (custom), JavaScript ES6 |
| Animations | GSAP 3.12, AOS 2.3 |
| Charts | Chart.js 4.4 |
| Backend | Python 3.11, Flask 3.0 |
| Database | MySQL 8.0, SQLAlchemy ORM |
| Auth | Flask-Login, bcrypt |
| PDF | ReportLab |
| QR Code | qrcode[pil] |
| Deployment | Gunicorn + Nginx + Ubuntu 22.04 |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
