# VoteSecure — Online Voting System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A **secure, anonymous online voting platform** built with FastAPI, SQLAlchemy, and a modern glassmorphism UI.
Ballot anonymity is enforced at the **database schema level** — no join path exists between a voter and their vote choice.

---

## Live Features

- **User Auth** — Register & login with bcrypt-hashed passwords + JWT tokens
- **Elections** — Create elections with multiple candidates
- **Anonymous Voting** — Privacy firewall at the DB level; duplicate votes blocked
- **Live Results** — Real-time animated bar charts
- **Modern UI** — Dark glassmorphism single-page app (no framework, pure HTML/CSS/JS)
- **SQLite Demo Mode** — Runs instantly with zero database setup

---

## Architecture — Privacy Firewall

```
┌─────────────────────────────────────────────────────────┐
│                   PRIVACY FIREWALL                      │
│                                                         │
│  users        vote_casts       elections   candidates   │
│  ┌──────┐    ┌──────────┐     ┌────────┐  ┌─────────┐  │
│  │  id  │───▶│ user_id  │     │  id    │  │   id    │  │
│  │ name │    │election_id│◀───│ title  │  │  name   │  │
│  │ pass │    └──────────┘     └────────┘  └────┬────┘  │
│  └──────┘    (WHO voted)      (WHAT election)  │       │
│                                                │       │
│              vote_tallies ◀────────────────────┘       │
│              ┌───────────┐                             │
│              │candidate_id│  (ANONYMOUS counts)         │
│              │vote_count │                             │
│              └───────────┘                             │
│                                                         │
│  ✅ No join path: users ↔ candidates                    │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | Python 3.11 + FastAPI + Uvicorn |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Database** | MySQL 8 (production) / SQLite (demo) |
| **Auth** | bcrypt + JWT (PyJWT) |
| **Frontend** | Vanilla HTML + CSS + JavaScript |
| **Fonts** | Google Fonts — Inter |

---

## Project Structure

```
voting_system/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── base.py        # Declarative base + UUID eager init
│   │   │   ├── user.py        # User identity model
│   │   │   ├── election.py    # Election + Candidate models
│   │   │   └── vote.py        # VoteCast + VoteTally (privacy-separated)
│   │   ├── core/
│   │   │   └── config.py      # Pydantic settings (.env)
│   │   ├── database.py        # Async engine + session factory
│   │   └── main.py            # FastAPI app + all routes
│   ├── test_models.py         # 11 offline unit tests (all passing)
│   └── requirements.txt
└── frontend/
    └── index.html             # Complete SPA — auth, voting, results
```

---

## Quick Start (Demo — no MySQL needed)

```bash
# 1. Clone
git clone git@github.com:immanuelisaac/voting_system.git
cd voting_system/backend

# 2. Install dependencies
pip install -r requirements.txt
pip install aiosqlite PyJWT

# 3. Run (SQLite demo mode)
$env:USE_SQLITE="True"   # PowerShell
python -m uvicorn app.main:app --port 8000 --reload

# 4. Open the UI
# Double-click: voting_system/frontend/index.html
```

**API Docs:** http://localhost:8000/docs  
**UI:** Open `frontend/index.html` directly in your browser

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | DB connectivity check |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login → returns JWT |
| `GET` | `/elections` | List all elections |
| `POST` | `/elections` | Create election (admin) |
| `POST` | `/elections/{id}/candidates` | Add candidate |
| `POST` | `/elections/{id}/vote` | Cast anonymous vote |
| `GET` | `/elections/{id}/results` | Live results with % |

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| username | VARCHAR | Unique |
| email | VARCHAR | Unique |
| hashed_password | TEXT | bcrypt |
| is_admin | BOOL | Default false |
| is_active | BOOL | Default true |

### `vote_casts` — WHO voted (no candidate info)
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | FK→users | |
| election_id | FK→elections | |
| — | — | **UNIQUE(user_id, election_id)** |

### `vote_tallies` — Anonymous counts (no user info)
| Column | Type | Notes |
|---|---|---|
| candidate_id | FK→candidates | |
| vote_count | INT | Incremented atomically |

---

## Test Results

```
11 tests passed in < 1s (offline, no DB required)
✓ Model imports
✓ Table names
✓ Privacy invariants (no user→candidate join)
✓ Unique constraints
✓ UUID defaults at instantiation time
```

---

## Development Roadmap

- [x] Module 1 — Database schema & privacy firewall
- [x] Module 2 — FastAPI REST API (auth + voting + results)
- [x] Module 3 — Frontend SPA (glassmorphism dark UI)
- [ ] Module 4 — JWT middleware (protected routes)
- [ ] Module 5 — Admin panel (election management)
- [ ] Module 6 — Production MySQL deployment

---

## License

MIT — see [LICENSE](LICENSE)