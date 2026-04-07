"""
Users API — CRUD for user accounts.

Password hashing is intentionally omitted here — that belongs in the auth
layer (Phase 3). For now, hashed_password is stored as an empty string and
users are created without credentials.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """Fields required to create a new user."""
    email: EmailStr
    name: str
    role: UserRole = UserRole.viewer


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    """Return all users. The frontend uses this to populate the Users table."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/", status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    Returns 409 if the email is already registered (email must be unique).
    """
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"A user with email '{body.email}' already exists.")

    user = User(email=body.email, name=body.name, role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "created_at": user.created_at}


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Return a single user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }
