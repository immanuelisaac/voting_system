# app/main.py
# FastAPI application entry point with all routes wired up for demo.

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel, EmailStr
import uuid, bcrypt, jwt as pyjwt
from datetime import datetime, timezone, timedelta

from app.database import get_db, create_all_tables
from app.models import User, Election, Candidate, VoteCast, VoteTally
from app.core.config import settings


# ---------------------------------------------------------------------------
# Lifespan — create tables on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield

app = FastAPI(
    title="🗳️ Online Voting System API",
    description="Secure anonymous voting — Module 1 & 2 Demo",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ElectionCreate(BaseModel):
    title: str
    description: str = ""

class CandidateCreate(BaseModel):
    name: str
    description: str = ""

class VoteRequest(BaseModel):
    candidate_id: str


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(
    authorization: str = None,
    db: AsyncSession = Depends(get_db)
):
    from fastapi import Header
    raise HTTPException(status_code=401, detail="Use /auth/login to get a token")


# ---------------------------------------------------------------------------
# ✅ Health Check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "✅ Online Voting System API is running",
        "version": "0.1.0",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"database": "✅ connected", "status": "healthy"}


# ---------------------------------------------------------------------------
# 👤 Auth Routes
# ---------------------------------------------------------------------------
@app.post("/auth/register", tags=["Auth"], status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate username
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    return {"message": "✅ Registered successfully", "user_id": user.id, "username": user.username}


@app.post("/auth/login", tags=["Auth"])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_token(user.id, user.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "is_admin": user.is_admin,
    }


# ---------------------------------------------------------------------------
# 🗳️ Election Routes
# ---------------------------------------------------------------------------
@app.get("/elections", tags=["Elections"])
async def list_elections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Election))
    elections = result.scalars().all()
    return [
        {
            "id": e.id, "title": e.title,
            "description": e.description,
            "is_active": e.is_active,
            "candidate_count": len(e.candidates)
        }
        for e in elections
    ]


@app.post("/elections", tags=["Elections"], status_code=201)
async def create_election(body: ElectionCreate, db: AsyncSession = Depends(get_db)):
    election = Election(title=body.title, description=body.description, is_active=True)
    db.add(election)
    await db.flush()
    return {"message": "✅ Election created", "election_id": election.id, "title": election.title}


@app.post("/elections/{election_id}/candidates", tags=["Elections"], status_code=201)
async def add_candidate(election_id: str, body: CandidateCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    candidate = Candidate(election_id=election_id, name=body.name, description=body.description)
    db.add(candidate)
    await db.flush()

    tally = VoteTally(candidate_id=candidate.id, vote_count=0)
    db.add(tally)
    await db.flush()

    return {"message": "✅ Candidate added", "candidate_id": candidate.id, "name": candidate.name}


@app.get("/elections/{election_id}/results", tags=["Elections"])
async def get_results(election_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    results = []
    for c in election.candidates:
        tally = c.tally
        results.append({
            "candidate_id": c.id,
            "candidate": c.name,
            "votes": tally.vote_count if tally else 0
        })

    total = sum(r["votes"] for r in results)
    for r in results:
        r["percentage"] = round((r["votes"] / total * 100), 1) if total > 0 else 0

    results.sort(key=lambda x: x["votes"], reverse=True)
    return {"election": election.title, "total_votes": total, "results": results}


# ---------------------------------------------------------------------------
# 🗳️ Vote Route — the privacy core
# ---------------------------------------------------------------------------
@app.post("/elections/{election_id}/vote", tags=["Vote"])
async def cast_vote(election_id: str, body: VoteRequest, voter_username: str, db: AsyncSession = Depends(get_db)):
    # Get election
    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election or not election.is_active:
        raise HTTPException(status_code=400, detail="Election not found or not active")

    # Get voter
    result = await db.execute(select(User).where(User.username == voter_username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check duplicate vote (DB constraint catches this too)
    existing = await db.execute(
        select(VoteCast).where(VoteCast.user_id == user.id, VoteCast.election_id == election_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="⛔ You have already voted in this election")

    # Verify candidate belongs to this election
    result = await db.execute(
        select(Candidate).where(Candidate.id == body.candidate_id, Candidate.election_id == election_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found in this election")

    # 🔒 PRIVACY: Record THAT user voted (no candidate info here)
    receipt = VoteCast(user_id=user.id, election_id=election_id)
    db.add(receipt)

    # 🔒 PRIVACY: Increment tally anonymously (no user info here)
    await db.execute(
        text("UPDATE vote_tallies SET vote_count = vote_count + 1 WHERE candidate_id = :cid"),
        {"cid": body.candidate_id}
    )

    return {
        "message": "✅ Vote cast successfully! Your ballot is anonymous.",
        "election": election.title,
        "privacy_note": "Your identity is stored separately from your vote choice."
    }
