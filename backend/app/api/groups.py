"""
Groups API — CRUD for user groups, plus member management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.group import Group
from app.models.user import User

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreate(BaseModel):
    """Fields required to create a new group."""
    name: str
    description: str | None = None


class AddMemberRequest(BaseModel):
    """Request body for adding a user to a group."""
    user_id: int


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.get("/")
def list_groups(db: Session = Depends(get_db)):
    """Return all groups with their member count. Used to populate the Groups table."""
    groups = db.query(Group).order_by(Group.created_at.desc()).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "member_count": len(g.members),
            "created_at": g.created_at,
        }
        for g in groups
    ]


@router.post("/", status_code=201)
def create_group(body: GroupCreate, db: Session = Depends(get_db)):
    """Create a new group."""
    existing = db.query(Group).filter(Group.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"A group named '{body.name}' already exists.")

    group = Group(name=body.name, description=body.description)
    db.add(group)
    db.commit()
    db.refresh(group)

    return {"id": group.id, "name": group.name, "description": group.description, "created_at": group.created_at}


@router.get("/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    """Return a single group with its full member list."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "created_at": group.created_at,
        "members": [
            {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
            for u in group.members
        ],
    }


@router.post("/{group_id}/members", status_code=201)
def add_member(group_id: int, body: AddMemberRequest, db: Session = Depends(get_db)):
    """
    Add a user to a group. SQLAlchemy handles inserting the row into
    the user_groups join table automatically via the `members` relationship.
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user in group.members:
        raise HTTPException(status_code=409, detail="User is already a member of this group.")

    group.members.append(user)
    db.commit()

    return {"group_id": group_id, "user_id": body.user_id, "member_count": len(group.members)}


@router.delete("/{group_id}/members/{user_id}", status_code=204)
def remove_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    """Remove a user from a group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user not in group.members:
        raise HTTPException(status_code=404, detail="User is not a member of this group.")

    group.members.remove(user)
    db.commit()
