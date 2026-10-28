<div align="center">

# 🗳️ Online Voting System

**A secure, anonymous, production-ready online voting platform**
built with FastAPI · SQLAlchemy · MySQL · Vanilla JS

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## 📌 Overview

This project is a full-stack online voting system that prioritises **ballot anonymity** and **duplicate-vote prevention** at the database architecture level — not just at the application layer.

The core privacy principle: **no single database query can ever link a voter's identity to their candidate choice.**

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 **Secure Auth** | bcrypt password hashing + JWT Bearer tokens |
| 🎭 **Ballot Anonymity** | Identity and vote data live in completely separate tables |
| 🚫 **Duplicate Prevention** | DB-level `UNIQUE` constraint — not just app logic |
| ⚡ **Async API** | FastAPI + aiomysql for high-throughput, low-latency responses |
| 🛡️ **Admin Controls** | Admins can create, open, and close elections |
| 📊 **Live Results** | Real-time vote tallies without exposing voter identities |
| 🌐 **Responsive UI** | Vanilla HTML/CSS/JS — no framework bloat |

---

## 🏗️ Architecture

### Privacy Firewall — The Core Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      IDENTITY LAYER                              │
│   ┌──────────┐         ┌──────────────┐                         │
│   │  users   │────────▶│  votes_cast  │  WHO voted in election Y │
│   │          │         │  (receipt)   │  ← NO candidate_id here  │
│   └──────────┘         └──────┬───────┘                         │
└──────────────────────────────-│-────────────────────────────────┘
                                │ election_id
┌───────────────────────────────│-────────────────────────────────┐
│                    BALLOT LAYER                 │                │
│                          ┌────▼──────┐          │               │
│                          │ elections │          │               │
│                          └────┬──────┘          │               │
│                               │                 │               │
│                        ┌──────▼──────┐          │               │
│                        │ candidates  │          │               │
│                        └──────┬──────┘          │               │
│                               │                 │               │
│                        ┌──────▼──────┐          │               │
│                        │vote_tallies │  HOW MANY votes ← NO user_id │
│                        └─────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

**Key invariant:** `VoteCast` records *that* a user voted. `VoteTally` records *what* was voted for. These two tables share no column that can join them.

---

## 📁 Project Structure

```
voting_system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py          # Async engine, session factory, get_db()
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # SQLAlchemy DeclarativeBase
│   │   │   ├── user.py          # User model (identity only)
│   │   │   ├── election.py      # Election + Candidate models
│   │   │   └── vote.py          # VoteCast + VoteTally (privacy core)
│   │   ├── api/                 # FastAPI routers (auth, elections, votes)
│   │   │   └── __init__.py
│   │   └── core/
│   │       ├── __init__.py
│   │       └── config.py        # Pydantic settings from .env
│   └── requirements.txt
├── frontend/                    # HTML / CSS / JS UI
├── .gitignore
└── README.md
```

---

## 🗄️ Database Schema

### `users` table
| Column | Type | Notes |
|--------|------|-------|
| `id` | VARCHAR(36) PK | UUID — non-guessable |
| `username` | VARCHAR(50) UNIQUE | Login handle |
| `email` | VARCHAR(255) UNIQUE | Account recovery only |
| `hashed_password` | VARCHAR(255) | bcrypt — raw passwords never stored |
| `is_active` | BOOL | Soft-disable without deletion |
| `is_admin` | BOOL | Can create/close elections |
| `created_at` | DATETIME | UTC |

### `elections` table
| Column | Type | Notes |
|--------|------|-------|
| `id` | VARCHAR(36) PK | UUID |
| `title` | VARCHAR(200) | Ballot name |
| `is_active` | BOOL | Controls whether voting is open |
| `start_time` / `end_time` | DATETIME | Scheduling info |

### `candidates` table
| Column | Type | Notes |
|--------|------|-------|
| `id` | VARCHAR(36) PK | UUID |
| `election_id` | FK → elections | CASCADE delete |
| `name` | VARCHAR(150) | Display name |

### `votes_cast` table — *the participation receipt*
| Column | Type | Notes |
|--------|------|-------|
| `id` | VARCHAR(36) PK | |
| `user_id` | FK → users | Who voted |
| `election_id` | FK → elections | In which election |
| `voted_at` | DATETIME | Audit trail |
| *(no candidate_id)* | — | **By design** |

> 🔒 `UNIQUE(user_id, election_id)` — DB enforces one ballot per user per election.

### `vote_tallies` table — *the anonymous counter*
| Column | Type | Notes |
|--------|------|-------|
| `id` | VARCHAR(36) PK | |
| `candidate_id` | FK → candidates UNIQUE | One row per candidate |
| `vote_count` | INT | Incremented atomically |
| *(no user_id)* | — | **By design** |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MySQL 8.0+ (running locally or via Docker)
- Git

### 1. Clone the repository
```bash
git clone https://github.com/immanuelisaac/voting_system.git
cd voting_system
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
# Create a .env file in backend/ — never commit this file
cp .env.example .env   # or create it manually
```

`.env` contents:
```env
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=voting_db
SECRET_KEY=your_secret_key_here   # openssl rand -hex 32
DEBUG=True
DB_ECHO=False
```

### 5. Create the MySQL database
```sql
CREATE DATABASE voting_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Open API docs
```
http://localhost:8000/docs       ← Swagger UI
http://localhost:8000/redoc      ← ReDoc
```

---

## 🔧 Development Roadmap

| Module | Status | Description |
|--------|--------|-------------|
| **Module 1** — DB Schema | ✅ Complete | SQLAlchemy models with privacy separation |
| **Module 2** — Auth API | 🔄 In Progress | Register, Login, JWT middleware |
| **Module 3** — Voting API | ⏳ Pending | Cast vote, results endpoints |
| **Module 4** — Admin API | ⏳ Pending | Create/manage elections & candidates |
| **Module 5** — Frontend | ⏳ Pending | Responsive HTML/CSS/JS UI |

---

## 🔐 Security Considerations

- Passwords are **never stored in plaintext** — bcrypt with salt rounds
- JWT tokens expire after a configurable window (default: 60 min)
- The `SECRET_KEY` must be generated with `openssl rand -hex 32` and stored in `.env`
- `.env` is in `.gitignore` and must **never** be committed
- Vote anonymity is guaranteed at the **schema level**, not just the application level
- All DB writes use parameterised queries via SQLAlchemy (no raw SQL, no injection risk)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit with conventional commits: `git commit -m "feat: add X"`
4. Push and open a Pull Request

---

## 📄 License

MIT © [immanuelisaac](https://github.com/immanuelisaac)
